"""
NetBrain MCP 资源模块

此模块提供了MCP资源管理和提供功能。
MCP资源是客户端可以访问的数据对象，通过URI标识。
"""

from typing import Dict, List, Any, Optional, Union
import logging
import sys
import json
import os
import datetime

# 确保正确处理中文字符
class JsonEncoderWithChinese(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, str):
            return obj
        return super().default(obj)

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

logger = logging.getLogger("mcp_resources")

# 资源类型定义
class ResourceType:
    DEVICE = "device"
    CREDENTIAL = "credential"
    TOPOLOGY = "topology"
    SYSTEM = "system"
    CONFIG = "config"
    LOG = "log"
    REPORT = "report"
    SCAN = "scan"

# 资源管理器类
class ResourceManager:
    """MCP资源管理器，负责资源注册和提供"""
    
    def __init__(self):
        self.resources = {}
        self.resource_patterns = {}
        self.resource_cache = {}
        self.cache_expiration = {}  # 缓存过期时间
        self.default_cache_ttl = 300  # 默认缓存5分钟
        
        # 缓存目录
        self.cache_dir = os.path.join(os.getcwd(), "resource_cache")
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
                logger.info(f"已创建资源缓存目录: {self.cache_dir}")
            except Exception as e:
                logger.warning(f"无法创建资源缓存目录: {str(e)}")
                
        logger.info("资源管理器初始化完成")
    
    def register_resource(self, uri_pattern: str, resource_type: str):
        """
        注册资源装饰器
        
        Args:
            uri_pattern: 资源URI模式，如"device://{id}"
            resource_type: 资源类型
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            if uri_pattern in self.resource_patterns:
                logger.warning(f"资源URI模式已存在: {uri_pattern}，将被覆盖")
            
            self.resource_patterns[uri_pattern] = {
                "func": func,
                "type": resource_type
            }
            
            logger.info(f"已注册资源: {uri_pattern} (类型: {resource_type})")
            return func
        
        return decorator
    
    async def get_resource(self, uri: str, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        获取资源
        
        Args:
            uri: 资源URI
            use_cache: 是否使用缓存
            cache_ttl: 缓存生存时间（秒）
            
        Returns:
            资源内容
        """
        # 检查缓存
        if use_cache and uri in self.resource_cache:
            # 检查缓存是否过期
            if uri in self.cache_expiration and self.cache_expiration[uri] > datetime.datetime.now():
                logger.info(f"从缓存获取资源: {uri}")
                return self.resource_cache[uri]
            else:
                # 缓存过期，从缓存中删除
                logger.info(f"资源缓存已过期: {uri}")
                if uri in self.resource_cache:
                    del self.resource_cache[uri]
                if uri in self.cache_expiration:
                    del self.cache_expiration[uri]
        
        # 从文件缓存加载
        if use_cache:
            cache_file = self._get_cache_filename(uri)
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    # 检查缓存是否过期
                    if "expiration" in cache_data:
                        expiration = datetime.datetime.fromisoformat(cache_data["expiration"])
                        if expiration > datetime.datetime.now():
                            logger.info(f"从文件缓存加载资源: {uri}")
                            self.resource_cache[uri] = cache_data["data"]
                            self.cache_expiration[uri] = expiration
                            return cache_data["data"]
                except Exception as e:
                    logger.warning(f"加载资源缓存文件失败: {str(e)}")
        
        # 查找匹配的资源处理函数
        handler_func = None
        parameters = {}
        
        for pattern, info in self.resource_patterns.items():
            match_result = self._match_uri_pattern(uri, pattern)
            if match_result:
                handler_func = info["func"]
                parameters = match_result
                break
        
        if not handler_func:
            logger.warning(f"未找到匹配的资源处理函数: {uri}")
            return {"error": f"资源不存在: {uri}"}
        
        try:
            # 调用资源处理函数
            result = await handler_func(**parameters) if callable(handler_func) else handler_func
            
            # 缓存结果
            if use_cache:
                self.resource_cache[uri] = result
                ttl = cache_ttl or self.default_cache_ttl
                expiration = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
                self.cache_expiration[uri] = expiration
                
                # 保存到文件缓存
                try:
                    cache_file = self._get_cache_filename(uri)
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "data": result,
                            "expiration": expiration.isoformat()
                        }, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.warning(f"保存资源缓存文件失败: {str(e)}")
            
            return result
        except Exception as e:
            logger.error(f"获取资源失败: {uri}, 错误: {str(e)}")
            return {"error": f"获取资源失败: {str(e)}"}
    
    def _match_uri_pattern(self, uri: str, pattern: str) -> Optional[Dict[str, str]]:
        """
        匹配URI模式
        
        Args:
            uri: 资源URI
            pattern: URI模式
            
        Returns:
            匹配参数或None
        """
        # 将模式转换为部分
        pattern_parts = pattern.split('/')
        uri_parts = uri.split('/')
        
        # 检查部分数量是否匹配
        if len(pattern_parts) != len(uri_parts):
            return None
        
        # 提取参数
        params = {}
        for i, (pattern_part, uri_part) in enumerate(zip(pattern_parts, uri_parts)):
            # 检查是否为参数占位符
            if '{' in pattern_part and '}' in pattern_part:
                # 提取参数名
                param_name = pattern_part.strip('{}')
                params[param_name] = uri_part
            # 否则，检查是否完全匹配
            elif pattern_part != uri_part:
                return None
        
        return params
    
    def _get_cache_filename(self, uri: str) -> str:
        """
        获取缓存文件名
        
        Args:
            uri: 资源URI
            
        Returns:
            缓存文件路径
        """
        # 将URI转换为文件名安全的字符串
        safe_uri = uri.replace(':', '_').replace('/', '_').replace('.', '_').replace('\\', '_')
        return os.path.join(self.cache_dir, f"{safe_uri}.json")
    
    def clear_cache(self, uri: Optional[str] = None) -> bool:
        """
        清除资源缓存
        
        Args:
            uri: 要清除的特定资源URI，如果为None则清除所有缓存
            
        Returns:
            是否成功清除缓存
        """
        try:
            if uri:
                if uri in self.resource_cache:
                    del self.resource_cache[uri]
                if uri in self.cache_expiration:
                    del self.cache_expiration[uri]
                
                # 删除文件缓存
                cache_file = self._get_cache_filename(uri)
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                
                logger.info(f"已清除资源缓存: {uri}")
            else:
                self.resource_cache.clear()
                self.cache_expiration.clear()
                
                # 删除所有缓存文件
                if os.path.exists(self.cache_dir):
                    for filename in os.listdir(self.cache_dir):
                        if filename.endswith('.json'):
                            os.remove(os.path.join(self.cache_dir, filename))
                
                logger.info("已清除所有资源缓存")
            
            return True
        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")
            return False
    
    def list_available_resources(self) -> List[Dict[str, Any]]:
        """
        列出可用的资源类型
        
        Returns:
            资源类型列表
        """
        resources = []
        
        for pattern, info in self.resource_patterns.items():
            resources.append({
                "uri_pattern": pattern,
                "type": info["type"],
                "description": info["func"].__doc__ if callable(info["func"]) and info["func"].__doc__ else "无描述"
            })
        
        return resources

# 创建全局资源管理器实例
resource_manager = ResourceManager()

# 提示模板管理器
class PromptTemplateManager:
    """MCP提示模板管理器，负责模板注册和渲染"""
    
    def __init__(self):
        self.templates = {}
        logger.info("提示模板管理器初始化完成")
    
    def register_template(self, name: str):
        """
        注册提示模板装饰器
        
        Args:
            name: 模板名称
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            if name in self.templates:
                logger.warning(f"提示模板已存在: {name}，将被覆盖")
            
            self.templates[name] = func
            
            logger.info(f"已注册提示模板: {name}")
            return func
        
        return decorator
    
    def get_template(self, name: str) -> Optional[str]:
        """
        获取提示模板
        
        Args:
            name: 模板名称
            
        Returns:
            模板内容或None
        """
        if name not in self.templates:
            return None
        
        template_func = self.templates[name]
        return template_func() if callable(template_func) else template_func
    
    def render_template(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        渲染提示模板
        
        Args:
            name: 模板名称
            context: 渲染上下文
            
        Returns:
            渲染后的模板或None
        """
        template = self.get_template(name)
        if not template:
            return None
        
        # 简单模板替换
        result = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            if isinstance(value, str):
                result = result.replace(placeholder, value)
            elif isinstance(value, dict):
                result = result.replace(placeholder, json.dumps(value, ensure_ascii=False, indent=2))
        
        return result
    
    def list_templates(self) -> List[Dict[str, str]]:
        """
        列出所有可用的提示模板
        
        Returns:
            模板列表
        """
        return [
            {
                "name": name,
                "description": func.__doc__ if callable(func) and func.__doc__ else "无描述"
            }
            for name, func in self.templates.items()
        ]

# 创建全局提示模板管理器实例
template_manager = PromptTemplateManager()

# 模板渲染帮助函数
def render_template_with_resources(template_name: str, context: Dict[str, Any], resource_uris: Dict[str, str]) -> str:
    """
    渲染带有资源的提示模板
    
    Args:
        template_name: 模板名称
        context: 渲染上下文
        resource_uris: 资源URI映射
        
    Returns:
        渲染后的模板
    """
    # 获取模板
    template = template_manager.get_template(template_name)
    if not template:
        return f"错误：未找到模板 '{template_name}'"
    
    # 加载资源内容
    for key, uri in resource_uris.items():
        # 实际加载资源的代码需要在使用时实现
        # 这里只是一个示例
        context[key] = f"{{{{ {uri} }}}}"
    
    # 渲染模板
    return template_manager.render_template(template_name, context) 