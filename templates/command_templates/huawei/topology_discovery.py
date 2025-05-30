"""
华为设备的拓扑发现命令模板
主要支持LLDP协议的邻居发现
"""

def get_lldp_neighbors():
    """获取LLDP邻居列表"""
    return "display lldp neighbor brief"

def get_lldp_neighbors_detail():
    """获取LLDP邻居详细信息"""
    return "display lldp neighbor verbose"

def enable_lldp():
    """全局启用LLDP"""
    return "lldp enable"

def enable_lldp_interface(interface: str):
    """在指定接口启用LLDP"""
    return f"""interface {interface}
lldp enable
quit"""

def get_interface_brief():
    """获取接口简要信息"""
    return "display ip interface brief"

def get_interface_description():
    """获取接口描述"""
    return "display interface description"

def get_lldp_interface(interface: str):
    """获取指定接口的LLDP信息"""
    return f"display lldp neighbor interface {interface}"

def get_lldp_statistics():
    """获取LLDP统计信息"""
    return "display lldp statistics"

def get_vlan_brief():
    """获取VLAN简要信息"""
    return "display vlan"

def get_mac_address_table():
    """获取MAC地址表"""
    return "display mac-address"

def get_interface_statistics():
    """获取接口统计信息"""
    return "display interface"

def get_arp_table():
    """获取ARP表（用于三层拓扑分析）"""
    return "display arp"

def get_routing_table():
    """获取路由表"""
    return "display ip routing-table"

def get_stp_brief():
    """获取STP简要信息"""
    return "display stp brief"

def get_device_info():
    """获取设备基本信息"""
    return "display device"

def get_system_info():
    """获取系统信息"""
    return "display version"

def discover_full_topology():
    """发现完整拓扑的命令序列"""
    commands = [
        "display lldp neighbor verbose",
        "display ip interface brief", 
        "display interface description",
        "display vlan",
        "display mac-address"
    ]
    return commands 