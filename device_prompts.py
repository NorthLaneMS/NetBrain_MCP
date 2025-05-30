"""
设备操作命令提示模板

将命令模板系统与MCP提示模板系统结合，提供网络设备操作相关的提示模板。
"""

from typing import Dict, List, Any, Optional, Union
import logging
import json

# 导入模板系统
from template_system import (
    template_manager,
    Message,
    UserMessage,
    AssistantMessage,
    SystemMessage
)

# 导入命令模板
from templates.command_templates import (
    get_command_template,
    SUPPORTED_VENDORS,
    TEMPLATE_TYPES
)

# 导入设备管理器获取设备信息
from network_devices import device_manager, DeviceVendor

# 设置日志
logger = logging.getLogger("device_prompts")

# ================== VLAN配置提示模板 ==================

@template_manager.register_template(
    name="configure_vlan",
    description="配置VLAN提示模板"
)
def configure_vlan_prompt(
    device_id: str,
    vlan_id: str,
    vlan_name: str = None,
    operation: str = "create"
) -> List[Message]:
    """
    配置VLAN的提示模板
    
    Args:
        device_id: 设备ID
        vlan_id: VLAN ID
        vlan_name: VLAN名称
        operation: 操作类型，create/delete
    
    Returns:
        消息列表
    """
    # 获取设备信息
    device = device_manager.get_device(device_id)
    if not device:
        return [
            SystemMessage("设备信息获取失败"),
            UserMessage(f"我想配置VLAN {vlan_id}，但无法找到指定设备。"),
            AssistantMessage("无法找到指定的设备。请确认设备ID是否正确，或者先添加该设备。")
        ]
    
    # 确定厂商
    vendor = device.vendor.value if hasattr(device.vendor, 'value') else str(device.vendor).lower()
    if vendor not in SUPPORTED_VENDORS:
        # 厂商不支持，返回通用提示
        return [
            SystemMessage(f"设备厂商({vendor})不在支持列表中"),
            UserMessage(f"我想在{device.name} ({device.ip_address})上配置VLAN {vlan_id}。"),
            AssistantMessage(f"该设备厂商({vendor})暂不支持自动生成配置命令。请手动输入适合该设备的VLAN配置命令。")
        ]
    
    # 获取VLAN配置命令
    command = None
    if operation.lower() == "create":
        command = get_command_template(
            vendor, 
            "vlan_config", 
            "create_vlan", 
            vlan_id=vlan_id, 
            vlan_name=vlan_name
        )
    elif operation.lower() == "delete":
        command = get_command_template(
            vendor, 
            "vlan_config", 
            "delete_vlan", 
            vlan_id=vlan_id
        )
    
    if not command:
        return [
            SystemMessage("命令生成失败"),
            UserMessage(f"我想在{device.name}上{operation} VLAN {vlan_id}。"),
            AssistantMessage(f"无法生成{vendor}设备的VLAN{operation}命令。请检查参数是否正确。")
        ]
    
    # 构建提示消息
    operation_text = "创建" if operation.lower() == "create" else "删除"
    vlan_desc = f"VLAN {vlan_id}" + (f" ({vlan_name})" if vlan_name else "")
    
    return [
        SystemMessage(f"为{vendor}设备生成VLAN配置命令"),
        UserMessage(f"我想在{device.name} ({device.ip_address})上{operation_text} {vlan_desc}。"),
        AssistantMessage(
            f"为{device.name} ({device.ip_address})设备生成{operation_text} {vlan_desc}的配置命令如下:\n\n"
            f"```\n{command}\n```\n\n"
            f"请确认命令无误后，可以使用`send_command`或`send_commands`工具执行这些命令。"
        )
    ]

@template_manager.register_template(
    name="add_interface_to_vlan",
    description="配置接口VLAN提示模板"
)
def add_interface_to_vlan_prompt(
    device_id: str,
    interface: str,
    vlan_id: str,
    mode: str = "access"
) -> List[Message]:
    """
    配置接口VLAN的提示模板
    
    Args:
        device_id: 设备ID
        interface: 接口名称
        vlan_id: VLAN ID
        mode: 接口模式，access或trunk
    
    Returns:
        消息列表
    """
    # 获取设备信息
    device = device_manager.get_device(device_id)
    if not device:
        return [
            SystemMessage("设备信息获取失败"),
            UserMessage(f"我想将接口{interface}添加到VLAN {vlan_id}，但无法找到指定设备。"),
            AssistantMessage("无法找到指定的设备。请确认设备ID是否正确，或者先添加该设备。")
        ]
    
    # 确定厂商
    vendor = device.vendor.value if hasattr(device.vendor, 'value') else str(device.vendor).lower()
    if vendor not in SUPPORTED_VENDORS:
        # 厂商不支持，返回通用提示
        return [
            SystemMessage(f"设备厂商({vendor})不在支持列表中"),
            UserMessage(f"我想在{device.name}上将接口{interface}添加到VLAN {vlan_id}。"),
            AssistantMessage(f"该设备厂商({vendor})暂不支持自动生成配置命令。请手动输入适合该设备的接口VLAN配置命令。")
        ]
    
    # 获取接口VLAN配置命令
    command = get_command_template(
        vendor, 
        "vlan_config", 
        "add_interface_to_vlan", 
        interface=interface,
        vlan_id=vlan_id,
        mode=mode
    )
    
    if not command:
        return [
            SystemMessage("命令生成失败"),
            UserMessage(f"我想在{device.name}上将接口{interface}配置为VLAN {vlan_id}。"),
            AssistantMessage(f"无法生成{vendor}设备的接口VLAN配置命令。请检查参数是否正确。")
        ]
    
    # 构建提示消息
    mode_text = "接入" if mode.lower() == "access" else "中继"
    
    return [
        SystemMessage(f"为{vendor}设备生成接口VLAN配置命令"),
        UserMessage(f"我想在{device.name} ({device.ip_address})上将接口{interface}配置为VLAN {vlan_id}的{mode_text}端口。"),
        AssistantMessage(
            f"为{device.name} ({device.ip_address})设备生成配置接口{interface}为VLAN {vlan_id}的{mode_text}端口命令如下:\n\n"
            f"```\n{command}\n```\n\n"
            f"请确认命令无误后，可以使用`send_command`或`send_commands`工具执行这些命令。"
        )
    ]

# ================== 接口配置提示模板 ==================

@template_manager.register_template(
    name="configure_interface_ip",
    description="配置接口IP地址提示模板"
)
def configure_interface_ip_prompt(
    device_id: str,
    interface: str,
    ip_address: str,
    subnet_mask: str
) -> List[Message]:
    """
    配置接口IP地址的提示模板
    
    Args:
        device_id: 设备ID
        interface: 接口名称
        ip_address: IP地址
        subnet_mask: 子网掩码
    
    Returns:
        消息列表
    """
    # 获取设备信息
    device = device_manager.get_device(device_id)
    if not device:
        return [
            SystemMessage("设备信息获取失败"),
            UserMessage(f"我想配置接口{interface}的IP地址，但无法找到指定设备。"),
            AssistantMessage("无法找到指定的设备。请确认设备ID是否正确，或者先添加该设备。")
        ]
    
    # 确定厂商
    vendor = device.vendor.value if hasattr(device.vendor, 'value') else str(device.vendor).lower()
    if vendor not in SUPPORTED_VENDORS:
        # 厂商不支持，返回通用提示
        return [
            SystemMessage(f"设备厂商({vendor})不在支持列表中"),
            UserMessage(f"我想在{device.name}上配置接口{interface}的IP地址为{ip_address} {subnet_mask}。"),
            AssistantMessage(f"该设备厂商({vendor})暂不支持自动生成配置命令。请手动输入适合该设备的接口IP配置命令。")
        ]
    
    # 获取接口IP配置命令
    command = get_command_template(
        vendor, 
        "interface_config", 
        "configure_interface_ip", 
        interface=interface,
        ip_address=ip_address,
        subnet_mask=subnet_mask
    )
    
    if not command:
        return [
            SystemMessage("命令生成失败"),
            UserMessage(f"我想在{device.name}上配置接口{interface}的IP地址。"),
            AssistantMessage(f"无法生成{vendor}设备的接口IP配置命令。请检查参数是否正确。")
        ]
    
    # 构建提示消息
    return [
        SystemMessage(f"为{vendor}设备生成接口IP配置命令"),
        UserMessage(f"我想在{device.name} ({device.ip_address})上配置接口{interface}的IP地址为{ip_address} {subnet_mask}。"),
        AssistantMessage(
            f"为{device.name} ({device.ip_address})设备生成配置接口{interface}的IP地址为{ip_address} {subnet_mask}的命令如下:\n\n"
            f"```\n{command}\n```\n\n"
            f"请确认命令无误后，可以使用`send_command`或`send_commands`工具执行这些命令。"
        )
    ]

@template_manager.register_template(
    name="configure_interface_state",
    description="配置接口状态提示模板"
)
def configure_interface_state_prompt(
    device_id: str,
    interface: str,
    state: str = "up"
) -> List[Message]:
    """
    配置接口状态的提示模板
    
    Args:
        device_id: 设备ID
        interface: 接口名称
        state: 接口状态，up或down
    
    Returns:
        消息列表
    """
    # 获取设备信息
    device = device_manager.get_device(device_id)
    if not device:
        return [
            SystemMessage("设备信息获取失败"),
            UserMessage(f"我想配置接口{interface}的状态，但无法找到指定设备。"),
            AssistantMessage("无法找到指定的设备。请确认设备ID是否正确，或者先添加该设备。")
        ]
    
    # 确定厂商
    vendor = device.vendor.value if hasattr(device.vendor, 'value') else str(device.vendor).lower()
    if vendor not in SUPPORTED_VENDORS:
        # 厂商不支持，返回通用提示
        return [
            SystemMessage(f"设备厂商({vendor})不在支持列表中"),
            UserMessage(f"我想在{device.name}上将接口{interface}设置为{state}状态。"),
            AssistantMessage(f"该设备厂商({vendor})暂不支持自动生成配置命令。请手动输入适合该设备的接口状态配置命令。")
        ]
    
    # 获取接口状态配置命令
    command = get_command_template(
        vendor, 
        "interface_config", 
        "configure_interface_state", 
        interface=interface,
        state=state
    )
    
    if not command:
        return [
            SystemMessage("命令生成失败"),
            UserMessage(f"我想在{device.name}上配置接口{interface}的状态。"),
            AssistantMessage(f"无法生成{vendor}设备的接口状态配置命令。请检查参数是否正确。")
        ]
    
    # 构建提示消息
    state_text = "启用" if state.lower() == "up" else "禁用"
    
    return [
        SystemMessage(f"为{vendor}设备生成接口状态配置命令"),
        UserMessage(f"我想在{device.name} ({device.ip_address})上{state_text}接口{interface}。"),
        AssistantMessage(
            f"为{device.name} ({device.ip_address})设备生成{state_text}接口{interface}的命令如下:\n\n"
            f"```\n{command}\n```\n\n"
            f"请确认命令无误后，可以使用`send_command`或`send_commands`工具执行这些命令。"
        )
    ]

# ================== 设备基本诊断提示模板 ==================

@template_manager.register_template(
    name="device_basic_diagnosis",
    description="设备基本诊断提示模板"
)
def device_basic_diagnosis_prompt(device_id: str) -> List[Message]:
    """
    设备基本诊断的提示模板
    
    Args:
        device_id: 设备ID
    
    Returns:
        消息列表
    """
    # 获取设备信息
    device = device_manager.get_device(device_id)
    if not device:
        return [
            SystemMessage("设备信息获取失败"),
            UserMessage(f"我想执行设备基本诊断，但无法找到指定设备。"),
            AssistantMessage("无法找到指定的设备。请确认设备ID是否正确，或者先添加该设备。")
        ]
    
    # 确定厂商
    vendor = device.vendor.value if hasattr(device.vendor, 'value') else str(device.vendor).lower()
    
    # 构建基本诊断提示
    diagnosis_steps = []
    
    if vendor.lower() == "cisco":
        diagnosis_steps = [
            "show version",
            "show interface",
            "show ip interface brief",
            "show running-config",
            "show vlan brief",
            "show ip route",
            "show cdp neighbors",
            "show environment all",
            "show log"
        ]
    elif vendor.lower() == "huawei":
        diagnosis_steps = [
            "display version",
            "display interface brief",
            "display ip interface brief",
            "display current-configuration",
            "display vlan",
            "display ip routing-table",
            "display lldp neighbor",
            "display environment",
            "display logbuffer"
        ]
    else:
        # 返回通用诊断步骤
        return [
            SystemMessage(f"未找到{vendor}设备的特定诊断步骤"),
            UserMessage(f"我想对{device.name}执行基本诊断。"),
            AssistantMessage(
                f"对于{device.name} ({device.ip_address})设备，建议执行以下基本诊断步骤:\n\n"
                f"1. 检查设备版本和硬件状态\n"
                f"2. 检查接口状态\n"
                f"3. 检查IP配置\n"
                f"4. 检查运行配置\n"
                f"5. 检查VLAN配置\n"
                f"6. 检查路由表\n"
                f"7. 检查邻居设备\n"
                f"8. 检查环境参数\n"
                f"9. 检查系统日志\n\n"
                f"由于{vendor}设备暂无预定义诊断命令，请根据设备特性输入相应命令。"
            )
        ]
    
    # 构建提示消息
    return [
        SystemMessage(f"为{vendor}设备生成基本诊断命令列表"),
        UserMessage(f"我想对{device.name} ({device.ip_address})执行基本诊断。"),
        AssistantMessage(
            f"为{device.name} ({device.ip_address})设备生成的基本诊断命令如下:\n\n"
            f"```\n" + "\n".join(diagnosis_steps) + "\n```\n\n"
            f"您可以使用`send_commands`工具执行这些命令，并根据输出分析设备状态。\n"
            f"命令格式: send_commands(device_id=\"{device_id}\", credential_id=\"您的凭据ID\", commands=\"" + 
            ";".join(diagnosis_steps[:3]) + "...\")"
        )
    ]

# 初始化提示模板模块
def init_device_prompts():
    """初始化设备提示模板模块"""
    logger.info("设备提示模板模块初始化完成")
    logger.info(f"已注册{len(template_manager.templates)}个提示模板")
    
# 调用初始化函数
init_device_prompts() 