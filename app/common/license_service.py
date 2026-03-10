"""
License Service - 离线授权验证服务
=====================================

安全特性：
1. 机器码绑定 - 基于硬件信息生成唯一机器码
2. 时间防篡改 - 检测系统时间回拨
3. 授权码签名 - HMAC-SHA256 签名验证
4. 分散存储 - 注册表 + 本地文件双重存储
5. 隐蔽逻辑 - 关键数据加密存储

授权码格式：
    Base64(Header) + "." + Base64(Payload) + "." + Base64(Signature)

Payload 字段：
    - email: 授权邮箱
    - machine_code: 绑定的机器码
    - salt: 随机盐值
    - start_date: 授权起始日期 (YYYY-MM-DD)
    - duration_days: 授权天数 (0 表示永久)
    - timestamp: 生成时间戳
"""

import hashlib
import hmac
import json
import base64
import os
import subprocess
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class LicenseInfo:
    """授权信息数据类"""
    email: str
    machine_code: str
    start_date: str
    duration_days: int
    is_valid: bool = False
    is_expired: bool = False
    days_remaining: int = 0
    
    @property
    def is_permanent(self) -> bool:
        return self.duration_days == 0
    
    @property
    def end_date(self) -> Optional[str]:
        if self.is_permanent:
            return None
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = start + timedelta(days=self.duration_days)
        return end.strftime("%Y-%m-%d")


class LicenseService:
    """授权服务核心类"""
    
    # 密钥（实际部署时应从安全的地方获取或编译时注入）
    SECRET_KEY = b"FastX-Gui-Secret-Key-2024-v1.0"
    
    # 存储路径
    REGISTRY_KEY = r"SOFTWARE\FastXGui\License"
    REGISTRY_VALUE_NAME = "LicenseData"
    TIME_ANCHOR_VALUE = "TimeAnchor"
    
    # 本地文件存储（作为备份和交叉验证）
    LOCAL_DATA_DIR = Path.home() / ".fastxgui"
    LICENSE_FILE = LOCAL_DATA_DIR / ".license.dat"
    TIME_FILE = LOCAL_DATA_DIR / ".time_anchor.dat"
    
    # 时间容差（秒）- 允许的时间回拨容差
    TIME_TOLERANCE = 300  # 5分钟
    
    def __init__(self):
        self._ensure_data_dir()
        self._cached_license: Optional[LicenseInfo] = None
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        self.LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
        # 设置隐藏属性（Windows）
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ["attrib", "+H", str(self.LOCAL_DATA_DIR)],
                    check=False, capture_output=True
                )
            except Exception:
                pass
    
    @staticmethod
    def get_machine_code() -> str:
        """
        生成机器码 - 基于硬件信息
        
        Returns:
            32位十六进制字符串
        """
        machine_info = []
        
        try:
            # Windows 平台获取硬件信息
            if sys.platform == "win32":
                try:
                    # 抑制 wmi 库的 SyntaxWarning
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", category=SyntaxWarning)
                        import wmi
                    c = wmi.WMI()
                    
                    # CPU 序列号
                    for cpu in c.Win32_Processor():
                        if cpu.ProcessorId:
                            machine_info.append(cpu.ProcessorId.strip())
                            break
                    
                    # 主板序列号
                    for board in c.Win32_BaseBoard():
                        if board.SerialNumber:
                            machine_info.append(board.SerialNumber.strip())
                            break
                    
                    # 硬盘序列号
                    for disk in c.Win32_DiskDrive():
                        if disk.SerialNumber:
                            machine_info.append(disk.SerialNumber.strip())
                            break
                except ImportError:
                    # wmi 模块未安装，使用备用方案
                    logger.debug("wmi 模块未安装，使用备用机器码生成方案")
                except Exception as e:
                    logger.debug(f"获取 WMI 信息失败: {e}")
                        
        except Exception as e:
            logger.warning(f"获取硬件信息失败: {e}")
        
        # 如果 WMI 信息获取失败，使用备用方案
        if not machine_info or all(not x for x in machine_info):
            import platform
            # 使用系统环境变量组合作为备选
            machine_info = [
                platform.node(),  # 计算机名
                platform.machine(),  # 架构
                os.environ.get("COMPUTERNAME", ""),
                os.environ.get("USERNAME", ""),
                str(os.path.getctime(sys.executable) if os.path.exists(sys.executable) else ""),
            ]
        
        # 生成哈希
        raw_string = "|".join(filter(None, machine_info))
        return hashlib.sha256(raw_string.encode()).hexdigest()[:32].upper()
    
    def _verify_signature(self, header_b64: str, payload_b64: str, signature: str) -> bool:
        """验证 HMAC 签名"""
        # 签名是对 header_b64.payload_b64 字符串进行 HMAC
        message = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(
            self.SECRET_KEY,
            message.encode(),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
        return hmac.compare_digest(expected_sig_b64, signature)
    
    def validate_license_code(self, license_code: str, email: str) -> Tuple[bool, str]:
        """
        验证授权码
        
        Args:
            license_code: 授权码
            email: 用户邮箱
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 解析授权码
            parts = license_code.split(".")
            if len(parts) != 3:
                return False, "授权码格式错误"
            
            header_b64 = parts[0]
            payload_b64 = parts[1]
            signature = parts[2]
            
            # 解码
            header = json.loads(base64.urlsafe_b64decode(header_b64 + "=="))
            payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
            
            # 验证签名
            if not self._verify_signature(header_b64, payload_b64, signature):
                return False, "授权码签名无效"
            
            # 验证邮箱
            if payload.get("email", "").lower() != email.lower():
                return False, "邮箱不匹配"
            
            # 验证机器码
            current_machine = self.get_machine_code()
            if payload.get("machine_code") != current_machine:
                return False, "机器码不匹配，授权码只能在本机使用"
            
            # 验证时间
            start_date = datetime.strptime(payload["start_date"], "%Y-%m-%d")
            duration_days = payload["duration_days"]
            
            if duration_days > 0:  # 非永久授权
                end_date = start_date + timedelta(days=duration_days)
                if datetime.now() > end_date:
                    return False, "授权已过期"
            
            return True, "验证成功"
            
        except Exception as e:
            logger.error(f"验证授权码失败: {e}")
            return False, f"验证失败: {str(e)}"
    
    def check_time_tampering(self) -> Tuple[bool, str]:
        """
        检测时间篡改
        
        Returns:
            (是否通过检测, 错误信息)
        """
        try:
            current_time = datetime.now()
            
            # 读取时间锚点
            last_run_time = self._get_last_run_time()
            first_run_time = self._get_first_run_time()
            
            # 首次运行，初始化时间锚点
            if first_run_time is None:
                self._update_time_anchor(current_time)
                return True, "首次运行"
            
            # 检查时间回拨
            if last_run_time is not None:
                time_diff = (last_run_time - current_time).total_seconds()
                if time_diff > self.TIME_TOLERANCE:
                    return False, "检测到系统时间被回拨，请检查系统时间设置"
            
            # 检查是否在授权起始日期之前
            license_info = self.get_license_info()
            if license_info and license_info.start_date:
                start = datetime.strptime(license_info.start_date, "%Y-%m-%d")
                if current_time.date() < start.date():
                    return False, "当前日期早于授权起始日期"
            
            # 更新时间锚点
            self._update_time_anchor(current_time)
            return True, "时间检测通过"
            
        except Exception as e:
            logger.error(f"时间检测失败: {e}")
            return False, f"时间检测失败: {str(e)}"
    
    def _get_last_run_time(self) -> Optional[datetime]:
        """获取上次运行时间"""
        try:
            # 尝试从注册表读取
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_KEY, 0, 
                               winreg.KEY_READ) as key:
                time_data, _ = winreg.QueryValueEx(key, self.TIME_ANCHOR_VALUE)
                data = json.loads(self._decrypt_data(time_data))
                return datetime.fromisoformat(data["last_run"])
        except Exception:
            pass
        
        try:
            # 尝试从文件读取
            if self.TIME_FILE.exists():
                data = json.loads(self._decrypt_data(self.TIME_FILE.read_text()))
                return datetime.fromisoformat(data["last_run"])
        except Exception:
            pass
        
        return None
    
    def _get_first_run_time(self) -> Optional[datetime]:
        """获取首次运行时间"""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_KEY, 0,
                               winreg.KEY_READ) as key:
                time_data, _ = winreg.QueryValueEx(key, self.TIME_ANCHOR_VALUE)
                data = json.loads(self._decrypt_data(time_data))
                return datetime.fromisoformat(data["first_run"])
        except Exception:
            pass
        return None
    
    def _update_time_anchor(self, current_time: datetime):
        """更新时间锚点"""
        try:
            first_run = self._get_first_run_time() or current_time
            data = {
                "first_run": first_run.isoformat(),
                "last_run": current_time.isoformat(),
                "check_count": 0
            }
            encrypted = self._encrypt_data(json.dumps(data))
            
            # 写入注册表
            try:
                import winreg
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_KEY) as key:
                    winreg.SetValueEx(key, self.TIME_ANCHOR_VALUE, 0, winreg.REG_SZ, encrypted)
            except Exception as e:
                logger.warning(f"写入注册表失败: {e}")
            
            # 写入文件（备份）
            self.TIME_FILE.write_text(encrypted)
            
        except Exception as e:
            logger.error(f"更新时间锚点失败: {e}")
    
    def _encrypt_data(self, data: str) -> str:
        """简单加密数据（XOR + Base64）"""
        key = hashlib.sha256(self.SECRET_KEY).digest()
        data_bytes = data.encode()
        encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(data_bytes)])
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def _decrypt_data(self, encrypted: str) -> str:
        """解密数据"""
        key = hashlib.sha256(self.SECRET_KEY).digest()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted + "==")
        decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted_bytes)])
        return decrypted.decode()
    
    def save_license(self, license_code: str, email: str):
        """保存授权信息"""
        try:
            data = {
                "license_code": license_code,
                "email": email,
                "activated_at": datetime.now().isoformat()
            }
            encrypted = self._encrypt_data(json.dumps(data))
            
            # 写入注册表
            try:
                import winreg
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_KEY) as key:
                    winreg.SetValueEx(key, self.REGISTRY_VALUE_NAME, 0, winreg.REG_SZ, encrypted)
            except Exception as e:
                logger.warning(f"写入注册表失败: {e}")
            
            # 写入文件
            self.LICENSE_FILE.write_text(encrypted)
            
        except Exception as e:
            logger.error(f"保存授权失败: {e}")
            raise
    
    def load_license(self) -> Optional[Tuple[str, str]]:
        """加载授权信息"""
        try:
            # 优先从注册表读取
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_KEY, 0,
                                   winreg.KEY_READ) as key:
                    encrypted, _ = winreg.QueryValueEx(key, self.REGISTRY_VALUE_NAME)
                    data = json.loads(self._decrypt_data(encrypted))
                    return data["license_code"], data["email"]
            except Exception:
                pass
            
            # 从文件读取
            if self.LICENSE_FILE.exists():
                data = json.loads(self._decrypt_data(self.LICENSE_FILE.read_text()))
                return data["license_code"], data["email"]
                
        except Exception as e:
            logger.error(f"加载授权失败: {e}")
        
        return None
    
    def get_license_info(self) -> Optional[LicenseInfo]:
        """获取授权信息"""
        if self._cached_license:
            return self._cached_license
        
        license_data = self.load_license()
        if not license_data:
            return None
        
        license_code, email = license_data
        
        try:
            # 解析授权码
            parts = license_code.split(".")
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
            
            # 计算剩余天数
            start_date = datetime.strptime(payload["start_date"], "%Y-%m-%d")
            duration_days = payload["duration_days"]
            
            if duration_days == 0:
                days_remaining = -1  # 永久
                is_expired = False
            else:
                end_date = start_date + timedelta(days=duration_days)
                days_remaining = (end_date - datetime.now()).days
                is_expired = days_remaining < 0
            
            # 验证有效性
            is_valid, _ = self.validate_license_code(license_code, email)
            
            info = LicenseInfo(
                email=email,
                machine_code=payload["machine_code"],
                start_date=payload["start_date"],
                duration_days=duration_days,
                is_valid=is_valid and not is_expired,
                is_expired=is_expired,
                days_remaining=max(0, days_remaining) if days_remaining > 0 else -1
            )
            
            self._cached_license = info
            return info
            
        except Exception as e:
            logger.error(f"解析授权信息失败: {e}")
            return None
    
    def validate(self, license_code: str, email: str) -> bool:
        """
        完整的验证流程
        
        Args:
            license_code: 授权码
            email: 邮箱
            
        Returns:
            是否验证通过
        """
        # 1. 验证授权码格式和签名
        is_valid, msg = self.validate_license_code(license_code, email)
        if not is_valid:
            logger.warning(f"授权码验证失败: {msg}")
            return False
        
        # 2. 检测时间篡改
        time_ok, time_msg = self.check_time_tampering()
        if not time_ok:
            logger.warning(f"时间检测失败: {time_msg}")
            return False
        
        # 3. 保存授权
        try:
            self.save_license(license_code, email)
            self._cached_license = None  # 清除缓存
        except Exception as e:
            logger.error(f"保存授权失败: {e}")
            return False
        
        return True
    
    def is_activated(self) -> bool:
        """检查是否已激活"""
        license_info = self.get_license_info()
        if not license_info:
            return False
        
        # 验证时间
        time_ok, _ = self.check_time_tampering()
        if not time_ok:
            return False
        
        return license_info.is_valid
    
    def clear_license(self):
        """清除授权（用于测试或注销）"""
        try:
            import winreg
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_KEY)
            except Exception:
                pass
        except Exception:
            pass
        
        try:
            if self.LICENSE_FILE.exists():
                self.LICENSE_FILE.unlink()
            if self.TIME_FILE.exists():
                self.TIME_FILE.unlink()
        except Exception:
            pass
        
        self._cached_license = None


# 单例实例
_license_service: Optional[LicenseService] = None


def get_license_service() -> LicenseService:
    """获取授权服务单例"""
    global _license_service
    if _license_service is None:
        _license_service = LicenseService()
    return _license_service
