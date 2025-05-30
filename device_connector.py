from typing import Dict, List, Optional, Any, Union, Tuple
import logging
import sys
import asyncio
import re
import os
from abc import ABC, abstractmethod
from datetime import datetime

# 创建日志目录
os.makedirs("logs", exist_ok=True)

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

logger = logging.getLogger("device_connector")

# 全局变量
HAS_HUAWEI_SUPPORT = False
SCRAPLI_IMPORT_SUCCESS = False

# 导入scrapli并记录版本信息
try:
    # 导入同步版本的Scrapli
    from scrapli import Scrapli
    # 导入异步版本的Scrapli
    from scrapli.driver.core import AsyncIOSXEDriver, AsyncNXOSDriver, AsyncJunosDriver

    # 导入更多平台支持
    try:
        from scrapli_community import huawei_vrp
        HAS_HUAWEI_SUPPORT = True
        logger.info("成功加载华为设备驱动")
    except ImportError:
        HAS_HUAWEI_SUPPORT = False
        logger.warning("未找到华为设备驱动，将使用通用驱动")
        
    logger.info(f"成功导入scrapli, 版本: {getattr(Scrapli, '__version__', '未知')}")
    
    # 打印可用的异常类，帮助调试
    import scrapli.exceptions
    logger.debug("Available scrapli exceptions:")
    for attr_name in dir(scrapli.exceptions):
        if 'Error' in attr_name:
            logger.debug(f"  - {attr_name}")
            
    SCRAPLI_IMPORT_SUCCESS = True
except ImportError as e:
    logger.error(f"导入scrapli失败: {str(e)}，请确保已经安装: pip install scrapli>=2025.1.30")
    # 这里不再抛出异常，而是允许程序继续运行
    SCRAPLI_IMPORT_SUCCESS = False

from network_devices import (
    NetworkDevice,
    DeviceCredential,
    ConnectionProtocol,
    DeviceStatus
)

class CommandResult:
    """命令执行结果类"""
    
    def __init__(self, 
                 command: str, 
                 output: str, 
                 success: bool = True, 
                 error_message: Optional[str] = None):
        self.command = command
        self.output = output
        self.success = success
        self.error_message = error_message
        self.execution_time = datetime.now()
    
    def __str__(self) -> str:
        status = "成功" if self.success else "失败"
        return f"命令 '{self.command}' 执行{status}: {len(self.output)}字节"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "command": self.command,
            "output": self.output,
            "success": self.success,
            "error_message": self.error_message,
            "execution_time": self.execution_time.isoformat()
        }

class DeviceConnector(ABC):
    """设备连接器抽象基类"""
    
    def __init__(self, device: NetworkDevice, credential: DeviceCredential):
        self.device = device
        self.credential = credential
        self.connection = None
        self.connected = False
        self.last_activity = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        连接到设备
        
        Returns:
            是否连接成功
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        断开与设备的连接
        
        Returns:
            是否断开成功
        """
        pass
    
    @abstractmethod
    async def send_command(self, command: str, timeout: int = 30) -> CommandResult:
        """
        发送命令到设备
        
        Args:
            command: 要执行的命令
            timeout: 命令超时时间（秒）
            
        Returns:
            命令执行结果
        """
        pass
    
    @abstractmethod
    async def send_commands(self, commands: List[str], timeout: int = 30) -> List[CommandResult]:
        """
        发送多个命令到设备
        
        Args:
            commands: 要执行的命令列表
            timeout: 每个命令的超时时间（秒）
            
        Returns:
            命令执行结果列表
        """
        pass

class ScrapliConnector(DeviceConnector):
    """Scrapli连接器实现"""
    
    async def connect(self) -> bool:
        """
        通过Scrapli连接到设备
        
        Returns:
            是否连接成功
        """
        if not SCRAPLI_IMPORT_SUCCESS:
            logger.error(f"无法连接到设备 {self.device.name}，Scrapli库导入失败")
            return False
            
        logger.info(f"正在通过Scrapli连接到设备: {self.device.name} ({self.device.ip_address})")
        
        try:
            # 优先使用设备的platform字段，如果不存在则从vendor推断
            if hasattr(self.device, 'platform') and self.device.platform:
                platform = self.device.platform
                logger.debug(f"使用设备指定的平台类型: {platform}")
            else:
                # 映射设备类型和厂商到Scrapli platform参数
                vendor = self.device.vendor.value.lower() if self.device.vendor else ""
                device_type = self.device.device_type.value.lower() if self.device.device_type else ""
                
                # 根据设备厂商和类型确定platform
                if "cisco" in vendor:
                    if "switch" in device_type:
                        platform = "cisco_iosxe"  # 思科交换机
                    elif "router" in device_type:
                        platform = "cisco_iosxe"  # 思科路由器
                    elif "nexus" in device_type or "nxos" in vendor:
                        platform = "cisco_nxos"   # 思科Nexus交换机
                    else:
                        platform = "cisco_iosxe"  # 默认思科平台
                elif "huawei" in vendor:
                    platform = "huawei_vrp"      # 华为平台
                elif "juniper" in vendor:
                    platform = "juniper_junos"   # Juniper平台
                elif "arista" in vendor:
                    platform = "arista_eos"      # Arista平台
                else:
                    platform = "cisco_iosxe"     # 默认使用思科IOS XE平台
                
                logger.debug(f"根据vendor推断平台类型: {platform}")
            
            logger.info(f"使用平台类型: {platform} 连接设备")
            
            # 准备连接参数
            device_params = {
                "host": self.device.ip_address,
                "auth_username": self.credential.username,
                "auth_strict_key": False,
                "timeout_socket": 15,         # 连接超时时间
                "timeout_transport": 30,      # 传输超时时间
                "platform": platform,
                "port": self.credential.port or 22,
                "transport": "paramiko"       # 在Windows上使用paramiko传输方式
            }
            
            # 设置认证方式：优先使用SSH密钥文件，如果没有则使用密码
            if self.credential.ssh_key_file and self.credential.protocol == ConnectionProtocol.SSH:
                logger.info(f"使用SSH密钥文件认证: {self.credential.ssh_key_file}")
                device_params["auth_private_key"] = self.credential.ssh_key_file
            elif self.credential.password:
                logger.info("使用密码认证")
                device_params["auth_password"] = self.credential.password
            else:
                logger.error("没有提供认证方式（密码或SSH密钥文件）")
                return False
            
            # 如果是SSH，添加SSH特有参数
            if self.credential.protocol == ConnectionProtocol.SSH:
                # 保留为异步方式连接
                if platform == "cisco_iosxe":
                    driver = AsyncIOSXEDriver
                elif platform == "cisco_nxos":
                    driver = AsyncNXOSDriver
                elif platform == "juniper_junos":
                    driver = AsyncJunosDriver
                else:
                    # 对于其他平台，尝试使用同步方式连接
                    logger.info(f"没有{platform}的专用异步驱动，使用同步Scrapli")
                    # 使用同步方式，但在异步方法中运行
                    # 使用设备参数中的platform自动选择合适的驱动
                    conn = Scrapli(**device_params)
                    
                    # 用asyncio运行同步打开连接操作
                    await asyncio.to_thread(conn.open)
                    self.connection = conn
                    self.connected = True
                    self.last_activity = datetime.now()
                    logger.info(f"已成功连接到设备: {self.device.name} ({self.device.ip_address})")
                    
                    # 获取并记录设备提示符
                    try:
                        prompt = await asyncio.to_thread(conn.get_prompt)
                        logger.info(f"设备提示符: {prompt}")
                    except Exception as e:
                        logger.warning(f"获取设备提示符失败: {str(e)}")
                    
                    return True
                
                # 这里使用异步方式连接
                logger.debug(f"使用异步驱动: {driver.__name__}")
                conn = driver(**device_params)
                
                logger.debug(f"正在打开连接到 {self.device.ip_address}...")
                await conn.open()
                self.connection = conn
            
            # 如果是Telnet，处理Telnet连接
            elif self.credential.protocol == ConnectionProtocol.TELNET:
                # 修改传输选项为telnet
                device_params["transport"] = "telnet"
                device_params["port"] = self.credential.port or 23
                
                # 使用同步方式，但在异步方法中运行
                conn = Scrapli(**device_params)
                # 用asyncio运行同步打开连接操作
                await asyncio.to_thread(conn.open)
                self.connection = conn
            
            self.connected = True
            self.last_activity = datetime.now()
            logger.info(f"已成功连接到设备: {self.device.name} ({self.device.ip_address})")
            
            # 获取并记录设备提示符
            try:
                if hasattr(self.connection, "get_prompt"):
                    if asyncio.iscoroutinefunction(self.connection.get_prompt):
                        prompt = await self.connection.get_prompt()
                    else:
                        prompt = await asyncio.to_thread(self.connection.get_prompt)
                    logger.info(f"设备提示符: {prompt}")
            except Exception as e:
                logger.warning(f"获取设备提示符失败: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"连接设备失败: {self.device.name} ({self.device.ip_address}) - {type(e).__name__}: {str(e)}")
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        断开Scrapli连接
        
        Returns:
            是否断开成功
        """
        if not self.connected:
            logger.warning(f"设备未连接: {self.device.name} ({self.device.ip_address})")
            return True
        
        try:
            if self.connection:
                await self.connection.close()
            
            self.connected = False
            logger.info(f"已断开与设备的连接: {self.device.name} ({self.device.ip_address})")
            return True
        except Exception as e:
            logger.error(f"断开连接失败: {self.device.name} ({self.device.ip_address}) - {str(e)}")
            return False
    
    async def send_command(self, command: str, timeout: int = 30) -> CommandResult:
        """
        通过Scrapli发送命令
        
        Args:
            command: 要执行的命令
            timeout: 命令超时时间（秒）
            
        Returns:
            命令执行结果
        """
        if not self.connected:
            logger.warning(f"设备未连接: {self.device.name} ({self.device.ip_address})")
            return CommandResult(
                command=command,
                output="",
                success=False,
                error_message="设备未连接"
            )
        
        logger.info(f"向设备 {self.device.name} 发送命令: {command}")
        
        try:
            # 根据连接对象是同步还是异步类型，采用不同的处理方式
            if asyncio.iscoroutinefunction(self.connection.send_command):
                # 异步方法直接调用
                logger.debug("使用异步方式发送命令")
                response = await self.connection.send_command(
                    command=command,
                    timeout_ops=timeout
                )
            else:
                # 同步方法需要在线程中运行
                logger.debug("使用同步方式在线程中发送命令")
                response = await asyncio.to_thread(
                    self.connection.send_command,
                    command=command,
                    timeout_ops=timeout
                )
            
            self.last_activity = datetime.now()
            
            # 处理响应对象，提取结果
            result = ""
            is_failed = False
            
            # 尝试提取结果和失败状态
            if hasattr(response, "result"):
                result = response.result
                if hasattr(response, "failed"):
                    is_failed = response.failed
            else:
                # 如果没有result属性，尝试将整个响应转为字符串
                result = str(response)
            
            # 规范化输出格式，确保换行符一致
            if isinstance(result, str):
                # 对齐输出格式，确保每行开头无多余空格
                lines = result.splitlines()
                # 修复：不再移除每行开头的空格，保留原始输出格式
                # 重新组合输出，使用统一的换行符
                result = '\n'.join(lines)
            
            # 命令执行完毕后，获取当前提示符
            try:
                # 获取最新的提示符
                if hasattr(self.connection, "get_prompt"):
                    if asyncio.iscoroutinefunction(self.connection.get_prompt):
                        prompt = await self.connection.get_prompt()
                    else:
                        prompt = await asyncio.to_thread(self.connection.get_prompt)
                    
                    # 确保输出末尾有提示符
                    if prompt and not result.endswith(prompt):
                        result = result + "\n" + prompt
                        logger.debug(f"添加提示符到输出: '{prompt}'")
            except Exception as e:
                logger.warning(f"获取提示符失败: {str(e)}")
            
            if is_failed:
                logger.error(f"命令 '{command}' 在设备 {self.device.name} 上执行失败: {result}")
                return CommandResult(
                    command=command,
                    output=result,
                    success=False,
                    error_message="命令执行失败"
                )
            
            logger.info(f"命令 '{command}' 在设备 {self.device.name} 上执行成功")
            return CommandResult(
                command=command,
                output=result,
                success=True
            )
        except asyncio.TimeoutError:
            logger.error(f"命令 '{command}' 在设备 {self.device.name} 上执行超时")
            return CommandResult(
                command=command,
                output="",
                success=False,
                error_message="命令执行超时"
            )
        except Exception as e:
            # 检查是否为连接断开错误
            error_name = type(e).__name__
            error_msg = str(e)
            
            # 检测连接相关错误
            if "ScrapliConnectionNotOpened" in error_name or "connection not opened" in error_msg:
                logger.warning(f"连接已断开，尝试重新连接: {self.device.name} ({self.device.ip_address})")
                
                try:
                    # 首先尝试关闭当前连接
                    try:
                        if self.connection:
                            await self.connection.close()
                    except Exception as close_error:
                        logger.warning(f"关闭旧连接失败: {str(close_error)}")
                    
                    # 标记为未连接状态
                    self.connected = False
                    
                    # 尝试重新连接
                    reconnect_success = await self.connect()
                    
                    if reconnect_success:
                        logger.info(f"重新连接成功，重试命令: {command}")
                        # 递归调用自身重试命令
                        return await self.send_command(command, timeout)
                    else:
                        logger.error(f"重新连接失败: {self.device.name} ({self.device.ip_address})")
                        return CommandResult(
                            command=command,
                            output="",
                            success=False,
                            error_message="连接断开且重连失败"
                        )
                except Exception as reconnect_error:
                    logger.error(f"重新连接过程中发生错误: {str(reconnect_error)}")
                    return CommandResult(
                        command=command,
                        output="",
                        success=False,
                        error_message=f"重连过程错误: {str(reconnect_error)}"
                    )
            
            # 其他错误正常处理
            logger.error(f"命令 '{command}' 在设备 {self.device.name} 上执行失败: {error_name}: {error_msg}")
            return CommandResult(
                command=command,
                output="",
                success=False,
                error_message=f"{error_name}: {error_msg}"
            )
    
    async def send_commands(self, commands: List[str], timeout: int = 30) -> List[CommandResult]:
        """
        通过Scrapli发送多个命令
        
        Args:
            commands: 要执行的命令列表
            timeout: 每个命令的超时时间（秒）
            
        Returns:
            命令执行结果列表
        """
        logger.info(f"向设备 {self.device.name} 发送多个命令，共 {len(commands)} 条")
        results = []
        
        for i, command in enumerate(commands):
            logger.debug(f"执行第 {i+1}/{len(commands)} 条命令: {command}")
            result = await self.send_command(command, timeout)
            results.append(result)
            
            # 如果命令执行失败，记录并中断执行
            if not result.success:
                logger.warning(f"命令 '{command}' 执行失败，中断后续命令执行")
                break
            
            # 命令之间添加短暂延迟，避免设备负载过高
            if i < len(commands) - 1:  # 如果不是最后一条命令
                await asyncio.sleep(0.5)
        
        return results

    async def send_control_command(self, control_code: str) -> CommandResult:
        """
        发送控制字符到设备
        
        Args:
            control_code: 控制字符代码，例如'C'表示Ctrl+C
            
        Returns:
            命令执行结果
        """
        if not self.connection or not self.connected:
            logger.warning(f"未连接到设备，无法发送控制命令: {control_code}")
            return CommandResult(
                command=f"CTRL+{control_code}", 
                output="", 
                success=False, 
                error_message="设备未连接"
            )
            
        try:
            logger.info(f"发送控制字符 CTRL+{control_code} 到设备: {self.device.name}")
            
            # 不同控制字符的处理
            if control_code == 'C':  # CTRL+C
                special_char = '\x03'
                description = "中断"
            elif control_code == 'D':  # CTRL+D
                special_char = '\x04'
                description = "EOF"
            elif control_code == 'Z':  # CTRL+Z
                special_char = '\x1A'
                description = "挂起"
            else:
                logger.warning(f"不支持的控制字符: CTRL+{control_code}")
                return CommandResult(
                    command=f"CTRL+{control_code}", 
                    output="", 
                    success=False, 
                    error_message=f"不支持的控制字符: CTRL+{control_code}"
                )
            
            # 发送特殊字符
            if hasattr(self.connection, 'channel'):
                # 直接通过channel发送控制字符
                await self.connection.channel.write(special_char)
                logger.debug(f"已发送{description}信号到设备: {self.device.name}")
                # 等待输出
                await asyncio.sleep(1)
                output = await self.connection.channel.read()
            else:
                # 尝试通过send_command发送
                logger.debug(f"尝试通过send_command发送控制命令")
                resp = await self.connection.send_command(special_char)
                output = resp.result
                
            self.last_activity = datetime.now()
            
            return CommandResult(
                command=f"CTRL+{control_code}", 
                output=output, 
                success=True
            )
        except Exception as e:
            error_name = type(e).__name__
            error_msg = str(e)
            
            # 检测连接相关错误
            if "ScrapliConnectionNotOpened" in error_name or "connection not opened" in error_msg:
                logger.warning(f"发送控制字符时检测到连接已断开，尝试重新连接: {self.device.name}")
                
                try:
                    # 尝试关闭当前连接
                    try:
                        if self.connection:
                            await self.connection.close()
                    except Exception as close_error:
                        logger.warning(f"关闭旧连接失败: {str(close_error)}")
                    
                    # 标记为未连接状态
                    self.connected = False
                    
                    # 尝试重新连接
                    reconnect_success = await self.connect()
                    
                    if reconnect_success:
                        logger.info(f"重新连接成功，重试发送控制字符: CTRL+{control_code}")
                        # 递归调用自身重试发送
                        return await self.send_control_command(control_code)
                    else:
                        logger.error(f"重新连接失败: {self.device.name}")
                        return CommandResult(
                            command=f"CTRL+{control_code}", 
                            output="", 
                            success=False, 
                            error_message="连接断开且重连失败"
                        )
                except Exception as reconnect_error:
                    logger.error(f"重新连接过程中发生错误: {str(reconnect_error)}")
                    return CommandResult(
                        command=f"CTRL+{control_code}", 
                        output="", 
                        success=False, 
                        error_message=f"重连过程错误: {str(reconnect_error)}"
                    )
            
            # 其他错误正常处理
            error_msg = f"发送控制字符失败: {error_name}: {error_msg}"
            logger.error(error_msg)
            return CommandResult(
                command=f"CTRL+{control_code}", 
                output="", 
                success=False, 
                error_message=error_msg
            )

class ConnectorFactory:
    """连接器工厂，根据设备和凭据创建适当的连接器"""
    
    @staticmethod
    def create_connector(device: NetworkDevice, credential: DeviceCredential) -> DeviceConnector:
        """
        创建设备连接器
        
        Args:
            device: 网络设备
            credential: 设备凭据
            
        Returns:
            设备连接器
            
        Raises:
            ValueError: 如果不支持的协议
        """
        # 无论是SSH还是TELNET，都使用ScrapliConnector
        # Scrapli将根据配置自动选择合适的传输机制
        if credential.protocol in [ConnectionProtocol.SSH, ConnectionProtocol.TELNET]:
            return ScrapliConnector(device, credential)
        else:
            raise ValueError(f"不支持的协议: {credential.protocol.value}")

# 连接管理器单例
class ConnectionManager:
    """连接管理器，管理设备连接和会话"""
    
    def __init__(self):
        self.active_connections: Dict[str, DeviceConnector] = {}
        logger.info("连接管理器初始化完成")
    
    async def connect_device(self, 
                            device: NetworkDevice, 
                            credential: DeviceCredential) -> Tuple[bool, Optional[str]]:
        """
        连接到设备
        
        Args:
            device: 网络设备
            credential: 设备凭据
            
        Returns:
            (是否成功, 错误消息)
        """
        # 检查是否已经连接
        connection_key = f"{device.id}_{credential.id}"
        if connection_key in self.active_connections:
            logger.info(f"设备已连接: {device.name} ({device.ip_address})")
            return True, None
        
        try:
            # 记录设备和凭据信息
            logger.info(f"尝试连接设备: {device.name} ({device.ip_address}), 凭据: {credential.username}@{credential.protocol.value}:{credential.port}")
            
            # 创建连接器
            connector = ConnectorFactory.create_connector(device, credential)
            
            # 连接到设备
            success = await connector.connect()
            
            if success:
                # 保存连接
                self.active_connections[connection_key] = connector
                return True, None
            else:
                return False, "连接失败"
        except Exception as e:
            logger.error(f"连接设备时发生错误: {str(e)}")
            return False, str(e)
    
    async def disconnect_device(self, device_id: str, credential_id: str) -> Tuple[bool, Optional[str]]:
        """
        断开与设备的连接
        
        Args:
            device_id: 设备ID
            credential_id: 凭据ID
            
        Returns:
            (是否成功, 错误消息)
        """
        connection_key = f"{device_id}_{credential_id}"
        connector = self.active_connections.get(connection_key)
        
        if not connector:
            logger.warning(f"设备未连接: {device_id}")
            return True, None
        
        try:
            # 断开连接
            success = await connector.disconnect()
            
            if success:
                # 移除连接
                del self.active_connections[connection_key]
            
            return success, None
        except Exception as e:
            logger.error(f"断开连接时发生错误: {str(e)}")
            return False, str(e)
    
    async def send_command(self, 
                          device_id: str, 
                          credential_id: str, 
                          command: str,
                          timeout: int = 30) -> Tuple[Optional[CommandResult], Optional[str]]:
        """
        向设备发送命令
        
        Args:
            device_id: 设备ID
            credential_id: 凭据ID
            command: 要执行的命令
            timeout: 命令超时时间（秒）
            
        Returns:
            (命令结果, 错误消息)
        """
        connection_key = f"{device_id}_{credential_id}"
        connector = self.active_connections.get(connection_key)
        
        if not connector:
            logger.warning(f"设备未连接: {device_id}，请先调用connect_device连接")
            return None, "设备未连接，请先连接设备"
        
        try:
            # 发送命令
            logger.info(f"通过连接管理器向设备 {device_id} 发送命令: {command}")
            result = await connector.send_command(command, timeout)
            
            # 如果成功执行，但输出为空，添加提示
            if result.success and not result.output.strip():
                logger.info("命令执行成功，但返回内容为空")
                result.output = "[命令执行成功，但没有返回内容]"
                
            return result, None
        except Exception as e:
            error_msg = f"发送命令时发生错误: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    async def send_commands(self, 
                           device_id: str, 
                           credential_id: str, 
                           commands: List[str],
                           timeout: int = 30) -> Tuple[Optional[List[CommandResult]], Optional[str]]:
        """
        向设备发送多个命令
        
        Args:
            device_id: 设备ID
            credential_id: 凭据ID
            commands: 要执行的命令列表
            timeout: 每个命令的超时时间（秒）
            
        Returns:
            (命令结果列表, 错误消息)
        """
        connection_key = f"{device_id}_{credential_id}"
        connector = self.active_connections.get(connection_key)
        
        if not connector:
            logger.warning(f"设备未连接: {device_id}，请先调用connect_device连接")
            return None, "设备未连接，请先连接设备"
        
        try:
            # 发送命令
            logger.info(f"通过连接管理器向设备 {device_id} 发送 {len(commands)} 条命令")
            results = await connector.send_commands(commands, timeout)
            return results, None
        except Exception as e:
            error_msg = f"发送命令时发生错误: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def get_active_connections(self) -> List[Dict[str, Any]]:
        """
        获取活动连接列表
        
        Returns:
            活动连接信息列表
        """
        result = []
        
        for connection_key, connector in self.active_connections.items():
            device_id, credential_id = connection_key.split('_')
            result.append({
                "device_id": device_id,
                "device_name": connector.device.name,
                "device_ip": connector.device.ip_address,
                "credential_id": credential_id,
                "protocol": connector.credential.protocol.value,
                "last_activity": connector.last_activity.isoformat() if connector.last_activity else None
            })
        
        return result

    async def send_control_command(self, 
                              device_id: str, 
                              credential_id: str, 
                              control_code: str) -> Tuple[Optional[CommandResult], Optional[str]]:
        """
        向设备发送控制字符
        
        Args:
            device_id: 设备ID
            credential_id: 凭证ID
            control_code: 控制字符代码，例如'C'表示Ctrl+C
            
        Returns:
            (命令结果, 错误信息)
        """
        # 获取连接
        connection_key = f"{device_id}_{credential_id}"
        connector = self.active_connections.get(connection_key)
        
        if not connector:
            error_msg = f"未找到活跃连接: {connection_key}"
            logger.error(error_msg)
            return None, error_msg
            
        try:
            result = await connector.send_control_command(control_code)
            return result, None
        except Exception as e:
            error_msg = f"发送控制字符失败: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

# 创建全局连接管理器实例
connection_manager = ConnectionManager() 