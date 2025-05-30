"""
思科设备的拓扑发现命令模板
支持CDP和LLDP协议的邻居发现
"""

def get_cdp_neighbors():
    """获取CDP邻居列表"""
    return "show cdp neighbors"

def get_cdp_neighbors_detail():
    """获取CDP邻居详细信息"""
    return "show cdp neighbors detail"

def get_lldp_neighbors():
    """获取LLDP邻居列表"""
    return "show lldp neighbors"

def get_lldp_neighbors_detail():
    """获取LLDP邻居详细信息"""
    return "show lldp neighbors detail"

def enable_cdp():
    """全局启用CDP"""
    return "cdp run"

def enable_cdp_interface(interface: str):
    """在指定接口启用CDP"""
    return f"""interface {interface}
cdp enable
exit"""

def enable_lldp():
    """全局启用LLDP"""
    return """lldp run"""

def enable_lldp_interface(interface: str):
    """在指定接口启用LLDP"""
    return f"""interface {interface}
lldp transmit
lldp receive
exit"""

def get_interface_brief():
    """获取接口简要信息"""
    return "show ip interface brief"

def get_interface_status():
    """获取接口状态"""
    return "show interface status"

def get_interface_description():
    """获取接口描述"""
    return "show interface description"

def get_cdp_interface(interface: str):
    """获取指定接口的CDP信息"""
    return f"show cdp interface {interface}"

def get_lldp_interface(interface: str):
    """获取指定接口的LLDP信息"""
    return f"show lldp interface {interface}"

def get_cdp_entry(device_name: str):
    """获取特定设备的CDP条目"""
    return f"show cdp entry {device_name}"

def get_vlan_brief():
    """获取VLAN简要信息（用于拓扑分析）"""
    return "show vlan brief"

def get_spanning_tree():
    """获取生成树信息（用于拓扑分析）"""
    return "show spanning-tree"

def get_mac_address_table():
    """获取MAC地址表（用于二层拓扑分析）"""
    return "show mac address-table"

def discover_full_topology():
    """发现完整拓扑的命令序列"""
    commands = [
        "show cdp neighbors detail",
        "show lldp neighbors detail", 
        "show ip interface brief",
        "show interface description",
        "show vlan brief"
    ]
    return commands 