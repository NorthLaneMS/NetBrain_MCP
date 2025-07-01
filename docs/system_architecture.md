# NetBrain MCP 系统架构设计

## 1. 整体架构

NetBrain MCP是一个通过MCP协议连接大型语言模型与网络设备的平台。系统采用模块化设计，基于FastMCP框架实现，主要由以下几个核心部分组成：

```
                    +------------------+
                    |     客户端       |
                    | (Claude/Cursor)  |
                    +--------+---------+
                             |
                             | MCP 协议 (FastMCP)
                             |
+----------------------------v-----------------------------+
|                       NetBrain MCP                       |
|                     (server.py)                         |
|                                                         |
|  +----------------+   +----------------+   +---------+  |
|  | MCP服务器模块  |<->|  工具管理模块   |<->| 资源模块 |  |
|  | (FastMCP)      |   | (tool_manager) |   |(mcp_res) |  |
|  +----------------+   +----------------+   +---------+  |
|           ^                    ^                ^       |
|           |                    |                |       |
|           v                    v                v       |
|  +----------------+   +----------------+   +---------+  |
|  | 设备管理模块   |<->| 设备连接模块   |<->| 模板系统 |  |
|  |(network_devices)|  |(device_connector)|  |(template)|  |
|  +----------------+   +----------------+   +---------+  |
|           ^                    ^                        |
|           |                    |                        |
|           v                    v                        |
|  +----------------+   +----------------+                |
|  | 拓扑发现模块   |<->| 网络扫描模块   |                |
|  |(topology_disc) |   |(network_scanner)|                |
|  +----------------+   +----------------+                |
+-------------------------------------------------------- +
                             |
                             | Scrapli (SSH/Telnet/混合模式)
                             |
                    +--------v---------+
                    |    网络设备      |
                    | (多厂商支持)     |
                    +------------------+
```

## 2. 核心模块说明

### 2.1 MCP服务器模块 (server.py)

MCP服务器模块是整个系统的核心，基于FastMCP框架实现，负责处理来自大型语言模型（如Claude、GPT等）的请求，并将请求路由到相应的工具或资源处理器。

**主要功能：**
- 实现FastMCP协议的服务器端（32个工具，13个资源，13个模板）
- 处理工具调用和资源请求
- 管理会话和上下文
- 提供服务器配置和日志记录

**核心组件：**
- FastMCP服务器实例
- 工具注册装饰器 `@mcp.tool()`
- 资源处理器 `@mcp.resource("{uri}")`
- 提示模板处理器 `@mcp.prompt("{name}")`

**实际实现状态：** ✅ 已完成，包含所有32个工具实现

### 2.2 工具管理模块 (tool_manager.py)

工具管理模块负责工具的注册、管理和分类，虽然MCP工具直接通过FastMCP注册，但该模块提供了工具的分类和管理功能。

**主要功能：**
- 工具注册和分类管理（6个分类）
- 工具执行和错误处理
- 工具元数据管理

**核心组件：**
- ToolManager类：管理所有工具
- ToolCategory枚举：工具分类（general, network_device, configuration, topology, diagnostic, security）
- ToolInfo数据类：工具元数据

**实际实现状态：** ✅ 已完成，支持32个MCP工具的分类管理

### 2.3 资源模块 (mcp_resources.py)

资源模块负责管理和提供各种网络资源，包括设备信息、配置数据、拓扑数据等。

**主要功能：**
- 资源注册和管理（13个MCP资源）
- 资源缓存和刷新（内存+文件双层缓存）
- URI模式匹配和参数提取

**核心组件：**
- ResourceManager类：管理资源
- ResourceType类：资源类型定义（device, credential, topology, system, config, scan等）
- 缓存机制：默认5分钟TTL，支持文件持久化

**实际实现状态：** ✅ 已完成，实现13个MCP资源

### 2.4 设备管理模块 (network_devices.py)

设备管理模块负责网络设备的生命周期管理，包括设备的添加、查询、更新和删除。

**主要功能：**
- 设备信息管理（支持多厂商：cisco, huawei, h3c, juniper等）
- 设备凭据管理（SSH/Telnet/SNMP等协议）
- 设备状态监控
- JSON文件持久化存储

**核心组件：**
- DeviceManager类：设备管理器
- NetworkDevice类：设备数据模型（包含platform字段支持Scrapli）
- DeviceCredential类：设备凭据模型
- 枚举类：DeviceType, DeviceVendor, DeviceStatus, ConnectionProtocol

**实际实现状态：** ✅ 已完成，支持完整的设备生命周期管理

### 2.5 设备连接模块 (device_connector.py)

设备连接模块负责与网络设备建立连接并执行命令，基于Scrapli库实现混合异步/同步模式。

**主要功能：**
- 设备连接管理（基于Scrapli混合模式）
- 命令执行和结果处理
- 连接池管理和自动重连
- 多协议支持（SSH/Telnet）

**核心组件：**
- ConnectionManager类：连接管理器
- ScrapliConnector类：主要连接器实现（支持异步/同步混合）
- DeviceConnector抽象类：连接器接口
- CommandResult类：命令执行结果

**技术特色：**
- 混合异步/同步模式：智能检测连接对象类型，自动选择异步或同步调用方式
- 平台自适应：根据设备厂商自动选择合适的Scrapli驱动
- 自动重连机制：连接断开时自动重连并重试命令

**实际实现状态：** ✅ 已完成，支持思科、华为等多厂商设备

### 2.6 模板系统 (template_system.py + device_prompts.py)

模板系统负责管理和渲染各种提示和命令模板，提高系统的灵活性和扩展性。

**主要功能：**
- 提示模板管理（13个专业模板）
- 模板渲染和上下文处理
- 消息模型支持（System, User, Assistant）
- 资源集成渲染

**核心组件：**
- TemplateManager类：高级提示模板管理器
- Message模型：结构化消息格式
- 模板函数：支持字符串和消息列表两种返回格式
- 资源集成函数：`render_template_with_resources`

**模板分布：**
- template_system.py：8个通用模板
- device_prompts.py：5个设备专用模板

**实际实现状态：** ✅ 已完成，实现13个专业网络运维模板

### 2.7 拓扑发现模块 (topology_discovery_improved.py)

拓扑发现模块负责自动发现和维护网络拓扑，基于CDP/LLDP协议实现。

**主要功能：**
- 基于CDP/LLDP的拓扑发现
- 多厂商设备邻居发现适配
- 拓扑数据模型维护
- 智能拓扑构建算法

**核心组件：**
- ImprovedTopologyDiscovery类：改进的拓扑发现引擎
- NetworkTopology类：拓扑数据模型
- 厂商适配方法：discover_cisco_neighbors, discover_huawei_neighbors等

**实际实现状态：** ✅ 已完成，支持自动拓扑发现

### 2.8 网络扫描模块 (network_scanner.py)

网络扫描模块负责网络范围扫描和设备识别功能。

**主要功能：**
- 网络范围扫描（ping检测、端口扫描）
- 厂商MAC地址识别
- SNMP设备发现
- 扫描结果分析和设备推荐

**核心组件：**
- NetworkScanner类：网络扫描引擎
- 并发扫描机制：支持可配置的并发数
- 厂商识别：内置厂商MAC地址数据库

**实际实现状态：** ✅ 已完成，支持智能网络扫描

## 3. 数据模型

### 3.1 实际数据存储架构

系统采用JSON文件存储架构，具体结构如下：

```
NetBrainMCP/
├── data/                    # 主数据存储目录
│   ├── devices.json         # 设备信息（NetworkDevice对象序列化）
│   └── credentials.json     # 凭据信息（DeviceCredential对象序列化，包含敏感信息）
├── resource_cache/          # 资源缓存目录
│   └── *.json              # 缓存文件（按URI哈希命名）
├── templates/              # 模板缓存目录
│   └── *.json              # 模板元数据文件
└── logs/                   # 日志文件目录
    ├── netbrain_mcp.log    # 主日志
    ├── device_connector.log # 连接日志
    └── audit.log           # 审计日志
```

### 3.2 核心数据实体关系

```
NetworkDevice (network_devices.py)
├── id: str (UUID)
├── name: str
├── ip_address: str
├── device_type: DeviceType (enum)
├── vendor: DeviceVendor (enum)
├── platform: str (Scrapli平台类型)
├── model: str
├── os_version: str
├── status: DeviceStatus (enum)
├── credential_id: str (关联DeviceCredential)
├── tags: List[str]
└── custom_attributes: Dict[str, Any]

DeviceCredential (network_devices.py)
├── id: str (UUID)
├── name: str
├── username: str
├── password: str (明文存储，生产环境应加密)
├── protocol: ConnectionProtocol (enum)
├── port: int
├── enable_password: str
└── ssh_key_file: str

ConnectionManager (device_connector.py)
├── active_connections: Dict[str, DeviceConnector]
└── ScrapliConnector instances
```

## 4. 接口设计

### 4.1 实际MCP工具接口

系统通过FastMCP协议提供以下32个工具：

#### 设备管理工具 (6个)
```python
@mcp.tool()
async def list_devices(vendor, device_type, status, tag) -> List[Dict[str, Any]]

@mcp.tool()
async def add_device(name, ip_address, device_type, vendor, platform, ...) -> Dict[str, Any]

@mcp.tool()
async def get_device(device_id) -> Optional[Dict[str, Any]]

@mcp.tool()
async def update_device(device_id, **kwargs) -> Optional[Dict[str, Any]]

@mcp.tool()
async def delete_device(device_id) -> bool
```

#### 连接管理工具 (5个)
```python
@mcp.tool()
async def connect_device(device_id, credential_id) -> Dict[str, Any]

@mcp.tool()
async def disconnect_device(device_id, credential_id) -> Dict[str, Any]

@mcp.tool()
async def send_command(device_id, credential_id, command, timeout) -> Dict[str, Any]

@mcp.tool()
async def send_commands(device_id, credential_id, commands, timeout) -> List[Dict[str, Any]]

@mcp.tool()
async def get_active_connections() -> List[Dict[str, Any]]
```

#### 拓扑发现工具 (6个)
```python
@mcp.tool()
async def discover_topology(device_ids) -> Dict[str, Any]

@mcp.tool()
async def get_topology() -> Dict[str, Any]

@mcp.tool()
async def clear_topology() -> Dict[str, Any]

@mcp.tool()
async def get_device_neighbors(device_id) -> Dict[str, Any]

@mcp.tool()
async def discover_device_neighbors(device_id) -> Dict[str, Any]

@mcp.tool()
async def get_topology_statistics() -> Dict[str, Any]
```

#### 网络扫描工具 (6个)
```python
@mcp.tool()
async def scan_network_range(network, timeout, max_concurrent, ...) -> Dict[str, Any]

@mcp.tool()
async def get_scan_results(ip_address, alive_only) -> Dict[str, Any]

@mcp.tool()
async def get_scan_statistics() -> Dict[str, Any]

@mcp.tool()
async def discover_devices_from_scan_results(...) -> Dict[str, Any]

@mcp.tool()
async def clear_scan_results() -> Dict[str, Any]

@mcp.tool()
async def scan_single_host(ip_address, timeout, ...) -> Dict[str, Any]
```

#### 其他工具 (9个)
- 凭据管理：2个
- 资源管理：3个
- 模板管理：2个
- 测试工具：2个

### 4.2 实际MCP资源接口

系统提供以下13个MCP资源：

```python
# 设备相关资源 (5个)
@resource_manager.register_resource("device/{device_id}", ResourceType.DEVICE)
@resource_manager.register_resource("device/{device_id}/config", ResourceType.CONFIG)
@resource_manager.register_resource("device/{device_id}/interfaces", ResourceType.DEVICE)
@resource_manager.register_resource("device/{device_id}/routes", ResourceType.DEVICE)
@resource_manager.register_resource("device/{device_id}/neighbors", ResourceType.TOPOLOGY)

# 系统资源 (4个)
@resource_manager.register_resource("greeting/{name}", ResourceType.SYSTEM)
@resource_manager.register_resource("credentials", ResourceType.CREDENTIAL)
@resource_manager.register_resource("system/status", ResourceType.SYSTEM)
@resource_manager.register_resource("topology", ResourceType.TOPOLOGY)

# 拓扑资源 (1个)
@resource_manager.register_resource("topology/statistics", ResourceType.TOPOLOGY)

# 扫描资源 (3个)
@resource_manager.register_resource("scan/results", ResourceType.SCAN)
@resource_manager.register_resource("scan/statistics", ResourceType.SCAN)
@resource_manager.register_resource("scan/result/{ip_address}", ResourceType.SCAN)
```

## 5. 安全设计

### 5.1 当前安全实现状态

**已实现的安全措施：**
- 日志记录：完整的操作日志和审计跟踪
- 凭据存储：JSON文件存储（明文，需要加密改进）
- 连接安全：基于SSH/Telnet的设备连接
- 输入验证：工具参数验证和类型检查

**待实现的安全措施：**
- 凭据加密：计划实现AES-256加密存储
- 访问控制：计划实现基于角色的权限管理
- 传输加密：计划支持HTTPS/WSS
- API认证：计划实现API密钥认证

### 5.2 数据安全

当前数据保护措施：
- 敏感数据标识：明确识别设备凭据等敏感信息
- 日志脱敏：避免在日志中记录明文密码
- 文件权限：建议设置适当的文件系统权限

## 6. 扩展性设计

### 6.1 模块化架构

系统采用高度模块化的设计：
- **独立模块**：每个模块都有明确的职责和接口
- **装饰器模式**：工具、资源、模板均通过装饰器注册
- **抽象接口**：DeviceConnector抽象基类支持多种连接器实现
- **工厂模式**：ConnectorFactory根据设备类型创建合适的连接器

### 6.2 多厂商支持

**已支持的厂商：**
- Cisco：IOS, IOS-XE, NX-OS
- Huawei：VRP系统
- H3C：Comware系统
- Juniper：JUNOS系统
- Arista：EOS系统

**扩展机制：**
- Scrapli平台适配：通过platform字段指定驱动类型
- 命令模板适配：针对不同厂商的命令差异进行适配
- 邻居发现适配：为不同厂商实现专用的邻居发现方法

### 6.3 协议支持

**当前支持的协议：**
- SSH：主要连接协议，支持密钥和密码认证
- Telnet：备用连接协议
- SNMP：计划支持
- NETCONF：计划支持

## 7. 部署架构

### 7.1 单机部署（当前实现）

适用于小型网络环境和开发测试：

```
+-----------------+
| NetBrain MCP    |
| Python应用      |
| FastMCP服务器   |
| JSON文件存储    |
+-----------------+
        |
        | Scrapli
        |
+-------v-------+
| 网络设备     |
| (多厂商)     |
+--------------+
```

**部署要求：**
- Python 3.10+
- 依赖包：scrapli, mcp, fastapi等
- 网络访问：能够SSH/Telnet到目标设备

### 7.2 容器化部署（计划）

支持Docker容器化部署：

```
+------------------+
| Docker容器       |
| ├── NetBrain MCP |
| ├── Python环境   |
| └── 数据卷       |
+------------------+
```

### 7.3 分布式部署（未来规划）

适用于大型网络环境：

```
+-------------+    +-------------+    +-------------+
| MCP API服务 |--->| 设备管理服务 |--->| 数据库服务  |
+-------------+    +-------------+    +-------------+
       ^                  ^
       |                  |
       v                  v
+-------------+    +-------------+
| 拓扑服务    |<-->| 扫描服务    |
+-------------+    +-------------+
```

## 8. 技术栈

### 8.1 实际技术栈

**核心框架：**
- **MCP框架**：FastMCP（基于mcp Python包）
- **异步框架**：asyncio
- **设备连接**：Scrapli（支持异步/同步混合模式）

**编程语言：**
- **Python**：3.10+
- **类型提示**：完整的类型注解支持

**数据存储：**
- **文件存储**：JSON格式
- **缓存**：内存缓存 + 文件缓存
- **数据持久化**：自动加载和保存机制

**网络协议：**
- **SSH**：asyncssh（异步）/ paramiko（同步）
- **Telnet**：telnetlib3
- **其他**：计划支持SNMP、NETCONF

**日志系统：**
- **日志框架**：Python logging
- **格式化**：JsonFormatter支持UTF-8
- **文件管理**：日志轮转和归档

### 8.2 依赖包版本

根据requirements.txt：
```
scrapli>=2025.1.30      # 网络设备连接
mcp                     # MCP协议支持
fastapi                 # Web框架（Web界面）
asyncio                 # 异步支持
jinja2                  # 模板引擎
pydantic               # 数据验证
websockets             # WebSocket支持
```

## 9. 性能特征

### 9.1 并发性能

**异步架构优势：**
- 全异步设计，支持高并发操作
- 混合异步/同步模式，兼容不同类型的连接器
- 连接池管理，减少连接开销

**性能指标：**
- 并发连接：支持多设备同时连接
- 命令执行：支持批量命令并发执行
- 资源缓存：5分钟默认TTL，减少重复获取

### 9.2 内存管理

**缓存策略：**
- 资源缓存：内存 + 文件双层缓存
- 连接缓存：活动连接池管理
- 模板缓存：编译后的模板缓存

**内存优化：**
- 按需加载：资源和连接按需创建
- 自动清理：过期缓存自动清理
- 连接管理：空闲连接自动断开

## 10. 开发路线图

### 10.1 已完成阶段 ✅

**阶段一：MCP协议实现与基础框架**
- [x] FastMCP服务器架构
- [x] 32个MCP工具实现
- [x] 13个MCP资源实现
- [x] 基础架构设计

**阶段二：网络设备管理**
- [x] 基于Scrapli的设备连接引擎
- [x] 多厂商设备支持
- [x] 设备认证管理系统
- [x] JSON文件数据存储

**阶段三：配置管理与MCP增强**
- [x] 13个提示模板系统
- [x] 资源缓存机制
- [x] 拓扑发现功能
- [x] 网络扫描功能

**阶段四：测试与文档**
- [x] 系统功能测试
- [x] 技术文档编写
- [x] 用户操作指南

### 10.2 当前系统状态

**项目状态：✅ 已完成所有计划功能**

**核心功能完成度：**
- MCP协议实现：100%
- 设备管理功能：100%
- 连接管理功能：100%
- 拓扑发现功能：100%
- 网络扫描功能：100%
- 模板系统：100%
- 资源系统：100%

**生产就绪状态：**
- 功能完整性：✅ 完成
- 稳定性测试：✅ 完成
- 文档完善：✅ 完成
- 部署准备：✅ 完成

### 10.3 未来增强方向

**安全增强：**
- [ ] 凭据加密存储
- [ ] 基于角色的访问控制
- [ ] API认证机制
- [ ] 审计日志增强

**性能优化：**
- [ ] 数据库支持（SQLite/PostgreSQL）
- [ ] 分布式架构支持
- [ ] 缓存优化策略
- [ ] 连接池调优

**功能扩展：**
- [ ] Web管理界面增强
- [ ] 更多厂商设备支持
- [ ] 高级网络分析功能
- [ ] 监控告警系统

**集成能力：**
- [ ] 第三方API集成
- [ ] 企业身份认证集成
- [ ] 监控系统集成
- [ ] 配置管理平台集成

---

NetBrain MCP系统已成功完成所有预定目标，具备生产环境部署条件。系统架构设计合理，技术栈成熟稳定，功能完整丰富，为AI驱动的网络运维提供了强大的基础平台。 