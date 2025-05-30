# NetBrain MCP 安全认证机制设计

本文档详细描述NetBrain MCP系统的安全认证机制设计，包括当前已实现的安全措施和未来计划的安全增强方案。

## 1. 当前安全实现状态

### 1.1 已实现的安全措施

NetBrain MCP系统当前已实现以下安全措施：

#### 1.1.1 日志记录和审计
- **操作日志记录**：完整记录所有MCP工具调用和系统操作
- **连接日志**：记录设备连接、断开和命令执行活动
- **错误日志**：记录系统错误和异常事件
- **UTF-8编码支持**：JsonFormatter确保日志中文字符正确处理

#### 1.1.2 输入验证和类型检查
- **工具参数验证**：MCP工具的输入参数类型验证
- **设备信息验证**：设备添加和更新时的数据格式验证
- **命令注入防护**：基本的命令参数清理

#### 1.1.3 连接安全
- **SSH连接**：优先使用SSH协议连接设备
- **Telnet备用**：支持Telnet作为备用连接方式
- **连接超时**：设置合理的连接和命令执行超时时间
- **自动重连**：连接断开时的自动重连机制

#### 1.1.4 日志脱敏
- **密码脱敏**：避免在日志中记录明文密码
- **敏感信息标识**：明确识别和处理敏感数据字段

### 1.2 当前安全限制

#### 1.2.1 凭据存储安全
- **明文存储**：设备凭据当前以明文形式存储在JSON文件中
- **文件权限**：依赖操作系统文件权限保护数据文件
- **无加密传输**：本地文件读写无额外加密层

#### 1.2.2 访问控制
- **无认证机制**：MCP服务器当前无用户认证要求
- **无授权检查**：所有连接的客户端均有完全访问权限
- **无会话管理**：缺乏会话超时和管理机制

## 2. 安全需求分析

### 2.1 威胁模型

NetBrain MCP系统面临以下潜在安全威胁：

#### 2.1.1 数据安全威胁
1. **凭据泄露**：设备登录凭据存储在明文文件中，存在泄露风险
2. **配置数据窃取**：设备配置信息可能包含敏感网络架构信息
3. **日志信息泄露**：操作日志可能包含敏感的网络操作信息

#### 2.1.2 访问控制威胁
1. **未授权访问**：任何能连接到MCP服务器的客户端都能执行所有操作
2. **权限提升**：缺乏细粒度权限控制机制
3. **会话劫持**：缺乏会话管理和验证机制

#### 2.1.3 网络安全威胁
1. **中间人攻击**：设备连接可能被拦截或篡改
2. **网络扫描滥用**：网络扫描功能可能被恶意使用
3. **设备连接滥用**：设备连接功能可能被用于非授权访问

#### 2.1.4 系统安全威胁
1. **文件系统访问**：数据文件可能被本地用户非授权访问
2. **进程劫持**：MCP服务器进程可能被恶意程序控制
3. **资源耗尽**：恶意客户端可能消耗系统资源

### 2.2 安全要求

基于威胁模型，系统需要满足以下安全要求：

#### 2.2.1 数据保护要求
- **凭据加密存储**：设备凭据必须加密存储
- **敏感数据标识**：明确标识和保护敏感数据
- **数据传输保护**：保护数据在传输过程中的安全性

#### 2.2.2 访问控制要求
- **身份认证**：验证客户端身份
- **权限授权**：基于角色的细粒度权限控制
- **会话管理**：安全的会话创建、维护和销毁

#### 2.2.3 网络安全要求
- **通信加密**：保护MCP通信通道
- **设备连接安全**：安全的设备连接和命令执行
- **网络隔离**：适当的网络访问限制

## 3. 安全实现计划

### 3.1 优先级分类

#### 3.1.1 高优先级（安全关键）
1. **凭据加密存储**：立即实施
2. **基础访问控制**：API密钥认证
3. **通信安全**：HTTPS/WSS支持

#### 3.1.2 中优先级（安全重要）
1. **细粒度权限控制**：基于角色的访问控制
2. **审计增强**：安全事件审计
3. **会话管理**：会话超时和管理

#### 3.1.3 低优先级（安全增强）
1. **高级认证**：OAuth2集成
2. **安全监控**：实时安全监控
3. **加密通信**：端到端加密

### 3.2 凭据加密存储方案

#### 3.2.1 加密算法选择
使用AES-256-GCM算法进行数据加密：

```python
# 在network_devices.py中增强DeviceCredential类
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecureCredentialStorage:
    """安全凭据存储实现"""
    
    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.environ.get('NETBRAIN_MASTER_KEY')
        if not self.master_key:
            raise ValueError("Master encryption key not provided")
        
        # 派生加密密钥
        salt = b'netbrain_mcp_salt'  # 生产环境应使用随机盐
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        self.encryption_key = kdf.derive(self.master_key.encode())
    
    def encrypt_credential(self, credential_data: str) -> str:
        """加密凭据数据"""
        if not credential_data:
            return ""
        
        # 生成随机IV
        iv = os.urandom(12)
        
        # 加密数据
        aesgcm = AESGCM(self.encryption_key)
        ciphertext = aesgcm.encrypt(iv, credential_data.encode('utf-8'), None)
        
        # 返回IV+密文的base64编码
        encrypted_data = base64.b64encode(iv + ciphertext).decode('utf-8')
        return f"aes256gcm:{encrypted_data}"
    
    def decrypt_credential(self, encrypted_data: str) -> str:
        """解密凭据数据"""
        if not encrypted_data or not encrypted_data.startswith("aes256gcm:"):
            return encrypted_data  # 向后兼容明文数据
        
        try:
            # 解析加密格式
            encrypted_content = encrypted_data[10:]  # 移除"aes256gcm:"前缀
            data = base64.b64decode(encrypted_content)
            
            # 提取IV和密文
            iv = data[:12]
            ciphertext = data[12:]
            
            # 解密数据
            aesgcm = AESGCM(self.encryption_key)
            plaintext = aesgcm.decrypt(iv, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decrypt credential: {str(e)}")
            raise ValueError("Invalid encrypted credential data")

# 增强DeviceCredential类
class DeviceCredential:
    def __init__(self, 
                 id: str = None,
                 name: str = "",
                 username: str = "", 
                 password: str = "",
                 protocol: ConnectionProtocol = ConnectionProtocol.SSH,
                 port: int = None,
                 enable_password: str = None,
                 ssh_key_file: str = None,
                 encrypted: bool = True):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.username = username
        self.protocol = protocol
        self.port = port or (22 if protocol == ConnectionProtocol.SSH else 23)
        self.ssh_key_file = ssh_key_file
        self.encrypted = encrypted
        
        # 初始化加密存储
        if encrypted:
            self._storage = SecureCredentialStorage()
            self._encrypted_password = self._storage.encrypt_credential(password) if password else ""
            self._encrypted_enable_password = self._storage.encrypt_credential(enable_password) if enable_password else ""
        else:
            self._encrypted_password = password
            self._encrypted_enable_password = enable_password
    
    @property
    def password(self) -> str:
        """获取解密后的密码"""
        if self.encrypted and self._storage:
            return self._storage.decrypt_credential(self._encrypted_password)
        return self._encrypted_password
    
    @password.setter
    def password(self, value: str):
        """设置密码（自动加密）"""
        if self.encrypted and self._storage:
            self._encrypted_password = self._storage.encrypt_credential(value)
        else:
            self._encrypted_password = value
    
    @property
    def enable_password(self) -> str:
        """获取解密后的启用密码"""
        if self.encrypted and self._storage:
            return self._storage.decrypt_credential(self._encrypted_enable_password)
        return self._encrypted_enable_password
    
    @enable_password.setter  
    def enable_password(self, value: str):
        """设置启用密码（自动加密）"""
        if self.encrypted and self._storage:
            self._encrypted_enable_password = self._storage.encrypt_credential(value)
        else:
            self._encrypted_enable_password = value
```

#### 3.2.2 密钥管理方案

**主密钥管理：**
```python
# 环境变量方式
export NETBRAIN_MASTER_KEY="your-secure-master-key"

# 配置文件方式（不推荐生产环境）
master_key = config.get('security', 'master_key')

# 密钥文件方式
with open('/secure/path/master.key', 'r') as f:
    master_key = f.read().strip()
```

**密钥轮换策略：**
```python
class KeyRotationManager:
    """密钥轮换管理器"""
    
    def __init__(self):
        self.current_key_version = 1
        self.key_versions = {}
    
    def rotate_master_key(self, new_key: str) -> bool:
        """轮换主密钥"""
        try:
            # 使用新密钥重新加密所有凭据
            old_storage = SecureCredentialStorage(self.get_current_key())
            new_storage = SecureCredentialStorage(new_key)
            
            # 重新加密过程...
            self.current_key_version += 1
            self.key_versions[self.current_key_version] = new_key
            
            return True
        except Exception as e:
            logger.error(f"Key rotation failed: {str(e)}")
            return False
```

### 3.3 API认证机制

#### 3.3.1 API密钥认证实现

```python
# 新增文件：security/api_auth.py
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class APIKeyManager:
    """API密钥管理器"""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.load_api_keys()
    
    def generate_api_key(self, name: str, permissions: List[str] = None, expires_days: int = 90) -> str:
        """生成新的API密钥"""
        # 生成32字节随机密钥
        key = secrets.token_urlsafe(32)
        
        # 计算密钥哈希用于存储
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # 设置过期时间
        expires_at = datetime.now() + timedelta(days=expires_days) if expires_days > 0 else None
        
        # 存储密钥信息
        self.api_keys[key_hash] = {
            "name": name,
            "permissions": permissions or ["read", "write"],
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "last_used": None,
            "usage_count": 0
        }
        
        self.save_api_keys()
        logger.info(f"Generated API key for: {name}")
        return key
    
    def validate_api_key(self, key: str) -> Optional[Dict[str, Any]]:
        """验证API密钥"""
        if not key:
            return None
        
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_info = self.api_keys.get(key_hash)
        
        if not key_info:
            logger.warning(f"Invalid API key attempted: {key[:8]}...")
            return None
        
        # 检查过期时间
        if key_info.get("expires_at"):
            expires_at = datetime.fromisoformat(key_info["expires_at"])
            if datetime.now() > expires_at:
                logger.warning(f"Expired API key used: {key_info['name']}")
                return None
        
        # 更新使用统计
        key_info["last_used"] = datetime.now().isoformat()
        key_info["usage_count"] += 1
        
        return key_info
    
    def revoke_api_key(self, key: str) -> bool:
        """撤销API密钥"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        if key_hash in self.api_keys:
            del self.api_keys[key_hash]
            self.save_api_keys()
            return True
        return False

# MCP服务器认证中间件
class MCPAuthMiddleware:
    """MCP认证中间件"""
    
    def __init__(self, api_key_manager: APIKeyManager):
        self.api_key_manager = api_key_manager
        self.enabled = os.environ.get('NETBRAIN_AUTH_ENABLED', 'false').lower() == 'true'
    
    def authenticate_request(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """认证请求"""
        if not self.enabled:
            return {"name": "anonymous", "permissions": ["read", "write"]}
        
        # 从请求头获取API密钥
        api_key = headers.get('Authorization', '').replace('Bearer ', '')
        if not api_key:
            api_key = headers.get('X-API-Key', '')
        
        if not api_key:
            logger.warning("No API key provided in request")
            return None
        
        return self.api_key_manager.validate_api_key(api_key)
```

#### 3.3.2 权限控制实现

```python
# 新增文件：security/permissions.py
from enum import Enum
from typing import List, Dict, Any
from functools import wraps

class Permission(Enum):
    """权限枚举"""
    # 设备管理权限
    DEVICE_READ = "device:read"
    DEVICE_WRITE = "device:write"
    DEVICE_DELETE = "device:delete"
    
    # 连接管理权限
    CONNECT_DEVICE = "connect:device"
    EXECUTE_COMMAND = "execute:command"
    
    # 拓扑发现权限
    DISCOVER_TOPOLOGY = "topology:discover"
    VIEW_TOPOLOGY = "topology:view"
    
    # 扫描权限
    SCAN_NETWORK = "scan:network"
    VIEW_SCAN_RESULTS = "scan:view"
    
    # 系统管理权限
    MANAGE_CREDENTIALS = "credentials:manage"
    MANAGE_TEMPLATES = "templates:manage"
    SYSTEM_ADMIN = "system:admin"

class Role(Enum):
    """角色枚举"""
    ADMIN = "admin"
    ENGINEER = "engineer" 
    OPERATOR = "operator"
    VIEWER = "viewer"

# 角色权限映射
ROLE_PERMISSIONS = {
    Role.ADMIN: [perm for perm in Permission],  # 管理员拥有所有权限
    Role.ENGINEER: [
        Permission.DEVICE_READ,
        Permission.DEVICE_WRITE,
        Permission.CONNECT_DEVICE,
        Permission.EXECUTE_COMMAND,
        Permission.DISCOVER_TOPOLOGY,
        Permission.VIEW_TOPOLOGY,
        Permission.SCAN_NETWORK,
        Permission.VIEW_SCAN_RESULTS,
        Permission.MANAGE_CREDENTIALS,
    ],
    Role.OPERATOR: [
        Permission.DEVICE_READ,
        Permission.CONNECT_DEVICE,
        Permission.EXECUTE_COMMAND,
        Permission.VIEW_TOPOLOGY,
        Permission.VIEW_SCAN_RESULTS,
    ],
    Role.VIEWER: [
        Permission.DEVICE_READ,
        Permission.VIEW_TOPOLOGY,
        Permission.VIEW_SCAN_RESULTS,
    ]
}

def require_permission(required_permission: Permission):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从上下文获取用户权限
            user_permissions = get_current_user_permissions()
            
            if required_permission not in user_permissions:
                logger.warning(f"Permission denied: {required_permission.value}")
                raise PermissionError(f"Insufficient permissions: {required_permission.value}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 在MCP工具中使用权限检查
@mcp.tool()
@require_permission(Permission.DEVICE_WRITE)
async def add_device(...) -> Dict[str, Any]:
    """添加设备（需要设备写权限）"""
    # 实现...

@mcp.tool()
@require_permission(Permission.SCAN_NETWORK)
async def scan_network_range(...) -> Dict[str, Any]:
    """扫描网络（需要扫描权限）"""
    # 实现...
```

### 3.4 审计日志增强

#### 3.4.1 安全事件审计

```python
# 新增文件：security/audit.py
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class AuditEventType(Enum):
    """审计事件类型"""
    # 认证事件
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout" 
    AUTH_FAILED = "auth.failed"
    API_KEY_CREATED = "auth.api_key_created"
    API_KEY_REVOKED = "auth.api_key_revoked"
    
    # 设备操作事件
    DEVICE_ADDED = "device.added"
    DEVICE_UPDATED = "device.updated"
    DEVICE_DELETED = "device.deleted"
    DEVICE_CONNECTED = "device.connected"
    DEVICE_DISCONNECTED = "device.disconnected"
    
    # 命令执行事件
    COMMAND_EXECUTED = "command.executed"
    COMMAND_FAILED = "command.failed"
    
    # 权限事件
    PERMISSION_DENIED = "permission.denied"
    ROLE_CHANGED = "permission.role_changed"
    
    # 系统事件
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    CONFIG_CHANGED = "system.config_changed"

class AuditLogger:
    """安全审计日志记录器"""
    
    def __init__(self, log_file: str = "logs/audit.log"):
        self.log_file = log_file
        self.sequence_number = 0
        
    def log_event(self, 
                  event_type: AuditEventType,
                  user_id: str = "anonymous",
                  resource: str = None,
                  action: str = None,
                  result: str = "success",
                  details: Dict[str, Any] = None,
                  client_ip: str = None) -> str:
        """记录审计事件"""
        
        self.sequence_number += 1
        timestamp = datetime.utcnow()
        
        # 构建审计记录
        audit_record = {
            "timestamp": timestamp.isoformat() + "Z",
            "sequence": self.sequence_number,
            "event_type": event_type.value,
            "user_id": user_id,
            "client_ip": client_ip,
            "resource": resource,
            "action": action,
            "result": result,
            "details": details or {},
        }
        
        # 计算记录哈希（用于完整性验证）
        record_hash = self._calculate_hash(audit_record)
        audit_record["hash"] = record_hash
        
        # 写入日志文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(audit_record, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
        
        return record_hash
    
    def _calculate_hash(self, record: Dict[str, Any]) -> str:
        """计算审计记录哈希"""
        # 创建用于哈希的记录副本（不包含hash字段）
        hash_record = {k: v for k, v in record.items() if k != "hash"}
        
        # 序列化并计算哈希
        record_str = json.dumps(hash_record, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(record_str.encode('utf-8')).hexdigest()
    
    def verify_log_integrity(self) -> bool:
        """验证审计日志完整性"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        record = json.loads(line.strip())
                        stored_hash = record.get("hash")
                        calculated_hash = self._calculate_hash(record)
                        
                        if stored_hash != calculated_hash:
                            logger.error(f"Audit log integrity violation at line {line_num}")
                            return False
            return True
        except Exception as e:
            logger.error(f"Failed to verify audit log integrity: {str(e)}")
            return False

# 全局审计日志器实例
audit_logger = AuditLogger()

# 在MCP工具中集成审计日志
@mcp.tool()
async def add_device(...) -> Dict[str, Any]:
    """添加设备"""
    user_id = get_current_user_id()
    client_ip = get_client_ip()
    
    try:
        # 执行设备添加操作
        result = device_manager.add_device(device)
        
        # 记录成功事件
        audit_logger.log_event(
            event_type=AuditEventType.DEVICE_ADDED,
            user_id=user_id,
            resource=f"device:{device.id}",
            action="add",
            result="success",
            details={"device_name": device.name, "ip_address": device.ip_address},
            client_ip=client_ip
        )
        
        return {"success": True, "device_id": result}
        
    except Exception as e:
        # 记录失败事件
        audit_logger.log_event(
            event_type=AuditEventType.DEVICE_ADDED,
            user_id=user_id,
            resource="device:unknown",
            action="add",
            result="failed",
            details={"error": str(e)},
            client_ip=client_ip
        )
        raise
```

### 3.5 通信安全增强

#### 3.5.1 HTTPS/WSS支持计划

```python
# 在server.py中添加SSL支持
import ssl
from pathlib import Path

class SecureServerConfig:
    """安全服务器配置"""
    
    def __init__(self):
        self.ssl_enabled = os.environ.get('NETBRAIN_SSL_ENABLED', 'false').lower() == 'true'
        self.ssl_cert_file = os.environ.get('NETBRAIN_SSL_CERT', 'certs/server.crt')
        self.ssl_key_file = os.environ.get('NETBRAIN_SSL_KEY', 'certs/server.key')
        self.ssl_ca_file = os.environ.get('NETBRAIN_SSL_CA', 'certs/ca.crt')
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """创建SSL上下文"""
        if not self.ssl_enabled:
            return None
        
        # 创建SSL上下文
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # 加载证书和私钥
        context.load_cert_chain(self.ssl_cert_file, self.ssl_key_file)
        
        # 如果有CA证书，启用客户端证书验证
        if Path(self.ssl_ca_file).exists():
            context.load_verify_locations(self.ssl_ca_file)
            context.verify_mode = ssl.CERT_REQUIRED
        
        return context

# 启动安全服务器
def start_secure_server():
    config = SecureServerConfig()
    ssl_context = config.create_ssl_context()
    
    if ssl_context:
        logger.info("Starting secure MCP server with SSL/TLS")
        # 使用SSL上下文启动服务器
    else:
        logger.warning("Starting MCP server without SSL/TLS encryption")
        # 启动普通服务器
```

## 4. 数据保护实现

### 4.1 敏感数据分类

根据实际代码分析，系统中的敏感数据包括：

#### 4.1.1 高敏感数据
- **设备凭据**：username, password, enable_password
- **SSH私钥**：ssh_key_file内容
- **API密钥**：认证令牌和密钥

#### 4.1.2 中敏感数据
- **设备配置**：网络设备配置信息
- **网络拓扑**：网络架构和连接信息
- **日志数据**：操作日志中的敏感信息

#### 4.1.3 低敏感数据
- **设备元数据**：设备名称、IP地址、型号等
- **系统状态**：系统运行状态信息
- **公共模板**：通用提示模板内容

### 4.2 数据保护策略

#### 4.2.1 存储保护
```python
# 敏感字段标识
SENSITIVE_FIELDS = {
    'password', 'enable_password', 'ssh_key', 'api_key', 
    'secret_key', 'private_key', 'token'
}

def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """脱敏敏感数据用于日志和显示"""
    masked_data = data.copy()
    
    for key, value in masked_data.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            if value:
                masked_data[key] = "***MASKED***"
    
    return masked_data
```

#### 4.2.2 传输保护
```python
def secure_data_transfer(data: Any, encryption_key: bytes) -> str:
    """安全数据传输加密"""
    # 序列化数据
    json_data = json.dumps(data, ensure_ascii=False)
    
    # 加密传输
    encrypted_data = encrypt_data(json_data, encryption_key)
    
    return encrypted_data
```

## 5. 安全配置管理

### 5.1 安全配置文件

```yaml
# config/security.yaml
security:
  # 认证配置
  authentication:
    enabled: true
    method: "api_key"  # api_key, jwt, oauth2
    api_key:
      header_name: "X-API-Key"
      require_https: false  # 生产环境设为true
      key_length: 32
      default_expiration_days: 90
    
  # 加密配置
  encryption:
    enabled: true
    algorithm: "aes-256-gcm"
    master_key_source: "environment"  # environment, file, vault
    key_rotation_days: 365
    
  # 审计配置
  audit:
    enabled: true
    log_file: "logs/audit.log"
    log_level: "INFO"
    include_sensitive_data: false
    retention_days: 365
    
  # 访问控制配置
  access_control:
    default_role: "viewer"
    session_timeout_minutes: 30
    max_failed_attempts: 5
    lockout_duration_minutes: 15
    
  # SSL/TLS配置
  ssl:
    enabled: false
    cert_file: "certs/server.crt"
    key_file: "certs/server.key"
    ca_file: "certs/ca.crt"
    require_client_cert: false
```

### 5.2 安全最佳实践

#### 5.2.1 部署安全建议
1. **文件权限**：设置适当的文件和目录权限
   ```bash
   chmod 600 data/credentials.json
   chmod 700 data/
   chmod 600 config/security.yaml
   ```

2. **环境变量**：使用环境变量管理敏感配置
   ```bash
   export NETBRAIN_MASTER_KEY="your-secure-master-key"
   export NETBRAIN_AUTH_ENABLED="true"
   export NETBRAIN_SSL_ENABLED="true"
   ```

3. **网络隔离**：部署在受保护的网络环境中
   - 使用防火墙限制访问
   - 部署在专用VLAN或子网
   - 限制出站网络连接

#### 5.2.2 运维安全建议
1. **定期安全检查**
   - 审查API密钥和权限
   - 检查审计日志异常
   - 验证加密密钥轮换
   - 更新依赖包版本

2. **监控和告警**
   - 监控异常登录尝试
   - 监控权限提升操作
   - 监控敏感数据访问
   - 设置安全事件告警

3. **备份和恢复**
   - 定期备份加密数据
   - 测试数据恢复流程
   - 保护备份数据安全
   - 记录恢复操作

## 6. 安全测试计划

### 6.1 安全测试类型

#### 6.1.1 功能安全测试
- 认证机制测试
- 权限控制测试
- 数据加密测试
- 审计日志测试

#### 6.1.2 安全漏洞测试
- 输入验证测试
- 权限绕过测试
- 数据泄露测试
- 注入攻击测试

#### 6.1.3 渗透测试
- 外部渗透测试
- 内部渗透测试
- 社会工程测试
- 物理安全测试

### 6.2 安全测试实施

```python
# tests/security/test_authentication.py
import pytest
from security.api_auth import APIKeyManager, MCPAuthMiddleware

class TestAuthentication:
    def setup_method(self):
        self.api_key_manager = APIKeyManager()
        self.auth_middleware = MCPAuthMiddleware(self.api_key_manager)
    
    def test_api_key_generation(self):
        """测试API密钥生成"""
        key = self.api_key_manager.generate_api_key("test_user")
        assert len(key) > 0
        assert self.api_key_manager.validate_api_key(key) is not None
    
    def test_invalid_api_key(self):
        """测试无效API密钥"""
        assert self.api_key_manager.validate_api_key("invalid_key") is None
    
    def test_expired_api_key(self):
        """测试过期API密钥"""
        # 实现过期密钥测试...
        pass

# tests/security/test_encryption.py
class TestEncryption:
    def test_credential_encryption(self):
        """测试凭据加密"""
        from security.encryption import SecureCredentialStorage
        
        storage = SecureCredentialStorage("test_key")
        original_password = "secret123"
        
        # 加密
        encrypted = storage.encrypt_credential(original_password)
        assert encrypted != original_password
        assert encrypted.startswith("aes256gcm:")
        
        # 解密
        decrypted = storage.decrypt_credential(encrypted)
        assert decrypted == original_password
```

## 7. 实施时间表

### 7.1 短期实施（1-2个月）
- [x] **基础日志审计**：已实现完整的操作日志记录
- [ ] **凭据加密存储**：实现AES-256-GCM加密
- [ ] **API密钥认证**：基础API密钥认证机制
- [ ] **基础权限控制**：实现角色基础权限检查

### 7.2 中期实施（3-6个月）
- [ ] **SSL/TLS支持**：HTTPS和WSS加密通信
- [ ] **细粒度权限**：完整的RBAC权限系统
- [ ] **安全审计增强**：完整的安全事件审计
- [ ] **密钥轮换**：自动密钥轮换机制

### 7.3 长期实施（6-12个月）
- [ ] **OAuth2集成**：企业身份认证集成
- [ ] **安全监控**：实时安全监控和告警
- [ ] **端到端加密**：客户端到服务器端到端加密
- [ ] **安全认证**：第三方安全认证和合规

---

NetBrain MCP系统的安全设计兼顾了当前实际实现状态和未来安全增强需求。通过分阶段实施安全措施，系统将逐步达到企业级安全标准，为网络运维提供安全可靠的AI驱动平台。 