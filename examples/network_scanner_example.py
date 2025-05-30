#!/usr/bin/env python3
"""
NetBrain MCP 网络扫描功能使用示例

本示例展示如何使用NetBrain MCP的网络扫描功能：
1. 扫描网络范围发现活跃主机
2. 扫描单个主机获取详细信息
3. 从扫描结果自动创建设备记录
4. 获取扫描统计和分析数据

使用方法：
1. 确保网络环境可达
2. 运行此脚本查看网络扫描示例
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('..'))

from network_devices import device_manager
from network_scanner import create_network_scanner, ScanConfiguration

async def example_basic_network_scan():
    """基础网络扫描示例"""
    print("=" * 60)
    print("基础网络扫描示例")
    print("=" * 60)
    
    # 创建网络扫描器
    scanner = create_network_scanner(device_manager)
    
    # 扫描本地网络范围 (示例)
    # 注意：请根据实际网络环境修改IP范围
    network_range = "127.0.0.1/30"  # 小范围测试
    
    print(f"\n扫描网络范围: {network_range}")
    
    # 创建扫描配置
    config = ScanConfiguration(
        timeout=3.0,
        max_concurrent=20,
        ping_enabled=True,
        port_scan_enabled=True,
        snmp_enabled=False,  # 在示例中禁用SNMP
        common_ports=[22, 23, 80, 161, 443, 8080]
    )
    
    try:
        # 执行网络扫描
        results = await scanner.scan_network_range(network_range, config)
        
        print(f"\n扫描完成!")
        print(f"  - 发现的活跃主机: {len(results)} 个")
        
        # 显示扫描结果
        for i, result in enumerate(results, 1):
            print(f"\n  主机 {i}: {result.ip_address}")
            print(f"    状态: {'活跃' if result.is_alive else '不可达'}")
            if result.response_time:
                print(f"    响应时间: {result.response_time}ms")
            if result.hostname:
                print(f"    主机名: {result.hostname}")
            if result.open_ports:
                print(f"    开放端口: {result.open_ports}")
            if result.vendor:
                print(f"    推断厂商: {result.vendor}")
            if result.device_type:
                print(f"    推断类型: {result.device_type}")
                
    except Exception as e:
        print(f"  扫描失败: {e}")

async def example_single_host_scan():
    """单个主机扫描示例"""
    print("\n" + "=" * 60)
    print("单个主机扫描示例")
    print("=" * 60)
    
    scanner = create_network_scanner(device_manager)
    
    # 扫描本地主机
    target_ip = "127.0.0.1"
    
    print(f"\n扫描目标主机: {target_ip}")
    
    # 创建扫描配置
    config = ScanConfiguration(
        timeout=5.0,
        port_scan_enabled=True,
        snmp_enabled=False,
        common_ports=[22, 23, 53, 80, 135, 139, 443, 445, 993, 995, 3389, 5985, 8080]
    )
    
    try:
        # 执行单个主机扫描
        result = await scanner.scan_single_host(target_ip, config)
        
        print(f"\n主机扫描结果:")
        print(f"  - IP地址: {result.ip_address}")
        print(f"  - 主机状态: {'活跃' if result.is_alive else '不可达'}")
        
        if result.response_time:
            print(f"  - 响应时间: {result.response_time}ms")
        
        if result.hostname:
            print(f"  - 主机名: {result.hostname}")
        
        if result.open_ports:
            print(f"  - 开放端口: {result.open_ports}")
            print(f"  - 识别的服务:")
            for port, service in result.services.items():
                print(f"    端口 {port}: {service}")
        
        print(f"  - 发现方法: {[method.value for method in result.discovery_method]}")
        
        if result.vendor:
            print(f"  - 推断厂商: {result.vendor}")
        
        if result.device_type:
            print(f"  - 推断设备类型: {result.device_type}")
            
    except Exception as e:
        print(f"  扫描失败: {e}")

async def example_device_discovery():
    """设备发现和创建示例"""
    print("\n" + "=" * 60)
    print("设备发现和创建示例")
    print("=" * 60)
    
    scanner = create_network_scanner(device_manager)
    
    # 创建一些模拟扫描结果用于演示
    from network_scanner import ScanResult, DeviceDiscoveryMethod
    from datetime import datetime
    
    # 模拟网络设备扫描结果
    mock_scan_results = [
        ScanResult(
            ip_address="192.168.10.1",
            is_alive=True,
            hostname="Core-Switch-01",
            vendor="Cisco",
            device_type="switch",
            open_ports=[22, 23, 80, 161, 443],
            response_time=2.5,
            discovered_at=datetime.now(),
            discovery_method={DeviceDiscoveryMethod.PING_SWEEP, DeviceDiscoveryMethod.PORT_SCAN}
        ),
        ScanResult(
            ip_address="192.168.10.2", 
            is_alive=True,
            hostname="Border-Router-01",
            vendor="Huawei",
            device_type="router",
            open_ports=[22, 161, 443],
            response_time=1.8,
            discovered_at=datetime.now(),
            discovery_method={DeviceDiscoveryMethod.PING_SWEEP, DeviceDiscoveryMethod.PORT_SCAN}
        ),
        ScanResult(
            ip_address="192.168.10.3",
            is_alive=True,
            hostname="Access-Switch-01",
            vendor="H3C",
            device_type="switch", 
            open_ports=[22, 80, 161],
            response_time=3.2,
            discovered_at=datetime.now(),
            discovery_method={DeviceDiscoveryMethod.PING_SWEEP, DeviceDiscoveryMethod.PORT_SCAN}
        )
    ]
    
    print(f"\n当前系统中的设备数量: {len(device_manager.list_devices())}")
    
    # 将模拟结果添加到扫描器
    for result in mock_scan_results:
        scanner.scan_results[result.ip_address] = result
    
    print(f"\n模拟扫描发现了 {len(mock_scan_results)} 个网络设备:")
    for result in mock_scan_results:
        print(f"  - {result.hostname} ({result.ip_address}) - {result.vendor} {result.device_type}")
    
    # 从扫描结果自动创建设备
    print(f"\n正在从扫描结果创建设备...")
    created_devices = await scanner.discover_devices_from_scan(mock_scan_results, auto_create=True)
    
    print(f"\n成功创建了 {len(created_devices)} 个设备:")
    for device in created_devices:
        print(f"\n  设备: {device.name}")
        print(f"    ID: {device.id}")
        print(f"    IP地址: {device.ip_address}")
        print(f"    厂商: {device.vendor.value}")
        print(f"    类型: {device.device_type.value}")
        print(f"    状态: {device.status.value}")
        print(f"    描述: {device.description}")
        if device.tags:
            print(f"    标签: {', '.join(device.tags)}")
    
    print(f"\n当前系统中的设备数量: {len(device_manager.list_devices())}")

def example_scan_statistics():
    """扫描统计示例"""
    print("\n" + "=" * 60)
    print("扫描统计示例")
    print("=" * 60)
    
    scanner = create_network_scanner(device_manager)
    
    # 获取扫描统计信息
    stats = scanner.get_scan_statistics()
    
    print(f"\n网络扫描统计信息:")
    print(f"  - 总扫描主机数: {stats['total_scanned']}")
    print(f"  - 活跃主机数: {stats['alive_hosts']}")
    print(f"  - 发现成功率: {stats['discovery_rate']}")
    
    if stats['vendor_distribution']:
        print(f"\n  厂商分布:")
        for vendor, count in stats['vendor_distribution'].items():
            print(f"    {vendor}: {count} 个设备")
    
    if stats['device_type_distribution']:
        print(f"\n  设备类型分布:")
        for device_type, count in stats['device_type_distribution'].items():
            print(f"    {device_type}: {count} 个设备")
    
    if stats['discovery_method_distribution']:
        print(f"\n  发现方法统计:")
        for method, count in stats['discovery_method_distribution'].items():
            print(f"    {method}: {count} 次使用")
    
    if stats['last_scan_time']:
        print(f"\n  最后扫描时间: {stats['last_scan_time']}")

async def example_filtered_device_creation():
    """过滤条件设备创建示例"""
    print("\n" + "=" * 60)
    print("过滤条件设备创建示例")
    print("=" * 60)
    
    scanner = create_network_scanner(device_manager)
    
    # 获取所有活跃的扫描结果
    all_results = [r for r in scanner.scan_results.values() if r.is_alive]
    
    if not all_results:
        print("  没有可用的扫描结果进行过滤测试")
        return
    
    print(f"\n当前有 {len(all_results)} 个活跃主机的扫描结果")
    
    # 示例1：只创建Cisco设备
    print(f"\n过滤条件示例1: 只创建Cisco设备")
    cisco_results = [r for r in all_results if r.vendor and "cisco" in r.vendor.lower()]
    if cisco_results:
        cisco_devices = await scanner.discover_devices_from_scan(cisco_results, auto_create=True)
        print(f"  创建了 {len(cisco_devices)} 个Cisco设备")
    else:
        print("  没有找到Cisco设备")
    
    # 示例2：只创建有SNMP端口的设备
    print(f"\n过滤条件示例2: 只创建有SNMP端口(161)的设备")
    snmp_results = [r for r in all_results if 161 in r.open_ports]
    if snmp_results:
        snmp_devices = await scanner.discover_devices_from_scan(snmp_results, auto_create=True)
        print(f"  创建了 {len(snmp_devices)} 个支持SNMP的设备")
    else:
        print("  没有找到支持SNMP的设备")
    
    # 示例3：只创建响应时间快的设备
    print(f"\n过滤条件示例3: 只创建响应时间小于5ms的设备")
    fast_results = [r for r in all_results if r.response_time and r.response_time < 5.0]
    if fast_results:
        fast_devices = await scanner.discover_devices_from_scan(fast_results, auto_create=True)
        print(f"  创建了 {len(fast_devices)} 个响应快速的设备")
        for device in fast_devices:
            result = scanner.scan_results.get(device.ip_address)
            if result:
                print(f"    {device.name} ({device.ip_address}) - 响应时间: {result.response_time}ms")
    else:
        print("  没有找到响应时间快的设备")

def example_vendor_identification():
    """厂商识别示例"""
    print("\n" + "=" * 60)
    print("厂商识别示例")
    print("=" * 60)
    
    scanner = create_network_scanner(device_manager)
    
    # 测试一些常见的MAC地址前缀
    test_macs = [
        ("00:00:0C:AB:CD:EF", "Cisco - 经典前缀"),
        ("00:1E:10:12:34:56", "华为 - 常见前缀"),
        ("00:01:A7:AA:BB:CC", "H3C - 标准前缀"),
        ("00:05:85:11:22:33", "Juniper - 网络前缀"),
        ("08:00:27:DD:EE:FF", "VirtualBox - 虚拟机"),
        ("52:54:00:12:34:56", "QEMU/KVM - 虚拟机"),
        ("AA:BB:CC:DD:EE:FF", "未知厂商")
    ]
    
    print(f"\nMAC地址厂商识别测试:")
    for mac, description in test_macs:
        vendor = scanner.get_vendor_by_mac(mac)
        print(f"  {mac} -> {vendor or '未知'} ({description})")
    
    print(f"\n系统支持的厂商OUI数量: {len(scanner.vendor_oui_map)}")
    print(f"支持的主要厂商: Cisco, Huawei, H3C, Juniper")

async def main():
    """主函数"""
    print("NetBrain MCP 网络扫描功能使用示例")
    print("本示例展示网络扫描的各种使用场景")
    
    # 1. 基础网络扫描
    await example_basic_network_scan()
    
    # 2. 单个主机扫描
    await example_single_host_scan()
    
    # 3. 设备发现和创建
    await example_device_discovery()
    
    # 4. 扫描统计
    example_scan_statistics()
    
    # 5. 过滤条件设备创建
    await example_filtered_device_creation()
    
    # 6. 厂商识别
    example_vendor_identification()
    
    print("\n" + "=" * 60)
    print("示例完成!")
    print("\n网络扫描功能特性:")
    print("✅ 支持网络范围扫描 (CIDR格式)")
    print("✅ 支持单个主机详细扫描")
    print("✅ 自动设备类型和厂商识别")
    print("✅ 基于扫描结果自动创建设备")
    print("✅ 丰富的过滤和统计功能")
    print("✅ 支持主流网络设备厂商")
    print("✅ 数据持久化存储")
    print("\n使用提示:")
    print("- 可以通过MCP工具调用: scan_network_range, scan_single_host等")
    print("- 可以通过Web API调用: POST /api/scan/network, GET /api/scan/results等")
    print("- 扫描结果自动保存到data/scan_results.json")
    print("- 支持与拓扑发现功能联动使用")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 