# NetBrain MCP 用户操作指南

本文档是NetBrain MCP系统的完整用户操作指南，将指导您从安装配置到高级功能使用的全过程。

## 1. 项目简介

### 1.1 什么是NetBrain MCP？

NetBrain MCP（Model Context Protocol）是一个开源的网络运维整合平台，通过MCP协议连接大型语言模型（LLM）与网络设备。它允许AI助手通过标准化协议执行网络配置、诊断和管理任务。

### 1.2 核心功能

#### 🔧 设备管理功能
- **统一设备管理**：支持思科、华为、H3C、Juniper等主流厂商设备
- **多协议连接**：支持SSH、Telnet、SNMP等连接协议
- **凭据安全管理**：加密存储设备访问凭据
- **设备状态监控**：实时监控设备连接状态

#### 🌐 网络操作功能
- **命令执行**：远程执行网络设备命令
- **配置管理**：设备配置备份、比较和部署
- **拓扑发现**：基于CDP/LLDP的自动拓扑发现
- **网络扫描**：网络范围扫描和设备识别

#### 🤖 AI集成功能
- **32个MCP工具**：涵盖设备管理、连接控制、拓扑分析等
- **13个MCP资源**：提供设备信息、配置数据、拓扑数据等
- **13个提示模板**：专业的网络诊断和配置模板
- **智能诊断**：AI驱动的网络问题分析和解决方案

#### 💻 Web界面功能
- **专业终端**：基于XTerm.js的多标签页终端体验
- **拓扑可视化**：基于D3.js的交互式网络拓扑图
- **设备管理界面**：直观的设备添加、编辑和监控界面
- **主题系统**：支持暗色/明亮主题切换

## 2. 系统要求

### 2.1 硬件要求
- **CPU**：2核心以上
- **内存**：4GB以上
- **存储**：10GB可用空间
- **网络**：能够访问目标网络设备

### 2.2 软件要求
- **操作系统**：Windows 10+、Linux、macOS
- **Python版本**：Python 3.10或更高版本
- **网络访问**：SSH/Telnet访问目标设备的权限

### 2.3 支持的设备
- **思科设备**：IOS、IOS-XE、NX-OS
- **华为设备**：VRP系统
- **H3C设备**：Comware系统
- **Juniper设备**：JUNOS系统
- **其他厂商**：支持标准SSH/Telnet协议的设备

## 3. 安装和配置

### 3.1 获取项目代码

```bash
# 克隆项目（假设从Git仓库）
git clone https://github.com/your-org/NetBrainMCP.git
cd NetBrainMCP

# 或者下载项目压缩包并解压
# wget https://github.com/your-org/NetBrainMCP/archive/main.zip
# unzip main.zip
# cd NetBrainMCP-main
```

### 3.2 创建Python虚拟环境

   ```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3.3 安装依赖

   ```bash
# 安装项目依赖
pip install -r requirements.txt

# 验证关键依赖安装
python -c "import scrapli; print('Scrapli版本:', scrapli.__version__)"
python -c "import mcp; print('MCP已安装')"
   ```

### 3.4 配置环境变量（可选）

```bash
# 设置日志级别
export LOG_LEVEL=INFO

# 设置数据目录
export DATA_DIR=./data

# 设置加密密钥（用于凭据加密）
export ENCRYPTION_KEY=your-secret-key
```

## 4. 快速开始

### 4.1 启动MCP服务器

```bash
# 启动MCP服务器（标准输入输出模式）
python server.py

# 或启动Web服务器模式
python server.py --web
```

### 4.2 连接到Claude Desktop

1. **安装Claude Desktop**
   - 从 https://claude.ai/download 下载并安装Claude Desktop

2. **配置MCP服务器**
   
   编辑Claude Desktop配置文件：
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

   添加配置：
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

3. **重启Claude Desktop**
   - 重启Claude Desktop，您将看到工具图标，表示MCP服务器已连接

### 4.3 连接到Cursor IDE

1. **启动SSE模式**
   ```bash
   python server.py --mode sse --port 8000
   ```

2. **配置Cursor**
   - 打开Cursor → 设置 → 功能 → MCP服务器
   - 添加新服务器：
     - **名称**: netbrain-mcp
     - **类型**: sse
     - **URL**: http://localhost:8000/sse

## 5. 基本操作指南

### 5.1 设备管理

#### 添加设备凭据

首先添加设备访问凭据：

```
# 在Claude或Cursor中输入：
请帮我添加一个思科设备的SSH凭据，用户名是admin，密码是cisco123
```

AI将调用`add_credential`工具：
- 用户名：admin
- 密码：cisco123
- 协议：ssh
- 端口：22

#### 添加网络设备

```
# 添加思科路由器
请添加一台思科路由器，名称是Router-01，IP地址是192.168.1.1，使用刚才添加的凭据
```

AI将调用`add_device`工具添加设备。

#### 查看设备列表

```
显示所有网络设备的列表
```

AI将调用`list_devices`工具显示所有已添加的设备。

### 5.2 设备连接和命令执行

#### 连接到设备

```
请连接到Router-01设备
```

AI将调用`connect_device`工具建立与设备的连接。

#### 执行命令

```
# 查看设备版本信息
在Router-01上执行 show version 命令

# 查看接口状态
在Router-01上执行 show ip interface brief 命令

# 执行多个命令
在Router-01上依次执行以下命令：
1. show running-config
2. show ip route
3. show interface status
```

AI将调用`send_command`或`send_commands`工具执行相应命令。

### 5.3 网络拓扑发现

#### 发现设备拓扑

```
请发现Router-01的网络拓扑
```

AI将调用`discover_topology`工具，通过CDP/LLDP协议发现网络拓扑。

#### 查看拓扑信息

```
显示当前网络拓扑的统计信息
```

AI将调用`get_topology_statistics`工具显示拓扑统计。

### 5.4 网络扫描

#### 扫描网络范围

```
请扫描192.168.1.0/24网段，发现网络设备
```

AI将调用`scan_network_range`工具进行网络扫描。

#### 查看扫描结果

```
显示网络扫描的结果
```

AI将调用`get_scan_results`工具显示扫描发现的设备。

## 6. 高级功能

### 6.1 使用提示模板

#### 设备诊断模板

```
使用设备诊断模板分析Router-01的状态
```

AI将使用`device_diagnosis`模板，结合设备信息和接口状态进行专业分析。

#### 配置审查模板

```
使用配置审查模板检查Router-01的配置
```

AI将使用`config_review`模板对设备配置进行安全和最佳实践审查。

#### 网络故障排除模板

```
使用故障排除模板分析网络连接问题
```

AI将使用`network_troubleshooting`模板进行系统化的故障排除。

### 6.2 使用MCP资源

#### 访问设备信息资源

```
获取device://router-01的设备信息资源
```

#### 访问配置资源

```
获取device://router-01/config的配置资源
```

#### 访问拓扑资源

```
获取topology://的网络拓扑资源
```

### 6.3 Web界面使用

#### 启动Web界面

```bash
python server.py --web --port 8080
```

然后在浏览器中访问：http://localhost:8080

#### Web界面功能

1. **设备管理页面**
   - 添加、编辑、删除设备
   - 管理设备凭据
   - 查看设备状态

2. **终端页面**
   - 多标签页终端
   - 实时命令执行
   - 命令历史和补全

3. **拓扑页面**
   - 交互式拓扑图
   - 拓扑发现控制
   - 设备详情查看

## 7. 配置管理

### 7.1 数据存储配置

系统数据存储在以下位置：

```
NetBrainMCP/
├── data/
│   ├── devices.json      # 设备信息
│   └── credentials.json  # 凭据信息（加密存储）
├── resource_cache/       # 资源缓存
└── templates/           # 模板缓存
```

### 7.2 日志配置

日志文件位置：

```
NetBrainMCP/
└── logs/
    ├── netbrain_mcp.log    # 主日志
    ├── device_connector.log # 连接日志
    └── audit.log           # 审计日志
```

### 7.3 缓存配置

- **资源缓存**：默认5分钟TTL
- **设备配置缓存**：默认10分钟TTL
- **拓扑缓存**：默认15分钟TTL

可在代码中调整缓存设置：

```python
# 在mcp_resources.py中
self.default_cache_ttl = 300  # 5分钟
```

## 8. 故障排除

### 8.1 常见问题

#### 连接问题

**问题**：无法连接到设备
```
解决方案：
1. 检查设备IP地址是否正确
2. 验证网络连通性（ping测试）
3. 确认SSH/Telnet服务已启用
4. 检查凭据是否正确
5. 查看防火墙设置
```

**问题**：连接超时
```
解决方案：
1. 增加连接超时时间
2. 检查网络延迟
3. 确认设备负载不高
4. 检查并发连接限制
```

#### MCP服务器问题

**问题**：Claude Desktop无法连接MCP服务器
```
解决方案：
1. 检查配置文件路径是否正确
2. 验证Python路径和脚本路径
3. 检查权限设置
4. 查看Claude Desktop日志
5. 重启Claude Desktop
```

**问题**：工具调用失败
```
解决方案：
1. 检查Python环境和依赖
2. 查看MCP服务器日志
3. 验证工具参数格式
4. 检查设备连接状态
```

### 8.2 调试技巧

#### 启用详细日志

```bash
# 设置日志级别为DEBUG
export LOG_LEVEL=DEBUG
python server.py
```

#### 查看实时日志

```bash
# Linux/macOS
tail -f logs/netbrain_mcp.log

# Windows (PowerShell)
Get-Content logs/netbrain_mcp.log -Wait
```

#### 测试设备连接

```python
# 使用test_scrapli_connection工具
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

### 8.3 性能优化

#### 连接池配置

```python
# 在device_connector.py中调整连接池大小
MAX_CONNECTIONS = 10  # 最大并发连接数
CONNECTION_TIMEOUT = 30  # 连接超时时间
```

#### 缓存优化

```python
# 调整缓存策略
RESOURCE_CACHE_TTL = 300    # 资源缓存时间
CONFIG_CACHE_TTL = 600      # 配置缓存时间
TOPOLOGY_CACHE_TTL = 900    # 拓扑缓存时间
```

## 9. 最佳实践

### 9.1 设备管理最佳实践

1. **统一命名规范**
   ```
   设备命名：<位置>-<类型>-<编号>
   示例：DC1-RTR-01、DC1-SW-02
   ```

2. **标签使用**
   ```
   按功能分类：core, access, distribution
   按环境分类：production, staging, development
   按位置分类：datacenter1, branch-office, remote
   ```

3. **凭据管理**
   ```
   - 为不同设备类型创建专用凭据
   - 定期轮换密码
   - 使用SSH密钥认证（推荐）
   - 设置不同权限级别的凭据
   ```

### 9.2 安全最佳实践

1. **网络安全**
   ```
   - 限制MCP服务器的网络访问
   - 使用VPN或专用网络连接
   - 启用设备访问日志记录
   - 定期审查访问权限
   ```

2. **数据保护**
   ```
   - 定期备份设备和凭据数据
   - 使用强密码和加密
   - 限制文件系统访问权限
   - 监控异常访问活动
   ```

### 9.3 运维最佳实践

1. **监控和告警**
   ```
   - 监控MCP服务器状态
   - 设置设备连接告警
   - 记录重要操作日志
   - 定期检查系统资源使用
   ```

2. **维护计划**
   ```
   - 定期更新依赖包
   - 清理过期缓存文件
   - 归档旧日志文件
   - 验证备份数据完整性
   ```

## 10. API参考

### 10.1 MCP工具列表

#### 设备管理工具
- `list_devices` - 列出设备
- `add_device` - 添加设备
- `get_device` - 获取设备信息
- `update_device` - 更新设备
- `delete_device` - 删除设备

#### 连接管理工具
- `connect_device` - 连接设备
- `disconnect_device` - 断开连接
- `send_command` - 发送命令
- `send_commands` - 发送多个命令
- `get_active_connections` - 获取活动连接

#### 拓扑发现工具
- `discover_topology` - 发现拓扑
- `get_topology` - 获取拓扑
- `clear_topology` - 清除拓扑
- `get_device_neighbors` - 获取邻居
- `get_topology_statistics` - 拓扑统计

### 10.2 MCP资源列表

#### 设备资源
- `device/{device_id}` - 设备基本信息
- `device/{device_id}/config` - 设备配置
- `device/{device_id}/interfaces` - 接口信息
- `device/{device_id}/routes` - 路由信息
- `device/{device_id}/neighbors` - 邻居信息

#### 系统资源
- `credentials` - 凭据列表
- `system/status` - 系统状态
- `topology` - 网络拓扑
- `scan/results` - 扫描结果

### 10.3 提示模板列表

#### 诊断模板
- `device_diagnosis` - 设备诊断
- `network_troubleshooting` - 网络故障排除
- `performance_optimization` - 性能优化

#### 配置模板
- `config_review` - 配置审查
- `security_audit` - 安全审计
- `vlan_config` - VLAN配置

## 11. 扩展开发

### 11.1 添加新的MCP工具

```python
@mcp.tool()
async def custom_tool(param1: str, param2: int) -> Dict[str, Any]:
    """自定义工具描述"""
    # 工具实现逻辑
    return {"result": "success"}
```

### 11.2 添加新的MCP资源

```python
@resource_manager.register_resource("custom/{id}", ResourceType.CUSTOM)
async def get_custom_resource(id: str) -> Dict[str, Any]:
    """自定义资源描述"""
    # 资源获取逻辑
    return {"data": "custom_data"}
```

### 11.3 添加新的提示模板

```python
@template_manager.register_template(
    name="custom_template",
    description="自定义模板描述"
)
def custom_template(param1: str, param2: str) -> str:
    """自定义模板实现"""
    return f"自定义提示：{param1} - {param2}"
```

## 12. 社区和支持

### 12.1 获取帮助

- **文档**：查看完整的技术文档
- **示例**：参考examples目录中的使用示例
- **FAQ**：查看常见问题解答

### 12.2 贡献代码

欢迎为NetBrain MCP项目贡献代码：

1. Fork项目仓库
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request

### 12.3 报告问题

如发现bug或有功能建议，请：

1. 检查已知问题列表
2. 提供详细的错误信息
3. 包含复现步骤
4. 提交Issue或联系维护团队

---

通过本指南，您应该能够熟练使用NetBrain MCP系统进行网络设备管理和AI驱动的网络运维工作。如有任何问题，请参考故障排除部分或联系技术支持团队。
