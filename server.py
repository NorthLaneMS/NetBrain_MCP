from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Optional, Any
import asyncio
import logging
import sys
import os
import glob
import json

# 导入我们创建的模块
from tool_manager import tool_manager, ToolCategory
from network_devices import (
    device_manager,
    NetworkDevice,
    DeviceCredential,
    DeviceVendor,
    DeviceType,
    DeviceStatus,
    ConnectionProtocol
)
from device_connector import connection_manager, CommandResult, SCRAPLI_IMPORT_SUCCESS
# 导入资源管理模块
from mcp_resources import (
    resource_manager,
    ResourceType
)
# 导入新的模板系统
from template_system import (
    template_manager,
    render_template_with_resources,
    Message,
    UserMessage,
    AssistantMessage,
    SystemMessage
)
# 导入设备命令提示模板系统
import device_prompts
# 导入拓扑发现模块
from topology_discovery_improved import create_improved_topology_discovery
# 导入网络扫描模块
from network_scanner import create_network_scanner

# 引入相同的日志格式化处理
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

logger = logging.getLogger("netbrain_mcp")

# 创建一个MCP服务器
mcp = FastMCP("NetBrain MCP")

# 创建拓扑发现引擎实例
topology_discovery = create_improved_topology_discovery(device_manager, connection_manager)

# 创建网络扫描器实例
network_scanner = create_network_scanner(device_manager)

# 工具分类：设备管理
@mcp.tool()
async def list_devices(
    vendor: Optional[str] = None,
    device_type: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    列出网络设备，支持过滤
    
    Args:
        vendor: 设备厂商，可选值：cisco, huawei, h3c, juniper, arista, fortinet, checkpoint, other
        device_type: 设备类型，可选值：router, switch, firewall, load_balancer, wireless_controller, access_point, other
        status: 设备状态，可选值：online, offline, unreachable, maintenance, unknown
        tag: 标签过滤
        
    Returns:
        设备列表
    """
    # 转换过滤参数
    vendor_enum = DeviceVendor(vendor) if vendor else None
    device_type_enum = DeviceType(device_type) if device_type else None
    status_enum = DeviceStatus(status) if status else None
    
    # 获取设备列表
    devices = device_manager.list_devices(
        vendor=vendor_enum,
        device_type=device_type_enum,
        status=status_enum,
        tag=tag
    )
    
    # 转换为字典列表
    return [device.to_dict() for device in devices]

@mcp.tool()
async def add_device(
    name: str,
    ip_address: str,
    device_type: str,
    vendor: str,
    platform: str = "",
    model: str = "",
    os_version: str = "",
    location: str = "",
    description: str = "",
    tags: str = ""
) -> Dict[str, Any]:
    """
    添加新的网络设备
    
    Args:
        name: 设备名称
        ip_address: 设备IP地址
        device_type: 设备类型，可选值：router, switch, firewall, load_balancer, wireless_controller, access_point, other
        vendor: 设备厂商，可选值：cisco, huawei, h3c, juniper, arista, fortinet, checkpoint, other
        platform: 设备平台(scrapli平台类型)，如 cisco_iosxe, huawei_vrp, juniper_junos 等
        model: 设备型号
        os_version: 操作系统版本
        location: 设备位置
        description: 设备描述
        tags: 设备标签，使用逗号分隔多个标签
        
    Returns:
        新添加的设备信息
    """
    # 转换参数
    device_type_enum = DeviceType(device_type)
    vendor_enum = DeviceVendor(vendor)
    
    # 如果未提供platform，根据vendor推断
    if not platform:
        if vendor.lower() == "cisco":
            platform = "cisco_iosxe"
        elif vendor.lower() == "huawei":
            platform = "huawei_vrp"
        elif vendor.lower() == "juniper":
            platform = "juniper_junos"
        elif vendor.lower() == "arista":
            platform = "arista_eos"
        else:
            platform = f"{vendor.lower()}"
    
    # 处理标签
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    # 创建设备对象
    device = NetworkDevice(
        name=name,
        ip_address=ip_address,
        device_type=device_type_enum,
        vendor=vendor_enum,
        platform=platform,
        model=model,
        os_version=os_version,
        location=location,
        description=description,
        tags=tag_list
    )
    
    # 添加设备
    device_id = device_manager.add_device(device)
    
    return device.to_dict()

@mcp.tool()
async def get_device(device_id: str) -> Optional[Dict[str, Any]]:
    """
    获取设备详细信息
    
    Args:
        device_id: 设备ID
        
    Returns:
        设备信息或None
    """
    device = device_manager.get_device(device_id)
    if device:
        return device.to_dict()
    return None

@mcp.tool()
async def update_device(
    device_id: str,
    name: str = "",
    ip_address: str = "",
    model: str = "",
    os_version: str = "",
    status: str = "",
    location: str = "",
    description: str = "",
    tags: str = ""
) -> Optional[Dict[str, Any]]:
    """
    更新设备信息
    
    Args:
        device_id: 设备ID
        name: 设备名称
        ip_address: 设备IP地址
        model: 设备型号
        os_version: 操作系统版本
        status: 设备状态，可选值：online, offline, unreachable, maintenance, unknown
        location: 设备位置
        description: 设备描述
        tags: 设备标签，使用逗号分隔多个标签
        
    Returns:
        更新后的设备信息或None
    """
    # 准备更新参数
    update_kwargs = {}
    if name:
        update_kwargs["name"] = name
    if ip_address:
        update_kwargs["ip_address"] = ip_address
    if model:
        update_kwargs["model"] = model
    if os_version:
        update_kwargs["os_version"] = os_version
    if status:
        update_kwargs["status"] = DeviceStatus(status)
    if location:
        update_kwargs["location"] = location
    if description:
        update_kwargs["description"] = description
    if tags:
        # 将逗号分隔的标签转换为列表
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        update_kwargs["tags"] = tag_list
    
    # 更新设备
    device = device_manager.update_device(device_id, **update_kwargs)
    if device:
        return device.to_dict()
    return None

@mcp.tool()
async def delete_device(device_id: str) -> bool:
    """
    删除设备
    
    Args:
        device_id: 设备ID
        
    Returns:
        是否删除成功
    """
    return device_manager.delete_device(device_id)

# 工具分类：凭据管理
@mcp.tool()
async def add_credential(
    name: str,
    username: str,
    password: str = "",
    protocol: str = "ssh",
    port: Optional[int] = None,
    enable_password: str = "",
    ssh_key_file: str = ""
) -> Dict[str, Any]:
    """
    添加设备凭据
    
    Args:
        name: 凭据名称
        username: 用户名
        password: 密码
        protocol: 连接协议，可选值：ssh, telnet, snmp, http, https, netconf
        port: 端口号，可选（默认SSH=22, Telnet=23）
        enable_password: 特权模式密码（思科设备）
        ssh_key_file: SSH密钥文件路径
        
    Returns:
        凭据ID
    """
    # 确保密码或SSH密钥的要求基于协议
    if protocol.lower() == "ssh" and not password and not ssh_key_file:
        return {"success": False, "message": "SSH连接需要提供密码或SSH密钥文件"}
    elif protocol.lower() != "ssh" and not password:
        return {"success": False, "message": f"{protocol.upper()}连接需要提供密码"}
    
    # 转换参数
    protocol_enum = ConnectionProtocol(protocol.lower())
    
    # 设置默认端口
    if port is None:
        if protocol_enum == ConnectionProtocol.SSH:
            port = 22
        elif protocol_enum == ConnectionProtocol.TELNET:
            port = 23
        elif protocol_enum == ConnectionProtocol.HTTP:
            port = 80
        elif protocol_enum == ConnectionProtocol.HTTPS:
            port = 443
        else:
            port = 0
    
    # 记录凭据信息(不包含敏感信息)
    logger.info(f"添加凭据: name={name}, username={username}, protocol={protocol}, port={port}")
    if ssh_key_file:
        logger.info(f"使用SSH密钥文件: {ssh_key_file}")
    
    # 创建凭据对象
    credential = DeviceCredential(
        name=name,
        username=username,
        password=password,
        protocol=protocol_enum,
        port=port,
        enable_password=enable_password,
        ssh_key_file=ssh_key_file
    )
    
    # 添加凭据
    credential_id = device_manager.add_credential(credential)
    
    return {"success": True, "id": credential_id, "name": name}

@mcp.tool()
async def list_credentials() -> List[Dict[str, Any]]:
    """
    列出所有设备凭据
    
    Returns:
        凭据列表
    """
    credentials = device_manager.list_credentials()
    return [
        {
            "id": cred.id,
            "name": cred.name,
            "username": cred.username,
            "password": cred.password,
            "protocol": cred.protocol.value,
            "port": cred.port,
            "ssh_key_file": cred.ssh_key_file
        }
        for cred in credentials
    ]

# 工具分类：设备连接
@mcp.tool()
async def connect_device(device_id: str, credential_id: str) -> Dict[str, Any]:
    """
    连接到网络设备
    
    Args:
        device_id: 设备ID
        credential_id: 凭据ID
        
    Returns:
        连接结果
    """
    # 获取设备和凭据
    device = device_manager.get_device(device_id)
    credential = device_manager.get_credential(credential_id)
    
    if not device:
        return {"success": False, "message": f"设备不存在: {device_id}"}
    
    if not credential:
        return {"success": False, "message": f"凭据不存在: {credential_id}"}
    
    # 记录连接信息
    logger.info(f"尝试连接设备: {device.name} ({device.ip_address}) 使用凭据: {credential.name}")
    logger.info(f"连接协议: {credential.protocol.value}, 端口: {credential.port or '默认'}")
    
    # 连接设备
    success, error = await connection_manager.connect_device(device, credential)
    
    if success:
        # 获取更多的连接信息
        prompt = ""
        version_info = ""
        
        try:
            # 获取连接的connector
            connection_key = f"{device_id}_{credential_id}"
            connector = connection_manager.active_connections.get(connection_key)
            
            if connector and connector.connection:
                # 获取提示符
                if hasattr(connector.connection, "get_prompt"):
                    if asyncio.iscoroutinefunction(connector.connection.get_prompt):
                        prompt = await connector.connection.get_prompt()
                    else:
                        prompt = await asyncio.to_thread(connector.connection.get_prompt)
                    logger.info(f"成功获取设备提示符: {prompt}")
                
                # 使用与test_scrapli_connection相同的方式获取版本信息
                try:
                    from scrapli import Scrapli
                    
                    # 确定平台类型
                    platform = device.platform if hasattr(device, 'platform') and device.platform else ""
                    
                    # 根据平台类型选择命令
                    if "huawei" in platform.lower():
                        command = "display version"
                    elif "cisco" in platform.lower():
                        command = "show version" 
                    else:
                        command = "show version"
                    
                    logger.info(f"尝试获取版本信息，平台: {platform}，命令: {command}")
                    
                    # 直接使用Scrapli连接对象发送命令
                    if hasattr(connector.connection, "send_command"):
                        # 等待1秒确保连接稳定
                        await asyncio.sleep(1)
                        
                        if asyncio.iscoroutinefunction(connector.connection.send_command):
                            resp = await connector.connection.send_command(command)
                            if hasattr(resp, "result"):
                                version_info = resp.result
                            else:
                                version_info = str(resp)
                        else:
                            # 同步调用需要运行在线程中
                            resp = await asyncio.to_thread(connector.connection.send_command, command)
                            if hasattr(resp, "result"):
                                version_info = resp.result
                            else:
                                version_info = str(resp)
                        
                        logger.info(f"成功获取版本信息，长度: {len(version_info)}")
                        
                        # 限制长度
                        if len(version_info) > 500:
                            version_info = version_info[:500] + "..."
                    else:
                        logger.warning("连接对象没有send_command方法")
                        version_info = "无法获取版本信息：连接对象不支持发送命令"
                except Exception as e:
                    logger.warning(f"获取版本信息时出错: {str(e)}")
                    # 回退到使用connection_manager发送命令
                    try:
                        result, _ = await connection_manager.send_command(
                            device_id=device_id,
                            credential_id=credential_id,
                            command=command,
                            timeout=60
                        )
                        
                        if result and result.success:
                            version_info = result.output
                            if len(version_info) > 500:
                                version_info = version_info[:500] + "..."
                        else:
                            version_info = "无法获取版本信息"
                    except Exception as e2:
                        logger.error(f"备用方法获取版本信息也失败: {str(e2)}")
                        version_info = "无法获取版本信息"
        except Exception as e:
            logger.warning(f"获取设备详细信息时出错: {str(e)}")
            version_info = "获取版本信息时出错"
        
        return {
            "success": True, 
            "message": f"成功连接到设备: {device.name} ({device.ip_address})",
            "protocol": credential.protocol.value,
            "prompt": prompt,
            "version_info": version_info
        }
    else:
        logger.error(f"连接设备失败: {device.name} ({device.ip_address}), 错误: {error}")
        return {"success": False, "message": f"连接设备失败: {error}"}

@mcp.tool()
async def disconnect_device(device_id: str, credential_id: str) -> Dict[str, Any]:
    """
    断开与网络设备的连接
    
    Args:
        device_id: 设备ID
        credential_id: 凭据ID
        
    Returns:
        断开连接结果
    """
    # 断开连接
    success, error = await connection_manager.disconnect_device(device_id, credential_id)
    
    if success:
        return {"success": True, "message": "成功断开连接"}
    else:
        return {"success": False, "message": f"断开连接失败: {error}"}

@mcp.tool()
async def send_command(
    device_id: str,
    credential_id: str,
    command: str,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    向网络设备发送命令
    
    Args:
        device_id: 设备ID
        credential_id: 凭据ID
        command: 要执行的命令
        timeout: 命令超时时间（秒）
        
    Returns:
        命令执行结果
    """
    # 发送命令
    result, error = await connection_manager.send_command(
        device_id=device_id,
        credential_id=credential_id,
        command=command,
        timeout=timeout
    )
    
    if result:
        return {
            "success": result.success,
            "command": result.command,
            "output": result.output,
            "error_message": result.error_message,
            "execution_time": result.execution_time.isoformat()
        }
    else:
        return {
            "success": False,
            "command": command,
            "output": "",
            "error_message": error,
            "execution_time": None
        }

@mcp.tool()
async def send_commands(
    device_id: str,
    credential_id: str,
    commands: str,
    timeout: int = 30
) -> List[Dict[str, Any]]:
    """
    向网络设备发送多个命令
    
    Args:
        device_id: 设备ID
        credential_id: 凭据ID
        commands: 要执行的命令列表，使用分号(;)分隔多个命令
        timeout: 每个命令的超时时间（秒）
        
    Returns:
        命令执行结果列表
    """
    # 将分号分隔的命令字符串转换为列表
    command_list = [cmd.strip() for cmd in commands.split(';') if cmd.strip()]
    
    if not command_list:
        return [{"success": False, "message": "未提供有效的命令"}]
        
    # 发送命令
    results, error = await connection_manager.send_commands(
        device_id=device_id,
        credential_id=credential_id,
        commands=command_list,
        timeout=timeout
    )
    
    if results:
        return [
            {
                "success": result.success,
                "command": result.command,
                "output": result.output,
                "error_message": result.error_message,
                "execution_time": result.execution_time.isoformat()
            }
            for result in results
        ]
    else:
        return [
            {
                "success": False,
                "command": command,
                "output": "",
                "error_message": error,
                "execution_time": None
            }
            for command in command_list
        ]

@mcp.tool()
async def get_active_connections() -> List[Dict[str, Any]]:
    """
    获取活动连接列表
    
    Returns:
        活动连接信息列表
    """
    return connection_manager.get_active_connections()

# 工具分类：拓扑发现
@mcp.tool()
async def discover_topology(device_ids: str) -> Dict[str, Any]:
    """
    从指定设备开始发现网络拓扑
    
    Args:
        device_ids: 设备ID列表，用逗号分隔，如"device1,device2"
        
    Returns:
        拓扑发现结果
    """
    try:
        # 解析设备ID列表
        if isinstance(device_ids, str):
            device_id_list = [device_id.strip() for device_id in device_ids.split(',') if device_id.strip()]
        else:
            device_id_list = device_ids
        
        if not device_id_list:
            return {"success": False, "message": "请提供至少一个设备ID"}
        
        logger.info(f"开始拓扑发现，设备列表: {device_id_list}")
        
        # 验证设备是否存在
        valid_devices = []
        for device_id in device_id_list:
            device = device_manager.get_device(device_id)
            if device:
                valid_devices.append(device_id)
            else:
                logger.warning(f"设备不存在: {device_id}")
        
        if not valid_devices:
            return {"success": False, "message": "没有找到有效的设备"}
        
        # 开始拓扑发现
        topology = await topology_discovery.discover_topology_from_devices(valid_devices)
        
        return {
            "success": True,
            "message": f"拓扑发现完成，发现{len(topology.nodes)}个节点，{len(topology.links)}条链路",
            "topology": topology.to_dict()
        }
    except Exception as e:
        logger.error(f"拓扑发现失败: {e}")
        return {"success": False, "message": f"拓扑发现失败: {str(e)}"}

@mcp.tool()
async def get_topology() -> Dict[str, Any]:
    """
    获取当前网络拓扑
    
    Returns:
        当前拓扑信息
    """
    try:
        topology = topology_discovery.get_topology()
        return {
            "success": True,
            "topology": topology.to_dict()
        }
    except Exception as e:
        logger.error(f"获取拓扑失败: {e}")
        return {"success": False, "message": f"获取拓扑失败: {str(e)}"}

@mcp.tool()
async def clear_topology() -> Dict[str, Any]:
    """
    清空拓扑数据
    
    Returns:
        操作结果
    """
    try:
        topology_discovery.clear_topology()
        return {"success": True, "message": "拓扑数据已清空"}
    except Exception as e:
        logger.error(f"清空拓扑失败: {e}")
        return {"success": False, "message": f"清空拓扑失败: {str(e)}"}

@mcp.tool()
async def get_device_neighbors(device_id: str) -> Dict[str, Any]:
    """
    获取指定设备的邻居设备
    
    Args:
        device_id: 设备ID
        
    Returns:
        邻居设备列表
    """
    try:
        topology = topology_discovery.get_topology()
        neighbors = topology.get_device_neighbors(device_id)
        
        # 获取邻居设备的详细信息
        neighbor_details = []
        for neighbor_id in neighbors:
            device = device_manager.get_device(neighbor_id)
            if device:
                neighbor_details.append(device.to_dict())
        
        return {
            "success": True,
            "device_id": device_id,
            "neighbors": neighbor_details
        }
    except Exception as e:
        logger.error(f"获取设备邻居失败: {e}")
        return {"success": False, "message": f"获取设备邻居失败: {str(e)}"}

@mcp.tool()
async def discover_device_neighbors(device_id: str) -> Dict[str, Any]:
    """
    发现单个设备的邻居（实时发现）
    
    Args:
        device_id: 设备ID
        
    Returns:
        发现的邻居信息
    """
    try:
        device = device_manager.get_device(device_id)
        if not device:
            return {"success": False, "message": f"设备不存在: {device_id}"}
        
        logger.info(f"开始发现设备 {device.name} 的邻居")
        
        # 发现设备邻居
        neighbors, interfaces = await topology_discovery.discover_device_neighbors(device)
        
        return {
            "success": True,
            "device_id": device_id,
            "device_name": device.name,
            "neighbors": neighbors,
            "interfaces": [iface.to_dict() for iface in interfaces],
            "neighbor_count": len(neighbors),
            "interface_count": len(interfaces)
        }
    except Exception as e:
        logger.error(f"发现设备邻居失败: {e}")
        return {"success": False, "message": f"发现设备邻居失败: {str(e)}"}

@mcp.tool()
async def get_topology_statistics() -> Dict[str, Any]:
    """
    获取拓扑统计信息
    
    Returns:
        拓扑统计数据
    """
    try:
        topology = topology_discovery.get_topology()
        
        # 统计不同协议的链路数量
        protocol_stats = {}
        for link in topology.links:
            protocol = link.protocol.value
            protocol_stats[protocol] = protocol_stats.get(protocol, 0) + 1
        
        # 统计不同厂商的设备数量
        vendor_stats = {}
        for node in topology.nodes.values():
            vendor = node.vendor
            vendor_stats[vendor] = vendor_stats.get(vendor, 0) + 1
        
        return {
            "success": True,
            "total_nodes": len(topology.nodes),
            "total_links": len(topology.links),
            "protocol_distribution": protocol_stats,
            "vendor_distribution": vendor_stats,
            "last_discovery": topology.last_discovery.isoformat() if topology.last_discovery else None,
            "discovery_scope": topology.discovery_scope
        }
    except Exception as e:
        logger.error(f"获取拓扑统计失败: {e}")
        return {"success": False, "message": f"获取拓扑统计失败: {str(e)}"}

# 工具分类：网络扫描
@mcp.tool()
async def scan_network_range(
    network: str,
    timeout: float = 3.0,
    max_concurrent: int = 50,
    ping_enabled: bool = True,
    port_scan_enabled: bool = True,
    snmp_enabled: bool = True,
    auto_create_devices: bool = False
) -> Dict[str, Any]:
    """
    扫描指定网络范围内的活跃设备
    
    Args:
        network: 网络范围，如 "192.168.1.0/24" 或 "10.0.0.0/16"
        timeout: 扫描超时时间（秒）
        max_concurrent: 最大并发扫描数
        ping_enabled: 是否启用ping扫描
        port_scan_enabled: 是否启用端口扫描
        snmp_enabled: 是否启用SNMP扫描
        auto_create_devices: 是否自动创建发现的设备
        
    Returns:
        扫描结果
    """
    try:
        from network_scanner import ScanConfiguration
        
        # 创建扫描配置
        config = ScanConfiguration(
            timeout=timeout,
            max_concurrent=max_concurrent,
            ping_enabled=ping_enabled,
            port_scan_enabled=port_scan_enabled,
            snmp_enabled=snmp_enabled
        )
        
        logger.info(f"开始网络扫描: {network}")
        
        # 执行网络扫描
        scan_results = await network_scanner.scan_network_range(network, config)
        
        # 如果启用自动创建设备，则创建发现的设备
        discovered_devices = []
        if auto_create_devices:
            discovered_devices = await network_scanner.discover_devices_from_scan(scan_results, auto_create=True)
        
        return {
            "success": True,
            "message": f"网络扫描完成，发现 {len(scan_results)} 个活跃主机",
            "network_range": network,
            "alive_hosts": len(scan_results),
            "scan_results": [result.to_dict() for result in scan_results],
            "auto_created_devices": len(discovered_devices),
            "discovered_devices": [device.to_dict() for device in discovered_devices]
        }
    except Exception as e:
        logger.error(f"网络扫描失败: {e}")
        return {"success": False, "message": f"网络扫描失败: {str(e)}"}

@mcp.tool()
async def get_scan_results(
    ip_address: Optional[str] = None,
    alive_only: bool = True
) -> Dict[str, Any]:
    """
    获取网络扫描结果
    
    Args:
        ip_address: 特定IP地址，如果不提供则返回所有结果
        alive_only: 是否只返回活跃主机
        
    Returns:
        扫描结果
    """
    try:
        if ip_address:
            # 获取特定IP的扫描结果
            result = network_scanner.scan_results.get(ip_address)
            if result:
                return {
                    "success": True,
                    "scan_result": result.to_dict()
                }
            else:
                return {"success": False, "message": f"未找到IP {ip_address} 的扫描结果"}
        else:
            # 获取所有扫描结果
            results = list(network_scanner.scan_results.values())
            if alive_only:
                results = [r for r in results if r.is_alive]
            
            return {
                "success": True,
                "total_results": len(results),
                "scan_results": [result.to_dict() for result in results]
            }
    except Exception as e:
        logger.error(f"获取扫描结果失败: {e}")
        return {"success": False, "message": f"获取扫描结果失败: {str(e)}"}

@mcp.tool()
async def get_scan_statistics() -> Dict[str, Any]:
    """
    获取网络扫描统计信息
    
    Returns:
        扫描统计数据
    """
    try:
        stats = network_scanner.get_scan_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"获取扫描统计失败: {e}")
        return {"success": False, "message": f"获取扫描统计失败: {str(e)}"}

@mcp.tool()
async def discover_devices_from_scan_results(
    min_response_time: Optional[float] = None,
    required_ports: str = "",
    vendor_filter: Optional[str] = None,
    device_type_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    从扫描结果中发现并创建设备
    
    Args:
        min_response_time: 最小响应时间过滤（毫秒）
        required_ports: 必需的开放端口，使用逗号分隔，如"22,23,161"
        vendor_filter: 厂商过滤，如"cisco"、"huawei"
        device_type_filter: 设备类型过滤，如"switch"、"router"
        
    Returns:
        发现和创建的设备信息
    """
    try:
        # 获取所有活跃的扫描结果
        all_results = [r for r in network_scanner.scan_results.values() if r.is_alive]
        
        # 应用过滤条件
        filtered_results = []
        for result in all_results:
            # 响应时间过滤
            if min_response_time and result.response_time and result.response_time > min_response_time:
                continue
            
            # 端口过滤
            if required_ports:
                required_port_list = [int(p.strip()) for p in required_ports.split(',') if p.strip().isdigit()]
                if not all(port in result.open_ports for port in required_port_list):
                    continue
            
            # 厂商过滤
            if vendor_filter and result.vendor:
                if vendor_filter.lower() not in result.vendor.lower():
                    continue
            
            # 设备类型过滤
            if device_type_filter and result.device_type:
                if device_type_filter.lower() not in result.device_type.lower():
                    continue
            
            filtered_results.append(result)
        
        # 从过滤后的结果创建设备
        discovered_devices = await network_scanner.discover_devices_from_scan(filtered_results, auto_create=True)
        
        return {
            "success": True,
            "message": f"从 {len(filtered_results)} 个扫描结果中创建了 {len(discovered_devices)} 个设备",
            "filtered_results_count": len(filtered_results),
            "created_devices_count": len(discovered_devices),
            "created_devices": [device.to_dict() for device in discovered_devices]
        }
    except Exception as e:
        logger.error(f"从扫描结果创建设备失败: {e}")
        return {"success": False, "message": f"从扫描结果创建设备失败: {str(e)}"}

@mcp.tool()
async def clear_scan_results() -> Dict[str, Any]:
    """
    清空网络扫描结果
    
    Returns:
        操作结果
    """
    try:
        network_scanner.clear_scan_results()
        return {"success": True, "message": "扫描结果已清空"}
    except Exception as e:
        logger.error(f"清空扫描结果失败: {e}")
        return {"success": False, "message": f"清空扫描结果失败: {str(e)}"}

@mcp.tool()
async def scan_single_host(
    ip_address: str,
    timeout: float = 3.0,
    port_scan_enabled: bool = True,
    snmp_enabled: bool = True
) -> Dict[str, Any]:
    """
    扫描单个主机
    
    Args:
        ip_address: 目标IP地址
        timeout: 扫描超时时间（秒）
        port_scan_enabled: 是否启用端口扫描
        snmp_enabled: 是否启用SNMP扫描
        
    Returns:
        单个主机扫描结果
    """
    try:
        from network_scanner import ScanConfiguration
        
        # 创建扫描配置
        config = ScanConfiguration(
            timeout=timeout,
            port_scan_enabled=port_scan_enabled,
            snmp_enabled=snmp_enabled
        )
        
        logger.info(f"开始扫描单个主机: {ip_address}")
        
        # 执行单个主机扫描
        scan_result = await network_scanner.scan_single_host(ip_address, config)
        
        # 保存到扫描结果
        network_scanner.scan_results[ip_address] = scan_result
        network_scanner.save_scan_results()
        
        return {
            "success": True,
            "message": f"主机扫描完成: {ip_address}",
            "is_alive": scan_result.is_alive,
            "scan_result": scan_result.to_dict()
        }
    except Exception as e:
        logger.error(f"扫描单个主机失败: {e}")
        return {"success": False, "message": f"扫描单个主机失败: {str(e)}"}

# =================== 资源工具 ===================

@mcp.tool()
async def list_resources() -> List[Dict[str, Any]]:
    """
    列出可用的MCP资源
    
    Returns:
        资源列表
    """
    return resource_manager.list_available_resources()

@mcp.tool()
async def get_resource(uri: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    获取指定URI的资源
    
    Args:
        uri: 资源URI
        use_cache: 是否使用缓存
        
    Returns:
        资源内容
    """
    return await resource_manager.get_resource(uri, use_cache)

@mcp.tool()
async def clear_resource_cache(uri: Optional[str] = None) -> Dict[str, Any]:
    """
    清除资源缓存
    
    Args:
        uri: 要清除的特定资源URI，如果为None则清除所有缓存
        
    Returns:
        操作结果
    """
    success = resource_manager.clear_cache(uri)
    if success:
        if uri:
            return {"success": True, "message": f"已清除资源缓存: {uri}"}
        else:
            return {"success": True, "message": "已清除所有资源缓存"}
    else:
        return {"success": False, "message": "清除缓存失败"}

# =================== 模板工具 ===================

@mcp.tool()
async def list_templates() -> List[Dict[str, Any]]:
    """
    列出可用的提示模板
    
    Returns:
        模板列表
    """
    return template_manager.list_templates()

@mcp.tool()
async def render_template(
    template_name: str,
    context: str = "{}",
    resource_uris: str = ""
) -> Dict[str, Any]:
    """
    渲染提示模板
    
    Args:
        template_name: 模板名称
        context: JSON格式的渲染上下文，如 {"name": "value"}
        resource_uris: 资源URI映射，格式为 "key1=uri1,key2=uri2"
        
    Returns:
        渲染结果
    """
    try:
        # 解析context
        context_dict = {}
        if context.strip():
            try:
                context_dict = json.loads(context)
                if not isinstance(context_dict, dict):
                    context_dict = {}
            except json.JSONDecodeError:
                logger.warning(f"无法解析context JSON: {context}")
                return {"success": False, "message": "无效的JSON上下文格式"}
        
        # 解析resource_uris
        resource_dict = {}
        if resource_uris.strip():
            uri_pairs = resource_uris.split(',')
            for pair in uri_pairs:
                if '=' in pair:
                    key, uri = pair.split('=', 1)
                    resource_dict[key.strip()] = uri.strip()
        
        if resource_dict:
            # 渲染带有资源的模板
            result = await render_template_with_resources(
                template_name=template_name, 
                context=context_dict, 
                resource_uris=resource_dict,
                resource_manager=resource_manager
            )
        else:
            # 渲染简单模板
            result = template_manager.render_template(template_name, context_dict)
        
        if result:
            if isinstance(result, list):
                # 处理消息列表
                messages = [
                    {
                        "role": msg.role,
                        "content": msg.content
                    } for msg in result
                ]
                return {"success": True, "messages": messages}
            else:
                # 处理字符串结果
                return {"success": True, "rendered_template": result}
        else:
            return {"success": False, "message": f"渲染模板失败: {template_name}"}
    except Exception as e:
        logger.error(f"渲染模板异常: {str(e)}")
        return {"success": False, "message": f"渲染模板异常: {str(e)}"}

# =================== 资源注册 ===================

# 将资源处理函数注册到资源管理器
@resource_manager.register_resource("greeting/{name}", ResourceType.SYSTEM)
async def get_greeting(name: str) -> str:
    """获取个性化问候语"""
    return f"你好，{name}！欢迎使用NetBrain MCP！"

@resource_manager.register_resource("device/{device_id}", ResourceType.DEVICE)
async def get_device_resource(device_id: str) -> Dict[str, Any]:
    """获取设备资源"""
    device = device_manager.get_device(device_id)
    if device:
        return device.to_dict()
    return {"error": f"设备不存在: {device_id}"}

@resource_manager.register_resource("device/{device_id}/config", ResourceType.CONFIG)
async def get_device_config(device_id: str) -> Dict[str, Any]:
    """获取设备配置资源"""
    device = device_manager.get_device(device_id)
    if not device:
        return {"error": f"设备不存在: {device_id}"}
    
    # 这里我们会尝试获取设备的运行配置
    # 首先获取默认凭据
    credentials = device_manager.list_credentials()
    if not credentials:
        return {"error": "没有可用的凭据"}
    
    credential_id = device.credential_id or credentials[0].id
    credential = device_manager.get_credential(credential_id)
    
    # 尝试获取设备配置
    if device.vendor == DeviceVendor.CISCO:
        command = "show running-config"
    elif device.vendor == DeviceVendor.HUAWEI:
        command = "display current-configuration"
    elif device.vendor == DeviceVendor.H3C:
        command = "display current-configuration"
    elif device.vendor == DeviceVendor.JUNIPER:
        command = "show configuration"
    else:
        command = "show running-config"  # 默认命令
    
    try:
        # 连接设备
        success, error = await connection_manager.connect_device(device, credential)
        if not success:
            return {"error": f"连接设备失败: {error}"}
        
        # 发送命令
        result, error = await connection_manager.send_command(
            device_id=device_id,
            credential_id=credential_id,
            command=command,
            timeout=60  # 配置命令可能需要更长时间
        )
        
        # 断开连接
        await connection_manager.disconnect_device(device_id, credential_id)
        
        if result and result.success:
            return {
                "device_id": device_id,
                "device_name": device.name,
                "config_type": "running",
                "config_content": result.output,
                "timestamp": result.execution_time.isoformat()
            }
        else:
            return {"error": f"获取配置失败: {error or '未知错误'}"}
    except Exception as e:
        return {"error": f"获取配置时发生错误: {str(e)}"}

@resource_manager.register_resource("device/{device_id}/interfaces", ResourceType.DEVICE)
async def get_device_interfaces(device_id: str) -> Dict[str, Any]:
    """获取设备接口资源"""
    device = device_manager.get_device(device_id)
    if not device:
        return {"error": f"设备不存在: {device_id}"}
    
    # 获取默认凭据
    credentials = device_manager.list_credentials()
    if not credentials:
        return {"error": "没有可用的凭据"}
    
    credential_id = device.credential_id or credentials[0].id
    credential = device_manager.get_credential(credential_id)
    
    # 根据设备类型确定接口命令
    if device.vendor == DeviceVendor.CISCO:
        command = "show interfaces"
    elif device.vendor == DeviceVendor.HUAWEI:
        command = "display interface"
    elif device.vendor == DeviceVendor.H3C:
        command = "display interface"
    elif device.vendor == DeviceVendor.JUNIPER:
        command = "show interfaces detail"
    else:
        command = "show interfaces"  # 默认命令
    
    try:
        # 连接设备
        success, error = await connection_manager.connect_device(device, credential)
        if not success:
            return {"error": f"连接设备失败: {error}"}
        
        # 发送命令
        result, error = await connection_manager.send_command(
            device_id=device_id,
            credential_id=credential_id,
            command=command,
            timeout=30
        )
        
        # 断开连接
        await connection_manager.disconnect_device(device_id, credential_id)
        
        if result and result.success:
            return {
                "device_id": device_id,
                "device_name": device.name,
                "interfaces_output": result.output,
                "timestamp": result.execution_time.isoformat()
            }
        else:
            return {"error": f"获取接口信息失败: {error or '未知错误'}"}
    except Exception as e:
        return {"error": f"获取接口信息时发生错误: {str(e)}"}

@resource_manager.register_resource("device/{device_id}/routes", ResourceType.DEVICE)
async def get_device_routes(device_id: str) -> Dict[str, Any]:
    """获取设备路由表资源"""
    device = device_manager.get_device(device_id)
    if not device:
        return {"error": f"设备不存在: {device_id}"}
    
    # 获取默认凭据
    credentials = device_manager.list_credentials()
    if not credentials:
        return {"error": "没有可用的凭据"}
    
    credential_id = device.credential_id or credentials[0].id
    credential = device_manager.get_credential(credential_id)
    
    # 根据设备类型确定路由命令
    if device.vendor == DeviceVendor.CISCO:
        command = "show ip route"
    elif device.vendor == DeviceVendor.HUAWEI:
        command = "display ip routing-table"
    elif device.vendor == DeviceVendor.H3C:
        command = "display ip routing-table"
    elif device.vendor == DeviceVendor.JUNIPER:
        command = "show route"
    else:
        command = "show ip route"  # 默认命令
    
    try:
        # 连接设备
        success, error = await connection_manager.connect_device(device, credential)
        if not success:
            return {"error": f"连接设备失败: {error}"}
        
        # 发送命令
        result, error = await connection_manager.send_command(
            device_id=device_id,
            credential_id=credential_id,
            command=command,
            timeout=30
        )
        
        # 断开连接
        await connection_manager.disconnect_device(device_id, credential_id)
        
        if result and result.success:
            return {
                "device_id": device_id,
                "device_name": device.name,
                "routes_output": result.output,
                "timestamp": result.execution_time.isoformat()
            }
        else:
            return {"error": f"获取路由表失败: {error or '未知错误'}"}
    except Exception as e:
        return {"error": f"获取路由表时发生错误: {str(e)}"}

@resource_manager.register_resource("credentials", ResourceType.CREDENTIAL)
async def list_credentials_resource() -> Dict[str, Any]:
    """
    列出所有设备凭据
    
    Returns:
        凭据列表
    """
    credentials = device_manager.list_credentials()
    return {
        "credentials": [
            {
                "id": cred.id,
                "name": cred.name,
                "username": cred.username,
                "password": cred.password,
                "protocol": cred.protocol.value,
                "port": cred.port,
                "ssh_key_file": cred.ssh_key_file
            }
            for cred in credentials
        ]
    }

@resource_manager.register_resource("system/status", ResourceType.SYSTEM)
async def get_system_status() -> Dict[str, Any]:
    """获取系统状态资源"""
    devices_count = len(device_manager.list_devices())
    credentials_count = len(device_manager.list_credentials())
    active_connections = len(connection_manager.get_active_connections())
    
    return {
        "status": "running",
        "devices_count": devices_count,
        "credentials_count": credentials_count,
        "active_connections": active_connections,
        "version": "0.1.0"
    }

@resource_manager.register_resource("topology", ResourceType.TOPOLOGY)
async def get_topology_resource() -> Dict[str, Any]:
    """获取网络拓扑资源"""
    try:
        topology = topology_discovery.get_topology()
        return topology.to_dict()
    except Exception as e:
        logger.error(f"获取拓扑资源失败: {e}")
        return {"error": f"获取拓扑资源失败: {str(e)}"}

@resource_manager.register_resource("topology/statistics", ResourceType.TOPOLOGY)
async def get_topology_statistics_resource() -> Dict[str, Any]:
    """获取拓扑统计资源"""
    try:
        topology = topology_discovery.get_topology()
        
        # 统计不同协议的链路数量
        protocol_stats = {}
        for link in topology.links:
            protocol = link.protocol.value
            protocol_stats[protocol] = protocol_stats.get(protocol, 0) + 1
        
        # 统计不同厂商的设备数量
        vendor_stats = {}
        for node in topology.nodes.values():
            vendor = node.vendor
            vendor_stats[vendor] = vendor_stats.get(vendor, 0) + 1
        
        return {
            "total_nodes": len(topology.nodes),
            "total_links": len(topology.links),
            "protocol_distribution": protocol_stats,
            "vendor_distribution": vendor_stats,
            "last_discovery": topology.last_discovery.isoformat() if topology.last_discovery else None,
            "discovery_scope": topology.discovery_scope
        }
    except Exception as e:
        logger.error(f"获取拓扑统计资源失败: {e}")
        return {"error": f"获取拓扑统计资源失败: {str(e)}"}

@resource_manager.register_resource("device/{device_id}/neighbors", ResourceType.TOPOLOGY)
async def get_device_neighbors_resource(device_id: str) -> Dict[str, Any]:
    """获取设备邻居资源"""
    try:
        topology = topology_discovery.get_topology()
        neighbors = topology.get_device_neighbors(device_id)
        
        # 获取邻居设备的详细信息
        neighbor_details = []
        for neighbor_id in neighbors:
            device = device_manager.get_device(neighbor_id)
            if device:
                neighbor_details.append(device.to_dict())
        
        return {
            "device_id": device_id,
            "neighbors": neighbor_details,
            "neighbor_count": len(neighbor_details)
        }
    except Exception as e:
        logger.error(f"获取设备邻居资源失败: {e}")
        return {"error": f"获取设备邻居资源失败: {str(e)}"}

@resource_manager.register_resource("scan/results", ResourceType.SCAN)
async def get_scan_results_resource() -> Dict[str, Any]:
    """获取网络扫描结果资源"""
    try:
        results = [r for r in network_scanner.scan_results.values() if r.is_alive]
        return {
            "total_results": len(results),
            "scan_results": [result.to_dict() for result in results]
        }
    except Exception as e:
        logger.error(f"获取扫描结果资源失败: {e}")
        return {"error": f"获取扫描结果资源失败: {str(e)}"}

@resource_manager.register_resource("scan/statistics", ResourceType.SCAN)
async def get_scan_statistics_resource() -> Dict[str, Any]:
    """获取网络扫描统计资源"""
    try:
        stats = network_scanner.get_scan_statistics()
        return stats
    except Exception as e:
        logger.error(f"获取扫描统计资源失败: {e}")
        return {"error": f"获取扫描统计资源失败: {str(e)}"}

@resource_manager.register_resource("scan/result/{ip_address}", ResourceType.SCAN)
async def get_scan_result_resource(ip_address: str) -> Dict[str, Any]:
    """获取特定IP的扫描结果资源"""
    try:
        result = network_scanner.scan_results.get(ip_address)
        if result:
            return result.to_dict()
        else:
            return {"error": f"未找到IP {ip_address} 的扫描结果"}
    except Exception as e:
        logger.error(f"获取扫描结果资源失败: {e}")
        return {"error": f"获取扫描结果资源失败: {str(e)}"}

# 向MCP服务器注册资源获取方法
@mcp.resource("{uri}")
async def mcp_resource_handler(uri: str) -> Any:
    """MCP资源处理器，处理所有资源请求"""
    logger.info(f"处理资源请求: {uri}")
    return await resource_manager.get_resource(uri)

# 向MCP服务器注册提示模板
@mcp.prompt("{name}")
async def mcp_prompt_handler(name: str) -> str:
    """MCP提示模板处理器，处理所有模板请求"""
    logger.info(f"处理模板请求: {name}")
    template = template_manager.get_template(name)
    if template:
        # 返回模板描述或模板名称
        return template.description or template.name
    return f"错误: 未找到模板 '{name}'"

# 测试工具
@mcp.tool()
async def test_scrapli_connection(
    host: str,
    username: str,
    password: str = None,
    platform: str = "cisco_iosxe",
    port: int = 22,
    protocol: str = "ssh",
    ssh_key_file: Optional[str] = None,
    connect_timeout: int = 15
) -> Dict[str, Any]:
    """
    测试Scrapli连接（直接使用Scrapli）
    
    Args:
        host: 设备主机名或IP地址
        username: 用户名
        password: 密码（与ssh_key_file至少提供一个）
        platform: 平台类型，如cisco_iosxe, huawei_vrp等
        port: 端口号（默认22，Telnet使用23）
        protocol: 连接协议，ssh或telnet
        ssh_key_file: SSH密钥文件路径，可选
        connect_timeout: 连接超时时间（秒）
        
    Returns:
        连接测试结果
    """
    # 从device_connector中导入SCRAPLI_IMPORT_SUCCESS检查scrapli是否可用
    if not SCRAPLI_IMPORT_SUCCESS:
        return {
            "success": False, 
            "message": "Scrapli库导入失败，请确保已安装: pip install scrapli scrapli-community"
        }
    
    try:
        from scrapli import Scrapli
        
        # 修正平台名称处理
        if platform.lower() == "huawei":
            platform = "huawei_vrp"
        
        # 确定连接协议
        is_telnet = protocol.lower() == "telnet"
        if is_telnet and port == 22:  # 如果是Telnet但端口仍为默认SSH端口，修正为默认Telnet端口
            port = 23
            
        logger.info(f"连接参数: host={host}, username={username}, platform={platform}, port={port}, protocol={protocol}")
        
        # 打印密码信息（安全地）
        if password:
            logger.info(f"密码类型: {type(password)}, 长度: {len(str(password))}")
            password = str(password)  # 确保密码是字符串类型
            
        # 准备连接参数
        device_params = {
            "host": host,
            "auth_username": username,
            "auth_strict_key": False,
            "platform": platform,
            "port": port,
            "timeout_socket": connect_timeout,
            "timeout_transport": connect_timeout * 2,
        }
        
        # 根据协议设置传输方式
        if is_telnet:
            device_params["transport"] = "telnet"
            logger.info("使用Telnet连接")
        else:
            # 指定Windows兼容的传输方式
            device_params["transport"] = "paramiko"  # 在Windows上使用paramiko而不是system
            logger.info("使用SSH连接 (paramiko)")
        
        # 设置认证方式，优先使用SSH密钥
        if not is_telnet and ssh_key_file and os.path.exists(ssh_key_file):
            device_params["auth_private_key"] = ssh_key_file
            logger.info(f"使用SSH密钥认证: {ssh_key_file}")
        elif password:
            device_params["auth_password"] = password
            logger.info("使用密码认证")
        else:
            return {"success": False, "message": "必须提供密码或SSH密钥文件"}
        
        # 详细记录连接参数（移除敏感信息）
        safe_params = device_params.copy()
        if "auth_password" in safe_params:
            safe_params["auth_password"] = "******"
        if "auth_private_key" in safe_params:
            safe_params["auth_private_key"] = f"[使用密钥文件: {ssh_key_file}]"
        
        logger.info(f"Scrapli测试连接参数: {safe_params}")
        
        # 建立连接
        conn = Scrapli(**device_params)
        conn.open()
        
        # 获取设备提示符
        prompt = conn.get_prompt()
        
        # 测试发送命令
        try:
            # 根据平台类型选择命令
            if "huawei" in platform:
                command = "display version"
            elif "cisco" in platform:
                command = "show version" 
            else:
                command = "show version"
                
            resp = conn.send_command(command)
            version_info = resp.result[:200] + "..." if len(resp.result) > 200 else resp.result
        except Exception as e:
            logger.warning(f"获取版本信息失败: {str(e)}")
            version_info = "无法获取版本信息"
        
        # 关闭连接
        conn.close()
        
        return {
            "success": True,
            "message": f"连接成功！设备提示符: {prompt}",
            "prompt": prompt,
            "version_info": version_info
        }
    except ImportError as e:
        return {"success": False, "message": f"Scrapli库未安装: {str(e)}"}
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(f"Scrapli连接测试失败: {error_type} - {error_msg}")
        return {
            "success": False, 
            "message": f"连接失败: {error_type} - {error_msg}",
            "error_type": error_type,
            "error_details": error_msg
        }

@mcp.tool()
async def test_telnet_connection(
    host: str,
    username: str,
    password: str,
    platform: str = "cisco_iosxe",
    port: int = 23,
    connect_timeout: int = 15
) -> Dict[str, Any]:
    """
    测试Telnet连接（快速测试）
    
    Args:
        host: 设备主机名或IP地址
        username: 用户名
        password: 密码
        platform: 平台类型，如cisco_iosxe, huawei_vrp等
        port: 端口号（默认23）
        connect_timeout: 连接超时时间（秒）
        
    Returns:
        连接测试结果
    """
    # 直接调用test_scrapli_connection，但固定protocol为telnet
    return await test_scrapli_connection(
        host=host,
        username=username,
        password=password,
        platform=platform,
        port=port,
        protocol="telnet",
        connect_timeout=connect_timeout
    )

@mcp.tool()
async def send_telnet_command(
    device_id: str,
    credential_id: str,
    command: str,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    向Telnet连接的网络设备发送命令（使用更长的超时时间）
    
    Args:
        device_id: 设备ID
        credential_id: 凭据ID
        command: 要执行的命令
        timeout: 命令超时时间（秒，默认比普通命令更长）
        
    Returns:
        命令执行结果
    """
    # 获取设备和凭据
    device = device_manager.get_device(device_id)
    credential = device_manager.get_credential(credential_id)
    
    if not device:
        return {"success": False, "message": f"设备不存在: {device_id}"}
    
    if not credential:
        return {"success": False, "message": f"凭据不存在: {credential_id}"}
    
    # 验证是否为Telnet凭据
    if credential.protocol != ConnectionProtocol.TELNET:
        return {"success": False, "message": f"此函数仅支持Telnet连接，当前凭据协议为: {credential.protocol.value}"}
    
    # 记录命令执行信息
    logger.info(f"通过Telnet向设备 {device.name} ({device.ip_address}) 发送命令: {command}")
    logger.info(f"超时设置: {timeout}秒")
    
    # 发送命令
    result, error = await connection_manager.send_command(
        device_id=device_id,
        credential_id=credential_id,
        command=command,
        timeout=timeout
    )
    
    if result:
        # 记录执行结果
        if result.success:
            logger.info(f"命令执行成功，输出长度: {len(result.output)}")
        else:
            logger.warning(f"命令执行失败: {result.error_message}")
            
        return {
            "success": result.success,
            "command": result.command,
            "output": result.output,
            "error_message": result.error_message,
            "execution_time": result.execution_time.isoformat()
        }
    else:
        logger.error(f"执行命令失败: {error}")
        return {
            "success": False,
            "command": command,
            "output": "",
            "error_message": error,
            "execution_time": None
        }

# 运行服务器
if __name__ == "__main__":
    # 检测启动方式
    import os
    
    # 获取启动命令行参数
    import sys
    command_args = " ".join(sys.argv)
    
    # 检查环境变量或命令行，判断是否通过MCP CLI运行
    is_mcp_cli = os.environ.get("MCP_CLI_RUN", "0") == "1" or "mcp dev" in command_args or "mcp run" in command_args
    
    # 设置环境变量，使其他模块也能知道是通过MCP CLI运行
    if is_mcp_cli:
        os.environ["MCP_CLI_RUN"] = "1"
    
    # 始终启动Web服务器（后台运行）
    import threading
    import uvicorn
    
    def start_web_server():
        """启动Web服务器"""
        from web.app import app
        uvicorn.run(app, host="0.0.0.0", port=8088)
    
    # 在另一个线程中启动Web服务器
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    print("NetBrain MCP Web界面已启动，访问 http://localhost:8088")
    
    if is_mcp_cli:
        print("MCP CLI模式已检测到")
    
    # 在8000端口运行，与MCP Inspector预期一致
    mcp.run()