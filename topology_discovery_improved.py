from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import sys
import os
import json
import re
import asyncio
from datetime import datetime, timedelta
import ipaddress
import uuid

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

logger = logging.getLogger("topology_discovery_improved")

from network_devices import DeviceManager, NetworkDevice, DeviceVendor, DeviceType, DeviceStatus
from device_connector import ConnectionManager

class TopologyProtocol(Enum):
    """拓扑发现协议枚举"""
    CDP = "cdp"
    LLDP = "lldp"
    UNKNOWN = "unknown"

class ConnectionType(Enum):
    """连接类型枚举"""
    ETHERNET = "ethernet"
    SERIAL = "serial"
    TRUNK = "trunk"
    ACCESS = "access"
    UNKNOWN = "unknown"

@dataclass
class InterfaceInfo:
    """接口信息"""
    name: str
    description: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    status: str = "unknown"  # up, down, administratively down
    protocol: str = "unknown"  # up, down
    speed: Optional[str] = None
    duplex: Optional[str] = None
    vlan: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "status": self.status,
            "protocol": self.protocol,
            "speed": self.speed,
            "duplex": self.duplex,
            "vlan": self.vlan
        }

@dataclass 
class TopologyLink:
    """拓扑链路"""
    source_device_id: str
    source_interface: str
    target_device_id: str
    target_interface: str
    protocol: TopologyProtocol = TopologyProtocol.UNKNOWN
    connection_type: ConnectionType = ConnectionType.UNKNOWN
    discovered_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_device_id": self.source_device_id,
            "source_interface": self.source_interface,
            "target_device_id": self.target_device_id,
            "target_interface": self.target_interface,
            "protocol": self.protocol.value,
            "connection_type": self.connection_type.value,
            "discovered_at": self.discovered_at.isoformat(),
            "last_seen": self.last_seen.isoformat()
        }

@dataclass
class TopologyNode:
    """拓扑节点"""
    device_id: str
    device_name: str
    device_type: str
    vendor: str
    ip_address: str
    interfaces: List[InterfaceInfo] = field(default_factory=list)
    position: Optional[Dict[str, float]] = None  # x, y坐标用于可视化
    discovered_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.device_name,  # 修正字段名称
            "ip_address": self.ip_address,
            "vendor": self.vendor,
            "device_type": self.device_type,
            "status": "unknown",  # 添加状态字段
            "interfaces": [iface.to_dict() for iface in self.interfaces],
            "position": self.position,
            "discovered_at": self.discovered_at.isoformat(),
            "last_seen": self.last_seen.isoformat()
        }

@dataclass
class NetworkTopology:
    """网络拓扑"""
    nodes: Dict[str, TopologyNode] = field(default_factory=dict)
    links: List[TopologyLink] = field(default_factory=list)
    last_discovery: Optional[datetime] = None
    discovery_scope: List[str] = field(default_factory=list)  # 发现范围（设备ID列表）
    
    def add_node(self, node: TopologyNode):
        """添加节点"""
        self.nodes[node.device_id] = node
        
    def add_link(self, link: TopologyLink):
        """添加链路（避免重复）"""
        # 检查是否已存在相同的链路
        for existing_link in self.links:
            if (existing_link.source_device_id == link.source_device_id and
                existing_link.source_interface == link.source_interface and
                existing_link.target_device_id == link.target_device_id and
                existing_link.target_interface == link.target_interface):
                # 更新现有链路的last_seen时间
                existing_link.last_seen = link.last_seen
                logger.debug(f"更新现有链路: {link.source_device_id} -> {link.target_device_id}")
                return
        
        # 添加新链路
        self.links.append(link)
        logger.info(f"添加新链路: {link.source_device_id}[{link.source_interface}] -> {link.target_device_id}[{link.target_interface}] ({link.protocol.value})")
    
    def get_device_neighbors(self, device_id: str) -> List[str]:
        """获取设备的邻居设备ID列表"""
        neighbors = set()
        for link in self.links:
            if link.source_device_id == device_id:
                neighbors.add(link.target_device_id)
            elif link.target_device_id == device_id:
                neighbors.add(link.source_device_id)
        return list(neighbors)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "links": [link.to_dict() for link in self.links],
            "last_discovery": self.last_discovery.isoformat() if self.last_discovery else None,
            "discovery_scope": self.discovery_scope
        }

class ImprovedTopologyDiscovery:
    """改进的拓扑发现引擎"""
    
    def __init__(self, device_manager: DeviceManager, connection_manager: ConnectionManager):
        self.device_manager = device_manager
        self.connection_manager = connection_manager
        self.topology = NetworkTopology()
        self.data_dir = "data"
        self.topology_file = os.path.join(self.data_dir, "topology.json")
        
        # 创建数据目录
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载持久化的拓扑数据
        self.load_topology()
    
    def save_topology(self):
        """保存拓扑数据到文件"""
        try:
            with open(self.topology_file, 'w', encoding='utf-8') as f:
                json.dump(self.topology.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"拓扑数据已保存到: {self.topology_file} ({len(self.topology.nodes)}个节点，{len(self.topology.links)}条链路)")
        except Exception as e:
            logger.error(f"保存拓扑数据失败: {e}")
    
    def load_topology(self):
        """从文件加载拓扑数据"""
        if not os.path.exists(self.topology_file):
            logger.info("拓扑数据文件不存在，将创建新的拓扑")
            return
        
        try:
            with open(self.topology_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重建拓扑对象
            self.topology = NetworkTopology()
            
            # 加载节点
            for node_id, node_data in data.get("nodes", {}).items():
                interfaces = []
                for iface_data in node_data.get("interfaces", []):
                    interfaces.append(InterfaceInfo(**iface_data))
                
                node = TopologyNode(
                    device_id=node_data["device_id"],
                    device_name=node_data.get("name", node_data.get("device_name", "Unknown")),
                    device_type=node_data["device_type"],
                    vendor=node_data["vendor"],
                    ip_address=node_data["ip_address"],
                    interfaces=interfaces,
                    position=node_data.get("position"),
                    discovered_at=datetime.fromisoformat(node_data["discovered_at"]),
                    last_seen=datetime.fromisoformat(node_data["last_seen"])
                )
                self.topology.add_node(node)
            
            # 加载链路
            for link_data in data.get("links", []):
                link = TopologyLink(
                    source_device_id=link_data["source_device_id"],
                    source_interface=link_data["source_interface"],
                    target_device_id=link_data["target_device_id"],
                    target_interface=link_data["target_interface"],
                    protocol=TopologyProtocol(link_data["protocol"]),
                    connection_type=ConnectionType(link_data.get("connection_type", "unknown")),
                    discovered_at=datetime.fromisoformat(link_data["discovered_at"]),
                    last_seen=datetime.fromisoformat(link_data["last_seen"])
                )
                self.topology.add_link(link)
            
            # 设置其他属性
            if data.get("last_discovery"):
                self.topology.last_discovery = datetime.fromisoformat(data["last_discovery"])
            self.topology.discovery_scope = data.get("discovery_scope", [])
            
            logger.info(f"已加载拓扑数据：{len(self.topology.nodes)}个节点，{len(self.topology.links)}条链路")
        except Exception as e:
            logger.error(f"加载拓扑数据失败: {e}")
    
    async def discover_topology_from_devices(self, device_ids: List[str]) -> NetworkTopology:
        """从指定设备开始发现拓扑（用户期望的工作流程）"""
        logger.info(f"🚀 开始网络拓扑发现，种子设备: {device_ids}")
        
        # 强制清空现有拓扑数据，确保从干净状态开始
        logger.info(f"🧹 清空现有拓扑数据，重新开始发现")
        self.topology = NetworkTopology()
        
        discovered_devices = set()
        pending_devices = set(device_ids)
        total_neighbors_found = 0
        
        # 更新发现范围
        self.topology.discovery_scope = device_ids
        
        while pending_devices:
            current_device_id = pending_devices.pop()
            
            if current_device_id in discovered_devices:
                continue
                
            logger.info(f"📡 正在发现设备拓扑: {current_device_id}")
            
            # 获取设备信息（A设备已经在MCP工具中添加，有生成ID）
            device = self.device_manager.get_device(current_device_id)
            if not device:
                logger.warning(f"⚠️ 设备不存在: {current_device_id}")
                discovered_devices.add(current_device_id)
                continue
            
            try:
                # 在A设备执行 dis lldp nei、show cdp neighbors 等命令获取邻居信息
                neighbors, interfaces = await self.discover_device_neighbors(device)
                
                # 创建拓扑节点
                node = TopologyNode(
                    device_id=device.id,
                    device_name=device.name,
                    device_type=device.device_type.value,
                    vendor=device.vendor.value,
                    ip_address=device.ip_address,
                    interfaces=interfaces
                )
                self.topology.add_node(node)
                
                # 处理发现的邻居设备
                for neighbor_info in neighbors:
                    # 自动使用添加设备的MCP工具创建新的邻居设备信息
                    neighbor_device = await self.find_or_create_neighbor_device(neighbor_info, device)
                    if neighbor_device:
                        # 创建拓扑链路
                        link = TopologyLink(
                            source_device_id=current_device_id,
                            source_interface=neighbor_info.get("local_interface", ""),
                            target_device_id=neighbor_device.id,
                            target_interface=neighbor_info.get("remote_interface", ""),
                            protocol=TopologyProtocol(neighbor_info.get("protocol", "unknown"))
                        )
                        self.topology.add_link(link)
                        total_neighbors_found += 1
                        
                        # 如果邻居设备不在已发现列表中，添加到待处理列表
                        if neighbor_device.id not in discovered_devices:
                            pending_devices.add(neighbor_device.id)
                            logger.info(f"📋 发现新设备，添加到发现队列: {neighbor_device.name}")
                
                discovered_devices.add(current_device_id)
                logger.info(f"✅ 设备 {device.name} 发现完成，找到 {len(neighbors)} 个邻居")
                
            except Exception as e:
                logger.error(f"❌ 发现设备 {device.name} 拓扑失败: {e}")
                discovered_devices.add(current_device_id)  # 标记为已处理，避免死循环
        
        # 更新发现时间并保存到JSON文件
        self.topology.last_discovery = datetime.now()
        self.save_topology()
        
        logger.info(f"🎉 拓扑发现完成：{len(self.topology.nodes)}个节点，{len(self.topology.links)}条链路，发现{total_neighbors_found}个邻居连接")
        return self.topology
    
    async def discover_device_neighbors(self, device: NetworkDevice) -> Tuple[List[Dict[str, Any]], List[InterfaceInfo]]:
        """发现单个设备的邻居信息（支持华为 dis lldp nei 等命令）"""
        neighbors = []
        interfaces = []
        
        # 获取设备的凭据
        credential = None
        if device.credential_id:
            credential = self.device_manager.get_credential(device.credential_id)
        
        if not credential:
            logger.error(f"❌ 设备 {device.name} 没有关联的凭据，无法执行邻居发现")
            return neighbors, interfaces
        
        try:
            # 连接到设备
            logger.info(f"🔗 连接设备: {device.name} ({device.ip_address})")
            success, error = await self.connection_manager.connect_device(device, credential)
            if not success:
                logger.error(f"❌ 连接设备 {device.name} 失败: {error}")
                return neighbors, interfaces
            
            # 获取接口信息
            interfaces = await self.get_device_interfaces(device, credential)
            
            # 根据设备厂商选择合适的邻居发现方法
            if device.vendor == DeviceVendor.CISCO:
                logger.info(f"🔍 执行Cisco设备邻居发现: {device.name}")
                cdp_neighbors = await self.discover_cisco_neighbors(device, credential)
                lldp_neighbors = await self.discover_cisco_lldp_neighbors(device, credential)
                neighbors.extend(cdp_neighbors)
                neighbors.extend(lldp_neighbors)
            elif device.vendor == DeviceVendor.HUAWEI:
                logger.info(f"🔍 执行华为设备邻居发现: {device.name}")
                lldp_neighbors = await self.discover_huawei_neighbors(device, credential)
                neighbors.extend(lldp_neighbors)
            elif device.vendor == DeviceVendor.H3C:
                logger.info(f"🔍 执行H3C设备邻居发现: {device.name}")
                lldp_neighbors = await self.discover_h3c_neighbors(device, credential)
                neighbors.extend(lldp_neighbors)
            else:
                logger.info(f"🔍 执行通用LLDP邻居发现: {device.name}")
                lldp_neighbors = await self.discover_generic_lldp_neighbors(device, credential)
                neighbors.extend(lldp_neighbors)
            
            logger.info(f"📊 设备 {device.name} 邻居发现结果: {len(neighbors)}个邻居, {len(interfaces)}个接口")
            
        except Exception as e:
            logger.error(f"❌ 发现设备 {device.name} 邻居失败: {e}")
        finally:
            # 断开连接
            try:
                await self.connection_manager.disconnect_device(device.id, credential.id)
                logger.debug(f"🔌 断开设备连接: {device.name}")
            except Exception as e:
                logger.error(f"❌ 断开设备连接失败: {e}")
        
        return neighbors, interfaces
    
    async def discover_huawei_neighbors(self, device: NetworkDevice, credential) -> List[Dict[str, Any]]:
        """发现华为设备邻居（支持 dis lldp nei 命令）"""
        neighbors = []
        
        # 华为设备LLDP命令列表
        huawei_commands = [
            "dis lldp nei",
            "display lldp neighbor",
            "display lldp neighbor brief"
        ]
        
        for command in huawei_commands:
            try:
                logger.info(f"🔍 执行华为命令: {command}")
                result, error = await self.connection_manager.send_command(
                    device.id, credential.id, command, timeout=60
                )
                
                if result and result.success and result.output:
                    parsed_neighbors = self.parse_huawei_lldp_neighbors(result.output)
                    if parsed_neighbors:
                        neighbors.extend(parsed_neighbors)
                        logger.info(f"✅ 华为设备 {device.name} 通过命令 '{command}' 发现 {len(parsed_neighbors)} 个邻居")
                        break  # 找到有效输出就停止尝试其他命令
                else:
                    logger.debug(f"❌ 华为命令 '{command}' 执行失败或无输出: {error}")
                    
            except Exception as e:
                logger.error(f"❌ 执行华为命令 '{command}' 异常: {e}")
        
        return neighbors
    
    def parse_huawei_lldp_neighbors(self, output: str) -> List[Dict[str, Any]]:
        """解析华为设备LLDP邻居信息（详细格式）"""
        neighbors = []
        
        try:
            logger.debug(f"🔍 解析华为LLDP输出，长度: {len(output)} 字符")
            logger.debug(f"📄 LLDP输出内容:\n{output}")
            
            # 华为设备实际输出格式：接口详细信息格式
            # 每个接口的信息以 "接口名 has X neighbors:" 开始
            
            # 按接口分割输出
            interface_sections = []
            current_interface = None
            current_content = []
            
            lines = output.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 检查是否是新接口的开始：接口名 has X neighbors:
                interface_match = re.match(r'^([\w/]+)\s+has\s+(\d+)\s+neighbors?:', line)
                if interface_match:
                    # 保存前一个接口的信息
                    if current_interface and current_content:
                        interface_sections.append((current_interface, '\n'.join(current_content)))
                    
                    # 开始新接口
                    current_interface = interface_match.group(1)
                    neighbor_count = int(interface_match.group(2))
                    current_content = []
                    
                    logger.debug(f"📍 发现接口: {current_interface}, 邻居数量: {neighbor_count}")
                    
                    # 如果没有邻居，跳过
                    if neighbor_count == 0:
                        current_interface = None
                        continue
                else:
                    # 添加到当前接口的内容
                    if current_interface:
                        current_content.append(line)
            
            # 处理最后一个接口
            if current_interface and current_content:
                interface_sections.append((current_interface, '\n'.join(current_content)))
            
            # 解析每个有邻居的接口
            for interface_name, interface_content in interface_sections:
                neighbor = self._parse_huawei_neighbor_detail(interface_name, interface_content)
                if neighbor:
                    neighbors.append(neighbor)
                    logger.debug(f"✅ 解析华为邻居: {interface_name} -> {neighbor['device_id']}[{neighbor.get('remote_interface', 'unknown')}]")
            
            logger.info(f"🎯 华为LLDP解析完成，发现 {len(neighbors)} 个有效邻居")
            
        except Exception as e:
            logger.error(f"❌ 解析华为LLDP邻居信息失败: {e}")
            logger.error(f"输出内容: {output}")
        
        return neighbors
    
    def _parse_huawei_neighbor_detail(self, interface_name: str, content: str) -> Optional[Dict[str, Any]]:
        """解析单个华为LLDP邻居的详细信息"""
        try:
            neighbor = {
                "protocol": "lldp",
                "local_interface": interface_name
            }
            
            # 提取系统名称 (设备名)
            sys_name_match = re.search(r'System name\s*:\s*([^\r\n]+)', content)
            if sys_name_match:
                sys_name = sys_name_match.group(1).strip()
                if self._is_valid_device_name(sys_name):
                    neighbor["device_id"] = sys_name
                else:
                    logger.debug(f"🚫 无效的系统名称: '{sys_name}'")
                    return None
            else:
                logger.debug(f"⚠️ 未找到系统名称，跳过此邻居")
                return None
            
            # 提取远程端口ID
            port_id_match = re.search(r'Port ID\s*:\s*([^\r\n]+)', content)
            if port_id_match:
                neighbor["remote_interface"] = port_id_match.group(1).strip()
            
            # 提取管理地址 (IP地址)
            mgmt_addr_match = re.search(r'Management address\s*:\s*(\d+\.\d+\.\d+\.\d+)', content)
            if mgmt_addr_match:
                neighbor["ip_address"] = mgmt_addr_match.group(1).strip()
            
            # 提取Chassis ID
            chassis_id_match = re.search(r'Chassis ID\s*:\s*([^\r\n]+)', content)
            if chassis_id_match:
                neighbor["chassis_id"] = chassis_id_match.group(1).strip()
            
            # 提取系统描述 (用于推断设备类型)
            sys_desc_match = re.search(r'System description\s*:\s*([^\r\n]+(?:\n[^\r\n]+)*)', content)
            if sys_desc_match:
                neighbor["platform"] = sys_desc_match.group(1).strip()
            
            logger.debug(f"📋 解析邻居详细信息: {neighbor}")
            return neighbor
            
        except Exception as e:
            logger.error(f"❌ 解析邻居详细信息失败: {e}")
            return None
    
    def _is_valid_device_name(self, name: str) -> bool:
        """验证是否为有效的设备名称"""
        if not name or len(name) < 2:
            return False
        
        # 排除明显不是设备名的词语
        invalid_patterns = [
            # 数字或标点符号
            r'^\d+$',  # 纯数字
            r'^[^\w]',  # 以非字母数字开头
            # 常见的非设备名词语
            r'^(yes|no|true|false|enabled?|disabled?|up|down)$',
            r'^(unknown|n/a|na|null|none|empty)$',
            r'^(local|remote|interface?|port|intf?)$',
            r'^(chassis|system|management|address)$',
            r'^(information|description|version|software)$',
            r'^(ethernet|gigabit|fastethernet|serial)$',
            r'^(vlan|trunk|access|routing|switching)$',
            r'^(supported|unsupported|classification)$',
            r'^(priority|capability|capabilities)$',
            r'^(endpoint|id|type|class|size|network)$',
            r'^(time|timer|timeout|interval|delay)$',
            # IP地址模式
            r'^\d+\.\d+\.\d+\.\d+$',
            # MAC地址模式
            r'^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$',
            # 短词或单字符
            r'^[a-zA-Z]$',  # 单字符
            r'^.{1,2}$',   # 长度小于等于2的词
            # 特殊符号
            r'^[+\-*/:;.,<>?|\\[\]{}()~`!@#$%^&*_=]+$'
        ]
        
        name_lower = name.lower()
        for pattern in invalid_patterns:
            if re.match(pattern, name_lower):
                logger.debug(f"🚫 排除无效设备名: '{name}' (匹配模式: {pattern})")
                return False
        
        # 设备名应该包含字母
        if not re.search(r'[a-zA-Z]', name):
            logger.debug(f"🚫 排除无效设备名: '{name}' (不包含字母)")
            return False
        
        logger.debug(f"✅ 验证有效设备名: '{name}'")
        return True
    
    async def discover_cisco_neighbors(self, device: NetworkDevice, credential) -> List[Dict[str, Any]]:
        """发现Cisco CDP邻居"""
        neighbors = []
        
        try:
            logger.info(f"🔍 执行Cisco CDP发现")
            result, error = await self.connection_manager.send_command(
                device.id, credential.id, "show cdp neighbors detail", timeout=60
            )
            
            if result and result.success:
                neighbors = self.parse_cisco_cdp_neighbors(result.output)
                logger.info(f"✅ Cisco设备 {device.name} 通过CDP发现 {len(neighbors)} 个邻居")
            else:
                logger.warning(f"❌ 获取Cisco CDP邻居失败: {error}")
                
        except Exception as e:
            logger.error(f"❌ 发现Cisco CDP邻居异常: {e}")
        
        return neighbors
    
    def parse_cisco_cdp_neighbors(self, output: str) -> List[Dict[str, Any]]:
        """解析Cisco CDP邻居信息"""
        neighbors = []
        
        try:
            # CDP详细信息的解析
            entries = re.split(r'-{20,}', output)
            
            for entry in entries:
                if "Device ID:" in entry:
                    neighbor = {"protocol": "cdp"}
                    
                    # 提取设备ID
                    device_id_match = re.search(r'Device ID:\s*(\S+)', entry)
                    if device_id_match:
                        neighbor["device_id"] = device_id_match.group(1)
                    
                    # 提取IP地址
                    ip_match = re.search(r'IP address:\s*(\d+\.\d+\.\d+\.\d+)', entry)
                    if ip_match:
                        neighbor["ip_address"] = ip_match.group(1)
                    
                    # 提取平台信息
                    platform_match = re.search(r'Platform:\s*([^,\n]+)', entry)
                    if platform_match:
                        neighbor["platform"] = platform_match.group(1).strip()
                    
                    # 提取本地接口
                    local_int_match = re.search(r'Interface:\s*(\S+)', entry)
                    if local_int_match:
                        neighbor["local_interface"] = local_int_match.group(1)
                    
                    # 提取远程接口
                    remote_int_match = re.search(r'Port ID \(outgoing port\):\s*(\S+)', entry)
                    if remote_int_match:
                        neighbor["remote_interface"] = remote_int_match.group(1)
                    
                    if "device_id" in neighbor:
                        neighbors.append(neighbor)
                        logger.debug(f"✅ 解析Cisco CDP邻居: {neighbor.get('local_interface', 'unknown')} -> {neighbor['device_id']}")
                        
        except Exception as e:
            logger.error(f"❌ 解析Cisco CDP邻居信息失败: {e}")
        
        return neighbors
    
    async def find_or_create_neighbor_device(self, neighbor_info: Dict[str, Any], source_device: NetworkDevice) -> Optional[NetworkDevice]:
        """查找或自动创建邻居设备（改进的自动创建逻辑）"""
        logger.info(f"🔍 查找或创建邻居设备: {neighbor_info}")
        
        # 1. 首先尝试通过IP地址查找现有设备
        if neighbor_info.get("ip_address"):
            for device in self.device_manager.list_devices():
                if device.ip_address == neighbor_info["ip_address"]:
                    logger.info(f"✅ 通过IP地址找到现有设备: {device.name} ({device.ip_address})")
                    return device
        
        # 2. 然后尝试通过设备名称查找
        device_id = neighbor_info.get("device_id", "")
        if device_id:
            for device in self.device_manager.list_devices():
                if device.name == device_id:
                    logger.info(f"✅ 通过设备名称找到现有设备: {device.name}")
                    return device
        
        # 3. 如果没有找到现有设备，自动创建一个新的邻居设备记录
        if device_id and self._is_valid_device_name(device_id):
            logger.info(f"🆕 自动创建新的邻居设备: {device_id}")
            
            # 推断设备厂商和类型
            vendor = self._infer_device_vendor(neighbor_info)
            device_type = self._infer_device_type(neighbor_info)
            
            # 标准化平台信息
            platform = self._standardize_platform_info(neighbor_info)
            
            # 生成设备IP地址
            ip_address = neighbor_info.get("ip_address")
            if not ip_address:
                # 如果没有IP地址，尝试从源设备网段推断
                ip_address = self._generate_placeholder_ip(source_device)
            
            # 创建新设备
            new_device = NetworkDevice(
                id=str(uuid.uuid4()),
                name=device_id,
                ip_address=ip_address,
                device_type=device_type,
                vendor=vendor,
                platform=platform,  # 使用标准化的平台信息
                status=DeviceStatus.UNKNOWN,
                description=f"通过拓扑发现自动创建 (从{source_device.name}发现，协议:{neighbor_info.get('protocol', 'unknown')})"
            )
            
            # 添加到设备管理器
            created_device_id = self.device_manager.add_device(new_device)
            logger.info(f"✅ 自动创建邻居设备成功: {new_device.name} ({new_device.ip_address}) [ID: {created_device_id}], 平台: {platform}")
            return new_device
        
        logger.warning(f"⚠️ 无法创建邻居设备，设备名无效或缺少必要信息: {neighbor_info}")
        return None
    
    def _infer_device_vendor(self, neighbor_info: Dict[str, Any]) -> DeviceVendor:
        """推断设备厂商"""
        platform = neighbor_info.get("platform", "").lower()
        device_id = neighbor_info.get("device_id", "").lower()
        
        if any(keyword in platform for keyword in ["cisco", "catalyst", "nexus", "asr"]) or \
           any(keyword in device_id for keyword in ["cisco", "cat", "asr"]):
            return DeviceVendor.CISCO
        elif any(keyword in platform for keyword in ["huawei", "vrp"]) or \
             any(keyword in device_id for keyword in ["huawei", "ce", "s5700", "s6720"]):
            return DeviceVendor.HUAWEI
        elif any(keyword in platform for keyword in ["h3c", "comware"]) or \
             any(keyword in device_id for keyword in ["h3c", "s5120", "s5130"]):
            return DeviceVendor.H3C
        elif any(keyword in platform for keyword in ["juniper", "junos"]):
            return DeviceVendor.JUNIPER
        else:
            return DeviceVendor.OTHER
    
    def _standardize_platform_info(self, neighbor_info: Dict[str, Any]) -> str:
        """标准化平台信息为简洁的平台代码"""
        platform = neighbor_info.get("platform", "").lower()
        device_id = neighbor_info.get("device_id", "").lower()
        
        # 华为设备平台标准化
        if "huawei" in platform or "vrp" in platform:
            if "s5700" in platform or "s5700" in device_id:
                return "huawei_s5700"
            elif "s6720" in platform or "s6720" in device_id:
                return "huawei_s6720"
            elif "s3700" in platform or "s3700" in device_id:
                return "huawei_s3700"
            elif "ce" in device_id:
                return "huawei_ce"
            else:
                return "huawei_vrp"
        
        # Cisco设备平台标准化
        elif "cisco" in platform:
            if "catalyst" in platform:
                return "cisco_catalyst"
            elif "nexus" in platform:
                return "cisco_nexus"
            elif "asr" in platform:
                return "cisco_asr"
            elif "isr" in platform:
                return "cisco_isr"
            else:
                return "cisco_ios"
        
        # H3C设备平台标准化
        elif "h3c" in platform or "comware" in platform:
            if "s5120" in platform:
                return "h3c_s5120"
            elif "s5130" in platform:
                return "h3c_s5130"
            else:
                return "h3c_comware"
        
        # Juniper设备平台标准化
        elif "juniper" in platform or "junos" in platform:
            return "juniper_junos"
        
        # 其他设备
        else:
            # 尝试从原始平台信息中提取关键型号信息
            if platform:
                # 提取型号信息（如S5700, S3700等）
                import re
                model_match = re.search(r'(s\d+[a-z]*-?\d*[a-z]*)', platform)
                if model_match:
                    return f"unknown_{model_match.group(1)}"
            
            return "unknown"
    
    def _infer_device_type(self, neighbor_info: Dict[str, Any]) -> DeviceType:
        """推断设备类型"""
        platform = neighbor_info.get("platform", "").lower()
        device_id = neighbor_info.get("device_id", "").lower()
        
        if any(keyword in platform for keyword in ["switch", "catalyst", "s5700", "s6720", "s5120"]) or \
           any(keyword in device_id for keyword in ["sw", "switch"]):
            return DeviceType.SWITCH
        elif any(keyword in platform for keyword in ["router", "asr", "isr", "ne"]) or \
             any(keyword in device_id for keyword in ["rt", "router"]):
            return DeviceType.ROUTER
        elif any(keyword in platform for keyword in ["firewall", "asa", "usg"]):
            return DeviceType.FIREWALL
        elif any(keyword in platform for keyword in ["ap", "access", "wireless"]):
            return DeviceType.ACCESS_POINT
        else:
            return DeviceType.OTHER
    
    def _generate_placeholder_ip(self, source_device: NetworkDevice) -> str:
        """为邻居设备生成占位符IP地址"""
        try:
            # 尝试从源设备IP地址推断网段
            source_ip = ipaddress.IPv4Address(source_device.ip_address)
            # 假设使用/24网段，生成一个可能的IP
            network = ipaddress.IPv4Network(f"{source_ip}/24", strict=False)
            # 使用网段的最后一个可用IP作为占位符
            return str(list(network.hosts())[-1])
        except:
            # 如果无法推断，使用默认占位符
            return "192.168.1.254"
    
    async def get_device_interfaces(self, device: NetworkDevice, credential) -> List[InterfaceInfo]:
        """获取设备接口信息（支持多厂商）"""
        interfaces = []
        
        try:
            # 根据厂商选择合适的命令
            if device.vendor == DeviceVendor.CISCO:
                command = "show ip interface brief"
            elif device.vendor == DeviceVendor.HUAWEI:
                command = "display ip interface brief"
            elif device.vendor == DeviceVendor.H3C:
                command = "display ip interface brief"
            else:
                command = "show ip interface brief"  # 默认使用Cisco命令
            
            result, error = await self.connection_manager.send_command(
                device.id, credential.id, command, timeout=60
            )
            
            if result and result.success:
                interfaces = self.parse_interface_info(result.output, device.vendor)
                logger.info(f"✅ 设备 {device.name} 发现 {len(interfaces)} 个接口")
            else:
                logger.warning(f"⚠️ 获取设备 {device.name} 接口信息失败: {error}")
                
        except Exception as e:
            logger.error(f"❌ 获取设备 {device.name} 接口信息异常: {e}")
        
        return interfaces
    
    def parse_interface_info(self, output: str, vendor: DeviceVendor) -> List[InterfaceInfo]:
        """解析接口信息输出（多厂商支持）"""
        interfaces = []
        
        try:
            logger.debug(f"🔍 解析接口信息输出，厂商: {vendor.value}")
            logger.debug(f"📄 接口信息输出内容:\n{output}")
            
            lines = output.strip().split('\n')
            
            if vendor == DeviceVendor.CISCO:
                # 解析Cisco格式的接口信息
                for line in lines[1:]:  # 跳过标题行
                    if line.strip() and not line.startswith('-'):
                        parts = line.split()
                        if len(parts) >= 6:
                            interface = InterfaceInfo(
                                name=parts[0],
                                ip_address=parts[1] if parts[1] != "unassigned" else None,
                                status=parts[4],
                                protocol=parts[5]
                            )
                            interfaces.append(interface)
            elif vendor in [DeviceVendor.HUAWEI, DeviceVendor.H3C]:
                # 华为/H3C设备接口信息解析 - 严格验证接口格式
                in_interface_table = False
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 检查是否进入接口表格区域
                    if "Interface" in line and ("IP" in line or "Status" in line):
                        in_interface_table = True
                        continue
                    
                    # 跳过分隔符行
                    if "----" in line or "====" in line:
                        continue
                    
                    # 只在接口表格内解析，并且必须是有效的接口名开头
                    if in_interface_table:
                        # 严格验证华为接口命名格式
                        if self._is_valid_huawei_interface_name(line.split()[0] if line.split() else ""):
                            parts = line.split()
                            if len(parts) >= 3:
                                interface = InterfaceInfo(
                                    name=parts[0],
                                    ip_address=parts[1] if len(parts) > 1 and parts[1] not in ["--", "unassigned", "down", "up"] else None,
                                    status=parts[2] if len(parts) > 2 else "unknown",
                                    protocol=parts[3] if len(parts) > 3 else "unknown"
                                )
                                interfaces.append(interface)
                                logger.debug(f"✅ 解析接口: {interface.name}")
                            
        except Exception as e:
            logger.error(f"❌ 解析接口信息失败: {e}")
        
        logger.info(f"📊 解析接口完成，发现 {len(interfaces)} 个有效接口")
        return interfaces
    
    def _is_valid_huawei_interface_name(self, name: str) -> bool:
        """验证是否为有效的华为接口名称"""
        if not name:
            return False
        
        # 华为接口命名格式
        valid_patterns = [
            r'^GigabitEthernet\d+/\d+(/\d+)?$',           # GigabitEthernet0/0/1
            r'^Ten-GigabitEthernet\d+/\d+(/\d+)?$',       # Ten-GigabitEthernet1/0/1  
            r'^Ethernet\d+/\d+(/\d+)?$',                  # Ethernet0/0/1
            r'^GE\d+/\d+(/\d+)?$',                        # GE1/0/1
            r'^XGE\d+/\d+(/\d+)?$',                       # XGE1/0/1
            r'^FE\d+/\d+(/\d+)?$',                        # FE1/0/1
            r'^Eth-Trunk\d+$',                            # Eth-Trunk1
            r'^Vlanif\d+$',                               # Vlanif100
            r'^LoopBack\d+$',                             # LoopBack0
            r'^NULL0$',                                   # NULL0
            r'^MEth\d+/\d+(/\d+)?$',                      # MEth0/0/1
        ]
        
        for pattern in valid_patterns:
            if re.match(pattern, name):
                logger.debug(f"✅ 有效接口名: {name}")
                return True
        
        logger.debug(f"🚫 无效接口名: {name}")
        return False
    
    # 为其他厂商添加占位符方法
    async def discover_cisco_lldp_neighbors(self, device: NetworkDevice, credential) -> List[Dict[str, Any]]:
        """发现Cisco LLDP邻居"""
        neighbors = []
        try:
            result, error = await self.connection_manager.send_command(
                device.id, credential.id, "show lldp neighbors detail", timeout=60
            )
            if result and result.success:
                neighbors = self.parse_cisco_lldp_neighbors(result.output)
        except Exception as e:
            logger.error(f"❌ 发现Cisco LLDP邻居异常: {e}")
        return neighbors
    
    def parse_cisco_lldp_neighbors(self, output: str) -> List[Dict[str, Any]]:
        """解析Cisco LLDP邻居"""
        # 简化实现，实际项目中需要完整解析
        return []
    
    async def discover_h3c_neighbors(self, device: NetworkDevice, credential) -> List[Dict[str, Any]]:
        """发现H3C设备邻居"""
        # H3C使用类似华为的命令
        return await self.discover_huawei_neighbors(device, credential)
    
    async def discover_generic_lldp_neighbors(self, device: NetworkDevice, credential) -> List[Dict[str, Any]]:
        """通用LLDP邻居发现"""
        neighbors = []
        try:
            result, error = await self.connection_manager.send_command(
                device.id, credential.id, "show lldp neighbors", timeout=60
            )
            if result and result.success:
                neighbors = self.parse_generic_lldp_neighbors(result.output)
        except Exception as e:
            logger.error(f"❌ 通用LLDP邻居发现异常: {e}")
        return neighbors
    
    def parse_generic_lldp_neighbors(self, output: str) -> List[Dict[str, Any]]:
        """解析通用LLDP邻居"""
        # 简化实现
        return []
    
    def get_topology(self) -> NetworkTopology:
        """获取当前拓扑"""
        return self.topology
    
    def clear_topology(self):
        """清空拓扑数据"""
        self.topology = NetworkTopology()
        self.save_topology()
        logger.info("🗑️ 拓扑数据已清空")

# 创建改进的拓扑发现引擎单例
def create_improved_topology_discovery(device_manager: DeviceManager, connection_manager: ConnectionManager) -> ImprovedTopologyDiscovery:
    """创建改进的拓扑发现引擎实例"""
    return ImprovedTopologyDiscovery(device_manager, connection_manager) 