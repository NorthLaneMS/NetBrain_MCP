"""
思科设备接口配置模板
支持配置接口IP、状态、带宽、描述等操作
"""

def configure_interface_ip(interface: str, ip_address: str, subnet_mask: str) -> str:
    """
    配置接口IP地址
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/1
        ip_address: IP地址
        subnet_mask: 子网掩码
    
    Returns:
        配置命令字符串
    """
    commands = [
        "configure terminal",
        f"interface {interface}",
        f"ip address {ip_address} {subnet_mask}",
        "no shutdown",
        "exit",
        "end"
    ]
    return "\n".join(commands)

def configure_interface_state(interface: str, state: str = "up") -> str:
    """
    配置接口状态
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/1
        state: 接口状态，up或down
    
    Returns:
        配置命令字符串
    """
    commands = [
        "configure terminal",
        f"interface {interface}"
    ]
    
    if state.lower() == "up":
        commands.append("no shutdown")
    elif state.lower() == "down":
        commands.append("shutdown")
        
    commands.append("exit")
    commands.append("end")
    return "\n".join(commands)

def configure_interface_description(interface: str, description: str) -> str:
    """
    配置接口描述
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/1
        description: 接口描述
    
    Returns:
        配置命令字符串
    """
    commands = [
        "configure terminal",
        f"interface {interface}",
        f"description {description}",
        "exit",
        "end"
    ]
    return "\n".join(commands)

def configure_interface_bandwidth(interface: str, bandwidth: str) -> str:
    """
    配置接口带宽
    
    Args:
        interface: 接口名称，如 GigabitEthernet0/1
        bandwidth: 带宽，单位kbps
    
    Returns:
        配置命令字符串
    """
    commands = [
        "configure terminal",
        f"interface {interface}",
        f"bandwidth {bandwidth}",
        "exit",
        "end"
    ]
    return "\n".join(commands)

def show_interface(interface: str = None) -> str:
    """
    显示接口信息
    
    Args:
        interface: 接口名称，如GigabitEthernet0/1，为None时显示所有接口
    
    Returns:
        显示命令字符串
    """
    if interface:
        return f"show interface {interface}"
    else:
        return "show interface"

def show_ip_interface(interface: str = None) -> str:
    """
    显示接口IP信息
    
    Args:
        interface: 接口名称，如GigabitEthernet0/1，为None时显示所有接口
    
    Returns:
        显示命令字符串
    """
    if interface:
        return f"show ip interface {interface}"
    else:
        return "show ip interface brief" 