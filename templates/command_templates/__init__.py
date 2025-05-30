"""
网络设备操作命令模板

这个模块集成了各个厂商的网络设备操作命令模板，提供统一的接口。
支持的厂商包括：思科(Cisco)、华为(Huawei)、H3C、Juniper等。
"""

import importlib
import os
import sys
import logging
from typing import Dict, Any, List, Optional

# 设置日志
logger = logging.getLogger("command_templates")

# 支持的厂商列表
SUPPORTED_VENDORS = ["cisco", "huawei", "h3c", "juniper"]

# 定义模板类型
TEMPLATE_TYPES = {
    "vlan_config": "VLAN配置",
    "interface_config": "接口配置",
    "routing_config": "路由配置",
    "acl_config": "ACL配置",
    "device_basic": "基本设备操作",
    "topology_discovery": "拓扑发现"
}

# 动态导入模板模块
_modules = {}

def _import_vendor_template(vendor: str, template_type: str) -> Optional[Any]:
    """
    动态导入供应商的特定模板模块
    
    Args:
        vendor: 厂商名称
        template_type: 模板类型
        
    Returns:
        导入的模块或None
    """
    module_path = f"templates.command_templates.{vendor}.{template_type}"
    
    if f"{vendor}_{template_type}" in _modules:
        return _modules[f"{vendor}_{template_type}"]
    
    try:
        module = importlib.import_module(module_path)
        _modules[f"{vendor}_{template_type}"] = module
        logger.info(f"已加载{vendor}的{template_type}模板")
        return module
    except ImportError as e:
        logger.warning(f"无法导入{vendor}的{template_type}模板: {str(e)}")
        return None

def get_command_template(vendor: str, template_type: str, function_name: str, **kwargs) -> Optional[str]:
    """
    获取特定厂商的命令模板
    
    Args:
        vendor: 厂商名称 (cisco, huawei, h3c, juniper等)
        template_type: 模板类型 (vlan_config, interface_config等)
        function_name: 函数名称
        **kwargs: 传递给模板函数的参数
        
    Returns:
        命令字符串或None
    """
    if vendor.lower() not in SUPPORTED_VENDORS:
        logger.warning(f"不支持的厂商: {vendor}")
        return None
    
    # 尝试导入模块
    module = _import_vendor_template(vendor.lower(), template_type)
    if not module:
        logger.warning(f"未找到{vendor}的{template_type}模板")
        return None
    
    # 获取函数
    if not hasattr(module, function_name):
        logger.warning(f"模板{vendor}.{template_type}没有{function_name}函数")
        return None
    
    func = getattr(module, function_name)
    
    # 调用函数
    try:
        result = func(**kwargs)
        return result
    except Exception as e:
        logger.error(f"执行模板函数失败: {str(e)}")
        return None

# 导出主要函数
__all__ = ["get_command_template", "SUPPORTED_VENDORS", "TEMPLATE_TYPES"] 