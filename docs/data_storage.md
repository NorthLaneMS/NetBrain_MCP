# NetBrain MCP 数据存储设计

本文档详细描述NetBrain MCP系统的数据存储设计，包括实际的数据存储方案、数据模型、缓存策略和数据操作方法。

## 1. 数据存储架构概述

### 1.1 存储方案选择

NetBrain MCP系统采用**JSON文件存储**作为主要数据持久化方案，具有以下特点：

- **轻量级部署**：无需额外的数据库服务器
- **简单维护**：人类可读的JSON格式，便于调试和维护
- **快速启动**：无需数据库初始化和配置
- **跨平台兼容**：完全兼容Windows、Linux、macOS
- **备份简单**：数据文件可直接复制备份

### 1.2 数据存储结构

```
NetBrainMCP/
├── data/                    # 主数据存储目录
│   ├── devices.json         # 设备信息存储
│   └── credentials.json     # 凭据信息存储（敏感数据）
├── resource_cache/          # 资源缓存目录
│   ├── device_*.json        # 设备资源缓存
│   ├── topology_*.json      # 拓扑资源缓存
│   └── scan_*.json          # 扫描结果缓存
├── templates/              # 模板缓存目录
│   └── *.json              # 模板元数据缓存
└── logs/                   # 日志文件目录
    ├── netbrain_mcp.log    # 应用主日志
    ├── device_connector.log # 设备连接日志
    └── audit.log           # 审计日志（安全增强）
```

## 2. 核心数据模型

### 2.1 网络设备模型

#### 2.1.1 NetworkDevice数据类

基于实际代码实现（`network_devices.py`第125-155行）：

```python
@dataclass
class NetworkDevice:
    """网络设备模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    ip_address: str = ""
    device_type: DeviceType = DeviceType.OTHER
    vendor: DeviceVendor = DeviceVendor.OTHER
    platform: str = ""  # Scrapli平台类型（重要字段）
    model: str = ""
    os_version: str = ""
    status: DeviceStatus = DeviceStatus.UNKNOWN
    location: str = ""
    credential_id: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    last_seen: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
```

#### 2.1.2 设备相关枚举

```python
class DeviceType(Enum):
    """网络设备类型枚举"""
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"
    WIRELESS_CONTROLLER = "wireless_controller"
    ACCESS_POINT = "access_point"
    OTHER = "other"

class DeviceVendor(Enum):
    """网络设备厂商枚举"""
    CISCO = "cisco"
    HUAWEI = "huawei"
    H3C = "h3c"
    JUNIPER = "juniper"
    ARISTA = "arista"
    FORTINET = "fortinet"
    CHECKPOINT = "checkpoint"
    OTHER = "other"

class DeviceStatus(Enum):
    """设备状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNREACHABLE = "unreachable"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"
```

#### 2.1.3 设备数据JSON示例

```json
{
  "device-uuid-123": {
    "id": "device-uuid-123",
    "name": "Router-01",
    "ip_address": "192.168.1.1",
    "device_type": "router",
    "vendor": "cisco",
    "platform": "cisco_iosxe",
    "model": "ISR4321",
    "os_version": "16.09.04",
    "status": "online",
    "location": "数据中心机房A",
    "credential_id": "cred-uuid-456",
    "description": "核心路由器",
    "tags": ["core", "production", "datacenter"],
    "last_seen": "2024-01-15T10:30:45.123456",
    "created_at": "2024-01-10T09:00:00.000000",
    "updated_at": "2024-01-15T10:30:45.123456",
    "custom_attributes": {
      "management_vlan": "100",
      "backup_schedule": "daily"
    }
  }
}
```

### 2.2 设备凭据模型

#### 2.2.1 DeviceCredential类

基于实际代码实现（`network_devices.py`第64-123行）：

```python
class DeviceCredential:
    """设备凭据类"""
    
    def __init__(self, 
                 id: str = None,
                 name: str = "",
                 username: str = "", 
                 password: str = "",
                 protocol: ConnectionProtocol = ConnectionProtocol.SSH,
                 port: int = None,
                 enable_password: str = None,
                 ssh_key_file: str = None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.username = username
        self.password = password
        self.protocol = protocol
        self.port = port or (22 if protocol == ConnectionProtocol.SSH else 23)
        self.enable_password = enable_password
        self.ssh_key_file = ssh_key_file
```

#### 2.2.2 连接协议枚举

```python
class ConnectionProtocol(Enum):
    """连接协议枚举"""
    SSH = "ssh"
    TELNET = "telnet"
    SNMP = "snmp"
    HTTP = "http"
    HTTPS = "https"
    NETCONF = "netconf"
```

#### 2.2.3 凭据数据JSON示例

```json
{
  "cred-uuid-456": {
    "id": "cred-uuid-456",
    "name": "思科设备SSH凭据",
    "username": "admin",
    "password": "cisco123",
    "protocol": "ssh",
    "port": 22,
    "enable_password": "enable123",
    "ssh_key_file": null
  }
}
```

**⚠️ 安全注意**: 当前凭据以明文形式存储，生产环境中应实施加密存储。

## 3. 数据管理器实现

### 3.1 DeviceManager类

基于实际代码实现（`network_devices.py`第161-462行）：

#### 3.1.1 初始化和配置

```python
class DeviceManager:
    """设备管理器，负责设备的创建、查询和管理"""
    
    def __init__(self):
        self.devices: Dict[str, NetworkDevice] = {}
        self.credentials: Dict[str, DeviceCredential] = {}
        self.data_dir = "data"
        self.devices_file = os.path.join(self.data_dir, "devices.json")
        self.credentials_file = os.path.join(self.data_dir, "credentials.json")
        
        # 创建数据目录(如不存在)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载持久化数据
        self.load_data()
        
        logger.info("设备管理器初始化完成")
```

#### 3.1.2 数据持久化方法

**保存数据**：
```python
def save_data(self):
    """将设备和凭据数据保存到文件"""
    # 保存设备数据
    devices_data = {}
    for device_id, device in self.devices.items():
        devices_data[device_id] = device.to_dict()
    
    with open(self.devices_file, 'w', encoding='utf-8') as f:
        json.dump(devices_data, f, ensure_ascii=False, indent=2)
    
    # 保存凭据数据
    credentials_data = {}
    for cred_id, credential in self.credentials.items():
        cred_dict = {
            "id": credential.id,
            "name": credential.name,
            "username": credential.username,
            "password": credential.password,  # 明文存储（待加密）
            "protocol": credential.protocol.value,
            "port": credential.port,
            "enable_password": credential.enable_password,
            "ssh_key_file": credential.ssh_key_file
        }
        credentials_data[cred_id] = cred_dict
    
    with open(self.credentials_file, 'w', encoding='utf-8') as f:
        json.dump(credentials_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"数据已保存到: {self.data_dir}")
```

**加载数据**：
```python
def load_data(self):
    """从文件加载设备和凭据数据"""
    # 加载设备数据
    if os.path.exists(self.devices_file):
        try:
            with open(self.devices_file, 'r', encoding='utf-8') as f:
                devices_data = json.load(f)
            
            for device_id, device_dict in devices_data.items():
                # 转换枚举类型
                device_type = DeviceType(device_dict.get("device_type", "other"))
                vendor = DeviceVendor(device_dict.get("vendor", "other"))
                status = DeviceStatus(device_dict.get("status", "unknown"))
                
                # 转换日期时间
                created_at = datetime.fromisoformat(device_dict.get("created_at", datetime.now().isoformat()))
                updated_at = datetime.fromisoformat(device_dict.get("updated_at", datetime.now().isoformat()))
                last_seen = None
                if device_dict.get("last_seen"):
                    last_seen = datetime.fromisoformat(device_dict.get("last_seen"))
                
                # 创建设备对象
                device = NetworkDevice(
                    id=device_id,
                    name=device_dict.get("name", ""),
                    ip_address=device_dict.get("ip_address", ""),
                    device_type=device_type,
                    vendor=vendor,
                    platform=device_dict.get("platform", ""),
                    model=device_dict.get("model", ""),
                    os_version=device_dict.get("os_version", ""),
                    status=status,
                    location=device_dict.get("location", ""),
                    credential_id=device_dict.get("credential_id"),
                    description=device_dict.get("description", ""),
                    tags=device_dict.get("tags", []),
                    last_seen=last_seen,
                    created_at=created_at,
                    updated_at=updated_at,
                    custom_attributes=device_dict.get("custom_attributes", {})
                )
                self.devices[device_id] = device
            
            logger.info(f"从 {self.devices_file} 加载了 {len(self.devices)} 个设备")
        except Exception as e:
            logger.error(f"加载设备数据失败: {e}")
```

#### 3.1.3 CRUD操作

**添加设备**：
```python
def add_device(self, device: NetworkDevice) -> str:
    """添加设备"""
    self.devices[device.id] = device
    logger.info(f"设备添加成功: {device.name} ({device.ip_address})")
    self.save_data()  # 立即保存到文件
    return device.id
```

**查询设备**：
```python
def get_device(self, device_id: str) -> Optional[NetworkDevice]:
    """获取设备"""
    return self.devices.get(device_id)

def list_devices(self, 
                vendor: Optional[DeviceVendor] = None,
                device_type: Optional[DeviceType] = None,
                status: Optional[DeviceStatus] = None,
                tag: Optional[str] = None) -> List[NetworkDevice]:
    """列出设备，支持过滤条件"""
    devices = list(self.devices.values())
    
    if vendor:
        devices = [d for d in devices if d.vendor == vendor]
    
    if device_type:
        devices = [d for d in devices if d.device_type == device_type]
    
    if status:
        devices = [d for d in devices if d.status == status]
    
    if tag:
        devices = [d for d in devices if tag in d.tags]
    
    return devices
```

**更新设备**：
```python
def update_device(self, device_id: str, **kwargs) -> Optional[NetworkDevice]:
    """更新设备信息"""
    device = self.get_device(device_id)
    if not device:
        logger.warning(f"设备不存在: {device_id}")
        return None
    
    for key, value in kwargs.items():
        if hasattr(device, key):
            setattr(device, key, value)
    
    device.updated_at = datetime.now()
    logger.info(f"设备更新成功: {device.name} ({device.ip_address})")
    self.save_data()  # 保存更改
    return device
```

**删除设备**：
```python
def delete_device(self, device_id: str) -> bool:
    """删除设备"""
    if device_id in self.devices:
        device = self.devices[device_id]
        del self.devices[device_id]
        logger.info(f"设备删除成功: {device.name} ({device.ip_address})")
        self.save_data()  # 保存更改
        return True
    return False
```

## 4. 缓存系统设计

### 4.1 资源缓存机制

基于实际代码实现（`mcp_resources.py`第56-180行）：

#### 4.1.1 ResourceManager缓存实现

```python
class ResourceManager:
    """MCP资源管理器，负责资源注册和提供"""
    
    def __init__(self):
        self.resources = {}
        self.resource_patterns = {}
        self.resource_cache = {}                # 内存缓存
        self.cache_expiration = {}              # 缓存过期时间
        self.default_cache_ttl = 300            # 默认缓存5分钟
        
        # 缓存目录
        self.cache_dir = os.path.join(os.getcwd(), "resource_cache")
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
                logger.info(f"已创建资源缓存目录: {self.cache_dir}")
            except Exception as e:
                logger.warning(f"无法创建资源缓存目录: {str(e)}")
```

#### 4.1.2 双层缓存策略

**内存缓存**：
```python
async def get_resource(self, uri: str, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict[str, Any]:
    """获取资源"""
    # 检查内存缓存
    if use_cache and uri in self.resource_cache:
        # 检查缓存是否过期
        if uri in self.cache_expiration and self.cache_expiration[uri] > datetime.datetime.now():
            logger.info(f"从内存缓存获取资源: {uri}")
            return self.resource_cache[uri]
        else:
            # 缓存过期，从缓存中删除
            logger.info(f"资源缓存已过期: {uri}")
            if uri in self.resource_cache:
                del self.resource_cache[uri]
            if uri in self.cache_expiration:
                del self.cache_expiration[uri]
```

**文件缓存**：
```python
    # 从文件缓存加载
    if use_cache:
        cache_file = self._get_cache_filename(uri)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 检查缓存是否过期
                if "expiration" in cache_data:
                    expiration = datetime.datetime.fromisoformat(cache_data["expiration"])
                    if expiration > datetime.datetime.now():
                        logger.info(f"从文件缓存加载资源: {uri}")
                        self.resource_cache[uri] = cache_data["data"]
                        self.cache_expiration[uri] = expiration
                        return cache_data["data"]
            except Exception as e:
                logger.warning(f"加载资源缓存文件失败: {str(e)}")
```

**缓存写入**：
```python
    # 缓存结果
    if use_cache:
        self.resource_cache[uri] = result
        ttl = cache_ttl or self.default_cache_ttl
        expiration = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        self.cache_expiration[uri] = expiration
        
        # 保存到文件缓存
        try:
            cache_file = self._get_cache_filename(uri)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "data": result,
                    "expiration": expiration.isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存资源缓存文件失败: {str(e)}")
```

#### 4.1.3 缓存文件命名

```python
def _get_cache_filename(self, uri: str) -> str:
    """获取缓存文件名"""
    # 将URI转换为文件名安全的字符串
    safe_uri = uri.replace(':', '_').replace('/', '_').replace('.', '_').replace('\\', '_')
    return os.path.join(self.cache_dir, f"{safe_uri}.json")
```

#### 4.1.4 缓存清理机制

```python
def clear_cache(self, uri: Optional[str] = None) -> bool:
    """清除资源缓存"""
    try:
        if uri:
            if uri in self.resource_cache:
                del self.resource_cache[uri]
            if uri in self.cache_expiration:
                del self.cache_expiration[uri]
            
            # 删除文件缓存
            cache_file = self._get_cache_filename(uri)
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            logger.info(f"已清除资源缓存: {uri}")
        else:
            self.resource_cache.clear()
            self.cache_expiration.clear()
            
            # 删除所有缓存文件
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(self.cache_dir, filename))
            
            logger.info("已清除所有资源缓存")
        
        return True
    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        return False
```

### 4.2 缓存配置策略

#### 4.2.1 默认缓存时间（TTL）

```python
# 资源类型对应的缓存时间
CACHE_TTL_CONFIG = {
    "device": 300,          # 设备信息：5分钟
    "config": 600,          # 设备配置：10分钟  
    "topology": 900,        # 拓扑信息：15分钟
    "scan": 1800,           # 扫描结果：30分钟
    "system": 60,           # 系统状态：1分钟
    "credential": 3600      # 凭据信息：1小时
}
```

#### 4.2.2 缓存策略

- **即时缓存**：数据获取后立即缓存
- **延迟过期**：使用TTL控制缓存生命周期
- **主动清理**：提供手动清理接口
- **容量控制**：内存缓存大小限制（待实现）

## 5. 连接数据管理

### 5.1 连接状态存储

基于实际代码实现（`device_connector.py`第659-865行）：

#### 5.1.1 ConnectionManager实现

```python
class ConnectionManager:
    """连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, DeviceConnector] = {}
        # 连接键格式："{device_id}:{credential_id}"
    
    def _get_connection_key(self, device_id: str, credential_id: str) -> str:
        """生成连接键"""
        return f"{device_id}:{credential_id}"
```

#### 5.1.2 连接状态数据结构

```python
# 活动连接信息示例
{
    "device-123:cred-456": {
        "device_connector": ScrapliConnector实例,
        "device_info": {
            "id": "device-123",
            "name": "Router-01",
            "ip_address": "192.168.1.1"
        },
        "credential_info": {
            "id": "cred-456", 
            "username": "admin",
            "protocol": "ssh"
        },
        "connection_status": {
            "connected": True,
            "last_activity": "2024-01-15T10:30:45",
            "connection_time": "2024-01-15T10:25:30"
        }
    }
}
```

#### 5.1.3 连接查询接口

```python
def get_active_connections(self) -> List[Dict[str, Any]]:
    """获取活动连接列表"""
    connections = []
    
    for connection_key, connector in self.active_connections.items():
        device_id, credential_id = connection_key.split(':', 1)
        
        connection_info = {
            "device_id": device_id,
            "credential_id": credential_id,
            "device_name": connector.device.name,
            "device_ip": connector.device.ip_address,
            "connected": connector.connected,
            "last_activity": connector.last_activity.isoformat() if connector.last_activity else None,
            "connection_key": connection_key
        }
        connections.append(connection_info)
    
    return connections
```

## 6. 日志数据管理

### 6.1 日志存储结构

#### 6.1.1 日志文件分类

**应用主日志**（`logs/netbrain_mcp.log`）：
```
2024-01-15 10:30:45,123 - netbrain_mcp - INFO - MCP服务器已启动
2024-01-15 10:31:02,456 - network_devices - INFO - 设备添加成功: Router-01 (192.168.1.1)
2024-01-15 10:31:15,789 - mcp_resources - INFO - 从缓存获取资源: device/device-123
```

**设备连接日志**（`logs/device_connector.log`）：
```
2024-01-15 10:32:00,123 - device_connector - INFO - 正在通过Scrapli连接到设备: Router-01 (192.168.1.1)
2024-01-15 10:32:03,456 - device_connector - INFO - 已成功连接到设备: Router-01 (192.168.1.1)
2024-01-15 10:32:10,789 - device_connector - INFO - 命令 'show version' 在设备 Router-01 上执行成功
```

**审计日志**（`logs/audit.log`，安全增强功能）：
```json
{"timestamp": "2024-01-15T10:30:45.123Z", "event_type": "device.added", "user_id": "admin", "resource": "device:123", "action": "add", "result": "success"}
{"timestamp": "2024-01-15T10:32:10.789Z", "event_type": "command.executed", "user_id": "admin", "resource": "device:123", "details": {"command": "show version"}}
```

#### 6.1.2 日志格式化

基于实际代码实现（所有模块的JsonFormatter）：

```python
class JsonFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
        
    def format(self, record):
        log_record = super().format(record)
        return log_record.encode('utf-8', errors='replace').decode('utf-8')

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)

# 设置所有处理器使用UTF-8编码格式化
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(JsonFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
```

## 7. 数据备份和恢复

### 7.1 数据备份策略

#### 7.1.1 手动备份

```bash
# 备份核心数据文件
cp -r data/ backup/data_$(date +%Y%m%d_%H%M%S)/

# 备份缓存数据（可选）
cp -r resource_cache/ backup/cache_$(date +%Y%m%d_%H%M%S)/

# 备份日志文件
cp -r logs/ backup/logs_$(date +%Y%m%d_%H%M%S)/
```

#### 7.1.2 自动备份脚本

```python
# backup.py - 数据备份脚本
import os
import shutil
import datetime
from pathlib import Path

def backup_data():
    """执行数据备份"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backup/backup_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 备份数据文件
    if Path("data").exists():
        shutil.copytree("data", backup_dir / "data")
        print(f"数据文件已备份到: {backup_dir / 'data'}")
    
    # 备份重要日志
    if Path("logs").exists():
        shutil.copytree("logs", backup_dir / "logs")
        print(f"日志文件已备份到: {backup_dir / 'logs'}")
    
    return backup_dir

if __name__ == "__main__":
    backup_path = backup_data()
    print(f"备份完成: {backup_path}")
```

### 7.2 数据恢复

#### 7.2.1 数据恢复流程

```python
def restore_data(backup_path: str):
    """从备份恢复数据"""
    backup_dir = Path(backup_path)
    
    if not backup_dir.exists():
        raise ValueError(f"备份目录不存在: {backup_path}")
    
    # 备份当前数据（安全措施）
    current_backup = backup_data()
    print(f"当前数据已备份到: {current_backup}")
    
    try:
        # 恢复数据文件
        if (backup_dir / "data").exists():
            if Path("data").exists():
                shutil.rmtree("data")
            shutil.copytree(backup_dir / "data", "data")
            print("数据文件恢复完成")
        
        # 重新加载数据到内存
        device_manager.load_data()
        print("数据已重新加载到内存")
        
    except Exception as e:
        print(f"恢复失败: {str(e)}")
        raise
```

## 8. 性能优化

### 8.1 数据访问优化

#### 8.1.1 内存索引

```python
class OptimizedDeviceManager(DeviceManager):
    """优化的设备管理器"""
    
    def __init__(self):
        super().__init__()
        self._ip_index = {}     # IP地址索引
        self._name_index = {}   # 设备名称索引
        self._vendor_index = {} # 厂商索引
        self._build_indexes()
    
    def _build_indexes(self):
        """构建索引"""
        for device_id, device in self.devices.items():
            # IP地址索引
            self._ip_index[device.ip_address] = device_id
            
            # 名称索引
            self._name_index[device.name.lower()] = device_id
            
            # 厂商索引
            vendor = device.vendor.value
            if vendor not in self._vendor_index:
                self._vendor_index[vendor] = []
            self._vendor_index[vendor].append(device_id)
    
    def get_device_by_ip(self, ip_address: str) -> Optional[NetworkDevice]:
        """通过IP地址快速查找设备"""
        device_id = self._ip_index.get(ip_address)
        return self.devices.get(device_id) if device_id else None
```

#### 8.1.2 批量操作优化

```python
def bulk_add_devices(self, devices: List[NetworkDevice]) -> List[str]:
    """批量添加设备（减少I/O操作）"""
    device_ids = []
    
    for device in devices:
        self.devices[device.id] = device
        device_ids.append(device.id)
        logger.info(f"设备添加到内存: {device.name}")
    
    # 一次性保存所有更改
    self.save_data()
    logger.info(f"批量添加 {len(devices)} 个设备完成")
    
    return device_ids
```

### 8.2 缓存优化

#### 8.2.1 预加载策略

```python
async def preload_common_resources(self):
    """预加载常用资源"""
    common_resources = [
        "system/status",
        "credentials", 
        "topology/statistics"
    ]
    
    for uri in common_resources:
        try:
            await self.get_resource(uri, use_cache=True)
            logger.info(f"预加载资源: {uri}")
        except Exception as e:
            logger.warning(f"预加载资源失败: {uri}, {str(e)}")
```

#### 8.2.2 智能缓存清理

```python
def cleanup_expired_cache(self):
    """清理过期缓存"""
    now = datetime.datetime.now()
    expired_uris = []
    
    for uri, expiration in self.cache_expiration.items():
        if expiration <= now:
            expired_uris.append(uri)
    
    for uri in expired_uris:
        self.clear_cache(uri)
    
    logger.info(f"清理了 {len(expired_uris)} 个过期缓存项")
```

## 9. 数据迁移

### 9.1 版本升级迁移

#### 9.1.1 数据格式版本管理

```python
DATA_FORMAT_VERSION = "1.0"

def check_data_format_version():
    """检查数据格式版本"""
    version_file = Path("data/version.json")
    
    if not version_file.exists():
        # 首次运行，创建版本文件
        create_version_file()
        return True
    
    with open(version_file, 'r') as f:
        version_data = json.load(f)
    
    current_version = version_data.get("version", "0.0")
    
    if current_version != DATA_FORMAT_VERSION:
        logger.info(f"检测到数据格式升级: {current_version} -> {DATA_FORMAT_VERSION}")
        migrate_data(current_version, DATA_FORMAT_VERSION)
        update_version_file()
    
    return True
```

#### 9.1.2 数据迁移处理

```python
def migrate_data(from_version: str, to_version: str):
    """执行数据迁移"""
    logger.info(f"开始数据迁移: {from_version} -> {to_version}")
    
    # 备份原始数据
    backup_path = backup_data()
    logger.info(f"原始数据已备份到: {backup_path}")
    
    try:
        if from_version == "0.9" and to_version == "1.0":
            migrate_0_9_to_1_0()
        # 添加其他版本迁移逻辑
        
        logger.info("数据迁移完成")
        
    except Exception as e:
        logger.error(f"数据迁移失败: {str(e)}")
        raise

def migrate_0_9_to_1_0():
    """0.9版本到1.0版本的迁移"""
    # 示例：添加platform字段
    for device in device_manager.devices.values():
        if not hasattr(device, 'platform') or not device.platform:
            # 根据vendor自动推断platform
            if device.vendor == DeviceVendor.CISCO:
                device.platform = "cisco_iosxe"
            elif device.vendor == DeviceVendor.HUAWEI:
                device.platform = "huawei_vrp"
            # 添加其他厂商映射
    
    # 保存迁移后的数据
    device_manager.save_data()
```

## 10. 监控和维护

### 10.1 数据健康检查

```python
def health_check():
    """数据健康检查"""
    issues = []
    
    # 检查数据文件完整性
    if not Path("data/devices.json").exists():
        issues.append("设备数据文件缺失")
    
    if not Path("data/credentials.json").exists():
        issues.append("凭据数据文件缺失")
    
    # 检查数据一致性
    for device in device_manager.devices.values():
        if device.credential_id and not device_manager.get_credential(device.credential_id):
            issues.append(f"设备 {device.name} 引用的凭据不存在: {device.credential_id}")
    
    # 检查缓存目录
    if not Path("resource_cache").exists():
        issues.append("资源缓存目录缺失")
    
    if issues:
        logger.warning(f"发现 {len(issues)} 个数据问题:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("数据健康检查通过")
    
    return len(issues) == 0
```

### 10.2 存储空间管理

```python
def get_storage_usage():
    """获取存储使用情况"""
    def get_dir_size(path):
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total += os.path.getsize(filepath)
        return total
    
    usage = {
        "data": get_dir_size("data") if Path("data").exists() else 0,
        "cache": get_dir_size("resource_cache") if Path("resource_cache").exists() else 0,
        "logs": get_dir_size("logs") if Path("logs").exists() else 0,
        "templates": get_dir_size("templates") if Path("templates").exists() else 0
    }
    
    total = sum(usage.values())
    
    logger.info(f"存储使用情况 (总计: {total / 1024 / 1024:.2f} MB):")
    for category, size in usage.items():
        logger.info(f"  {category}: {size / 1024 / 1024:.2f} MB")
    
    return usage
```

## 11. 总结

NetBrain MCP的数据存储设计采用了轻量级、高效的JSON文件存储方案，具有以下特点：

### 11.1 设计优势

- **简单可靠**：JSON格式人类可读，便于维护和调试
- **无依赖性**：无需额外的数据库服务器
- **跨平台**：完全兼容各种操作系统
- **快速部署**：零配置即可使用
- **易于备份**：简单的文件复制即可备份

### 11.2 性能特性

- **双层缓存**：内存+文件双层缓存机制
- **智能过期**：基于TTL的缓存过期策略
- **批量操作**：支持批量数据操作以减少I/O
- **索引优化**：内存索引提高查询性能

### 11.3 扩展能力

- **版本迁移**：完整的数据格式升级迁移机制
- **健康检查**：数据完整性和一致性检查
- **监控告警**：存储使用情况监控
- **安全增强**：计划实施数据加密存储

这种数据存储设计很好地平衡了简单性、性能和可维护性，为NetBrain MCP系统提供了稳定可靠的数据持久化基础。 