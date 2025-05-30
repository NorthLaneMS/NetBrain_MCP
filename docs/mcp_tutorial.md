# NetBrain MCP 项目教程

本教程详细介绍如何使用NetBrain MCP项目，包括MCP协议的基本概念、实际实现方式和高级使用技巧。

## 1. MCP协议概述

### 1.1 什么是MCP？

MCP（Model Context Protocol）是一个开放标准，用于连接LLM（大型语言模型）应用程序与外部数据源和工具。可以将MCP视为"AI领域的USB-C"——一种通用连接器，使AI模型能够与外部工具或数据源建立安全的双向连接。

### 1.2 NetBrain MCP的实现特点

NetBrain MCP基于**FastMCP框架**实现，具有以下特点：

- **32个MCP工具**：涵盖设备管理、连接控制、拓扑发现、网络扫描等
- **13个MCP资源**：提供设备、配置、拓扑、扫描等数据资源
- **13个提示模板**：专业的网络运维AI提示模板
- **混合异步/同步模式**：智能适配不同类型的设备连接
- **多厂商支持**：思科、华为、H3C、Juniper等主流设备

## 2. MCP核心概念

### 2.1 工具（Tools）

工具是模型控制的函数，允许LLM执行动作和产生副作用。

#### 2.1.1 NetBrain MCP工具分类

**设备管理工具（6个）**
```python
@mcp.tool()
async def list_devices(vendor: str = None, device_type: str = None, status: str = None, tag: str = None) -> List[Dict[str, Any]]:
    """列出网络设备，支持过滤条件"""

@mcp.tool()  
async def add_device(name: str, ip_address: str, device_type: str, vendor: str, platform: str = None, ...) -> Dict[str, Any]:
    """添加新的网络设备"""

@mcp.tool()
async def get_device(device_id: str) -> Optional[Dict[str, Any]]:
    """获取设备详细信息"""

@mcp.tool()
async def update_device(device_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """更新设备信息"""

@mcp.tool()
async def delete_device(device_id: str) -> bool:
    """删除设备"""
```

**连接管理工具（5个）**
```python
@mcp.tool()
async def connect_device(device_id: str, credential_id: str) -> Dict[str, Any]:
    """连接到网络设备"""

@mcp.tool()
async def disconnect_device(device_id: str, credential_id: str) -> Dict[str, Any]:
    """断开设备连接"""

@mcp.tool()
async def send_command(device_id: str, credential_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
    """发送单个命令到设备"""

@mcp.tool()
async def send_commands(device_id: str, credential_id: str, commands: List[str], timeout: int = 30) -> List[Dict[str, Any]]:
    """发送多个命令到设备"""

@mcp.tool()
async def get_active_connections() -> List[Dict[str, Any]]:
    """获取当前活动的设备连接"""
```

**拓扑发现工具（6个）**
```python
@mcp.tool()
async def discover_topology(device_ids: List[str]) -> Dict[str, Any]:
    """发现网络拓扑结构"""

@mcp.tool()
async def get_topology() -> Dict[str, Any]:
    """获取当前网络拓扑"""

@mcp.tool()
async def clear_topology() -> Dict[str, Any]:
    """清除拓扑缓存"""

@mcp.tool()
async def get_device_neighbors(device_id: str) -> Dict[str, Any]:
    """获取设备的邻居信息"""

@mcp.tool()
async def discover_device_neighbors(device_id: str) -> Dict[str, Any]:
    """发现设备邻居"""

@mcp.tool()
async def get_topology_statistics() -> Dict[str, Any]:
    """获取拓扑统计信息"""
```

#### 2.1.2 工具实现方式

NetBrain MCP使用FastMCP的装饰器方式注册工具：

```python
# 在server.py中的实际实现
from mcp.server.fastmcp import FastMCP
from network_devices import device_manager
from device_connector import connection_manager

# 创建FastMCP服务器实例
mcp = FastMCP("NetBrain MCP")

@mcp.tool()
async def add_device(
    name: str,
    ip_address: str, 
    device_type: str,
    vendor: str,
    platform: str = None,
    model: str = None,
    os_version: str = None,
    location: str = None,
    description: str = None
) -> Dict[str, Any]:
    """添加新的网络设备到系统中"""
    try:
        # 创建设备对象
        device = NetworkDevice(
            name=name,
            ip_address=ip_address,
            device_type=DeviceType(device_type),
            vendor=DeviceVendor(vendor),
            platform=platform or "",
            model=model or "",
            os_version=os_version or "",
            location=location or "",
            description=description or ""
        )
        
        # 添加设备
        device_id = device_manager.add_device(device)
        
        return {
            "success": True,
            "device_id": device_id,
            "message": f"设备 {name} 添加成功"
        }
        
            except Exception as e:
        logger.error(f"添加设备失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

### 2.2 资源（Resources）

资源是应用程序控制的数据对象，通过URI标识，用于为LLM提供上下文信息。

#### 2.2.1 NetBrain MCP资源列表

系统实现了13个MCP资源：

**设备相关资源（5个）**
```python
@resource_manager.register_resource("device/{device_id}", ResourceType.DEVICE)
async def get_device_resource(device_id: str) -> Dict[str, Any]:
    """获取设备基本信息"""

@resource_manager.register_resource("device/{device_id}/config", ResourceType.CONFIG)
async def get_device_config_resource(device_id: str) -> Dict[str, Any]:
    """获取设备配置信息"""

@resource_manager.register_resource("device/{device_id}/interfaces", ResourceType.DEVICE)
async def get_device_interfaces_resource(device_id: str) -> Dict[str, Any]:
    """获取设备接口信息"""

@resource_manager.register_resource("device/{device_id}/routes", ResourceType.DEVICE)
async def get_device_routes_resource(device_id: str) -> Dict[str, Any]:
    """获取设备路由信息"""

@resource_manager.register_resource("device/{device_id}/neighbors", ResourceType.TOPOLOGY)
async def get_device_neighbors_resource(device_id: str) -> Dict[str, Any]:
    """获取设备邻居信息"""
```

**系统资源（4个）**
```python
@resource_manager.register_resource("greeting/{name}", ResourceType.SYSTEM)
async def get_greeting_resource(name: str) -> Dict[str, Any]:
    """问候信息资源（示例）"""

@resource_manager.register_resource("credentials", ResourceType.CREDENTIAL)
async def get_credentials_resource() -> Dict[str, Any]:
    """获取凭据列表"""

@resource_manager.register_resource("system/status", ResourceType.SYSTEM)
async def get_system_status_resource() -> Dict[str, Any]:
    """获取系统状态"""

@resource_manager.register_resource("topology", ResourceType.TOPOLOGY)
async def get_topology_resource() -> Dict[str, Any]:
    """获取网络拓扑"""
```

#### 2.2.2 资源实现方式

```python
# 在server.py中的实际资源处理器
@mcp.resource("{uri}")
async def mcp_resource_handler(uri: str) -> Any:
    """
    MCP资源处理器，处理所有资源请求
    
    Args:
        uri: 资源URI
        
    Returns:
        资源内容
    """
    try:
        result = await resource_manager.get_resource(uri)
        return result
    except Exception as e:
        logger.error(f"获取资源失败: {uri}, 错误: {str(e)}")
        return {"error": f"获取资源失败: {str(e)}"}
```

### 2.3 提示模板（Prompts）

提示模板是用户控制的交互模板，帮助构造有效的LLM提示。

#### 2.3.1 NetBrain MCP提示模板

系统实现了13个专业网络运维提示模板：

**template_system.py中的模板（8个）**
```python
@template_manager.register_template(
    name="device_diagnosis",
    description="网络设备诊断模板"
)
def device_diagnosis_template(device_info: Dict[str, Any], interfaces_info: str = None, logs: str = None) -> List[Message]:
    """网络设备诊断提示模板，用于分析设备状态和接口信息"""
    system_prompt = f"""你是一位专业的网络工程师，负责诊断{device_info.get('vendor', '未知厂商')}的{device_info.get('device_type', '网络设备')}。
请根据提供的设备信息、接口状态和日志，进行专业分析并提供诊断报告。"""
    
    return [
        SystemMessage(system_prompt),
        UserMessage(f"请诊断设备：{device_info}")
    ]

@template_manager.register_template(
    name="config_review", 
    description="网络设备配置审查模板"
)
def config_review_template(device_info: Dict[str, Any], config_content: str, focus_area: str = None) -> List[Message]:
    """网络配置审查提示模板，用于审查设备配置并提供改进建议"""
    # 实现...
```

**device_prompts.py中的模板（5个）**
```python
@template_manager.register_template(
    name="cisco_device_analysis",
    description="思科设备专业分析模板"
)
def cisco_device_analysis_template(device_info: Dict[str, Any], command_outputs: Dict[str, str]) -> List[Message]:
    """思科设备专业分析模板"""
    # 实现...

@template_manager.register_template(
    name="huawei_device_analysis", 
    description="华为设备专业分析模板"
)
def huawei_device_analysis_template(device_info: Dict[str, Any], command_outputs: Dict[str, str]) -> List[Message]:
    """华为设备专业分析模板"""
    # 实现...
```

#### 2.3.2 模板实现方式

```python
# 在server.py中的模板处理器
@mcp.prompt("{name}")
async def mcp_prompt_handler(name: str, arguments: dict = None) -> str:
    """
    MCP提示模板处理器
    
    Args:
        name: 模板名称
        arguments: 模板参数
        
    Returns:
        渲染后的提示内容
    """
    try:
        result = template_manager.render_template(name, arguments or {})
        if isinstance(result, list):
            # 如果返回消息列表，转换为字符串
            return "\n".join([msg.content for msg in result])
        return result or ""
    except Exception as e:
        logger.error(f"渲染模板失败: {name}, 错误: {str(e)}")
        return f"模板渲染失败: {str(e)}"
```

## 3. 实际使用示例

### 3.1 基本设备管理

#### 3.1.1 添加设备凭据

```
# 在Claude或其他MCP客户端中输入：
请帮我添加一个思科设备的SSH凭据，用户名是admin，密码是cisco123，端口是22
```

AI将自动调用`add_credential`工具：
```python
# 实际调用的工具
await add_credential(
    name="思科SSH凭据",
    username="admin", 
    password="cisco123",
    protocol="ssh",
    port=22
)
```

#### 3.1.2 添加网络设备

```
请添加一台思科路由器，名称是Router-01，IP地址是192.168.1.1，型号是ISR4321，使用刚才添加的凭据
```

AI将调用`add_device`工具：
```python
await add_device(
    name="Router-01",
    ip_address="192.168.1.1",
    device_type="router",
    vendor="cisco", 
    platform="cisco_iosxe",
    model="ISR4321"
)
```

### 3.2 设备连接和命令执行

#### 3.2.1 连接设备

```
请连接到Router-01设备
```

AI将调用连接工具：
```python
await connect_device(
    device_id="router-01-uuid",
    credential_id="credential-uuid"
)
```

#### 3.2.2 执行命令

```
在Router-01上执行 show version 命令
```

AI将调用命令执行工具：
```python
await send_command(
    device_id="router-01-uuid",
    credential_id="credential-uuid", 
    command="show version",
    timeout=30
)
```

### 3.3 拓扑发现

```
请发现Router-01的网络拓扑
```

AI将调用拓扑发现工具：
```python
await discover_topology(
    device_ids=["router-01-uuid"]
)
```

### 3.4 使用提示模板

```
使用设备诊断模板分析Router-01的状态
```

AI将：
1. 获取设备信息资源
2. 获取设备接口信息 
3. 使用device_diagnosis模板进行分析

## 4. 高级功能

### 4.1 批量操作

#### 4.1.1 批量命令执行

```
在Router-01上依次执行以下命令：
1. show running-config
2. show ip route
3. show interface status
```

AI将调用`send_commands`工具：
```python
await send_commands(
    device_id="router-01-uuid",
    credential_id="credential-uuid",
    commands=[
        "show running-config",
        "show ip route", 
        "show interface status"
    ]
)
```

#### 4.1.2 网络扫描

```
请扫描192.168.1.0/24网段，发现网络设备
```

AI将调用网络扫描工具：
```python
await scan_network_range(
    network="192.168.1.0/24",
    timeout=5,
    max_concurrent=50,
    ports=[22, 23, 80, 443, 161]
)
```

### 4.2 资源访问

#### 4.2.1 获取设备配置

```
请获取Router-01的配置信息
```

AI将访问配置资源：
```
资源URI: device/router-01-uuid/config
```

#### 4.2.2 获取拓扑信息

```
显示当前网络拓扑的统计信息
```

AI将访问拓扑资源：
```
资源URI: topology/statistics
```

### 4.3 智能诊断

#### 4.3.1 使用诊断模板

```
使用华为设备分析模板检查Switch-01的状态
```

AI将：
1. 识别设备是华为设备
2. 获取设备相关信息和命令输出
3. 使用`huawei_device_analysis`模板
4. 提供专业的分析报告

#### 4.3.2 配置审查

```
使用配置审查模板检查Router-01的安全配置
```

AI将使用`config_review`模板，重点关注安全配置。

## 5. 系统集成

### 5.1 连接到Claude Desktop

#### 5.1.1 配置文件

编辑Claude Desktop配置文件：

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

   ```json
   {
   "mcpServers": {
    "netbrain-mcp": {
       "command": "python",
      "args": ["/path/to/NetBrainMCP/server.py"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
     }
   }
   }
   ```

#### 5.1.2 验证连接

重启Claude Desktop后，在对话中输入：
```
请列出所有可用的网络设备
```

如果看到工具图标并得到设备列表响应，说明连接成功。

### 5.2 连接到Cursor IDE

#### 5.2.1 启动SSE模式

```bash
cd /path/to/NetBrainMCP
python server.py --mode sse --port 8000
```

#### 5.2.2 配置Cursor

1. 打开Cursor → 设置 → 功能 → MCP服务器
2. 添加新服务器：
   - **名称**: netbrain-mcp
   - **类型**: sse  
   - **URL**: http://localhost:8000/sse

### 5.3 Web界面使用

#### 5.3.1 启动Web服务器

```bash
python server.py --web --port 8080
```

#### 5.3.2 访问Web界面

在浏览器中访问：http://localhost:8080

Web界面提供：
- 设备管理页面
- 多标签页终端
- 交互式拓扑图

## 6. 故障排除

### 6.1 常见问题

#### 6.1.1 MCP服务器无法启动

**问题症状**：
```
ModuleNotFoundError: No module named 'mcp'
```

**解决方案**：
```bash
pip install -r requirements.txt
```

#### 6.1.2 设备连接失败

**问题症状**：
```
{"success": false, "error": "连接超时"}
```

**解决方案**：
1. 检查网络连通性：`ping 192.168.1.1`
2. 验证SSH/Telnet服务：`telnet 192.168.1.1 22`
3. 确认凭据正确性
4. 检查防火墙设置

#### 6.1.3 Claude Desktop连接问题

**问题症状**：Claude Desktop不显示工具图标

**解决方案**：
1. 检查配置文件路径和格式
2. 验证Python路径和脚本路径
3. 查看Claude Desktop日志
4. 重启Claude Desktop

### 6.2 调试技巧

#### 6.2.1 启用详细日志

```bash
export LOG_LEVEL=DEBUG
python server.py
```

#### 6.2.2 测试工具连接

```python
# 测试Scrapli连接
python -c "
import asyncio
from server import test_scrapli_connection
result = asyncio.run(test_scrapli_connection(
    host='192.168.1.1',
    username='admin',
    password='cisco123',
    platform='cisco_iosxe'
))
print(result)
"
```

## 7. 扩展开发

### 7.1 添加自定义工具

```python
@mcp.tool()
async def custom_network_tool(param1: str, param2: int) -> Dict[str, Any]:
    """自定义网络工具"""
    try:
        # 实现自定义逻辑
        result = perform_custom_operation(param1, param2)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 7.2 添加自定义资源

```python
@resource_manager.register_resource("custom/{id}", ResourceType.CUSTOM)
async def get_custom_resource(id: str) -> Dict[str, Any]:
    """自定义资源处理器"""
    # 实现自定义资源获取逻辑
    return {"data": f"自定义数据 for {id}"}
```

### 7.3 添加自定义模板

```python
@template_manager.register_template(
    name="custom_analysis",
    description="自定义分析模板"
)
def custom_analysis_template(data: Dict[str, Any]) -> str:
    """自定义分析模板"""
    return f"基于数据 {data} 进行自定义分析..."
```

## 8. 最佳实践

### 8.1 设备管理最佳实践

1. **统一命名规范**：使用一致的设备命名格式
2. **合理分组标签**：按功能、位置、环境分组
3. **定期更新信息**：保持设备信息的准确性
4. **备份配置数据**：定期备份重要配置

### 8.2 使用技巧

1. **充分利用模板**：使用专业模板获得更好的分析结果
2. **批量操作**：对多个设备执行相同操作时使用批量工具
3. **资源组合**：结合多个资源获得全面的设备视图
4. **缓存机制**：利用系统缓存提高查询效率

### 8.3 安全建议

1. **凭据管理**：使用强密码和定期轮换
2. **网络隔离**：在安全的网络环境中部署
3. **访问控制**：限制MCP服务器的访问权限
4. **日志监控**：定期检查操作日志

## 9. 性能优化

### 9.1 连接优化

```python
# 调整连接池设置
MAX_CONNECTIONS = 10
CONNECTION_TIMEOUT = 30
COMMAND_TIMEOUT = 60
```

### 9.2 缓存优化

```python
# 调整缓存策略
RESOURCE_CACHE_TTL = 300  # 5分钟
CONFIG_CACHE_TTL = 600    # 10分钟
TOPOLOGY_CACHE_TTL = 900  # 15分钟
```

### 9.3 并发控制

```python
# 网络扫描并发控制
DEFAULT_MAX_CONCURRENT = 50
SCAN_TIMEOUT = 5
```

## 10. 总结

NetBrain MCP项目提供了一个完整的网络运维AI集成平台，通过MCP协议实现：

- **32个专业工具**：涵盖网络设备管理的各个方面
- **13个数据资源**：提供丰富的网络设备和拓扑信息
- **13个提示模板**：专业的网络运维AI指导
- **多厂商支持**：思科、华为等主流设备厂商
- **灵活部署**：支持Claude Desktop、Cursor IDE和Web界面

通过本教程，您应该能够熟练使用NetBrain MCP系统进行AI驱动的网络运维工作。系统的模块化设计和丰富的扩展机制，也为进一步的定制和开发提供了良好的基础。 