"""
NetBrain MCP 提示模板系统

此模块提供了符合MCP协议的提示模板系统，支持：
1. 模板注册和管理
2. 带有占位符的模板渲染
3. 支持字符串和结构化消息格式
4. 与资源系统集成
"""

from typing import Dict, List, Any, Optional, Union, Callable
import logging
import sys
import json
import os
import datetime
import re
from dataclasses import dataclass, asdict, field

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)
logger = logging.getLogger("mcp_templates")

# 消息对象
@dataclass
class Message:
    """基础消息类"""
    role: str
    content: str


@dataclass
class UserMessage(Message):
    """用户消息"""
    def __init__(self, content: str):
        super().__init__(role="user", content=content)


@dataclass
class AssistantMessage(Message):
    """助手消息"""
    def __init__(self, content: str):
        super().__init__(role="assistant", content=content)


@dataclass
class SystemMessage(Message):
    """系统消息"""
    def __init__(self, content: str):
        super().__init__(role="system", content=content)


@dataclass
class PromptTemplate:
    """提示模板"""
    name: str
    description: str
    fn: Callable
    arguments: List[Dict[str, Any]] = field(default_factory=list)


class TemplateManager:
    """高级提示模板管理器"""
    
    def __init__(self):
        self.templates = {}
        
        # 缓存目录
        self.templates_dir = os.path.join(os.getcwd(), "templates")
        if not os.path.exists(self.templates_dir):
            try:
                os.makedirs(self.templates_dir)
                logger.info(f"已创建模板目录: {self.templates_dir}")
            except Exception as e:
                logger.warning(f"无法创建模板目录: {str(e)}")
                
        logger.info("模板管理器初始化完成")
    
    def register_template(self, name: str = None, description: str = None):
        """
        注册模板装饰器
        
        Args:
            name: 模板名称（可选，默认使用函数名）
            description: 模板描述（可选）
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            nonlocal name, description
            
            # 如果没有提供名称，使用函数名
            template_name = name or func.__name__
            
            # 如果没有提供描述，使用函数文档
            template_description = description or (func.__doc__ or "").strip()
            
            if template_name in self.templates:
                logger.warning(f"模板已存在: {template_name}，将被覆盖")
            
            # 解析函数参数作为模板参数
            import inspect
            sig = inspect.signature(func)
            args = []
            
            for param_name, param in sig.parameters.items():
                # 忽略self和cls参数
                if param_name in ('self', 'cls'):
                    continue
                    
                param_desc = ""
                if func.__doc__:
                    # 尝试从文档中提取参数描述
                    pattern = rf":param {param_name}:\s*(.*?)(?:\n|$)"
                    match = re.search(pattern, func.__doc__)
                    if match:
                        param_desc = match.group(1).strip()
                
                # 确定参数是否必需
                required = param.default == inspect.Parameter.empty
                
                args.append({
                    "name": param_name,
                    "description": param_desc,
                    "required": required
                })
            
            self.templates[template_name] = PromptTemplate(
                name=template_name,
                description=template_description,
                fn=func,
                arguments=args
            )
            
            logger.info(f"已注册模板: {template_name}")
            return func
        
        return decorator
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        获取模板
        
        Args:
            name: 模板名称
            
        Returns:
            模板对象或None
        """
        return self.templates.get(name)
    
    def render_template(self, name: str, arguments: Dict[str, Any] = None) -> Optional[Union[str, List[Message]]]:
        """
        渲染模板
        
        Args:
            name: 模板名称
            arguments: 模板参数
            
        Returns:
            渲染后的模板内容（字符串或消息列表）
        """
        arguments = arguments or {}
        
        template = self.get_template(name)
        if not template:
            logger.warning(f"模板不存在: {name}")
            return None
        
        try:
            # 调用模板函数
            result = template.fn(**arguments)
            logger.info(f"已渲染模板: {name}")
            return result
        except Exception as e:
            logger.error(f"渲染模板失败: {name}, 错误: {str(e)}")
            return None
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        列出所有可用模板
        
        Returns:
            模板列表
        """
        return [
            {
                "name": template.name,
                "description": template.description,
                "arguments": template.arguments
            }
            for template in self.templates.values()
        ]
    
    def save_templates(self):
        """保存模板到文件"""
        try:
            # 将模板序列化并保存
            for name, template in self.templates.items():
                # 无法直接序列化函数，只保存元数据
                template_data = {
                    "name": template.name,
                    "description": template.description,
                    "arguments": template.arguments
                }
                
                file_path = os.path.join(self.templates_dir, f"{name}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已保存所有模板到: {self.templates_dir}")
        except Exception as e:
            logger.error(f"保存模板失败: {str(e)}")
    
    def load_templates(self):
        """从文件加载模板"""
        if not os.path.exists(self.templates_dir):
            logger.warning(f"模板目录不存在: {self.templates_dir}")
            return
        
        try:
            # 加载所有模板文件
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.templates_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    # 注意：无法加载函数实现，仅加载元数据
                    logger.info(f"已加载模板元数据: {template_data['name']}")
            
            logger.info(f"已加载所有模板")
        except Exception as e:
            logger.error(f"加载模板失败: {str(e)}")


# 创建全局模板管理器实例
template_manager = TemplateManager()


# 与资源系统集成的渲染函数
async def render_template_with_resources(
    template_name: str, 
    context: Dict[str, Any], 
    resource_uris: Dict[str, str],
    resource_manager=None
) -> Union[str, List[Message]]:
    """
    渲染包含资源引用的模板
    
    Args:
        template_name: 模板名称
        context: 渲染上下文
        resource_uris: 资源URI映射，格式为 {context_key: resource_uri}
        resource_manager: 资源管理器实例（可选）
        
    Returns:
        渲染后的模板内容
    """
    if resource_manager is None:
        # 尝试导入资源管理器
        try:
            from mcp_resources import resource_manager
        except ImportError:
            logger.error("无法导入资源管理器")
            return None
    
    # 扩展上下文，添加资源内容
    extended_context = context.copy()
    
    for context_key, uri in resource_uris.items():
        try:
            # 获取资源内容
            resource_content = await resource_manager.get_resource(uri)
            extended_context[context_key] = resource_content
        except Exception as e:
            logger.error(f"获取资源失败: {uri}, 错误: {str(e)}")
            extended_context[context_key] = f"错误: 无法加载资源 {uri}"
    
    # 渲染模板
    return template_manager.render_template(template_name, extended_context)


# 示例模板
@template_manager.register_template(
    name="network_diagnosis",
    description="网络诊断提示模板"
)
def network_diagnosis_prompt(device_name: str, issue_description: str, verbose: bool = False) -> str:
    """
    创建网络诊断提示
    
    :param device_name: 设备名称
    :param issue_description: 问题描述
    :param verbose: 是否生成详细输出
    """
    base_prompt = f"""
    请针对设备 {device_name} 的以下问题进行诊断：
    
    问题描述: {issue_description}
    
    请提供可能的根本原因和解决方案。
    """
    
    if verbose:
        base_prompt += """
        请详细说明诊断思路和解决步骤，包括：
        1. 初步分析和可能原因
        2. 建议的排查命令
        3. 可能的解决方案，按优先级排序
        4. 预防此类问题的最佳实践
        """
    
    return base_prompt


@template_manager.register_template()
def device_configuration(device_type: str, purpose: str) -> List[Message]:
    """
    创建设备配置会话
    
    :param device_type: 设备类型（路由器/交换机/防火墙）
    :param purpose: 配置目的（新设备/更新/安全强化）
    """
    system_message = SystemMessage(
        f"你是一名网络工程师，正在帮助配置一台{device_type}，目的是{purpose}。"
    )
    
    user_message = UserMessage(
        f"我需要为{purpose}配置一台{device_type}，请提供配置步骤和命令。"
    )
    
    assistant_message = AssistantMessage(
        f"我很乐意帮助您配置{device_type}。让我们开始：\n\n"
        f"首先，让我了解一下您的网络环境和具体需求..."
    )
    
    return [system_message, user_message, assistant_message]


# 网络设备专用模板
@template_manager.register_template(
    name="device_diagnosis",
    description="网络设备诊断模板"
)
def device_diagnosis_template(device_info: Dict[str, Any], interfaces_info: str = None, logs: str = None) -> List[Message]:
    """
    网络设备诊断提示模板，用于分析设备状态和接口信息
    
    :param device_info: 设备基本信息对象
    :param interfaces_info: 接口详细信息
    :param logs: 设备日志信息
    """
    system_prompt = f"""你是一位专业的网络工程师，负责诊断{device_info.get('vendor', '未知厂商')}的{device_info.get('device_type', '网络设备')}。
请根据提供的设备信息、接口状态和日志，进行专业分析并提供诊断报告。
诊断需要包括：
1. 设备基本状态总结
2. 接口状态分析
3. 潜在问题识别
4. 具体解决方案建议
5. 后续优化建议"""

    # 格式化设备信息
    device_details = f"""
设备基本信息:
- 名称: {device_info.get('name', 'N/A')}
- IP地址: {device_info.get('ip_address', 'N/A')}
- 型号: {device_info.get('model', 'N/A')}
- 操作系统: {device_info.get('os_version', 'N/A')}
- 状态: {device_info.get('status', 'N/A')}
- 位置: {device_info.get('location', 'N/A')}
- 描述: {device_info.get('description', 'N/A')}
"""

    user_prompt = f"""请帮我诊断以下网络设备的状态：
    
{device_details}

"""

    if interfaces_info:
        user_prompt += f"""
接口信息:
{interfaces_info}
"""

    if logs:
        user_prompt += f"""
设备日志:
{logs}
"""

    user_prompt += """
请提供详细的诊断报告，包括问题分析和解决方案。"""

    return [
        SystemMessage(system_prompt),
        UserMessage(user_prompt)
    ]


@template_manager.register_template(
    name="config_review",
    description="网络设备配置审查模板"
)
def config_review_template(device_info: Dict[str, Any], config_content: str, focus_area: str = None) -> List[Message]:
    """
    网络配置审查提示模板，用于审查设备配置并提供改进建议
    
    :param device_info: 设备基本信息对象
    :param config_content: 设备配置内容
    :param focus_area: 审查重点领域（安全/性能/路由/其他）
    """
    # 根据厂商确定专业技能
    vendor = device_info.get('vendor', '').lower()
    if 'cisco' in vendor:
        vendor_expertise = "思科IOS/IOS-XE/NX-OS配置专家"
    elif 'huawei' in vendor:
        vendor_expertise = "华为VRP配置专家"
    elif 'juniper' in vendor:
        vendor_expertise = "Juniper JUNOS配置专家"
    elif 'h3c' in vendor:
        vendor_expertise = "H3C Comware配置专家"
    else:
        vendor_expertise = "多厂商网络设备配置专家"
    
    system_prompt = f"""你是一名{vendor_expertise}，拥有多年网络配置审查经验。
请对提供的设备配置进行全面审查并提供专业的改进建议。
审查需要包括：
1. 总体配置评估
2. 配置最佳实践符合度
3. 安全风险识别
4. 潜在性能优化点
5. 具体改进建议（包括命令示例）"""

    # 格式化设备信息
    device_details = f"""
设备信息:
- 名称: {device_info.get('name', 'N/A')}
- 型号: {device_info.get('model', 'N/A')}
- 操作系统: {device_info.get('os_version', 'N/A')}
- 厂商: {device_info.get('vendor', 'N/A')}
"""

    user_prompt = f"""请审查以下网络设备的配置：
    
{device_details}

配置内容:
```
{config_content}
```
"""

    if focus_area:
        user_prompt += f"""
特别关注以下方面: {focus_area}
"""

    user_prompt += """
请提供详细的配置审查报告，包括问题分析和具体改进建议。"""

    return [
        SystemMessage(system_prompt),
        UserMessage(user_prompt)
    ]


@template_manager.register_template(
    name="route_analysis",
    description="网络路由分析模板"
)
def route_analysis_template(device_info: Dict[str, Any], routes_output: str, target_network: str = None) -> str:
    """
    路由分析提示模板，用于分析路由表并提供优化建议
    
    :param device_info: 设备基本信息对象
    :param routes_output: 路由表输出
    :param target_network: 目标网络（可选）
    """
    prompt = f"""
# 路由分析任务

## 设备信息
- 名称: {device_info.get('name', 'N/A')}
- IP地址: {device_info.get('ip_address', 'N/A')}
- 设备类型: {device_info.get('device_type', 'N/A')}
- 厂商: {device_info.get('vendor', 'N/A')}
- 操作系统: {device_info.get('os_version', 'N/A')}

## 路由表
```
{routes_output}
```

请作为网络工程师分析上述路由表，包括：
1. 默认路由检查
2. 路由类型分布（静态/动态）统计
3. 路由协议使用情况
4. 潜在的路由问题识别
5. 路由优化建议
"""

    if target_network:
        prompt += f"""
## 特定网络分析
请特别分析到 {target_network} 的路由路径，包括下一跳、出接口、管理距离和度量值。
"""

    return prompt


@template_manager.register_template(
    name="vlan_config",
    description="VLAN配置生成模板"
)
def vlan_config_template(
    device_vendor: str,
    vlan_id: int,
    vlan_name: str,
    interfaces: List[str] = None,
    ip_address: str = None,
    vlan_purpose: str = None
) -> str:
    """
    VLAN配置生成提示模板
    
    :param device_vendor: 设备厂商（cisco/huawei/h3c/juniper等）
    :param vlan_id: VLAN ID
    :param vlan_name: VLAN名称
    :param interfaces: 要添加到VLAN的接口列表
    :param ip_address: VLAN接口IP地址（可选）
    :param vlan_purpose: VLAN用途描述（可选）
    """
    # 标准化厂商名称
    vendor = device_vendor.lower()
    
    prompt = f"""
# {vlan_name} (VLAN {vlan_id}) 配置生成

请为{device_vendor}设备生成配置VLAN {vlan_id}的完整命令序列，包括：

1. 创建VLAN {vlan_id}
2. 设置VLAN名称为"{vlan_name}"
"""

    if vlan_purpose:
        prompt += f"3. VLAN用途：{vlan_purpose}\n"
    
    if interfaces:
        prompt += f"\n## 需要添加到VLAN {vlan_id}的接口：\n"
        for interface in interfaces:
            prompt += f"- {interface}\n"
    
    if ip_address:
        prompt += f"\n## 配置VLAN接口IP地址：{ip_address}\n"
    
    prompt += f"""
请提供适用于{device_vendor}设备的完整配置命令，包括进入配置模式和退出保存的完整步骤。如果有多种方式，请提供最佳实践方案。
"""
    
    return prompt


@template_manager.register_template(
    name="network_topology",
    description="网络拓扑分析模板"
)
def network_topology_template(devices: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> List[Message]:
    """
    网络拓扑分析提示模板
    
    :param devices: 设备列表
    :param connections: 连接列表
    """
    # 格式化设备信息
    devices_text = "设备清单:\n"
    for i, device in enumerate(devices, 1):
        devices_text += f"{i}. {device.get('name', 'Unknown')} ({device.get('ip_address', 'N/A')}) - {device.get('device_type', 'N/A')} - {device.get('vendor', 'N/A')}\n"
    
    # 格式化连接信息
    connections_text = "连接清单:\n"
    for i, conn in enumerate(connections, 1):
        source = conn.get('source_device', 'Unknown')
        target = conn.get('target_device', 'Unknown')
        src_if = conn.get('source_interface', 'N/A')
        tgt_if = conn.get('target_interface', 'N/A')
        connections_text += f"{i}. {source} ({src_if}) <--> {target} ({tgt_if})\n"
    
    system_prompt = """你是一名网络拓扑专家，擅长分析网络设计和提供优化建议。
请分析提供的网络拓扑信息，包括设备和连接，然后：
1. 识别网络架构模式（例如核心-汇聚-接入、叶脊等）
2. 评估当前拓扑的优缺点
3. 识别潜在的单点故障
4. 提供拓扑优化建议
5. 讨论可扩展性考虑"""

    user_prompt = f"""请分析以下网络拓扑并提供专业评估：

{devices_text}

{connections_text}

请提供详细的拓扑分析报告，包括架构评估、风险点和优化建议。"""

    return [
        SystemMessage(system_prompt),
        UserMessage(user_prompt)
    ]


@template_manager.register_template(
    name="network_security",
    description="网络安全评估模板"
)
def network_security_template(
    device_info: Dict[str, Any],
    config_content: str,
    acl_content: str = None,
    security_focus: str = None
) -> str:
    """
    网络安全评估提示模板
    
    :param device_info: 设备基本信息
    :param config_content: 设备配置内容
    :param acl_content: 访问控制列表内容（可选）
    :param security_focus: 安全评估重点（可选）
    """
    prompt = f"""
# 网络安全评估

## 设备信息
- 名称: {device_info.get('name', 'N/A')}
- 类型: {device_info.get('device_type', 'N/A')}
- 厂商: {device_info.get('vendor', 'N/A')}
- 操作系统: {device_info.get('os_version', 'N/A')}

## 设备配置
```
{config_content}
```
"""

    if acl_content:
        prompt += f"""
## 访问控制列表
```
{acl_content}
```
"""

    if security_focus:
        prompt += f"""
## 评估重点
{security_focus}
"""

    prompt += """
请作为网络安全专家，评估上述配置的安全性，包括：

1. 安全风险识别和严重级别评估
2. 是否符合网络安全最佳实践
3. 身份验证和访问控制评估
4. 加密和安全协议使用情况
5. 详细的安全强化建议（带具体命令）
6. 安全监控和审计建议

请提供全面的安全评估报告和具体改进措施。
"""

    return prompt 