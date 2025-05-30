from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import sys
import os
import json
import asyncio
import ipaddress
import socket
import subprocess
import re
import concurrent.futures
from datetime import datetime, timedelta
import aiohttp
import platform

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

logger = logging.getLogger("network_scanner")

from network_devices import DeviceManager, NetworkDevice, DeviceVendor, DeviceType, DeviceStatus

class ScanMethod(Enum):
    """扫描方法枚举"""
    PING = "ping"
    TCP_CONNECT = "tcp_connect"
    SNMP = "snmp"
    HTTP = "http"
    SSH_BANNER = "ssh_banner"

class DeviceDiscoveryMethod(Enum):
    """设备发现方法枚举"""
    PING_SWEEP = "ping_sweep"
    ARP_TABLE = "arp_table"  
    SNMP_WALK = "snmp_walk"
    PORT_SCAN = "port_scan"
    CDP_LLDP = "cdp_lldp"

@dataclass
class ScanResult:
    """单个IP扫描结果"""
    ip_address: str
    is_alive: bool = False
    response_time: Optional[float] = None
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    vendor: Optional[str] = None
    device_type: Optional[str] = None
    open_ports: List[int] = field(default_factory=list)
    services: Dict[int, str] = field(default_factory=dict)
    snmp_info: Dict[str, Any] = field(default_factory=dict)
    os_info: Optional[str] = None
    discovered_at: datetime = field(default_factory=datetime.now)
    discovery_method: Set[DeviceDiscoveryMethod] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ip_address": self.ip_address,
            "is_alive": self.is_alive,
            "response_time": self.response_time,
            "hostname": self.hostname,
            "mac_address": self.mac_address,
            "vendor": self.vendor,
            "device_type": self.device_type,
            "open_ports": self.open_ports,
            "services": self.services,
            "snmp_info": self.snmp_info,
            "os_info": self.os_info,
            "discovered_at": self.discovered_at.isoformat(),
            "discovery_method": [method.value for method in self.discovery_method]
        }

@dataclass
class ScanConfiguration:
    """扫描配置"""
    timeout: float = 3.0
    max_concurrent: int = 50
    ping_enabled: bool = True
    port_scan_enabled: bool = True
    snmp_enabled: bool = True
    http_check_enabled: bool = True
    ssh_banner_enabled: bool = True
    common_ports: List[int] = field(default_factory=lambda: [22, 23, 80, 161, 443, 8080, 8443])
    snmp_communities: List[str] = field(default_factory=lambda: ["public", "private"])
    
class NetworkScanner:
    """网络扫描器"""
    
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.data_dir = "data"
        self.scan_results_file = os.path.join(self.data_dir, "scan_results.json")
        
        # 创建数据目录
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载历史扫描结果
        self.scan_results: Dict[str, ScanResult] = {}
        self.load_scan_results()
        
        # 厂商MAC地址前缀映射（OUI - Organizationally Unique Identifier）
        self.vendor_oui_map = {
            "00:00:0C": "Cisco",
            "00:01:42": "Cisco", 
            "00:01:43": "Cisco",
            "00:01:96": "Cisco",
            "00:01:97": "Cisco",
            "00:02:16": "Cisco",
            "00:02:17": "Cisco",
            "00:02:3D": "Cisco",
            "00:02:4A": "Cisco",
            "00:02:4B": "Cisco",
            "00:02:B9": "Cisco",
            "00:02:BA": "Cisco",
            "00:02:FC": "Cisco",
            "00:02:FD": "Cisco",
            "00:03:6B": "Cisco",
            "00:03:6C": "Cisco",
            "00:03:E3": "Cisco",
            "00:03:FD": "Cisco",
            "00:04:27": "Cisco",
            "00:04:28": "Cisco",
            "00:04:4D": "Cisco",
            "00:04:6D": "Cisco",
            "00:04:9A": "Cisco",
            "00:04:C0": "Cisco",
            "00:04:C1": "Cisco",
            "00:04:DD": "Cisco",
            "00:05:00": "Cisco",
            "00:05:01": "Cisco",
            "00:05:31": "Cisco",
            "00:05:32": "Cisco",
            "00:05:5E": "Cisco",
            "00:05:73": "Cisco",
            "00:05:74": "Cisco",
            "00:05:9A": "Cisco",
            "00:05:DC": "Cisco",
            "00:05:DD": "Cisco",
            "00:06:28": "Cisco",
            "00:06:2A": "Cisco",
            "00:06:52": "Cisco",
            "00:06:53": "Cisco",
            "00:06:7C": "Cisco",
            "00:06:C1": "Cisco",
            "00:06:D6": "Cisco",
            "00:06:D7": "Cisco",
            "00:06:F6": "Cisco",
            "00:07:0D": "Cisco",
            "00:07:0E": "Cisco",
            "00:07:4F": "Cisco",
            "00:07:50": "Cisco",
            "00:07:84": "Cisco",
            "00:07:85": "Cisco",
            "00:07:B3": "Cisco",
            "00:07:B4": "Cisco",
            "00:07:EB": "Cisco",
            "00:07:EC": "Cisco",
            "00:08:20": "Cisco",
            "00:08:21": "Cisco",
            "00:08:30": "Cisco",
            "00:08:31": "Cisco",
            "00:08:7C": "Cisco",
            "00:08:7D": "Cisco",
            "00:08:A3": "Cisco",
            "00:08:A4": "Cisco",
            "00:08:C2": "Cisco",
            "00:08:E2": "Cisco",
            "00:08:E3": "Cisco",
            "00:09:11": "Cisco",
            "00:09:12": "Cisco",
            "00:09:43": "Cisco",
            "00:09:44": "Cisco",
            "00:09:7B": "Cisco",
            "00:09:7C": "Cisco",
            "00:09:B6": "Cisco",
            "00:09:B7": "Cisco",
            "00:09:E8": "Cisco",
            "00:09:E9": "Cisco",
            "00:0A:41": "Cisco",
            "00:0A:42": "Cisco",
            "00:0A:8A": "Cisco",
            "00:0A:8B": "Cisco",
            "00:0A:B7": "Cisco",
            "00:0A:B8": "Cisco",
            "00:0A:F3": "Cisco",
            "00:0A:F4": "Cisco",
            "00:0B:45": "Cisco",
            "00:0B:46": "Cisco",
            "00:0B:5F": "Cisco",
            "00:0B:60": "Cisco",
            "00:0B:85": "Cisco",
            "00:0B:BE": "Cisco",
            "00:0B:BF": "Cisco",
            "00:0B:FC": "Cisco",
            "00:0B:FD": "Cisco",
            "00:0C:30": "Cisco",
            "00:0C:31": "Cisco",
            "00:0C:41": "Cisco",
            "00:0C:85": "Cisco",
            "00:0C:86": "Cisco",
            "00:0C:CE": "Cisco",
            "00:0C:CF": "Cisco",
            "00:0D:28": "Cisco",
            "00:0D:29": "Cisco",
            "00:0D:65": "Cisco",
            "00:0D:66": "Cisco",
            "00:0D:BC": "Cisco",
            "00:0D:BD": "Cisco",
            "00:0D:EC": "Cisco",
            "00:0D:ED": "Cisco",
            "00:0E:08": "Cisco",
            "00:0E:38": "Cisco",
            "00:0E:39": "Cisco",
            "00:0E:83": "Cisco",
            "00:0E:84": "Cisco",
            "00:0E:D6": "Cisco",
            "00:0E:D7": "Cisco",
            "00:0F:23": "Cisco",
            "00:0F:24": "Cisco",
            "00:0F:34": "Cisco",
            "00:0F:35": "Cisco",
            "00:0F:66": "Cisco",
            "00:0F:8F": "Cisco",
            "00:0F:90": "Cisco",
            "00:0F:F7": "Cisco",
            "00:0F:F8": "Cisco",
            "00:10:07": "Cisco",
            "00:10:11": "Cisco",
            "00:10:29": "Cisco",
            "00:10:2F": "Cisco",
            "00:10:54": "Cisco",
            "00:10:79": "Cisco",
            "00:10:7B": "Cisco",
            "00:10:A6": "Cisco",
            "00:10:F6": "Cisco",
            "00:11:20": "Cisco",
            "00:11:21": "Cisco",
            "00:11:5C": "Cisco",
            "00:11:5D": "Cisco",
            "00:11:92": "Cisco",
            "00:11:93": "Cisco",
            "00:11:BB": "Cisco",
            "00:11:BC": "Cisco",
            "00:12:00": "Cisco",
            "00:12:01": "Cisco",
            "00:12:17": "Cisco",
            "00:12:43": "Cisco",
            "00:12:44": "Cisco",
            "00:12:7F": "Cisco",
            "00:12:80": "Cisco",
            "00:12:D9": "Cisco",
            "00:12:DA": "Cisco",
            "00:13:19": "Cisco",
            "00:13:1A": "Cisco",
            "00:13:5F": "Cisco",
            "00:13:60": "Cisco",
            "00:13:7F": "Cisco",
            "00:13:80": "Cisco",
            "00:13:C3": "Cisco",
            "00:13:C4": "Cisco",
            "00:14:1B": "Cisco",
            "00:14:1C": "Cisco",
            "00:14:69": "Cisco",
            "00:14:6A": "Cisco",
            "00:14:A8": "Cisco",
            "00:14:A9": "Cisco",
            "00:14:BF": "Cisco",
            "00:14:F1": "Cisco",
            "00:14:F2": "Cisco",
            "00:15:2B": "Cisco",
            "00:15:2C": "Cisco",
            "00:15:62": "Cisco",
            "00:15:63": "Cisco",
            "00:15:C6": "Cisco",
            "00:15:C7": "Cisco",
            "00:15:F9": "Cisco",
            "00:15:FA": "Cisco",
            "00:16:46": "Cisco",
            "00:16:47": "Cisco",
            "00:16:9C": "Cisco",
            "00:16:9D": "Cisco",
            "00:16:B6": "Cisco",
            "00:16:C7": "Cisco",
            "00:16:C8": "Cisco",
            "00:17:0E": "Cisco",
            "00:17:0F": "Cisco",
            "00:17:33": "Cisco",
            "00:17:34": "Cisco",
            "00:17:59": "Cisco",
            "00:17:5A": "Cisco",
            "00:17:94": "Cisco",
            "00:17:95": "Cisco",
            "00:17:DF": "Cisco",
            "00:17:E0": "Cisco",
            "00:18:18": "Cisco",
            "00:18:19": "Cisco",
            "00:18:39": "Cisco",
            "00:18:68": "Cisco",
            "00:18:73": "Cisco",
            "00:18:74": "Cisco",
            "00:18:B9": "Cisco",
            "00:18:BA": "Cisco",
            "00:19:06": "Cisco",
            "00:19:07": "Cisco",
            "00:19:2F": "Cisco",
            "00:19:30": "Cisco",
            "00:19:47": "Cisco",
            "00:19:55": "Cisco",
            "00:19:56": "Cisco",
            "00:19:A9": "Cisco",
            "00:19:AA": "Cisco",
            "00:19:E7": "Cisco",
            "00:19:E8": "Cisco",
            "00:1A:2F": "Cisco",
            "00:1A:30": "Cisco",
            "00:1A:6C": "Cisco",
            "00:1A:6D": "Cisco",
            "00:1A:A1": "Cisco",
            "00:1A:A2": "Cisco",
            "00:1A:E2": "Cisco",
            "00:1A:E3": "Cisco",
            "00:1B:0C": "Cisco",
            "00:1B:0D": "Cisco",
            "00:1B:2A": "Cisco",
            "00:1B:2B": "Cisco",
            "00:1B:53": "Cisco",
            "00:1B:54": "Cisco",
            "00:1B:67": "Cisco",
            "00:1B:8F": "Cisco",
            "00:1B:90": "Cisco",
            "00:1B:D4": "Cisco",
            "00:1B:D5": "Cisco",
            "00:1C:0E": "Cisco",
            "00:1C:0F": "Cisco",
            "00:1C:57": "Cisco",
            "00:1C:58": "Cisco",
            "00:1C:B0": "Cisco",
            "00:1C:B1": "Cisco",
            "00:1C:F6": "Cisco",
            "00:1C:F9": "Cisco",
            "00:1D:45": "Cisco",
            "00:1D:46": "Cisco",
            "00:1D:70": "Cisco",
            "00:1D:71": "Cisco",
            "00:1D:A1": "Cisco",
            "00:1D:A2": "Cisco",
            "00:1D:E5": "Cisco",
            "00:1D:E6": "Cisco",
            "00:1E:13": "Cisco",
            "00:1E:14": "Cisco",
            "00:1E:49": "Cisco",
            "00:1E:4A": "Cisco",
            "00:1E:6B": "Cisco",
            "00:1E:79": "Cisco",
            "00:1E:7A": "Cisco",
            "00:1E:BD": "Cisco",
            "00:1E:BE": "Cisco",
            "00:1E:F6": "Cisco",
            "00:1E:F7": "Cisco",
            "00:1F:26": "Cisco",
            "00:1F:27": "Cisco",
            "00:1F:6C": "Cisco",
            "00:1F:6D": "Cisco",
            "00:1F:9D": "Cisco",
            "00:1F:9E": "Cisco",
            "00:1F:C9": "Cisco",
            "00:1F:CA": "Cisco",
            "00:20:35": "Cisco",
            "00:20:36": "Cisco",
            "00:20:BA": "Cisco",
            "00:20:BB": "Cisco",
            "00:21:1B": "Cisco",
            "00:21:1C": "Cisco",
            "00:21:29": "Cisco",
            "00:21:55": "Cisco",
            "00:21:56": "Cisco",
            "00:21:A0": "Cisco",
            "00:21:A1": "Cisco",
            "00:21:BE": "Cisco",
            "00:21:D7": "Cisco",
            "00:21:D8": "Cisco",
            "00:22:0C": "Cisco",
            "00:22:0D": "Cisco",
            "00:22:55": "Cisco",
            "00:22:56": "Cisco",
            "00:22:6B": "Cisco",
            "00:22:90": "Cisco",
            "00:22:91": "Cisco",
            "00:22:BD": "Cisco",
            "00:22:BE": "Cisco",
            "00:23:04": "Cisco",
            "00:23:05": "Cisco",
            "00:23:33": "Cisco",
            "00:23:34": "Cisco",
            "00:23:5D": "Cisco",
            "00:23:5E": "Cisco",
            "00:23:AB": "Cisco",
            "00:23:AC": "Cisco",
            "00:23:BE": "Cisco",
            "00:23:EA": "Cisco",
            "00:23:EB": "Cisco",
            "00:24:13": "Cisco",
            "00:24:14": "Cisco",
            "00:24:50": "Cisco",
            "00:24:51": "Cisco",
            "00:24:C3": "Cisco",
            "00:24:C4": "Cisco",
            "00:24:F7": "Cisco",
            "00:24:F9": "Cisco",
            "00:25:2E": "Cisco",
            "00:25:45": "Cisco",
            "00:25:46": "Cisco",
            "00:25:83": "Cisco",
            "00:25:84": "Cisco",
            "00:25:B4": "Cisco",
            "00:25:B5": "Cisco",
            "00:26:0A": "Cisco",
            "00:26:0B": "Cisco",
            "00:26:51": "Cisco",
            "00:26:52": "Cisco",
            "00:26:98": "Cisco",
            "00:26:99": "Cisco",
            "00:26:CA": "Cisco",
            "00:26:CB": "Cisco",
            "00:27:0C": "Cisco",
            "00:27:0D": "Cisco",
            "00:27:23": "Cisco",
            "00:27:24": "Cisco",
            "00:40:96": "Cisco",
            "00:50:0B": "Cisco",
            "00:50:14": "Cisco",
            "00:50:50": "Cisco",
            "00:50:53": "Cisco",
            "00:50:54": "Cisco",
            "00:50:73": "Cisco",
            "00:50:80": "Cisco",
            "00:50:A2": "Cisco",
            "00:50:BD": "Cisco",
            "00:50:D1": "Cisco",
            "00:50:E2": "Cisco",
            "00:50:F0": "Cisco",
            "00:60:2F": "Cisco",
            "00:60:3E": "Cisco",
            "00:60:47": "Cisco",
            "00:60:5C": "Cisco",
            "00:60:70": "Cisco",
            "00:60:83": "Cisco",
            "00:90:21": "Cisco",
            "00:90:2B": "Cisco",
            "00:90:86": "Cisco",
            "00:90:92": "Cisco",
            "00:90:A6": "Cisco",
            "00:90:AB": "Cisco",
            "00:90:B1": "Cisco",
            "00:90:BF": "Cisco",
            "00:90:F2": "Cisco",
            "00:A0:C9": "Cisco",
            "00:B0:64": "Cisco",
            "00:C0:1D": "Cisco",
            "00:D0:06": "Cisco",
            "00:D0:58": "Cisco",
            "00:D0:79": "Cisco",
            "00:D0:90": "Cisco",
            "00:D0:97": "Cisco",
            "00:D0:BA": "Cisco",
            "00:D0:BB": "Cisco",
            "00:D0:BC": "Cisco",
            "00:D0:C0": "Cisco",
            "00:D0:C4": "Cisco",
            "00:D0:FF": "Cisco",
            "00:E0:14": "Cisco",
            "00:E0:1E": "Cisco",
            "00:E0:34": "Cisco",
            "00:E0:4F": "Cisco",
            "00:E0:8F": "Cisco",
            "00:E0:A3": "Cisco",
            "00:E0:B0": "Cisco",
            "00:E0:F7": "Cisco",
            "00:E0:F9": "Cisco",
            "00:E0:FE": "Cisco",
            "04:2C:6A": "Cisco",
            "04:6C:59": "Cisco",
            "04:C5:A4": "Cisco",
            "04:DA:D2": "Cisco",
            "04:FE:7F": "Cisco",
            "08:17:35": "Cisco",
            "08:1F:F3": "Cisco",
            "08:7A:4C": "Cisco",
            "08:96:AD": "Cisco",
            "08:CC:68": "Cisco",
            "0C:27:24": "Cisco",
            "0C:68:03": "Cisco",
            "0C:75:BD": "Cisco",
            "0C:85:25": "Cisco",
            "0C:D9:96": "Cisco",
            "0C:F5:A4": "Cisco",
            "10:8C:CF": "Cisco",
            "10:BD:18": "Cisco",
            "14:B8:6F": "Cisco",
            "14:DA:E9": "Cisco",
            "14:F6:D8": "Cisco",
            "18:8B:9D": "Cisco",
            "18:8B:45": "Cisco",
            "18:9C:5D": "Cisco",
            "18:EF:63": "Cisco",
            "1C:17:D3": "Cisco",
            "1C:6A:7A": "Cisco",
            "1C:DE:A7": "Cisco",
            "1C:E6:C7": "Cisco",
            "1C:E8:5D": "Cisco",
            "20:37:06": "Cisco",
            "20:3A:07": "Cisco",
            "20:4C:03": "Cisco",
            "20:BB:C0": "Cisco",
            "24:01:C7": "Cisco",
            "24:B6:57": "Cisco",
            "24:E9:B3": "Cisco",
            "28:0D:FC": "Cisco",
            "28:39:5E": "Cisco",
            "28:6F:7F": "Cisco",
            "28:94:0F": "Cisco",
            "2C:36:F8": "Cisco",
            "2C:3E:CF": "Cisco",
            "2C:54:2D": "Cisco",
            "2C:5A:0F": "Cisco",
            "30:37:A6": "Cisco",
            "30:E4:DB": "Cisco",
            "34:A8:4E": "Cisco",
            "34:DB:FD": "Cisco",
            "38:C8:5C": "Cisco",
            "3C:CE:73": "Cisco",
            "40:55:39": "Cisco",
            "44:58:29": "Cisco",
            "44:AD:D9": "Cisco",
            "44:E0:8E": "Cisco",
            "48:F8:B3": "Cisco",
            "4C:4E:35": "Cisco",
            "50:06:04": "Cisco",
            "50:17:FF": "Cisco",
            "50:3D:E5": "Cisco",
            "50:57:A8": "Cisco",
            "50:87:89": "Cisco",
            "54:7F:EE": "Cisco",
            "54:78:1A": "Cisco",
            "58:6D:8F": "Cisco",
            "58:97:1E": "Cisco",
            "58:AC:78": "Cisco",
            "58:BF:EA": "Cisco",
            "5C:50:15": "Cisco",
            "5C:83:8F": "Cisco",
            "60:73:5C": "Cisco",
            "64:00:F1": "Cisco",
            "64:16:8D": "Cisco",
            "64:A0:E7": "Cisco",
            "64:D1:54": "Cisco",
            "68:BD:AB": "Cisco",
            "68:EF:BD": "Cisco",
            "6C:20:56": "Cisco",
            "6C:41:6A": "Cisco",
            "6C:FA:89": "Cisco",
            "70:0D:B9": "Cisco",
            "70:10:5C": "Cisco",
            "70:81:05": "Cisco",
            "70:CA:9B": "Cisco",
            "74:26:AC": "Cisco",
            "74:A0:2F": "Cisco",
            "78:9A:18": "Cisco",
            "78:BA:F9": "Cisco",
            "7C:0E:CE": "Cisco",
            "7C:69:F6": "Cisco",
            "7C:95:F3": "Cisco",
            "80:E0:1D": "Cisco",
            "84:3D:C6": "Cisco",
            "84:78:AC": "Cisco",
            "84:B5:17": "Cisco",
            "84:B8:02": "Cisco",
            "88:43:E1": "Cisco",
            "88:90:8D": "Cisco",
            "88:F0:31": "Cisco",
            "8C:60:4F": "Cisco",
            "8C:B6:4F": "Cisco",
            "90:E2:BA": "Cisco",
            "94:D4:69": "Cisco",
            "98:FC:11": "Cisco",
            "9C:37:F4": "Cisco",
            "9C:4E:20": "Cisco",
            "A0:E0:AF": "Cisco",
            "A0:F8:49": "Cisco",
            "A4:0C:C3": "Cisco",
            "A4:4C:11": "Cisco",
            "A4:6C:2A": "Cisco",
            "A4:93:4C": "Cisco",
            "A8:9D:21": "Cisco",
            "AC:4A:67": "Cisco",
            "B0:7D:47": "Cisco",
            "B4:14:89": "Cisco",
            "B4:A4:E3": "Cisco",
            "B8:38:61": "Cisco",
            "B8:62:1F": "Cisco",
            "BC:16:65": "Cisco",
            "BC:67:1C": "Cisco",
            "C0:62:6B": "Cisco",
            "C0:67:AF": "Cisco",
            "C4:14:3C": "Cisco",
            "C4:64:13": "Cisco",
            "C4:71:54": "Cisco",
            "C8:4C:75": "Cisco",
            "C8:9C:1D": "Cisco",
            "CC:16:7E": "Cisco",
            "CC:46:D6": "Cisco",
            "CC:EF:48": "Cisco",
            "D0:72:DC": "Cisco",
            "D0:D0:FD": "Cisco",
            "D4:8C:B5": "Cisco",
            "D4:A0:2A": "Cisco",
            "D8:24:BD": "Cisco",
            "D8:B1:90": "Cisco",
            "DC:7B:94": "Cisco",
            "E0:5F:B9": "Cisco",
            "E4:48:C7": "Cisco",
            "E4:AA:5D": "Cisco",
            "E4:C7:22": "Cisco",
            "E8:65:49": "Cisco",
            "E8:B7:48": "Cisco",
            "EC:1D:8B": "Cisco",
            "EC:44:76": "Cisco",
            "EC:BD:1D": "Cisco",
            "F0:25:72": "Cisco",
            "F0:29:29": "Cisco",
            "F0:7D:68": "Cisco",
            "F4:CF:E2": "Cisco",
            "F8:0B:CB": "Cisco",
            "F8:4F:57": "Cisco",
            "F8:66:F2": "Cisco",
            "F8:C2:88": "Cisco",
            "FC:99:47": "Cisco",
            # 华为 OUI 前缀
            "00:1E:10": "Huawei",
            "00:25:9E": "Huawei",
            "00:46:A7": "Huawei",
            "00:E0:FC": "Huawei",
            "10:47:80": "Huawei",
            "14:5A:05": "Huawei",
            "18:66:DA": "Huawei",
            "1C:61:B4": "Huawei",
            "20:F9:E0": "Huawei",
            "28:6E:D4": "Huawei",
            "2C:AB:00": "Huawei",
            "34:29:8F": "Huawei",
            "34:6B:D3": "Huawei",
            "34:CE:00": "Huawei",
            "38:90:A5": "Huawei",
            "3C:DF:A9": "Huawei",
            "40:B0:34": "Huawei",
            "44:31:92": "Huawei",
            "48:46:FB": "Huawei",
            "4C:54:99": "Huawei",
            "50:3D:E5": "Huawei",
            "54:89:98": "Huawei",
            "5C:63:BF": "Huawei",
            "60:DE:44": "Huawei",
            "68:BD:AB": "Huawei",
            "6C:92:BF": "Huawei",
            "70:72:3C": "Huawei",
            "74:51:BA": "Huawei",
            "78:11:DC": "Huawei",
            "7C:A2:3E": "Huawei",
            "80:89:17": "Huawei",
            "84:A9:3E": "Huawei",
            "88:CF:98": "Huawei",
            "8C:BE:BE": "Huawei",
            "90:2B:34": "Huawei",
            "94:23:3C": "Huawei",
            "A0:B4:A5": "Huawei",
            "A4:5E:60": "Huawei",
            "A8:4C:A6": "Huawei",
            "AC:85:3D": "Huawei",
            "B0:5A:DA": "Huawei",
            "B4:3A:28": "Huawei",
            "B8:50:01": "Huawei",
            "BC:3F:8F": "Huawei",
            "BC:76:70": "Huawei",
            "C0:A5:DD": "Huawei",
            "C4:F0:81": "Huawei",
            "C8:9C:1D": "Huawei",
            "CC:2D:21": "Huawei",
            "D0:54:2D": "Huawei",
            "D4:D7:48": "Huawei",
            "D8:49:2F": "Huawei",
            "DC:D2:FC": "Huawei",
            "E0:19:1D": "Huawei",
            "E4:3E:D7": "Huawei",
            "E8:4E:84": "Huawei",
            "EC:23:3D": "Huawei",
            "F0:92:1C": "Huawei",
            "F4:28:53": "Huawei",
            "F8:E7:1E": "Huawei",
            "FC:48:EF": "Huawei",
            # H3C OUI 前缀
            "00:01:A7": "H3C",
            "00:13:AC": "H3C",
            "00:1E:C9": "H3C", 
            "00:22:A1": "H3C",
            "00:24:A1": "H3C",
            "04:C5:A4": "H3C",
            "08:00:09": "H3C",
            "0C:45:BA": "H3C",
            "18:A9:05": "H3C",
            "1C:B7:2C": "H3C",
            "20:89:84": "H3C",
            "24:E9:B3": "H3C",
            "28:6E:D4": "H3C",
            "2C:AB:00": "H3C",
            "30:89:4A": "H3C",
            "3C:52:82": "H3C",
            "48:7B:6B": "H3C",
            "4C:60:DE": "H3C",
            "58:69:6C": "H3C",
            "6C:50:4D": "H3C",
            "70:F9:6D": "H3C",
            "78:AC:C0": "H3C",
            "7C:A2:3E": "H3C",
            "80:71:1F": "H3C",
            "84:A9:C4": "H3C",
            "94:75:2A": "H3C",
            "A0:1D:48": "H3C",
            "A4:5E:60": "H3C",
            "A8:40:25": "H3C",
            "B0:18:32": "H3C",
            "B4:99:BA": "H3C",
            "BC:54:36": "H3C",
            "C0:A5:DD": "H3C",
            "C8:9C:1D": "H3C",
            "D0:27:88": "H3C",
            "D4:6D:7D": "H3C",
            "E0:D9:E3": "H3C",
            "E4:AF:A1": "H3C",
            "EC:38:8F": "H3C",
            "F0:7D:68": "H3C",
            "F4:E2:C6": "H3C",
            "F8:63:3F": "H3C",
            # Juniper OUI 前缀
            "00:05:85": "Juniper",
            "00:10:DB": "Juniper",
            "00:12:1E": "Juniper",
            "00:17:CB": "Juniper",
            "00:19:E2": "Juniper",
            "00:1B:C0": "Juniper",
            "00:1D:B5": "Juniper",
            "00:1F:12": "Juniper",
            "00:21:59": "Juniper",
            "00:23:9C": "Juniper",
            "00:26:88": "Juniper",
            "00:90:69": "Juniper",
            "02:05:85": "Juniper",
            "08:81:F4": "Juniper",
            "0C:86:10": "Juniper",
            "10:0E:7E": "Juniper",
            "14:4F:8A": "Juniper",
            "2C:21:72": "Juniper",
            "2C:6B:F5": "Juniper",
            "3C:94:D5": "Juniper",
            "40:A6:77": "Juniper",
            "44:F4:77": "Juniper",
            "5C:45:27": "Juniper",
            "64:64:9B": "Juniper",
            "78:19:F7": "Juniper",
            "78:FE:3D": "Juniper",
            "80:71:1F": "Juniper",
            "84:18:88": "Juniper",
            "9C:CC:83": "Juniper",
            "A8:D0:E5": "Juniper",
            "B0:C6:9A": "Juniper",
            "DC:38:E1": "Juniper",
            "EC:3E:F7": "Juniper",
            "F0:1C:2D": "Juniper",
            "F4:A7:39": "Juniper",
            "F4:CC:55": "Juniper"
        }
        
        # 常见网络设备端口映射
        self.device_port_signatures = {
            22: "SSH/Network Device",
            23: "Telnet/Network Device", 
            80: "HTTP/Web Management",
            161: "SNMP/Network Device",
            443: "HTTPS/Web Management",
            830: "NETCONF",
            8080: "HTTP Alt/Web Management",
            8443: "HTTPS Alt/Web Management"
        }
    
    def save_scan_results(self):
        """保存扫描结果到文件"""
        try:
            results_dict = {
                ip: result.to_dict() for ip, result in self.scan_results.items()
            }
            with open(self.scan_results_file, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, ensure_ascii=False, indent=2)
            logger.info(f"扫描结果已保存到: {self.scan_results_file}")
        except Exception as e:
            logger.error(f"保存扫描结果失败: {e}")
    
    def load_scan_results(self):
        """从文件加载扫描结果"""
        if not os.path.exists(self.scan_results_file):
            logger.info("扫描结果文件不存在，将创建新的")
            return
        
        try:
            with open(self.scan_results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for ip, result_data in data.items():
                result = ScanResult(
                    ip_address=result_data["ip_address"],
                    is_alive=result_data["is_alive"],
                    response_time=result_data.get("response_time"),
                    hostname=result_data.get("hostname"),
                    mac_address=result_data.get("mac_address"),
                    vendor=result_data.get("vendor"),
                    device_type=result_data.get("device_type"),
                    open_ports=result_data.get("open_ports", []),
                    services=result_data.get("services", {}),
                    snmp_info=result_data.get("snmp_info", {}),
                    os_info=result_data.get("os_info"),
                    discovered_at=datetime.fromisoformat(result_data["discovered_at"]),
                    discovery_method=set(DeviceDiscoveryMethod(method) for method in result_data.get("discovery_method", []))
                )
                self.scan_results[ip] = result
            
            logger.info(f"已加载{len(self.scan_results)}个扫描结果")
        except Exception as e:
            logger.error(f"加载扫描结果失败: {e}")
    
    async def ping_host(self, ip: str, timeout: float = 3.0) -> Tuple[bool, Optional[float]]:
        """异步ping主机"""
        try:
            # 根据操作系统选择ping命令
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(timeout)), ip]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout + 1
            )
            
            if process.returncode == 0:
                # 解析ping时间
                output = stdout.decode()
                if platform.system().lower() == "windows":
                    # Windows ping输出解析
                    time_match = re.search(r'时间[<=](\d+)ms|time[<=](\d+)ms', output, re.IGNORECASE)
                    if time_match:
                        time_value = time_match.group(1) or time_match.group(2)
                        return True, float(time_value)
                else:
                    # Linux/Unix ping输出解析
                    time_match = re.search(r'time=(\d+\.?\d*)ms', output)
                    if time_match:
                        return True, float(time_match.group(1))
                
                return True, None
            else:
                return False, None
                
        except asyncio.TimeoutError:
            return False, None
        except Exception as e:
            logger.debug(f"Ping {ip} 失败: {e}")
            return False, None
    
    async def scan_port(self, ip: str, port: int, timeout: float = 3.0) -> bool:
        """异步扫描单个端口"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    async def scan_ports(self, ip: str, ports: List[int], timeout: float = 3.0) -> List[int]:
        """异步扫描多个端口"""
        tasks = [self.scan_port(ip, port, timeout) for port in ports]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        open_ports = []
        for port, result in zip(ports, results):
            if isinstance(result, bool) and result:
                open_ports.append(port)
        
        return open_ports
    
    async def get_hostname(self, ip: str) -> Optional[str]:
        """获取主机名"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return None
    
    def get_vendor_by_mac(self, mac_address: str) -> Optional[str]:
        """根据MAC地址前缀获取厂商信息"""
        if not mac_address:
            return None
        
        # 标准化MAC地址格式
        mac_upper = mac_address.upper().replace("-", ":").replace(".", ":")
        
        # 获取前6位字符（OUI部分）
        if len(mac_upper) >= 8:
            oui = mac_upper[:8]  # XX:XX:XX 格式
            return self.vendor_oui_map.get(oui)
        
        return None
    
    def infer_device_type(self, scan_result: ScanResult) -> DeviceType:
        """根据扫描结果推断设备类型"""
        open_ports = scan_result.open_ports
        vendor = scan_result.vendor or ""
        hostname = scan_result.hostname or ""
        
        # 基于端口判断
        if 161 in open_ports:  # SNMP端口
            if 22 in open_ports or 23 in open_ports:
                # 同时有SSH/Telnet和SNMP，可能是网络设备
                if any(keyword in hostname.lower() for keyword in ["switch", "sw", "router", "rt", "gw", "gateway"]):
                    if "switch" in hostname.lower() or "sw" in hostname.lower():
                        return DeviceType.SWITCH
                    elif "router" in hostname.lower() or "rt" in hostname.lower() or "gw" in hostname.lower():
                        return DeviceType.ROUTER
                elif vendor.lower() in ["cisco", "huawei", "h3c", "juniper"]:
                    return DeviceType.SWITCH  # 默认网络设备厂商为交换机
        
        # 基于厂商判断
        if vendor.lower() == "cisco":
            return DeviceType.SWITCH
        elif vendor.lower() in ["huawei", "h3c"]:
            return DeviceType.SWITCH
        elif vendor.lower() == "juniper":
            return DeviceType.ROUTER
        
        # 基于主机名判断
        hostname_lower = hostname.lower()
        if any(keyword in hostname_lower for keyword in ["switch", "sw"]):
            return DeviceType.SWITCH
        elif any(keyword in hostname_lower for keyword in ["router", "rt", "gw", "gateway"]):
            return DeviceType.ROUTER
        elif any(keyword in hostname_lower for keyword in ["firewall", "fw", "asa", "pix"]):
            return DeviceType.FIREWALL
        elif any(keyword in hostname_lower for keyword in ["ap", "wireless", "wifi"]):
            return DeviceType.ACCESS_POINT
        
        # 默认返回其他类型
        return DeviceType.OTHER
    
    def infer_device_vendor(self, scan_result: ScanResult) -> DeviceVendor:
        """根据扫描结果推断设备厂商"""
        vendor = scan_result.vendor or ""
        hostname = scan_result.hostname or ""
        
        # 优先使用MAC地址推断的厂商
        if vendor:
            vendor_lower = vendor.lower()
            if "cisco" in vendor_lower:
                return DeviceVendor.CISCO
            elif "huawei" in vendor_lower:
                return DeviceVendor.HUAWEI
            elif "h3c" in vendor_lower:
                return DeviceVendor.H3C
            elif "juniper" in vendor_lower:
                return DeviceVendor.JUNIPER
        
        # 基于主机名判断
        hostname_lower = hostname.lower()
        if any(keyword in hostname_lower for keyword in ["cisco", "cat", "nexus"]):
            return DeviceVendor.CISCO
        elif any(keyword in hostname_lower for keyword in ["huawei", "hw"]):
            return DeviceVendor.HUAWEI
        elif "h3c" in hostname_lower:
            return DeviceVendor.H3C
        elif any(keyword in hostname_lower for keyword in ["juniper", "mx", "ex", "qfx"]):
            return DeviceVendor.JUNIPER
        
        return DeviceVendor.OTHER
    
    async def snmp_query(self, ip: str, community: str = "public", oid: str = "1.3.6.1.2.1.1.1.0", timeout: float = 3.0) -> Optional[str]:
        """SNMP查询（需要安装pysnmp库）"""
        try:
            # 这里应该使用pysnmp库，但为了避免依赖，先返回None
            # 可以后续添加SNMP支持
            return None
        except Exception as e:
            logger.debug(f"SNMP查询 {ip} 失败: {e}")
            return None
    
    async def scan_single_host(self, ip: str, config: ScanConfiguration) -> ScanResult:
        """扫描单个主机"""
        result = ScanResult(ip_address=ip)
        
        try:
            # 1. Ping检测
            if config.ping_enabled:
                is_alive, response_time = await self.ping_host(ip, config.timeout)
                result.is_alive = is_alive
                result.response_time = response_time
                if is_alive:
                    result.discovery_method.add(DeviceDiscoveryMethod.PING_SWEEP)
            
            # 如果主机不可达，跳过其他检测
            if not result.is_alive:
                return result
            
            # 2. 端口扫描
            if config.port_scan_enabled:
                open_ports = await self.scan_ports(ip, config.common_ports, config.timeout)
                result.open_ports = open_ports
                if open_ports:
                    result.discovery_method.add(DeviceDiscoveryMethod.PORT_SCAN)
                
                # 识别服务
                for port in open_ports:
                    service = self.device_port_signatures.get(port, f"Unknown/{port}")
                    result.services[port] = service
            
            # 3. 获取主机名
            hostname = await self.get_hostname(ip)
            if hostname and hostname != ip:
                result.hostname = hostname
            
            # 4. SNMP检测
            if config.snmp_enabled and 161 in result.open_ports:
                for community in config.snmp_communities:
                    snmp_result = await self.snmp_query(ip, community, timeout=config.timeout)
                    if snmp_result:
                        result.snmp_info[community] = snmp_result
                        result.discovery_method.add(DeviceDiscoveryMethod.SNMP_WALK)
                        break
            
            # 5. 推断设备信息
            if result.mac_address:
                result.vendor = self.get_vendor_by_mac(result.mac_address)
            
            result.device_type = self.infer_device_type(result).value
            vendor_enum = self.infer_device_vendor(result)
            if result.vendor is None:
                result.vendor = vendor_enum.value
            
        except Exception as e:
            logger.error(f"扫描主机 {ip} 时出错: {e}")
        
        return result
    
    async def scan_network_range(self, network: str, config: Optional[ScanConfiguration] = None) -> List[ScanResult]:
        """扫描网络范围"""
        if config is None:
            config = ScanConfiguration()
        
        logger.info(f"开始扫描网络范围: {network}")
        
        try:
            # 解析网络范围
            net = ipaddress.ip_network(network, strict=False)
            ip_list = [str(ip) for ip in net.hosts()]
            
            # 限制扫描范围（避免扫描过大的网络）
            if len(ip_list) > 1000:
                logger.warning(f"网络范围过大 ({len(ip_list)} 个主机)，限制为前1000个")
                ip_list = ip_list[:1000]
            
            logger.info(f"将扫描 {len(ip_list)} 个主机")
            
            # 使用信号量限制并发数
            semaphore = asyncio.Semaphore(config.max_concurrent)
            
            async def scan_with_semaphore(ip):
                async with semaphore:
                    return await self.scan_single_host(ip, config)
            
            # 并发扫描
            tasks = [scan_with_semaphore(ip) for ip in ip_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 过滤成功的结果
            valid_results = []
            for result in results:
                if isinstance(result, ScanResult):
                    valid_results.append(result)
                    # 保存到结果字典
                    self.scan_results[result.ip_address] = result
                elif isinstance(result, Exception):
                    logger.error(f"扫描任务异常: {result}")
            
            # 过滤活跃主机
            alive_results = [r for r in valid_results if r.is_alive]
            
            logger.info(f"扫描完成，发现 {len(alive_results)} 个活跃主机")
            
            # 保存扫描结果
            self.save_scan_results()
            
            return alive_results
            
        except Exception as e:
            logger.error(f"扫描网络范围失败: {e}")
            return []
    
    async def discover_devices_from_scan(self, scan_results: List[ScanResult], auto_create: bool = True) -> List[NetworkDevice]:
        """从扫描结果中发现并创建设备"""
        discovered_devices = []
        
        for result in scan_results:
            if not result.is_alive:
                continue
                
            # 检查设备是否已存在
            existing_devices = self.device_manager.list_devices()
            device_exists = any(device.ip_address == result.ip_address for device in existing_devices)
            
            if device_exists:
                logger.debug(f"设备已存在: {result.ip_address}")
                continue
            
            if auto_create:
                # 创建新设备
                device_name = result.hostname or f"Device-{result.ip_address.replace('.', '-')}"
                
                try:
                    device_type = DeviceType(result.device_type) if result.device_type else DeviceType.OTHER
                except ValueError:
                    device_type = DeviceType.OTHER
                
                try:
                    vendor = DeviceVendor(result.vendor.lower()) if result.vendor else DeviceVendor.OTHER
                except (ValueError, AttributeError):
                    vendor = DeviceVendor.OTHER
                
                new_device = NetworkDevice(
                    name=device_name,
                    ip_address=result.ip_address,
                    device_type=device_type,
                    vendor=vendor,
                    status=DeviceStatus.UNKNOWN,
                    description=f"通过网络扫描自动发现 (扫描时间: {result.discovered_at.strftime('%Y-%m-%d %H:%M:%S')})",
                    tags=["网络扫描发现", f"响应时间:{result.response_time}ms" if result.response_time else ""]
                )
                
                # 添加到设备管理器
                device_id = self.device_manager.add_device(new_device)
                discovered_devices.append(new_device)
                
                logger.info(f"创建新设备: {new_device.name} ({new_device.ip_address}) - {new_device.vendor.value}")
        
        return discovered_devices
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """获取扫描统计信息"""
        total_scanned = len(self.scan_results)
        alive_hosts = len([r for r in self.scan_results.values() if r.is_alive])
        
        # 厂商统计
        vendor_stats = {}
        for result in self.scan_results.values():
            if result.is_alive and result.vendor:
                vendor_stats[result.vendor] = vendor_stats.get(result.vendor, 0) + 1
        
        # 设备类型统计
        device_type_stats = {}
        for result in self.scan_results.values():
            if result.is_alive and result.device_type:
                device_type_stats[result.device_type] = device_type_stats.get(result.device_type, 0) + 1
        
        # 发现方法统计
        discovery_method_stats = {}
        for result in self.scan_results.values():
            if result.is_alive:
                for method in result.discovery_method:
                    discovery_method_stats[method.value] = discovery_method_stats.get(method.value, 0) + 1
        
        return {
            "total_scanned": total_scanned,
            "alive_hosts": alive_hosts,
            "discovery_rate": f"{(alive_hosts/total_scanned*100):.1f}%" if total_scanned > 0 else "0%",
            "vendor_distribution": vendor_stats,
            "device_type_distribution": device_type_stats,
            "discovery_method_distribution": discovery_method_stats,
            "last_scan_time": max([r.discovered_at for r in self.scan_results.values()]).isoformat() if self.scan_results else None
        }
    
    def clear_scan_results(self):
        """清空扫描结果"""
        self.scan_results.clear()
        self.save_scan_results()
        logger.info("扫描结果已清空")

# 创建网络扫描器单例
def create_network_scanner(device_manager: DeviceManager) -> NetworkScanner:
    """创建网络扫描器实例"""
    return NetworkScanner(device_manager) 