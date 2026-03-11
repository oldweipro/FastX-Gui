# FastX-Gui 授权系统技术文档

## 目录

1. [系统概述](#系统概述)
2. [激活码结构](#激活码结构)
3. [本地存储](#本地存储)
4. [注册表存储](#注册表存储)
5. [验证流程](#验证流程)
6. [管理员权限](#管理员权限)
7. [安全机制](#安全机制)
8. [非法场景防护](#非法场景防护)
9. [API 参考](#api-参考)

---

## 系统概述

FastX-Gui 采用**离线授权验证系统**，具有以下特性：

| 特性 | 说明 |
|------|------|
| 机器码绑定 | 基于硬件信息生成唯一机器码 |
| 时间防篡改 | 检测系统时间回拨 |
| 授权码签名 | HMAC-SHA256 签名验证 |
| 分散存储 | 注册表 + 本地文件双重存储 |
| 数据加密 | XOR + Base64 加密存储敏感数据 |

### 核心组件

```
app/common/license_service.py    # 授权服务核心类
app/view/register_window.py      # 登录/注册界面
app/view/main_window.py          # 用户信息对话框 + 隐藏管理界面
scripts/license_generator.py     # 命令行授权码生成工具
```

---

## 激活码结构

### 格式定义

```
激活码 = Base64(Header) + "." + Base64(Payload) + "." + Base64(Signature)
```

### Header 结构

```json
{
    "alg": "HS256",
    "typ": "FXG"
}
```

| 字段 | 说明 |
|------|------|
| alg | 签名算法：HS256 (HMAC-SHA256) |
| typ | 类型标识：FXG (FastX-Gui) |

### Payload 结构

```json
{
    "email": "user@example.com",
    "machine_code": "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6",
    "salt": "a1b2c3d4e5f6g7h8",
    "start_date": "2024-01-01",
    "duration_days": 365,
    "timestamp": "2024-01-01T10:30:00.000000",
    "version": "1.0"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| email | string | 授权邮箱（小写） |
| machine_code | string | 绑定的机器码，"GENERAL" 表示通用授权 |
| salt | string | 随机盐值（16位十六进制） |
| start_date | string | 授权起始日期 (YYYY-MM-DD) |
| duration_days | int | 授权天数，0 表示永久授权 |
| timestamp | string | 生成时间戳 (ISO 8601) |
| version | string | 版本号 |

### 签名算法

```
message = Base64(Header) + "." + Base64(Payload)
signature = HMAC-SHA256(message, SECRET_KEY)
```

**密钥**：`FastX-Gui-Secret-Key-2024-v1.0`

### 示例激活码

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkZYRyJ9.eyJlbWFpbCI6IjAxOTc0MDU3NEBxcS5jb20iLCJtYWNoaW5lX2NvZGUiOiJHRU5FUkFMIiwic2FsdCI6ImExYjJjM2Q0ZTVmNmc3aDgiLCJzdGFydF9kYXRlIjoiMjAyNC0wMS0wMSIsImR1cmF0aW9uX2RheXMiOjM2NSwidGltZXN0YW1wIjoiMjAyNC0wMS0wMVQxMDozMDowMC4wMDAwMDAiLCJ2ZXJzaW9uIjoiMS4wIn0.a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

---

## 本地存储

### 存储路径

所有用户数据统一存储在用户目录下的 `.fastxgui` 文件夹中：

```
Windows: C:\Users\<用户名>\.fastxgui\
macOS:   /Users/<用户名>/.fastxgui/
Linux:   /home/<用户名>/.fastxgui/
```

### 统一路径配置

路径配置统一在 `app/common/paths.py` 中管理：

```python
from app.common.paths import AppPaths

# 用户数据目录
AppPaths.USER_DATA_DIR      # ~/.fastxgui/

# 授权相关文件
AppPaths.LICENSE_FILE       # ~/.fastxgui/.license.dat
AppPaths.TIME_ANCHOR_FILE   # ~/.fastxgui/.time_anchor.dat
AppPaths.ADMIN_DATA_FILE    # ~/.fastxgui/.admin.dat
AppPaths.AUDIT_LOG_FILE     # ~/.fastxgui/.audit.dat

# 配置和数据库
AppPaths.CONFIG_FILE        # ~/.fastxgui/config.json
AppPaths.DATABASE_FILE      # ~/.fastxgui/fastx.db

# 其他目录
AppPaths.LOG_DIR            # ~/.fastxgui/logs/
AppPaths.CACHE_DIR          # ~/.fastxgui/cache/
AppPaths.EXPORT_DIR         # ~/.fastxgui/exports/
```

### 目录结构

```
~/.fastxgui/
├── config.json           # 应用配置
├── fastx.db              # 数据库文件
├── .license.dat          # 授权信息
├── .time_anchor.dat      # 时间锚点
├── .admin.dat            # 管理员数据
├── .audit.dat            # 审计日志
├── logs/                 # 日志目录
├── cache/                # 缓存目录
│   └── backgrounds/      # 背景图片缓存
└── exports/              # 导出文件目录
```

### 文件列表

| 文件 | 说明 | 内容 |
|------|------|------|
| `.license.dat` | 授权信息 | 加密的授权码 + 邮箱 + 激活时间 |
| `.time_anchor.dat` | 时间锚点 | 首次运行时间 + 上次运行时间 |
| `.admin.dat` | 管理员数据 | 密码哈希 + 会话信息 |
| `.audit.dat` | 审计日志 | 操作记录（最多100条） |

### 文件加密

所有本地文件使用 **XOR + Base64** 加密：

```python
def _encrypt_data(data: str) -> str:
    key = SHA256(SECRET_KEY)
    encrypted = XOR(data_bytes, key)
    return Base64Encode(encrypted)

def _decrypt_data(encrypted: str) -> str:
    key = SHA256(SECRET_KEY)
    decrypted = XOR(Base64Decode(encrypted), key)
    return decrypted
```

### `.license.dat` 内容结构

```json
{
    "license_code": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkZYRyJ9...",
    "email": "user@example.com",
    "activated_at": "2024-01-01T10:30:00.000000"
}
```

### `.time_anchor.dat` 内容结构

```json
{
    "first_run": "2024-01-01T10:00:00.000000",
    "last_run": "2024-01-15T14:30:00.000000",
    "check_count": 0
}
```

### `.admin.dat` 内容结构

```json
{
    "token": "a1b2c3d4e5f6g7h8...",
    "created_at": "2024-01-01T10:00:00.000000",
    "machine_code": "A1B2C3D4E5F6G7H8..."
}
```

### `.audit.dat` 内容结构

```json
[
    {
        "timestamp": "2024-01-01T10:30:00.000000",
        "action": "generate_license",
        "email": "user@example.com",
        "machine_code": "A1B2C3D4...",
        "details": "类型: 365天, 起始: 2024-01-01",
        "operator_machine": "A1B2C3D4..."
    }
]
```

---

## 注册表存储

### 注册表路径

```
HKEY_CURRENT_USER\SOFTWARE\FastXGui\License
```

### 键值列表

| 键名 | 说明 | 对应文件 |
|------|------|----------|
| `LicenseData` | 授权信息 | `.license.dat` |
| `TimeAnchor` | 时间锚点 | `.time_anchor.dat` |
| `AdminAuth` | 管理员密码哈希 | 内嵌于 `.admin.dat` |
| `AdminSession` | 管理员会话 | `.admin.dat` |
| `AuditLog` | 审计日志 | `.audit.dat` |

### 存储策略

```
┌─────────────────────────────────────────────────────┐
│                    双重存储策略                      │
├─────────────────────────────────────────────────────┤
│  写入时：                                           │
│  1. 先写入注册表                                    │
│  2. 再写入本地文件（作为备份）                       │
│                                                     │
│  读取时：                                           │
│  1. 优先从注册表读取                                │
│  2. 失败则从本地文件读取                            │
│                                                     │
│  目的：防止单点故障，增加篡改难度                    │
└─────────────────────────────────────────────────────┘
```

---

## 验证流程

### 启动验证流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      软件启动验证流程                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 加载授权信息                                                 │
│     ├─ 从注册表读取 LicenseData                                  │
│     ├─ 失败则从 .license.dat 读取                                │
│     └─ 无授权信息 → 显示登录界面                                 │
│                                                                 │
│  2. 解析授权码                                                   │
│     ├─ 分割 Header.Payload.Signature                            │
│     ├─ Base64 解码 Header 和 Payload                            │
│     └─ 验证签名完整性                                            │
│                                                                 │
│  3. 验证签名                                                     │
│     ├─ 计算 HMAC-SHA256(header_b64.payload_b64)                 │
│     └─ 比对签名是否一致                                          │
│                                                                 │
│  4. 验证机器码                                                   │
│     ├─ 获取当前机器码                                            │
│     └─ 与授权码中的 machine_code 比对                            │
│                                                                 │
│  5. 验证时间                                                     │
│     ├─ 检查时间篡改（时间锚点）                                   │
│     ├─ 检查是否在授权起始日期之后                                 │
│     └─ 检查是否已过期                                            │
│                                                                 │
│  6. 验证结果                                                     │
│     ├─ 全部通过 → 进入主界面                                     │
│     └─ 任何失败 → 显示登录界面                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 登录验证流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户登录验证流程                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 用户输入邮箱 + 激活码                                        │
│                                                                 │
│  2. 验证激活码                                                   │
│     ├─ 格式验证（三段式）                                        │
│     ├─ 签名验证                                                  │
│     ├─ 邮箱匹配验证                                              │
│     ├─ 机器码匹配验证                                            │
│     └─ 时间有效性验证                                            │
│                                                                 │
│  3. 时间篡改检测                                                 │
│     ├─ 读取时间锚点                                              │
│     ├─ 检测时间回拨（容差5分钟）                                  │
│     └─ 更新时间锚点                                              │
│                                                                 │
│  4. 保存授权                                                     │
│     ├─ 加密存储到注册表                                          │
│     └─ 加密存储到本地文件                                        │
│                                                                 │
│  5. 进入主界面                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 管理员权限

### 管理员邮箱

```python
ADMIN_EMAIL = "919740574@qq.com"
```

**硬编码在代码中，不可通过配置篡改。**

### 管理员密码

#### 密码存储

```
存储格式: salt:hash
算法: PBKDF2-SHA256
迭代次数: 100,000 次
盐长度: 16 字节（随机生成）
```

#### 密码验证流程

```
1. 用户输入密码
2. 从存储中读取 salt 和 hash
3. 使用 PBKDF2-SHA256 计算输入密码的哈希
4. 使用常量时间比较（防止时序攻击）
```

### 管理员会话

```
会话有效期: 24 小时
会话内容: token + created_at + machine_code
验证条件: 
  - 未过期
  - 机器码匹配
```

### 访问隐藏界面流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    访问隐藏界面流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 点击用户头像 → 打开用户信息对话框                            │
│                                                                 │
│  2. 快速点击标题"用户信息" 5 次（2秒内）                         │
│                                                                 │
│  3. 【第一步】验证管理员邮箱                                     │
│     ├─ 检查当前登录邮箱是否为 919740574@qq.com                   │
│     ├─ 不是 → "权限不足" + 记录审计日志                          │
│     └─ 是 → 继续                                                │
│                                                                 │
│  4. 【第二步】检查管理员会话                                     │
│     ├─ 会话有效 → 直接打开授权码生成器                           │
│     └─ 会话无效 → 继续                                          │
│                                                                 │
│  5. 【第三步】密码验证                                           │
│     ├─ 未设置密码 → 显示密码设置对话框                           │
│     └─ 已设置密码 → 显示密码验证对话框                           │
│                                                                 │
│  6. 验证成功 → 创建会话 → 打开授权码生成器                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 安全机制

### 机器码生成

```
┌─────────────────────────────────────────────────────────────────┐
│                      机器码生成逻辑                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  优先方案（Windows + WMI可用）:                                  │
│  ├─ CPU ProcessorId                                             │
│  ├─ 主板 SerialNumber                                           │
│  └─ 硬盘 SerialNumber                                           │
│                                                                 │
│  备用方案（WMI不可用）:                                          │
│  ├─ 计算机名 (platform.node)                                    │
│  ├─ 架构 (platform.machine)                                     │
│  ├─ COMPUTERNAME 环境变量                                       │
│  ├─ USERNAME 环境变量                                           │
│  └─ Python 解释器创建时间                                       │
│                                                                 │
│  最终: SHA256(硬件信息拼接)的前32位 → 大写                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 时间防篡改

```
┌─────────────────────────────────────────────────────────────────┐
│                      时间篡改检测                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  检测机制:                                                       │
│  ├─ 记录首次运行时间 (first_run)                                 │
│  ├─ 记录上次运行时间 (last_run)                                  │
│  └─ 每次启动比对当前时间                                        │
│                                                                 │
│  检测条件:                                                       │
│  ├─ 当前时间 < 上次运行时间 - 5分钟 → 时间回拨                   │
│  └─ 当前日期 < 授权起始日期 → 异常                               │
│                                                                 │
│  容差设置: 5 分钟（允许正常时间误差）                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 审计日志

```
记录的操作类型:
├─ generate_license     - 生成授权码
├─ admin_password_set   - 设置管理员密码
├─ admin_verify_success - 管理员密码验证成功
├─ admin_verify_failed  - 管理员密码验证失败
└─ admin_access_denied  - 非管理员尝试访问

保留策略: 最近 100 条记录
```

---

## 非法场景防护

### 场景 1：删除本地文件重新激活

```
┌─────────────────────────────────────────────────────────────────┐
│  攻击方式: 删除所有本地文件，用同一激活码重新激活                 │
├─────────────────────────────────────────────────────────────────┤
│  防护机制:                                                       │
│  ├─ 授权起始时间存储在激活码的 payload 中                        │
│  ├─ payload 有 HMAC 签名保护，无法篡改                           │
│  └─ 重新激活后，起始时间仍是原日期                               │
│                                                                 │
│  结果: 无法延长授权期限                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 场景 2：修改系统时间

```
┌─────────────────────────────────────────────────────────────────┐
│  攻击方式: 将系统时间调回到授权有效期内                           │
├─────────────────────────────────────────────────────────────────┤
│  防护机制:                                                       │
│  ├─ 时间锚点记录上次运行时间                                     │
│  ├─ 检测到时间回拨超过5分钟 → 拒绝                               │
│  └─ 时间锚点存储在注册表 + 文件双重存储                          │
│                                                                 │
│  结果: 时间回拨被检测，授权失效                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 场景 3：复制激活码到另一台机器

```
┌─────────────────────────────────────────────────────────────────┐
│  攻击方式: 将激活码复制到另一台电脑使用                           │
├─────────────────────────────────────────────────────────────────┤
│  防护机制:                                                       │
│  ├─ 激活码包含机器码绑定                                         │
│  ├─ 验证时比对当前机器码与激活码中的机器码                        │
│  └─ 不匹配 → "机器码不匹配，授权码只能在本机使用"                 │
│                                                                 │
│  结果: 无法跨机器使用                                            │
│                                                                 │
│  注意: GENERAL 类型激活码可跨机器使用（管理员授权时留空机器码）    │
└─────────────────────────────────────────────────────────────────┘
```

### 场景 4：篡改激活码

```
┌─────────────────────────────────────────────────────────────────┐
│  攻击方式: 修改激活码中的邮箱或有效期                             │
├─────────────────────────────────────────────────────────────────┤
│  防护机制:                                                       │
│  ├─ 激活码使用 HMAC-SHA256 签名                                  │
│  ├─ 任何修改都会导致签名验证失败                                 │
│  └─ 无法伪造有效签名（密钥未知）                                 │
│                                                                 │
│  结果: 签名验证失败，激活码无效                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 场景 5：非管理员访问隐藏界面

```
┌─────────────────────────────────────────────────────────────────┐
│  攻击方式: 非管理员用户尝试访问授权码生成器                       │
├─────────────────────────────────────────────────────────────────┤
│  防护机制:                                                       │
│  ├─ 第一层：必须登录管理员邮箱 (919740574@qq.com)                │
│  ├─ 第二层：必须设置管理员密码                                   │
│  ├─ 第三层：必须验证管理员密码                                   │
│  └─ 所有尝试记录审计日志                                         │
│                                                                 │
│  结果: 非管理员无法访问                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 场景 6：删除时间锚点文件

```
┌─────────────────────────────────────────────────────────────────┐
│  攻击方式: 删除 .time_anchor.dat 绕过时间检测                     │
├─────────────────────────────────────────────────────────────────┤
│  防护机制:                                                       │
│  ├─ 时间锚点同时存储在注册表和文件                               │
│  ├─ 删除文件后，从注册表读取                                     │
│  └─ 两者都删除 → 认为首次运行，但授权起始时间不变                 │
│                                                                 │
│  结果: 无法绕过授权时间限制                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 场景 7：暴力破解管理员密码

```
┌─────────────────────────────────────────────────────────────────┐
│  攻击方式: 多次尝试管理员密码                                     │
├─────────────────────────────────────────────────────────────────┤
│  当前防护:                                                       │
│  ├─ PBKDF2-SHA256 哈希（100,000次迭代）                          │
│  ├─ 常量时间比较（防止时序攻击）                                 │
│  └─ 审计日志记录所有失败尝试                                     │
│                                                                 │
│  建议: 可添加尝试次数限制和锁定机制                              │
└─────────────────────────────────────────────────────────────────┘
```

### 场景 8：逆向工程获取密钥

```
┌─────────────────────────────────────────────────────────────────┐
│  攻击方式: 逆向工程代码获取 SECRET_KEY                            │
├─────────────────────────────────────────────────────────────────┤
│  当前状态:                                                       │
│  ├─ 密钥硬编码在代码中                                           │
│  └─ 可被逆向工程获取                                             │
│                                                                 │
│  建议增强:                                                       │
│  ├─ 使用代码混淆                                                 │
│  ├─ 密钥分散存储                                                 │
│  ├─ 运行时动态计算密钥                                           │
│  └─ 使用硬件安全模块 (HSM)                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## API 参考

### LicenseService 类

#### 属性

```python
SECRET_KEY: bytes           # 签名密钥
REGISTRY_KEY: str           # 注册表路径
LOCAL_DATA_DIR: Path        # 本地存储目录
TIME_TOLERANCE: int         # 时间容差（秒）
ADMIN_SESSION_TIMEOUT: int  # 会话超时（秒）
PBKDF2_ITERATIONS: int      # PBKDF2 迭代次数
```

#### 核心方法

```python
# 机器码
@classmethod
def get_machine_code(cls) -> str
    """获取当前机器码（带缓存）"""

# 授权验证
def validate_license_code(license_code: str, email: str) -> Tuple[bool, str]
    """验证授权码"""

def get_license_info() -> Optional[LicenseInfo]
    """获取授权信息"""

def is_activated() -> bool
    """检查是否已激活"""

# 时间检测
def check_time_tampering() -> Tuple[bool, str]
    """检测时间篡改"""

# 授权存储
def save_license(license_code: str, email: str) -> None
    """保存授权信息"""

def load_license() -> Optional[Tuple[str, str]]
    """加载授权信息"""

def clear_license() -> None
    """清除授权"""

# 管理员密码
def has_admin_password() -> bool
    """检查是否已设置管理员密码"""

def set_admin_password(password: str) -> bool
    """设置管理员密码"""

def verify_admin_password(password: str) -> bool
    """验证管理员密码"""

# 管理员会话
def create_admin_session() -> str
    """创建管理员会话"""

def validate_admin_session() -> bool
    """验证管理员会话"""

def clear_admin_session() -> None
    """清除管理员会话"""

# 审计日志
def add_audit_log(action: str, email: str, machine_code: str, details: str) -> None
    """添加审计日志"""

def get_audit_logs(limit: int = 50) -> list
    """获取审计日志"""
```

### LicenseInfo 数据类

```python
@dataclass
class LicenseInfo:
    email: str              # 授权邮箱
    machine_code: str       # 机器码
    start_date: str         # 起始日期
    duration_days: int      # 授权天数
    is_valid: bool = False  # 是否有效
    is_expired: bool = False # 是否过期
    days_remaining: int = 0  # 剩余天数
    
    @property
    def is_permanent(self) -> bool
        """是否永久授权"""
    
    @property
    def end_date(self) -> Optional[str]
        """到期日期"""
```

### 单例获取

```python
from app.common.license_service import get_license_service

license_service = get_license_service()
```

---

## 命令行工具

### license_generator.py

```bash
# 生成限时授权（365天）
python scripts/license_generator.py --email user@example.com --machine-code A1B2C3D4... --days 365

# 生成永久授权
python scripts/license_generator.py --email user@example.com --machine-code A1B2C3D4... --permanent

# 生成通用授权（不限机器）
python scripts/license_generator.py --email user@example.com --days 365

# 指定起始日期
python scripts/license_generator.py --email user@example.com --days 365 --start-date 2024-06-01
```

### 参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| `--email` | 授权邮箱 | 是 |
| `--machine-code` | 机器码（留空为通用授权） | 否 |
| `--days` | 授权天数 | 与 --permanent 二选一 |
| `--permanent` | 永久授权 | 与 --days 二选一 |
| `--start-date` | 起始日期 (YYYY-MM-DD) | 否，默认今天 |

---

## 故障排除

### 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| "机器码不匹配" | 激活码绑定了其他机器 | 重新生成绑定当前机器码的激活码 |
| "授权已过期" | 授权期限已到 | 联系管理员续期 |
| "检测到时间回拨" | 系统时间被修改 | 恢复正确系统时间 |
| "签名无效" | 激活码被篡改 | 重新获取激活码 |
| "权限不足" | 非管理员邮箱 | 使用管理员邮箱登录 |

### 日志位置

```
控制台输出: loguru 日志
审计日志: .audit.dat / 注册表 AuditLog
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2024-01 | 初始版本，基础授权验证 |
| 1.1 | 2024-03 | 添加时间防篡改 |
| 1.2 | 2024-06 | 添加管理员密码验证 |
| 1.3 | 2024-09 | 添加审计日志 |
