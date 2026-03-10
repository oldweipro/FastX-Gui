"""
授权码生成器工具
================

用于生成合法的授权码。

使用方法：
    python license_generator.py --email user@example.com --days 365
    python license_generator.py --email user@example.com --permanent

生成的授权码格式：
    Base64(Header).Base64(Payload).Base64(Signature)

Payload 包含：
    - email: 授权邮箱
    - machine_code: 绑定的机器码（可选，不指定则生成通用授权码）
    - salt: 随机盐值
    - start_date: 授权起始日期
    - duration_days: 授权天数（0 表示永久）
"""

import argparse
import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime
from pathlib import Path


# 必须与 LicenseService 中的密钥一致
SECRET_KEY = b"FastX-Gui-Secret-Key-2024-v1.0"


def generate_machine_code():
    """提示用户输入机器码"""
    print("\n请输入用户机器码（32位十六进制字符串）：")
    print("用户可以通过以下方式获取机器码：")
    print("  1. 运行程序到注册界面")
    print("  2. 点击'复制机器码'按钮")
    print("  3. 将机器码粘贴到这里\n")
    
    while True:
        code = input("机器码（直接回车生成通用授权码）: ").strip().upper()
        if not code:
            return None
        if len(code) == 32 and all(c in "0123456789ABCDEF" for c in code):
            return code
        print("机器码格式错误，应为32位十六进制字符串")


def generate_license_code(email: str, machine_code: str = None, duration_days: int = 365, 
                         start_date: str = None) -> str:
    """
    生成授权码
    
    Args:
        email: 授权邮箱
        machine_code: 绑定的机器码（None 表示通用授权码）
        duration_days: 授权天数（0 表示永久）
        start_date: 授权起始日期（默认今天）
        
    Returns:
        授权码字符串
    """
    # Header
    header = {
        "alg": "HS256",
        "typ": "FXG"
    }
    
    # 起始日期
    if start_date is None:
        start_date = datetime.now().strftime("%Y-%m-%d")
    
    # Payload
    payload = {
        "email": email.lower().strip(),
        "machine_code": machine_code or "GENERAL",
        "salt": secrets.token_hex(8),
        "start_date": start_date,
        "duration_days": duration_days,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    }
    
    # 编码 Header 和 Payload
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    # 生成签名
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        SECRET_KEY,
        message.encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    # 组合授权码
    license_code = f"{header_b64}.{payload_b64}.{signature_b64}"
    
    return license_code


def decode_license_code(license_code: str) -> dict:
    """解码授权码（用于验证）"""
    parts = license_code.split(".")
    if len(parts) != 3:
        raise ValueError("授权码格式错误")
    
    header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    
    return {
        "header": header,
        "payload": payload,
        "signature": parts[2]
    }


def verify_license_code(license_code: str) -> bool:
    """验证授权码签名"""
    try:
        parts = license_code.split(".")
        if len(parts) != 3:
            return False
        
        message = f"{parts[0]}.{parts[1]}"
        expected_sig = hmac.new(
            SECRET_KEY,
            message.encode(),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
        
        return hmac.compare_digest(expected_sig_b64, parts[2])
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="FastX-Gui 授权码生成器")
    parser.add_argument("--email", "-e", required=True, help="授权邮箱")
    parser.add_argument("--days", "-d", type=int, default=365, help="授权天数（默认365）")
    parser.add_argument("--permanent", "-p", action="store_true", help="永久授权")
    parser.add_argument("--start-date", "-s", help="授权起始日期（YYYY-MM-DD，默认今天）")
    parser.add_argument("--machine-code", "-m", help="绑定的机器码（32位十六进制）")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("FastX-Gui 授权码生成器")
    print("=" * 60)
    
    # 交互模式
    if args.interactive:
        email = input(f"邮箱 [{args.email}]: ").strip() or args.email
        
        print("\n授权类型：")
        print("  1. 限时授权")
        print("  2. 永久授权")
        choice = input("选择 [1]: ").strip() or "1"
        
        if choice == "2":
            duration_days = 0
        else:
            days = input(f"授权天数 [{args.days}]: ").strip()
            duration_days = int(days) if days else args.days
        
        machine_code = generate_machine_code()
    else:
        email = args.email
        duration_days = 0 if args.permanent else args.days
        machine_code = args.machine_code
    
    # 生成授权码
    license_code = generate_license_code(
        email=email,
        machine_code=machine_code,
        duration_days=duration_days,
        start_date=args.start_date
    )
    
    # 验证生成的授权码
    is_valid = verify_license_code(license_code)
    decoded = decode_license_code(license_code)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("授权码生成成功！")
    print("=" * 60)
    print(f"\n授权码:\n{license_code}\n")
    print("-" * 60)
    print("授权信息：")
    print(f"  邮箱: {decoded['payload']['email']}")
    print(f"  机器码: {decoded['payload']['machine_code']}")
    print(f"  起始日期: {decoded['payload']['start_date']}")
    
    if duration_days == 0:
        print(f"  授权期限: 永久")
    else:
        print(f"  授权期限: {duration_days} 天")
        from datetime import datetime, timedelta
        start = datetime.strptime(decoded['payload']['start_date'], "%Y-%m-%d")
        end = start + timedelta(days=duration_days)
        print(f"  到期日期: {end.strftime('%Y-%m-%d')}")
    
    print(f"  签名验证: {'通过' if is_valid else '失败'}")
    print("-" * 60)
    
    # 保存到文件
    save_option = input("\n是否保存到文件？(y/n): ").strip().lower()
    if save_option == 'y':
        filename = f"license_{email.split('@')[0]}_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath = Path(filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("FastX-Gui 授权码\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"邮箱: {decoded['payload']['email']}\n")
            f.write(f"机器码: {decoded['payload']['machine_code']}\n")
            f.write(f"起始日期: {decoded['payload']['start_date']}\n")
            if duration_days == 0:
                f.write(f"授权期限: 永久\n")
            else:
                f.write(f"授权期限: {duration_days} 天\n")
                from datetime import datetime, timedelta
                start = datetime.strptime(decoded['payload']['start_date'], "%Y-%m-%d")
                end = start + timedelta(days=duration_days)
                f.write(f"到期日期: {end.strftime('%Y-%m-%d')}\n")
            f.write("\n" + "=" * 60 + "\n")
            f.write("授权码:\n")
            f.write(license_code + "\n")
            f.write("=" * 60 + "\n")
        
        print(f"已保存到: {filepath.absolute()}")
    
    print("\n请将授权码发送给用户完成激活。")


if __name__ == "__main__":
    main()
