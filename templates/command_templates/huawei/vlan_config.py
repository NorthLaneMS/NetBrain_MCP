"""
华为设备VLAN配置模板
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
        "system-view",
        f"vlan {vlan_id}"
    ]
    
    if vlan_name:
        commands.append(f"description {vlan_name}")
    
    commands.append("quit")
    return "\n".join(commands)

def add_interface_to_vlan(interface: str, vlan_id: str, mode: str = "access") -> str:
    """
    将接口添加到VLAN
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/0/1
        vlan_id: VLAN ID
        mode: 接口模式，access或trunk
    
    Returns:
        配置命令字符串
    """
    commands = [
        "system-view",
        f"interface {interface}"
    ]
    
    if mode.lower() == "access":
        commands.append("port link-type access")
        commands.append(f"port default vlan {vlan_id}")
    elif mode.lower() == "trunk":
        commands.append("port link-type trunk")
        commands.append(f"port trunk allow-pass vlan {vlan_id}")
    
    commands.append("quit")
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
        "system-view",
        f"undo vlan {vlan_id}",
        "quit"
    ]
    return "\n".join(commands)

def show_vlan() -> str:
    """
    显示VLAN信息
    
    Returns:
        显示命令字符串
    """
    return "display vlan"

def show_vlan_detail(vlan_id: str) -> str:
    """
    显示特定VLAN的详细信息
    
    Args:
        vlan_id: VLAN ID
    
    Returns:
        显示命令字符串
    """
    return f"display vlan {vlan_id}" 