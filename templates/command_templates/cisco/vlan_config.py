"""
思科设备VLAN配置模板
支持创建VLAN、配置VLAN名称、将接口添加到VLAN等操作
"""

def create_vlan(vlan_id: str, vlan_name: str = None) -> str:
    """
    创建VLAN
    
    Args:
        vlan_id: VLAN ID
        vlan_name: VLAN名称(可选)
    
    Returns:
        配置命令字符串
    """
    commands = [
        "configure terminal",
        f"vlan {vlan_id}"
    ]
    
    if vlan_name:
        commands.append(f"name {vlan_name}")
    
    commands.append("exit")
    commands.append("end")
    return "\n".join(commands)

def add_interface_to_vlan(interface: str, vlan_id: str, mode: str = "access") -> str:
    """
    将接口添加到VLAN
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/1
        vlan_id: VLAN ID
        mode: 接口模式，access或trunk
    
    Returns:
        配置命令字符串
    """
    commands = [
        "configure terminal",
        f"interface {interface}",
        "switchport"
    ]
    
    if mode.lower() == "access":
        commands.append("switchport mode access")
        commands.append(f"switchport access vlan {vlan_id}")
    elif mode.lower() == "trunk":
        commands.append("switchport mode trunk")
        commands.append(f"switchport trunk allowed vlan add {vlan_id}")
    
    commands.append("exit")
    commands.append("end")
    return "\n".join(commands)

def delete_vlan(vlan_id: str) -> str:
    """
    删除VLAN
    
    Args:
        vlan_id: VLAN ID
    
    Returns:
        配置命令字符串
    """
    commands = [
        "configure terminal",
        f"no vlan {vlan_id}",
        "end"
    ]
    return "\n".join(commands)

def show_vlan() -> str:
    """
    显示VLAN信息
    
    Returns:
        显示命令字符串
    """
    return "show vlan brief"

def show_vlan_detail(vlan_id: str) -> str:
    """
    显示特定VLAN的详细信息
    
    Args:
        vlan_id: VLAN ID
    
    Returns:
        显示命令字符串
    """
    return f"show vlan id {vlan_id}" 