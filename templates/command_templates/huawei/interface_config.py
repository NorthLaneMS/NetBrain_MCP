"""
华为设备接口配置模板
支持配置接口IP、状态、带宽、描述等操作
"""

def configure_interface_ip(interface: str, ip_address: str, subnet_mask: str) -> str:
    """
    配置接口IP地址
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/0/1
        ip_address: IP地址
        subnet_mask: 子网掩码
    
    Returns:
        配置命令字符串
    """
    commands = [
        "system-view",
        f"interface {interface}",
        f"ip address {ip_address} {subnet_mask}",
        "undo shutdown",
        "quit"
    ]
    return "\n".join(commands)

def configure_interface_state(interface: str, state: str = "up") -> str:
    """
    配置接口状态
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/0/1
        state: 接口状态，up或down
    
    Returns:
        配置命令字符串
    """
    commands = [
        "system-view",
        f"interface {interface}"
    ]
    
    if state.lower() == "up":
        commands.append("undo shutdown")
    elif state.lower() == "down":
        commands.append("shutdown")
        
    commands.append("quit")
    return "\n".join(commands)

def configure_interface_description(interface: str, description: str) -> str:
    """
    配置接口描述
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/0/1
        description: 接口描述
    
    Returns:
        配置命令字符串
    """
    commands = [
        "system-view",
        f"interface {interface}",
        f"description {description}",
        "quit"
    ]
    return "\n".join(commands)

def configure_interface_speed(interface: str, speed: str) -> str:
    """
    配置接口速率
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/0/1
        speed: 速率，如10, 100, 1000, auto
    
    Returns:
        配置命令字符串
    """
    commands = [
        "system-view",
        f"interface {interface}",
        f"speed {speed}",
        "quit"
    ]
    return "\n".join(commands)

def configure_interface_duplex(interface: str, duplex: str) -> str:
    """
    配置接口双工模式
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/0/1
        duplex: 双工模式，full, half, auto
    
    Returns:
        配置命令字符串
    """
    commands = [
        "system-view",
        f"interface {interface}",
        f"duplex {duplex}",
        "quit"
    ]
    return "\n".join(commands)

def show_interface(interface: str = None) -> str:
    """
    显示接口信息
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/0/1，为None时显示所有接口
    
    Returns:
        显示命令字符串
    """
    if interface:
        return f"display interface {interface}"
    else:
        return "display interface brief"

def show_ip_interface(interface: str = None) -> str:
    """
    显示接口IP信息
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/0/1，为None时显示所有接口
    
    Returns:
        显示命令字符串
    """
    if interface:
        return f"display ip interface {interface}"
    else:
        return "display ip interface brief" 