from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
import uuid
import logging
import sys
import os
import json
from datetime import datetime

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

logger = logging.getLogger("network_devices")

class DeviceType(Enum):
    """网络设备类型枚举"""
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"
    WIRELESS_CONTROLLER = "wireless_controller"
    ACCESS_POINT = "access_point"
    OTHER = "other"

class DeviceVendor(Enum):
    """网络设备厂商枚举"""
    CISCO = "cisco"
    HUAWEI = "huawei"
    H3C = "h3c"
    JUNIPER = "juniper"
    ARISTA = "arista"
    FORTINET = "fortinet"
    CHECKPOINT = "checkpoint"
    OTHER = "other"

class DeviceStatus(Enum):
    """设备状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNREACHABLE = "unreachable"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"

class ConnectionProtocol(Enum):
    """连接协议枚举"""
    SSH = "ssh"
    TELNET = "telnet"
    SNMP = "snmp"
    HTTP = "http"
    HTTPS = "https"
    NETCONF = "netconf"

class DeviceCredential:
    """设备凭据类"""
    
    def __init__(self, 
                 id: str = None,
                 name: str = "",
                 username: str = "", 
                 password: str = "",
                 protocol: ConnectionProtocol = ConnectionProtocol.SSH,
                 port: int = None,
                 enable_password: str = None,
                 ssh_key_file: str = None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.username = username
        self.password = password
        self.protocol = protocol
        self.port = port or (22 if protocol == ConnectionProtocol.SSH else 23)
        self.enable_password = enable_password
        self.ssh_key_file = ssh_key_file
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "protocol": self.protocol.value,
            "port": self.port,
            "ssh_key_file": self.ssh_key_file if self.ssh_key_file else None,
            # 不包含密码，保护敏感信息
        }
    
    def to_full_dict(self) -> Dict[str, Any]:
        """转换为完整字典表示，包括敏感信息（仅用于调试）"""
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "password": "********" if self.password else None,  # 隐藏实际密码
            "protocol": self.protocol.value,
            "port": self.port,
            "enable_password": "********" if self.enable_password else None,  # 隐藏实际密码
            "ssh_key_file": self.ssh_key_file if self.ssh_key_file else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceCredential':
        """从字典创建凭据"""
        protocol_str = data.get("protocol", "ssh")
        protocol = ConnectionProtocol.SSH if protocol_str.lower() == "ssh" else ConnectionProtocol.TELNET
        
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            protocol=protocol,
            port=data.get("port"),
            enable_password=data.get("enable_password"),
            ssh_key_file=data.get("ssh_key_file")
        )

@dataclass
class NetworkDevice:
    """网络设备模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    ip_address: str = ""
    device_type: DeviceType = DeviceType.OTHER
    vendor: DeviceVendor = DeviceVendor.OTHER
    platform: str = ""
    model: str = ""
    os_version: str = ""
    status: DeviceStatus = DeviceStatus.UNKNOWN
    location: str = ""
    credential_id: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    last_seen: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "id": self.id,
            "name": self.name,
            "ip_address": self.ip_address,
            "device_type": self.device_type.value,
            "vendor": self.vendor.value,
            "platform": self.platform,
            "model": self.model,
            "os_version": self.os_version,
            "status": self.status.value,
            "location": self.location,
            "credential_id": self.credential_id,
            "description": self.description,
            "tags": self.tags,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "custom_attributes": self.custom_attributes
        }

class DeviceManager:
    """设备管理器，负责设备的创建、查询和管理"""
    
    def __init__(self):
        self.devices: Dict[str, NetworkDevice] = {}
        self.credentials: Dict[str, DeviceCredential] = {}
        self.data_dir = "data"
        self.devices_file = os.path.join(self.data_dir, "devices.json")
        self.credentials_file = os.path.join(self.data_dir, "credentials.json")
        
        # 创建数据目录(如不存在)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载持久化数据
        self.load_data()
        
        logger.info("设备管理器初始化完成")
    
    def save_data(self):
        """将设备和凭据数据保存到文件"""
        # 保存设备数据
        devices_data = {}
        for device_id, device in self.devices.items():
            devices_data[device_id] = device.to_dict()
        
        with open(self.devices_file, 'w', encoding='utf-8') as f:
            json.dump(devices_data, f, ensure_ascii=False, indent=2)
        
        # 保存凭据数据(包括敏感信息)
        credentials_data = {}
        for cred_id, credential in self.credentials.items():
            # 创建一个包含所有属性的字典
            cred_dict = {
                "id": credential.id,
                "name": credential.name,
                "username": credential.username,
                "password": credential.password,  # 注意：这将保存明文密码
                "protocol": credential.protocol.value,
                "port": credential.port,
                "enable_password": credential.enable_password,
                "ssh_key_file": credential.ssh_key_file
            }
            credentials_data[cred_id] = cred_dict
        
        with open(self.credentials_file, 'w', encoding='utf-8') as f:
            json.dump(credentials_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存到: {self.data_dir}")
    
    def load_data(self):
        """从文件加载设备和凭据数据"""
        # 加载设备数据
        if os.path.exists(self.devices_file):
            try:
                with open(self.devices_file, 'r', encoding='utf-8') as f:
                    devices_data = json.load(f)
                
                for device_id, device_dict in devices_data.items():
                    # 转换枚举类型
                    device_type = DeviceType(device_dict.get("device_type", "other"))
                    vendor = DeviceVendor(device_dict.get("vendor", "other"))
                    status = DeviceStatus(device_dict.get("status", "unknown"))
                    
                    # 转换日期时间
                    created_at = datetime.fromisoformat(device_dict.get("created_at", datetime.now().isoformat()))
                    updated_at = datetime.fromisoformat(device_dict.get("updated_at", datetime.now().isoformat()))
                    last_seen = None
                    if device_dict.get("last_seen"):
                        last_seen = datetime.fromisoformat(device_dict.get("last_seen"))
                    
                    # 创建设备对象
                    device = NetworkDevice(
                        id=device_id,
                        name=device_dict.get("name", ""),
                        ip_address=device_dict.get("ip_address", ""),
                        device_type=device_type,
                        vendor=vendor,
                        platform=device_dict.get("platform", ""),
                        model=device_dict.get("model", ""),
                        os_version=device_dict.get("os_version", ""),
                        status=status,
                        location=device_dict.get("location", ""),
                        credential_id=device_dict.get("credential_id"),
                        description=device_dict.get("description", ""),
                        tags=device_dict.get("tags", []),
                        last_seen=last_seen,
                        created_at=created_at,
                        updated_at=updated_at,
                        custom_attributes=device_dict.get("custom_attributes", {})
                    )
                    self.devices[device_id] = device
                
                logger.info(f"从 {self.devices_file} 加载了 {len(self.devices)} 个设备")
            except Exception as e:
                logger.error(f"加载设备数据失败: {e}")
        
        # 加载凭据数据
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    credentials_data = json.load(f)
                
                for cred_id, cred_dict in credentials_data.items():
                    # 转换协议类型
                    protocol_str = cred_dict.get("protocol", "ssh")
                    protocol = ConnectionProtocol(protocol_str)
                    
                    # 创建凭据对象
                    credential = DeviceCredential(
                        id=cred_id,
                        name=cred_dict.get("name", ""),
                        username=cred_dict.get("username", ""),
                        password=cred_dict.get("password", ""),
                        protocol=protocol,
                        port=cred_dict.get("port", 22 if protocol == ConnectionProtocol.SSH else 23),
                        enable_password=cred_dict.get("enable_password"),
                        ssh_key_file=cred_dict.get("ssh_key_file")
                    )
                    self.credentials[cred_id] = credential
                
                logger.info(f"从 {self.credentials_file} 加载了 {len(self.credentials)} 个凭据")
            except Exception as e:
                logger.error(f"加载凭据数据失败: {e}")
    
    def add_device(self, device: NetworkDevice) -> str:
        """
        添加设备
        
        Args:
            device: 网络设备对象
            
        Returns:
            设备ID
        """
        self.devices[device.id] = device
        logger.info(f"设备添加成功: {device.name} ({device.ip_address})")
        self.save_data()  # 保存到文件
        return device.id
    
    def get_device(self, device_id: str) -> Optional[NetworkDevice]:
        """
        获取设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            设备对象或None
        """
        return self.devices.get(device_id)
    
    def update_device(self, device_id: str, **kwargs) -> Optional[NetworkDevice]:
        """
        更新设备信息
        
        Args:
            device_id: 设备ID
            kwargs: 要更新的属性
            
        Returns:
            更新后的设备对象或None
        """
        device = self.get_device(device_id)
        if not device:
            logger.warning(f"设备不存在: {device_id}")
            return None
        
        for key, value in kwargs.items():
            if hasattr(device, key):
                setattr(device, key, value)
        
        device.updated_at = datetime.now()
        logger.info(f"设备更新成功: {device.name} ({device.ip_address})")
        self.save_data()  # 保存到文件
        return device
    
    def delete_device(self, device_id: str) -> bool:
        """
        删除设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            是否删除成功
        """
        if device_id in self.devices:
            device = self.devices[device_id]
            del self.devices[device_id]
            logger.info(f"设备删除成功: {device.name} ({device.ip_address})")
            self.save_data()  # 保存到文件
            return True
        return False
    
    def list_devices(self, 
                    vendor: Optional[DeviceVendor] = None,
                    device_type: Optional[DeviceType] = None,
                    status: Optional[DeviceStatus] = None,
                    tag: Optional[str] = None) -> List[NetworkDevice]:
        """
        列出设备，可按条件筛选
        
        Args:
            vendor: 按厂商筛选
            device_type: 按设备类型筛选
            status: 按状态筛选
            tag: 按标签筛选
            
        Returns:
            设备列表
        """
        devices = list(self.devices.values())
        
        if vendor:
            devices = [d for d in devices if d.vendor == vendor]
        
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]
        
        if status:
            devices = [d for d in devices if d.status == status]
        
        if tag:
            devices = [d for d in devices if tag in d.tags]
        
        return devices
    
    def add_credential(self, credential: DeviceCredential) -> str:
        """
        添加凭据
        
        Args:
            credential: 凭据对象
            
        Returns:
            凭据ID
        """
        self.credentials[credential.id] = credential
        logger.info(f"凭据添加成功: {credential.name} ({credential.username}@{credential.protocol.value})")
        self.save_data()  # 保存到文件
        return credential.id
    
    def get_credential(self, credential_id: str) -> Optional[DeviceCredential]:
        """
        获取凭据
        
        Args:
            credential_id: 凭据ID
            
        Returns:
            凭据对象或None
        """
        return self.credentials.get(credential_id)
    
    def delete_credential(self, credential_id: str) -> bool:
        """
        删除凭据
        
        Args:
            credential_id: 凭据ID
            
        Returns:
            是否删除成功
        """
        if credential_id in self.credentials:
            credential = self.credentials[credential_id]
            del self.credentials[credential_id]
            logger.info(f"凭据删除成功: {credential.name}")
            self.save_data()  # 保存到文件
            return True
        return False
    
    def list_credentials(self) -> List[DeviceCredential]:
        """
        列出所有凭据
        
        Returns:
            凭据列表
        """
        return list(self.credentials.values())

# 创建设备管理器单例
device_manager = DeviceManager() 