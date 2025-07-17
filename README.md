[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/northlanems-netbrain-mcp-badge.png)](https://mseep.ai/app/northlanems-netbrain-mcp)

# NetBrain MCP

NetBrain MCP 是一个开源的网络运维整合平台，通过 Model Context Protocol (MCP) 连接大型语言模型（LLM）与网络设备。它允许 AI 助手通过标准化协议执行网络配置、诊断和管理任务。

**🎉 项目状态：已完成所有计划功能，具备生产环境部署条件**

## 功能特点

### 🔧 核心功能
- **网络设备管理** - 统一管理各种厂商（思科、华为等）的网络设备
- **设备连接** - 支持 SSH 和 Telnet 协议连接到网络设备
- **命令执行** - 远程执行网络命令并获取结果
- **凭据管理** - 安全管理设备访问凭据
- **MCP 协议支持** - 使大型语言模型能够访问和控制网络设备
- **资源提供功能** - 通过 URI 将设备、配置等资源提供给 LLM
- **提示模板系统** - 提供网络诊断、配置审查等专用提示模板

### 🌐 Web界面功能
- **专业终端体验** - 基于 XTerm.js 的多标签页终端，支持命令补全和历史记录
- **网络拓扑可视化** - 基于 D3.js 的交互式拓扑图，支持CDP/LLDP自动发现
- **设备管理界面** - 直观的设备添加、编辑和状态监控界面
- **会话管理** - 多设备连接会话管理，支持重连和心跳检测
- **主题系统** - 完整的暗色/明亮主题切换，包括登录页面
- **响应式设计** - 跨设备兼容的现代化用户界面

### 🚀 高级功能
- **自动拓扑发现** - 基于CDP/LLDP协议的网络拓扑自动识别
- **智能设备识别** - 内置厂商MAC地址识别功能，自动推断设备类型
- **数据持久化** - JSON文件存储系统，支持数据备份和恢复
- **多厂商支持** - 思科、华为、H3C等主流厂商设备适配
- **命令模板库** - 预置厂商特定的命令模板和配置片段
- **网络扫描** - 支持网络范围扫描和设备自动发现

## 技术架构

### 🔧 后端技术栈
- **语言**: Python 3.10+
- **MCP 框架**: FastMCP (基于 `mcp` Python 包)
- **Web 框架**: FastAPI + WebSocket
- **设备连接**: Scrapli (支持异步/同步混合模式)
- **异步支持**: 使用 `asyncio` 实现高效的网络操作
- **数据存储**: JSON文件存储 + 内存缓存
- **模块化设计**: 网络设备管理、连接器、工具管理和资源提供等独立模块

### 🌐 前端技术栈
- **终端模拟**: XTerm.js - 专业级终端体验
- **数据可视化**: D3.js - 网络拓扑可视化
- **实时通信**: WebSocket - 双向实时通信
- **界面框架**: 现代Web技术 + CSS3动画
- **主题系统**: CSS变量 + JavaScript主题管理
- **响应式设计**: Flexbox + Grid布局

## 系统组件

### 🔧 核心组件
- **工具管理器** (tool_manager.py): 管理工具的注册、分类和调用
- **设备管理器** (network_devices.py): 管理网络设备信息和凭据
- **连接管理器** (device_connector.py): 处理与网络设备的连接和命令执行
- **资源管理器** (mcp_resources.py): 管理 MCP 资源和提示模板
- **MCP 服务器** (server.py): 提供 MCP 接口，集成其他组件
- **模板系统** (template_system.py): 提供AI提示模板管理和渲染

### 🌐 Web界面组件
- **Web服务器** (web/app.py): FastAPI Web服务器，提供RESTful API和WebSocket支持
- **WebSocket终端** (web/static/js/terminal.js): 实时终端通信和XTerm.js集成
- **拓扑可视化** (web/static/js/topology.js): D3.js网络拓扑渲染引擎
- **主题管理** (web/static/js/theme.js): 全局主题切换和持久化
- **设备管理界面** (web/templates/): HTML模板和用户界面

### 🚀 扩展组件
- **拓扑发现引擎** (topology_discovery_improved.py): CDP/LLDP协议拓扑发现
- **网络扫描器** (network_scanner.py): 网络范围扫描和厂商MAC地址识别
- **设备提示模板** (device_prompts.py): 设备特定的AI提示模板
- **数据存储层** (data/): JSON文件存储和数据持久化
- **命令模板库** (templates/): 厂商特定的命令模板和配置片段

## 可用工具

NetBrain MCP 提供以下网络管理工具:

### 设备管理工具
- `list_devices` - 列出网络设备，支持按厂商、类型、状态、标签过滤
- `add_device` - 添加新的网络设备
- `get_device` - 获取设备详细信息
- `update_device` - 更新设备信息
- `delete_device` - 删除设备

### 凭据管理工具
- `add_credential` - 添加设备访问凭据
- `list_credentials` - 列出所有设备凭据

### 设备连接工具
- `connect_device` - 连接到网络设备
- `disconnect_device` - 断开与网络设备的连接
- `send_command` - 向网络设备发送命令
- `send_commands` - 向网络设备发送多个命令
- `get_active_connections` - 获取当前活动的设备连接

### 拓扑发现工具
- `discover_topology` - 基于CDP/LLDP协议自动发现网络拓扑
- `get_topology` - 获取已发现的拓扑数据
- `clear_topology` - 清除拓扑数据
- `get_device_neighbors` - 获取设备邻居信息
- `discover_device_neighbors` - 发现单个设备的邻居
- `get_topology_statistics` - 获取拓扑统计信息

### 网络扫描工具
- `scan_network_range` - 扫描网络地址范围
- `get_scan_results` - 获取扫描结果
- `get_scan_statistics` - 获取扫描统计信息
- `discover_devices_from_scan_results` - 从扫描结果中发现设备
- `clear_scan_results` - 清除扫描结果
- `scan_single_host` - 扫描单个主机

### 资源管理工具
- `list_resources` - 列出可用的 MCP 资源
- `get_resource` - 获取指定 URI 的资源
- `clear_resource_cache` - 清除资源缓存

### 模板管理工具
- `list_templates` - 列出可用的提示模板
- `render_template` - 渲染提示模板

### 测试工具
- `test_scrapli_connection` - 测试Scrapli连接
- `test_telnet_connection` - 测试Telnet连接
- `send_telnet_command` - 发送Telnet命令

## 可用资源

NetBrain MCP 提供以下 MCP 资源:

### 设备资源
- `device/{device_id}` - 获取设备详细信息
- `device/{device_id}/config` - 获取设备配置信息
- `device/{device_id}/interfaces` - 获取设备接口信息
- `device/{device_id}/routes` - 获取设备路由表信息
- `device/{device_id}/neighbors` - 获取设备邻居信息

### 拓扑资源
- `topology` - 获取网络拓扑数据
- `topology/statistics` - 获取拓扑统计信息

### 扫描资源
- `scan/results` - 获取网络扫描结果
- `scan/statistics` - 获取扫描统计信息
- `scan/result/{ip_address}` - 获取特定IP的扫描结果

### 系统资源
- `greeting/{name}` - 获取个性化问候语
- `system/status` - 获取系统状态信息
- `credentials` - 获取所有凭据信息（敏感信息已脱敏）

## 提示模板

NetBrain MCP 提供以下提示模板:

- `device_diagnosis` - 设备诊断提示模板
- `config_review` - 设备配置审查提示模板
- `route_analysis` - 路由分析提示模板
- `network_diagnosis` - 网络诊断提示模板
- `vlan_config` - VLAN配置生成模板
- `network_topology` - 网络拓扑分析模板
- `network_security` - 网络安全评估模板

## 运行服务器

### 🔧 MCP服务器模式

#### 使用 Python 直接运行

```bash
python server.py
```

#### 使用 MCP 开发工具运行

```bash
mcp run server.py
```

#### 带调试界面运行 (MCP Inspector)

```bash
mcp dev server.py
```

### 🚀 生产环境部署

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器
python server.py
```

## 使用示例

### 🌐 Web界面使用

1. **启动服务器**
   ```bash
   python server.py
   ```

2. **访问Web界面**
   - 打开浏览器访问 `http://localhost:8088`
   - 使用登录页面进入系统

3. **使用终端功能**
   - 点击"终端"标签页
   - 添加新设备或选择现有设备
   - 建立SSH/Telnet连接
   - 享受专业级终端体验（命令补全、历史记录等）

4. **查看网络拓扑**
   - 点击"网络拓扑"标签页  
   - 点击"发现拓扑"开始自动扫描
   - 查看可视化的网络拓扑图
   - 双击节点可快速连接设备

5. **管理设备**
   - 在"设备"页面添加、编辑设备信息
   - 配置设备凭据和连接参数
   - 监控设备在线状态

### 🔧 MCP协议使用

可以通过以下步骤测试功能:

1. 运行 MCP 服务器
2. 使用 MCP Inspector 查看可用工具
3. 使用 `list_devices` 工具列出预配置的设备
4. 使用设备 ID 和凭据 ID 连接设备
5. 发送命令查看模拟输出

### 📊 资源访问示例

获取设备信息:
```
GET device/1
```

获取设备配置:
```
GET device/1/config
```

获取拓扑数据:
```
GET topology
```

使用提示模板:
```
POST render_template
{
  "template_name": "device_diagnosis",
  "context": {
    "device_info": "...",
    "interfaces_info": "..."
  }
}
```

### 🚀 高级功能示例

**自动拓扑发现**:
```python
# 通过MCP工具调用
discover_topology({
  "device_ids": "device1,device2"
})
```

**网络扫描**:
```python
# 扫描网络范围
scan_network_range({
  "network": "192.168.1.0/24",
  "timeout": 3.0,
  "auto_create_devices": true
})
```

**批量设备配置**:
```python
# 使用命令模板
send_commands({
  "device_id": "cisco_router_1", 
  "credential_id": "admin_cred",
  "commands": "interface gi0/1;ip address 192.168.10.1 255.255.255.0;no shutdown"
})
```

## 项目亮点

### 🎯 已完成的核心功能

✅ **完整的MCP协议实现** - 基于FastMCP的标准化AI-设备通信协议  
✅ **专业级终端体验** - 基于XTerm.js，支持命令补全、历史记录、真实提示符  
✅ **网络拓扑可视化** - 基于D3.js的交互式拓扑图，支持CDP/LLDP自动发现  
✅ **多厂商设备支持** - 思科、华为、H3C等主流厂商统一接入  
✅ **现代化Web界面** - 响应式设计，暗色/明亮主题，跨设备兼容  
✅ **数据持久化存储** - JSON文件存储，自动备份恢复  
✅ **智能设备识别** - 内置厂商MAC地址库，自动设备类型推断  
✅ **网络扫描功能** - 支持大规模网络发现和设备自动识别

### 🚀 技术特色

- **高度模块化架构** - 基于抽象工厂和策略模式的可扩展设计
- **异步性能优化** - 全异步架构带来高并发处理能力  
- **AI驱动操作** - MCP协议实现AI与网络设备的无缝集成
- **专业工程实践** - 完整的错误处理、日志记录、配置管理
- **混合连接模式** - Scrapli异步/同步智能适配，确保最佳兼容性

### 🔮 未来扩展方向

虽然项目核心功能已完成，未来可考虑以下增强：

- **企业级功能** - 用户权限管理、审计日志、合规报告
- **监控告警** - 网络性能监控、故障自动诊断、预测性维护  
- **协议扩展** - SNMP、NETCONF、RESTCONF等更多网络协议
- **虚拟化集成** - eNSP、GNS3、EVE-NG等网络模拟器支持
- **AI能力增强** - 网络故障智能分析、配置优化建议

## 项目团队

- **技术负责人：Koreyoshi** - MCP协议实现、系统架构设计
- **功能开发：Koreyoshi** - 设备管理、数据存储、拓扑发现  
- **前端开发：Koreyoshi** - Web界面、终端功能、可视化设计

## 贡献

欢迎通过 Pull Requests 或 Issues 提交您的建议和改进。
