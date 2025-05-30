#!/usr/bin/env python3
"""
NetBrain MCP 拓扑发现功能使用示例

本示例展示如何使用NetBrain MCP的拓扑发现功能：
1. 从种子设备开始发现整个网络拓扑
2. 查询设备的邻居信息
3. 获取拓扑统计数据
4. 使用不同厂商的设备进行拓扑发现

使用方法：
1. 确保已添加网络设备和凭据
2. 运行此脚本查看拓扑发现示例
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('..'))

from network_devices import (
    device_manager, 
    NetworkDevice, 
    DeviceCredential, 
    DeviceType, 
    DeviceVendor, 
    ConnectionProtocol
)
from device_connector import connection_manager
from topology_discovery_improved import create_improved_topology_discovery

async def example_basic_topology_discovery():
    """基础拓扑发现示例"""
    print("=" * 60)
    print("基础拓扑发现示例")
    print("=" * 60)
    
    # 创建拓扑发现引擎
    topology_discovery = create_improved_topology_discovery(device_manager, connection_manager)
    
    # 查看当前设备列表
    devices = device_manager.list_devices()
    print(f"\n当前系统中的设备:")
    for i, device in enumerate(devices, 1):
        credential_info = ""
        if device.credential_id:
            cred = device_manager.get_credential(device.credential_id)
            if cred:
                credential_info = f" (凭据: {cred.name})"
        print(f"  {i}. {device.name} - {device.ip_address} - {device.vendor.value}{credential_info}")
    
    if not devices:
        print("  没有找到设备。请先添加一些设备再运行此示例。")
        return
    
    # 从第一个设备开始拓扑发现
    device = devices[0]
    print(f"\n从设备 '{device.name}' 开始拓扑发现...")
    
    try:
        topology = await topology_discovery.discover_topology_from_devices([device.id])
        
        print(f"\n拓扑发现完成!")
        print(f"  - 发现的节点数量: {len(topology.nodes)}")
        print(f"  - 发现的链路数量: {len(topology.links)}")
        print(f"  - 发现时间: {topology.last_discovery}")
        
        # 显示发现的节点
        if topology.nodes:
            print(f"\n发现的网络节点:")
            for node_id, node in topology.nodes.items():
                print(f"  - {node.device_name} ({node.ip_address}) - {node.vendor}")
                print(f"    接口数量: {len(node.interfaces)}")
        
        # 显示发现的链路
        if topology.links:
            print(f"\n发现的网络链路:")
            for link in topology.links:
                source_node = topology.nodes.get(link.source_device_id)
                target_node = topology.nodes.get(link.target_device_id)
                source_name = source_node.device_name if source_node else "未知设备"
                target_name = target_node.device_name if target_node else "未知设备"
                
                print(f"  - {source_name}[{link.source_interface}] <--> {target_name}[{link.target_interface}]")
                print(f"    协议: {link.protocol.value}")
        
    except Exception as e:
        print(f"  拓扑发现失败: {e}")

async def example_device_neighbor_discovery():
    """设备邻居发现示例"""
    print("\n" + "=" * 60)
    print("设备邻居发现示例")
    print("=" * 60)
    
    topology_discovery = create_improved_topology_discovery(device_manager, connection_manager)
    devices = device_manager.list_devices()
    
    if not devices:
        print("没有找到设备。")
        return
    
    device = devices[0]
    print(f"\n发现设备 '{device.name}' 的邻居...")
    
    try:
        neighbors, interfaces = await topology_discovery.discover_device_neighbors(device)
        
        print(f"\n邻居发现结果:")
        print(f"  - 发现的邻居数量: {len(neighbors)}")
        print(f"  - 发现的接口数量: {len(interfaces)}")
        
        if neighbors:
            print(f"\n邻居设备信息:")
            for neighbor in neighbors:
                print(f"  - 设备ID: {neighbor.get('device_id', '未知')}")
                print(f"    IP地址: {neighbor.get('ip_address', '未知')}")
                print(f"    本地接口: {neighbor.get('local_interface', '未知')}")
                print(f"    远程接口: {neighbor.get('remote_interface', '未知')}")
                print(f"    协议: {neighbor.get('protocol', '未知')}")
                print()
        
        if interfaces:
            print(f"设备接口信息 (前5个):")
            for i, interface in enumerate(interfaces[:5]):
                print(f"  {i+1}. {interface.name}")
                print(f"     IP地址: {interface.ip_address or '未配置'}")
                print(f"     状态: {interface.status}/{interface.protocol}")
                
    except Exception as e:
        print(f"  邻居发现失败: {e}")

def example_topology_statistics():
    """拓扑统计示例"""
    print("\n" + "=" * 60)
    print("拓扑统计示例")
    print("=" * 60)
    
    topology_discovery = create_improved_topology_discovery(device_manager, connection_manager)
    topology = topology_discovery.get_topology()
    
    print(f"\n当前拓扑统计:")
    print(f"  - 总节点数: {len(topology.nodes)}")
    print(f"  - 总链路数: {len(topology.links)}")
    print(f"  - 最后发现时间: {topology.last_discovery or '从未发现'}")
    
    # 协议分布统计
    if topology.links:
        protocol_stats = {}
        for link in topology.links:
            protocol = link.protocol.value
            protocol_stats[protocol] = protocol_stats.get(protocol, 0) + 1
        
        print(f"\n协议分布:")
        for protocol, count in protocol_stats.items():
            print(f"  - {protocol.upper()}: {count} 条链路")
    
    # 厂商分布统计
    if topology.nodes:
        vendor_stats = {}
        for node in topology.nodes.values():
            vendor = node.vendor
            vendor_stats[vendor] = vendor_stats.get(vendor, 0) + 1
        
        print(f"\n厂商分布:")
        for vendor, count in vendor_stats.items():
            print(f"  - {vendor.upper()}: {count} 个设备")

def example_add_sample_devices():
    """添加示例设备"""
    print("\n" + "=" * 60)
    print("添加示例设备 (仅用于演示，不连接真实设备)")
    print("=" * 60)
    
    # 添加示例凭据
    sample_credential = DeviceCredential(
        name="示例SSH凭据",
        username="admin",
        password="admin123",
        protocol=ConnectionProtocol.SSH,
        port=22
    )
    cred_id = device_manager.add_credential(sample_credential)
    
    # 添加思科路由器示例
    cisco_router = NetworkDevice(
        name="Core-Router-01",
        ip_address="192.168.1.1",
        device_type=DeviceType.ROUTER,
        vendor=DeviceVendor.CISCO,
        platform="cisco_iosxe",
        model="ISR4431",
        location="数据中心机房A",
        description="核心路由器",
        credential_id=cred_id
    )
    device_manager.add_device(cisco_router)
    
    # 添加华为交换机示例
    huawei_switch = NetworkDevice(
        name="Access-Switch-01", 
        ip_address="192.168.1.10",
        device_type=DeviceType.SWITCH,
        vendor=DeviceVendor.HUAWEI,
        platform="huawei_vrp",
        model="S5720-28P-LI",
        location="数据中心机房A",
        description="接入交换机",
        credential_id=cred_id
    )
    device_manager.add_device(huawei_switch)
    
    print("已添加示例设备:")
    print(f"  - {cisco_router.name} ({cisco_router.ip_address}) - 思科路由器")
    print(f"  - {huawei_switch.name} ({huawei_switch.ip_address}) - 华为交换机")

def example_command_templates():
    """命令模板使用示例"""
    print("\n" + "=" * 60)
    print("命令模板使用示例")
    print("=" * 60)
    
    from templates.command_templates import get_command_template
    
    print("\n思科设备拓扑发现命令:")
    cisco_commands = [
        ("CDP邻居详情", get_command_template("cisco", "topology_discovery", "get_cdp_neighbors_detail")),
        ("LLDP邻居详情", get_command_template("cisco", "topology_discovery", "get_lldp_neighbors_detail")),
        ("接口简要信息", get_command_template("cisco", "topology_discovery", "get_interface_brief")),
        ("启用CDP", get_command_template("cisco", "topology_discovery", "enable_cdp")),
    ]
    
    for desc, cmd in cisco_commands:
        print(f"  - {desc}: {cmd}")
    
    print("\n华为设备拓扑发现命令:")
    huawei_commands = [
        ("LLDP邻居详情", get_command_template("huawei", "topology_discovery", "get_lldp_neighbors_detail")),
        ("接口简要信息", get_command_template("huawei", "topology_discovery", "get_interface_brief")),
        ("启用LLDP", get_command_template("huawei", "topology_discovery", "enable_lldp")),
        ("MAC地址表", get_command_template("huawei", "topology_discovery", "get_mac_address_table")),
    ]
    
    for desc, cmd in huawei_commands:
        print(f"  - {desc}: {cmd}")

async def main():
    """主函数"""
    print("NetBrain MCP 拓扑发现功能使用示例")
    print("本示例展示拓扑发现的各种功能和用法")
    
    # 1. 显示命令模板
    example_command_templates()
    
    # 2. 显示当前拓扑统计
    example_topology_statistics()
    
    # 3. 基础拓扑发现
    await example_basic_topology_discovery()
    
    # 4. 设备邻居发现
    await example_device_neighbor_discovery()
    
    # 5. 再次显示统计（可能已有数据）
    example_topology_statistics()
    
    print("\n" + "=" * 60)
    print("示例完成!")
    print("\n提示:")
    print("- 要进行真实的拓扑发现，请确保设备可达且凭据正确")
    print("- 支持思科CDP和标准LLDP协议")
    print("- 可以通过Web API或MCP工具调用拓扑发现功能")
    print("- 拓扑数据会自动保存到data/topology.json文件")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 