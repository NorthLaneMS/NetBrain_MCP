# NetBrain MCP 核心模块设计

本文档详细描述NetBrain MCP系统的核心模块设计，包括模块功能、接口以及之间的交互关系。

## 1. MCP服务器模块

### 1.1 模块概述

MCP服务器模块是整个系统的入口点，负责处理来自大型语言模型的请求，并将其路由到相应的工具或资源处理器。该模块基于FastMCP框架实现，封装了MCP协议的实现细节，提供了统一的API接口。

**实现文件**: `server.py`

### 1.2 核心类与接口

#### 1.2.1 FastMCP服务器

```python
# 创建MCP服务器实例
mcp = FastMCP("NetBrain MCP")

# 工具注册装饰器
@mcp.tool()
async def tool_function(param1: str, param2: int) -> Dict[str, Any]:
    """工具功能实现"""
    pass

# 资源注册装饰器
@mcp.resource("{uri}")
async def mcp_resource_handler(uri: str) -> Any:
    """MCP资源处理器，处理所有资源请求"""
    return await resource_manager.get_resource(uri)

# 提示模板注册装饰器
@mcp.prompt("{name}")
async def mcp_prompt_handler(name: str) -> str:
    """MCP提示模板处理器"""
    return await template_manager.render_template(name)
```

### 1.3 功能特性

- **工具注册与执行**：目前已实现32个MCP工具，涵盖设备管理、连接管理、拓扑发现等功能
- **资源注册与提供**：实现13个MCP资源，包括设备、配置、拓扑等资源类型
- **提示模板管理**：集成模板系统，支持动态模板渲染
- **会话管理**：维护客户端会话状态和连接信息
- **错误处理**：统一的错误处理机制和日志记录

### 1.4 与其他模块的交互

- 与工具管理模块交互，通过装饰器方式注册工具
- 与资源模块交互，通过resource_manager获取和管理资源
- 与模板系统交互，通过template_manager渲染提示模板
- 与设备管理和连接模块交互，提供网络设备操作功能

## 2. 工具管理模块

### 2.1 模块概述

工具管理模块负责工具的注册、分类和执行管理，虽然MCP工具直接通过FastMCP注册，但该模块提供了工具的分类和管理功能。

**实现文件**: `tool_manager.py`

### 2.2 核心类与接口

#### 2.2.1 ToolManager类

```python
class ToolManager:
    """工具管理器，负责工具的注册和调用"""
    
    def __init__(self):
        self.tools: Dict[str, ToolInfo] = {}
        self.categories: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}
        
    def register_tool(self, 
                      name: Optional[str] = None, 
                      description: Optional[str] = None,
                      category: ToolCategory = ToolCategory.GENERAL) -> Callable:
        """工具注册装饰器"""
        
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[Dict[str, Any]]:
        """列出已注册的工具"""
        
    def get_tool(self, name: str) -> Optional[ToolInfo]:
        """获取工具信息"""
        
    def execute_tool(self, name: str, *args, **kwargs) -> Any:
        """执行工具"""
```

#### 2.2.2 ToolCategory枚举

```python
class ToolCategory(Enum):
    """工具分类枚举"""
    GENERAL = "general"                # 通用工具
    NETWORK_DEVICE = "network_device"  # 网络设备相关工具
    CONFIGURATION = "configuration"    # 配置管理工具
    TOPOLOGY = "topology"              # 拓扑相关工具
    DIAGNOSTIC = "diagnostic"          # 诊断工具
    SECURITY = "security"              # 安全相关工具
```

#### 2.2.3 ToolInfo数据类

```python
@dataclass
class ToolInfo:
    """工具信息数据类"""
    name: str                           # 工具名称
    func: Callable                      # 工具函数
    description: str                    # 工具描述
    category: ToolCategory              # 工具分类
    parameters: Dict[str, Dict[str, Any]] # 参数信息
    return_type: str                    # 返回类型
```

### 2.3 实际工具实现

系统中实际实现的32个MCP工具分类如下：

#### 设备管理工具 (6个)
- `list_devices` - 列出网络设备
- `add_device` - 添加新的网络设备
- `get_device` - 获取设备详细信息
- `update_device` - 更新设备信息
- `delete_device` - 删除设备

#### 凭据管理工具 (2个)
- `add_credential` - 添加设备凭据
- `list_credentials` - 列出所有设备凭据

#### 设备连接工具 (4个)
- `connect_device` - 连接到网络设备
- `disconnect_device` - 断开与网络设备的连接
- `send_command` - 发送单个命令
- `send_commands` - 发送多个命令
- `get_active_connections` - 获取活动连接

#### 拓扑发现工具 (6个)
- `discover_topology` - 发现网络拓扑
- `get_topology` - 获取网络拓扑
- `clear_topology` - 清除拓扑缓存
- `get_device_neighbors` - 获取设备邻居
- `discover_device_neighbors` - 发现设备邻居
- `get_topology_statistics` - 获取拓扑统计

#### 网络扫描工具 (5个)
- `scan_network_range` - 扫描网络范围
- `get_scan_results` - 获取扫描结果
- `get_scan_statistics` - 获取扫描统计
- `discover_devices_from_scan_results` - 从扫描结果发现设备
- `clear_scan_results` - 清除扫描结果
- `scan_single_host` - 扫描单个主机

#### 资源管理工具 (3个)
- `list_resources` - 列出可用资源
- `get_resource` - 获取资源内容
- `clear_resource_cache` - 清除资源缓存

#### 模板管理工具 (2个)
- `list_templates` - 列出可用模板
- `render_template` - 渲染模板

#### 测试工具 (4个)
- `test_scrapli_connection` - 测试Scrapli连接
- `test_telnet_connection` - 测试Telnet连接
- `send_telnet_command` - 发送Telnet命令

## 3. 资源模块

### 3.1 模块概述

资源模块负责管理和提供各种网络资源，资源是客户端可以访问的数据对象，通过URI标识。系统实现了13个MCP资源。

**实现文件**: `mcp_resources.py`

### 3.2 核心类与接口

#### 3.2.1 ResourceManager类

```python
class ResourceManager:
    """MCP资源管理器，负责资源注册和提供"""
    
    def __init__(self):
        self.resources = {}
        self.resource_patterns = {}
        self.resource_cache = {}
        self.cache_expiration = {}
        self.default_cache_ttl = 300  # 默认缓存5分钟
        self.cache_dir = os.path.join(os.getcwd(), "resource_cache")
        
    def register_resource(self, uri_pattern: str, resource_type: str):
        """注册资源装饰器"""
        
    async def get_resource(self, uri: str, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """获取资源"""
        
    def clear_cache(self, uri: Optional[str] = None) -> bool:
        """清除资源缓存"""
        
    def list_available_resources(self) -> List[Dict[str, Any]]:
        """列出可用的资源"""
```

#### 3.2.2 ResourceType类

```python
class ResourceType:
    """资源类型定义"""
    DEVICE = "device"         # 设备资源
    CREDENTIAL = "credential" # 凭据资源
    TOPOLOGY = "topology"     # 拓扑资源
    SYSTEM = "system"         # 系统资源
    CONFIG = "config"         # 配置资源
    LOG = "log"               # 日志资源
    REPORT = "report"         # 报告资源
    SCAN = "scan"             # 扫描资源
```

### 3.3 实际资源实现

系统中实际实现的13个MCP资源：

1. `greeting/{name}` - 问候信息（示例资源）
2. `device/{device_id}` - 设备基本信息
3. `device/{device_id}/config` - 设备配置信息
4. `device/{device_id}/interfaces` - 设备接口信息
5. `device/{device_id}/routes` - 设备路由信息
6. `credentials` - 凭据列表
7. `system/status` - 系统状态
8. `topology` - 网络拓扑
9. `topology/statistics` - 拓扑统计
10. `device/{device_id}/neighbors` - 设备邻居
11. `scan/results` - 扫描结果
12. `scan/statistics` - 扫描统计
13. `scan/result/{ip_address}` - 单个IP扫描结果

## 4. 设备管理模块

### 4.1 模块概述

设备管理模块负责网络设备的生命周期管理，包括设备的添加、查询、更新和删除，以及设备凭据的管理。

**实现文件**: `network_devices.py`

### 4.2 核心类与接口

#### 4.2.1 DeviceManager类

```python
class DeviceManager:
    """设备管理器，负责设备的创建、查询和管理"""
    
    def __init__(self):
        self.devices: Dict[str, NetworkDevice] = {}
        self.credentials: Dict[str, DeviceCredential] = {}
        self.data_dir = "data"
        self.devices_file = os.path.join(self.data_dir, "devices.json")
        self.credentials_file = os.path.join(self.data_dir, "credentials.json")
        
    def add_device(self, device: NetworkDevice) -> str:
        """添加设备"""
        
    def get_device(self, device_id: str) -> Optional[NetworkDevice]:
        """获取设备"""
        
    def update_device(self, device_id: str, **kwargs) -> Optional[NetworkDevice]:
        """更新设备信息"""
        
    def delete_device(self, device_id: str) -> bool:
        """删除设备"""
        
    def list_devices(self, 
                    vendor: Optional[DeviceVendor] = None,
                    device_type: Optional[DeviceType] = None,
                    status: Optional[DeviceStatus] = None,
                    tag: Optional[str] = None) -> List[NetworkDevice]:
        """列出设备，支持过滤"""
        
    def add_credential(self, credential: DeviceCredential) -> str:
        """添加凭据"""
        
    def get_credential(self, credential_id: str) -> Optional[DeviceCredential]:
        """获取凭据"""
        
    def delete_credential(self, credential_id: str) -> bool:
        """删除凭据"""
        
    def list_credentials(self) -> List[DeviceCredential]:
        """列出所有凭据"""
```

#### 4.2.2 网络设备相关枚举

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

class ConnectionProtocol(Enum):
    """连接协议枚举"""
    SSH = "ssh"
    TELNET = "telnet"
    SNMP = "snmp"
    HTTP = "http"
    HTTPS = "https"
    NETCONF = "netconf"
```

#### 4.2.3 设备数据模型

```python
@dataclass
class NetworkDevice:
    """网络设备模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    ip_address: str = ""
    device_type: DeviceType = DeviceType.OTHER
    vendor: DeviceVendor = DeviceVendor.OTHER
    platform: str = ""  # Scrapli平台类型
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

#### 4.2.4 凭据数据模型

```python
class DeviceCredential:
    """设备认证凭据"""
    def __init__(self, 
                 id: str = None,
                 name: str = "",
                 username: str = "", 
                 password: str = "",
                 protocol: ConnectionProtocol = ConnectionProtocol.SSH,
                 port: int = None,
                 enable_password: str = None,
                 ssh_key_file: str = None):
        # 实现细节...
```

## 5. 设备连接模块

### 5.1 模块概述

设备连接模块负责与网络设备建立连接并执行命令。该模块基于Scrapli库实现，支持SSH、Telnet等多种连接协议，并提供统一的命令执行接口。

**实现文件**: `device_connector.py`

### 5.2 核心类与接口

#### 5.2.1 ConnectionManager类

```python
class ConnectionManager:
    """连接管理器，负责管理所有设备连接"""
    
    def __init__(self):
        self.active_connections: Dict[str, DeviceConnector] = {}
        
    async def connect_device(self, 
                            device: NetworkDevice, 
                            credential: DeviceCredential) -> Tuple[bool, Optional[str]]:
        """连接设备"""
        
    async def disconnect_device(self, device_id: str, credential_id: str) -> Tuple[bool, Optional[str]]:
        """断开设备连接"""
        
    async def send_command(self, 
                          device_id: str, 
                          credential_id: str, 
                          command: str,
                          timeout: int = 30) -> Tuple[Optional[CommandResult], Optional[str]]:
        """发送命令到设备"""
        
    async def send_commands(self, 
                           device_id: str, 
                           credential_id: str, 
                           commands: List[str],
                           timeout: int = 30) -> Tuple[Optional[List[CommandResult]], Optional[str]]:
        """发送多个命令到设备"""
        
    def get_active_connections(self) -> List[Dict[str, Any]]:
        """获取活动连接列表"""
```

#### 5.2.2 ConnectorFactory类

```python
class ConnectorFactory:
    """连接器工厂，根据设备和凭据创建合适的连接器"""
    
    @staticmethod
    def create_connector(device: NetworkDevice, credential: DeviceCredential) -> DeviceConnector:
        """创建设备连接器，目前主要使用ScrapliConnector"""
        return ScrapliConnector(device, credential)
```

#### 5.2.3 DeviceConnector抽象基类

```python
class DeviceConnector(ABC):
    """设备连接器抽象基类"""
    
    def __init__(self, device: NetworkDevice, credential: DeviceCredential):
        self.device = device
        self.credential = credential
        self.connection = None
        self.connected = False
        self.last_activity = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接到设备"""
        
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开与设备的连接"""
        
    @abstractmethod
    async def send_command(self, command: str, timeout: int = 30) -> CommandResult:
        """发送命令到设备"""
        
    @abstractmethod
    async def send_commands(self, commands: List[str], timeout: int = 30) -> List[CommandResult]:
        """发送多个命令到设备"""
```

#### 5.2.4 ScrapliConnector实现

```python
class ScrapliConnector(DeviceConnector):
    """Scrapli连接器实现，支持混合异步/同步模式"""
    
    async def connect(self) -> bool:
        """通过Scrapli连接到设备，支持多种平台"""
        # 根据设备平台选择合适的驱动
        # 支持异步和同步两种模式
        # 实现自动重连机制
        
    async def send_command(self, command: str, timeout: int = 30) -> CommandResult:
        """发送命令，支持异步/同步混合模式"""
        # 根据连接对象类型选择调用方式
        if asyncio.iscoroutinefunction(self.connection.send_command):
            # 异步方法直接调用
            response = await self.connection.send_command(command=command, timeout_ops=timeout)
        else:
            # 同步方法需要在线程中运行
            response = await asyncio.to_thread(self.connection.send_command, command=command, timeout_ops=timeout)
```

#### 5.2.5 CommandResult类

```python
class CommandResult:
    """命令执行结果类"""
    
    def __init__(self, 
                 command: str, 
                 output: str, 
                 success: bool = True, 
                 error_message: Optional[str] = None):
        self.command = command
        self.output = output
        self.success = success
        self.error_message = error_message
        self.execution_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
```

## 6. 模板系统

### 6.1 模块概述

模板系统负责管理和渲染各种提示和命令模板，提高系统的灵活性和扩展性。系统实现了13个提示模板。

**实现文件**: `template_system.py`, `device_prompts.py`

### 6.2 核心类与接口

#### 6.2.1 TemplateManager类

```python
class TemplateManager:
    """高级提示模板管理器"""
    
    def __init__(self):
        self.templates = {}
        self.templates_dir = os.path.join(os.getcwd(), "templates")
        
    def register_template(self, name: str = None, description: str = None):
        """注册模板装饰器"""
        
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        
    def render_template(self, name: str, arguments: Dict[str, Any] = None) -> Optional[Union[str, List[Message]]]:
        """渲染模板"""
        
    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有可用模板"""
```

#### 6.2.2 消息模型

```python
@dataclass
class Message:
    """基础消息类"""
    role: str
    content: str

class SystemMessage(Message):
    """系统消息"""
    def __init__(self, content: str):
        super().__init__(role="system", content=content)

class UserMessage(Message):
    """用户消息"""
    def __init__(self, content: str):
        super().__init__(role="user", content=content)

class AssistantMessage(Message):
    """助手消息"""
    def __init__(self, content: str):
        super().__init__(role="assistant", content=content)
```

### 6.3 实际模板实现

系统中实际实现的13个提示模板：

#### template_system.py中的模板 (8个)
1. `network_diagnosis` - 网络诊断提示模板
2. `device_configuration` - 设备配置会话模板
3. `device_diagnosis` - 网络设备诊断模板
4. `config_review` - 网络设备配置审查模板
5. `route_analysis` - 网络路由分析模板
6. `vlan_config` - VLAN配置生成模板
7. `network_topology` - 网络拓扑分析模板
8. `network_security` - 网络安全评估模板

#### device_prompts.py中的模板 (5个)
1. `cisco_device_analysis` - 思科设备分析模板
2. `huawei_device_analysis` - 华为设备分析模板
3. `network_troubleshooting` - 网络故障排除模板
4. `security_audit` - 网络安全审计模板
5. `performance_optimization` - 网络性能优化模板

#### 6.2.3 模板渲染函数

```python
async def render_template_with_resources(
    template_name: str, 
    context: Dict[str, Any], 
    resource_uris: Dict[str, str],
    resource_manager=None
) -> Union[str, List[Message]]:
    """渲染包含资源引用的模板"""
```

## 7. 扩展模块

### 7.1 拓扑发现模块

**实现文件**: `topology_discovery_improved.py`

该模块实现了基于CDP/LLDP协议的网络拓扑自动发现功能，支持多厂商设备的邻居发现和拓扑构建。

### 7.2 网络扫描模块

**实现文件**: `network_scanner.py`

该模块实现了网络范围扫描和设备发现功能，支持ping检测、端口扫描、SNMP检测等多种发现方式。

## 8. 数据持久化

系统采用JSON文件存储方式进行数据持久化：

- **设备数据**: `data/devices.json`
- **凭据数据**: `data/credentials.json`
- **资源缓存**: `resource_cache/` 目录
- **模板缓存**: `templates/` 目录

## 9. 模块间交互

```
MCP服务器 (server.py)
    ↓
    ├── 工具管理 (tool_manager.py) → 功能分类
    ├── 资源管理 (mcp_resources.py) → 数据提供
    ├── 模板系统 (template_system.py + device_prompts.py) → 提示生成
    ├── 设备管理 (network_devices.py) → 设备CRUD
    ├── 设备连接 (device_connector.py) → 连接管理
    ├── 拓扑发现 (topology_discovery_improved.py) → 拓扑构建
    └── 网络扫描 (network_scanner.py) → 设备发现
```

这种模块化设计确保了系统的可维护性和扩展性，每个模块都有明确的职责和接口，便于独立开发和测试。 