from typing import Dict, List, Callable, Any, Optional, Union, TypeVar, Generic
import inspect
from enum import Enum
from dataclasses import dataclass
from functools import wraps
import logging
import sys

# 引入相同的日志格式化处理
class JsonFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
        
    def format(self, record):
        log_record = super().format(record)
        return log_record.encode('utf-8', errors='replace').decode('utf-8')

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)

# 设置所有处理器使用UTF-8编码格式化
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(JsonFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger("tool_manager")

class ToolCategory(Enum):
    """工具分类枚举"""
    GENERAL = "general"
    NETWORK_DEVICE = "network_device"
    CONFIGURATION = "configuration"
    TOPOLOGY = "topology"
    DIAGNOSTIC = "diagnostic"
    SECURITY = "security"

@dataclass
class ToolInfo:
    """工具信息数据类"""
    name: str
    func: Callable
    description: str
    category: ToolCategory
    parameters: Dict[str, Dict[str, Any]]
    return_type: str

class ToolManager:
    """工具管理器，负责工具的注册和调用"""
    
    def __init__(self):
        self.tools: Dict[str, ToolInfo] = {}
        self.categories: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}
        logger.info("工具管理器初始化完成")
    
    def register_tool(self, 
                      name: Optional[str] = None, 
                      description: Optional[str] = None,
                      category: ToolCategory = ToolCategory.GENERAL) -> Callable:
        """
        工具注册装饰器
        
        Args:
            name: 工具名称，默认使用函数名
            description: 工具描述，默认使用函数文档字符串
            category: 工具分类，默认为通用类
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            # 获取工具名称
            tool_name = name or func.__name__
            
            # 获取工具描述
            tool_description = description or func.__doc__ or "无描述"
            
            # 获取函数签名
            sig = inspect.signature(func)
            
            # 提取参数信息
            params = {}
            for param_name, param in sig.parameters.items():
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
                param_default = None if param.default == inspect.Parameter.empty else param.default
                params[param_name] = {
                    "type": str(param_type),
                    "default": param_default,
                    "required": param.default == inspect.Parameter.empty
                }
            
            # 提取返回类型
            return_type = str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else "Any"
            
            # 创建工具信息对象
            tool_info = ToolInfo(
                name=tool_name,
                func=func,
                description=tool_description,
                category=category,
                parameters=params,
                return_type=return_type
            )
            
            # 注册工具
            self.tools[tool_name] = tool_info
            self.categories[category].append(tool_name)
            
            logger.info(f"工具 '{tool_name}' 已注册到类别 '{category.value}'")
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                logger.info(f"调用工具: {tool_name}")
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    logger.error(f"工具 '{tool_name}' 执行错误: {str(e)}")
                    raise
            
            return wrapper
        
        return decorator
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[Dict[str, Any]]:
        """
        列出已注册的工具
        
        Args:
            category: 可选的工具分类过滤器
            
        Returns:
            工具信息列表
        """
        result = []
        
        if category:
            tool_names = self.categories.get(category, [])
        else:
            tool_names = self.tools.keys()
        
        for name in tool_names:
            tool = self.tools.get(name)
            if tool:
                result.append({
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category.value,
                    "parameters": tool.parameters,
                    "return_type": tool.return_type
                })
                
        return result
    
    def get_tool(self, name: str) -> Optional[ToolInfo]:
        """
        获取工具信息
        
        Args:
            name: 工具名称
            
        Returns:
            工具信息或None
        """
        return self.tools.get(name)
    
    def execute_tool(self, name: str, *args, **kwargs) -> Any:
        """
        执行工具
        
        Args:
            name: 工具名称
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            工具执行结果
            
        Raises:
            ValueError: 如果工具不存在
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"工具 '{name}' 不存在")
        
        logger.info(f"执行工具: {name}")
        try:
            return tool.func(*args, **kwargs)
        except Exception as e:
            logger.error(f"工具 '{name}' 执行错误: {str(e)}")
            raise

# 创建全局工具管理器实例
tool_manager = ToolManager() 