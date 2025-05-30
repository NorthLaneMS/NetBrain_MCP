from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import json
import asyncio
import logging
import traceback
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目模块
from network_devices import device_manager, DeviceType, DeviceVendor, DeviceStatus, ConnectionProtocol, NetworkDevice, DeviceCredential
from device_connector import connection_manager
from topology_discovery_improved import create_improved_topology_discovery  # 使用改进的拓扑发现模块
# 导入网络扫描模块
from network_scanner import create_network_scanner

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("web_server")

# 定义请求模型
class DeviceCreate(BaseModel):
    name: str
    ip_address: str
    device_type: str
    vendor: str
    platform: str = ""
    model: str = ""
    os_version: str = ""
    location: str = ""
    description: str = ""
    tags: List[str] = []
    credential_id: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    platform: Optional[str] = None
    model: Optional[str] = None
    os_version: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    credential_id: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class CredentialCreate(BaseModel):
    name: str
    username: str
    password: str
    protocol: str = "ssh"
    port: Optional[int] = None
    enable_password: Optional[str] = None
    ssh_key_file: Optional[str] = None

class CredentialUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    enable_password: Optional[str] = None
    ssh_key_file: Optional[str] = None

# 创建FastAPI应用
app = FastAPI(title="NetBrain MCP", description="网络设备管理与MCP协议平台")

# 添加CORS中间件以允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 明确指定允许的HTTP方法
    allow_headers=["*"],  # 允许所有头信息
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# 设置模板目录
templates = Jinja2Templates(directory="web/templates")

# 创建拓扑发现引擎实例
topology_discovery = create_improved_topology_discovery(device_manager, connection_manager)

# 创建网络扫描器实例
network_scanner = create_network_scanner(device_manager)

# 活动的WebSocket终端连接
active_terminals: Dict[str, WebSocket] = {}

# 设备API路由
@app.get("/api/devices")
async def list_devices():
    """获取所有设备列表"""
    devices = device_manager.list_devices()
    return [device.to_dict() for device in devices]

@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """获取指定设备详情"""
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")
    return device.to_dict()

@app.post("/api/devices")
async def create_device(device_data: DeviceCreate):
    """创建新设备"""
    try:
        # 日志记录请求数据
        logger.debug(f"收到添加设备请求：{device_data}")
        
        # 转换类型
        try:
            device_type = DeviceType(device_data.device_type)
        except ValueError:
            logger.error(f"无效的设备类型: {device_data.device_type}")
            raise HTTPException(status_code=400, detail=f"无效的设备类型: {device_data.device_type}")
        
        try:
            vendor = DeviceVendor(device_data.vendor)
        except ValueError:
            logger.error(f"无效的厂商: {device_data.vendor}")
            raise HTTPException(status_code=400, detail=f"无效的厂商: {device_data.vendor}")
        
        # 创建设备对象
        logger.debug(f"创建设备对象: {device_data.name}, {device_data.ip_address}")
        new_device = NetworkDevice(
            name=device_data.name,
            ip_address=device_data.ip_address,
            device_type=device_type,
            vendor=vendor,
            platform=device_data.platform,
            model=device_data.model,
            os_version=device_data.os_version,
            status=DeviceStatus.UNKNOWN,
            location=device_data.location,
            credential_id=device_data.credential_id,
            description=device_data.description,
            tags=device_data.tags
        )
        
        # 添加到设备管理器
        device_id = device_manager.add_device(new_device)
        logger.info(f"通过Web API添加设备成功: {new_device.name} ({new_device.ip_address})")
        
        # 返回创建的设备
        result = new_device.to_dict()
        logger.debug(f"返回结果: {result}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加设备失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"添加设备失败: {str(e)}")

@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: str):
    """删除设备"""
    success = device_manager.delete_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="设备未找到")
    return {"success": True}

@app.put("/api/devices/{device_id}")
async def update_device(device_id: str, device_data: DeviceUpdate = Body(...)):
    """更新设备信息"""
    try:
        # 日志记录请求数据
        logger.debug(f"收到更新设备请求：{device_data}")
        logger.debug(f"请求体内容: {device_data.dict()}")
        
        # 获取设备
        device = device_manager.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 准备更新数据
        update_data = {}
        
        # 处理名称
        if device_data.name is not None:
            update_data["name"] = device_data.name
            
        # 处理IP地址
        if device_data.ip_address is not None:
            update_data["ip_address"] = device_data.ip_address
            
        # 处理设备类型
        if device_data.device_type is not None:
            try:
                update_data["device_type"] = DeviceType(device_data.device_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的设备类型: {device_data.device_type}")
                
        # 处理厂商
        if device_data.vendor is not None:
            try:
                update_data["vendor"] = DeviceVendor(device_data.vendor)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的厂商: {device_data.vendor}")
                
        # 处理状态
        if device_data.status is not None:
            try:
                update_data["status"] = DeviceStatus(device_data.status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的状态: {device_data.status}")
                
        # 处理其他简单字段
        for field in ["platform", "model", "os_version", "location", "credential_id", "description", "tags"]:
            value = getattr(device_data, field, None)
            if value is not None:
                update_data[field] = value
                
        # 更新设备
        updated_device = device_manager.update_device(device_id, **update_data)
        if not updated_device:
            raise HTTPException(status_code=404, detail="设备更新失败")
            
        logger.info(f"设备更新成功: {updated_device.name} ({updated_device.ip_address})")
        return updated_device.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新设备失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"更新设备失败: {str(e)}")

# 凭据API路由
@app.get("/api/credentials")
async def list_credentials():
    """获取所有凭据列表"""
    credentials = device_manager.list_credentials()
    return [
        {
            "id": cred.id,
            "name": cred.name,
            "username": cred.username,
            "protocol": cred.protocol.value,
            "port": cred.port
        }
        for cred in credentials
    ]

@app.get("/api/credentials/{credential_id}")
async def get_credential(credential_id: str):
    """获取指定凭据详情"""
    credential = device_manager.get_credential(credential_id)
    if not credential:
        raise HTTPException(status_code=404, detail="凭据未找到")
    
    return {
        "id": credential.id,
        "name": credential.name,
        "username": credential.username,
        "protocol": credential.protocol.value,
        "port": credential.port,
        "ssh_key_file": credential.ssh_key_file
    }

@app.post("/api/credentials")
async def create_credential(credential_data: CredentialCreate):
    """创建新凭据"""
    try:
        # 日志记录请求
        logger.debug(f"收到添加凭据请求：{credential_data}")
        
        # 转换协议类型
        try:
            protocol = ConnectionProtocol(credential_data.protocol)
        except ValueError:
            logger.error(f"无效的协议类型: {credential_data.protocol}")
            raise HTTPException(status_code=400, detail=f"无效的协议类型: {credential_data.protocol}")
        
        # 处理端口
        port = credential_data.port
        if port is None:
            port = 22 if protocol == ConnectionProtocol.SSH else 23
            logger.debug(f"使用默认端口: {port}")
        
        # 创建凭据对象
        logger.debug(f"创建凭据对象: {credential_data.name}, {credential_data.username}")
        new_credential = DeviceCredential(
            name=credential_data.name,
            username=credential_data.username,
            password=credential_data.password,
            protocol=protocol,
            port=port,
            enable_password=credential_data.enable_password,
            ssh_key_file=credential_data.ssh_key_file
        )
        
        # 添加到设备管理器
        credential_id = device_manager.add_credential(new_credential)
        logger.info(f"通过Web API添加凭据成功: {new_credential.name} ({new_credential.username}@{protocol.value})")
        
        # 返回创建的凭据(不包含密码)
        result = new_credential.to_dict()
        logger.debug(f"返回结果: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加凭据失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"添加凭据失败: {str(e)}")

@app.delete("/api/credentials/{credential_id}")
async def delete_credential(credential_id: str):
    """删除凭据"""
    success = device_manager.delete_credential(credential_id)
    if not success:
        raise HTTPException(status_code=404, detail="凭据未找到")
    return {"success": True}

@app.put("/api/credentials/{credential_id}")
async def update_credential(credential_id: str, credential_data: CredentialUpdate = Body(...)):
    """更新凭据信息"""
    try:
        # 日志记录请求数据
        logger.debug(f"收到更新凭据请求：{credential_data}")
        logger.debug(f"请求体内容: {credential_data.dict()}")
        
        # 获取凭据
        credential = device_manager.get_credential(credential_id)
        if not credential:
            raise HTTPException(status_code=404, detail="凭据未找到")
            
        # 处理协议
        protocol = None
        if credential_data.protocol:
            try:
                protocol = ConnectionProtocol(credential_data.protocol)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的协议类型: {credential_data.protocol}")
        
        # 更新属性
        if credential_data.name is not None:
            credential.name = credential_data.name
        if credential_data.username is not None:
            credential.username = credential_data.username
        if credential_data.password is not None:
            credential.password = credential_data.password
        if protocol is not None:
            credential.protocol = protocol
        if credential_data.port is not None:
            credential.port = credential_data.port
        if credential_data.enable_password is not None:
            credential.enable_password = credential_data.enable_password
        if credential_data.ssh_key_file is not None:
            credential.ssh_key_file = credential_data.ssh_key_file
            
        # 保存更新
        device_manager.save_data()
        logger.info(f"凭据更新成功: {credential.name} ({credential.username}@{credential.protocol.value})")
        
        # 返回更新后的凭据(不包含密码)
        return credential.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新凭据失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"更新凭据失败: {str(e)}")

# 连接管理API路由
@app.get("/api/connections/active")
async def get_active_connections():
    """获取活跃连接列表"""
    try:
        connections = connection_manager.get_active_connections()
        logger.debug(f"获取活跃连接: {len(connections)} 个连接")
        return connections
    except Exception as e:
        logger.error(f"获取活跃连接失败: {str(e)}")
        return []

# WebSocket终端路由
@app.websocket("/ws/terminal/{device_id}/{credential_id}")
async def terminal_websocket(websocket: WebSocket, device_id: str, credential_id: str):
    """处理终端WebSocket连接"""
    await websocket.accept()
    connection_key = f"{device_id}_{credential_id}"
    terminal_key = f"{connection_key}_{id(websocket)}"
    
    try:
        # 记录连接
        active_terminals[terminal_key] = websocket
        logger.info(f"新的终端WebSocket连接: {terminal_key}")
        
        # 发送连接状态
        device = device_manager.get_device(device_id)
        if not device:
            await websocket.send_json({
                "type": "error",
                "message": "设备未找到"
            })
            return
            
        credential = device_manager.get_credential(credential_id)
        if not credential:
            await websocket.send_json({
                "type": "error",
                "message": "凭据未找到"
            })
            return
            
        # 连接设备
        await websocket.send_json({
            "type": "status",
            "connected": False,
            "message": f"正在连接设备: {device.name} ({device.ip_address})..."
        })
        
        success, error = await connection_manager.connect_device(device, credential)
        
        if not success:
            await websocket.send_json({
                "type": "error",
                "message": f"连接失败: {error}"
            })
            return
            
        # 连接成功通知
        await websocket.send_json({
            "type": "status",
            "connected": True,
            "device_name": device.name,
            "device_ip": device.ip_address,
            "vendor": device.vendor.value
        })
        
        # 进入交互循环
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                if message.get("type") == "input":
                    content = message.get("content", "")
                    
                    # 日志记录输入命令
                    logger.debug(f"执行设备命令: [{device.name}] {content.strip()}")
                    
                    # 发送命令到设备
                    if content:
                        try:
                            # 处理特殊控制字符
                            if content == '\x03':  # CTRL+C
                                logger.info(f"收到CTRL+C，发送中断信号到设备: {device.name}")
                                # 此处实现CTRL+C处理逻辑
                                await connection_manager.send_control_command(
                                    device_id=device_id,
                                    credential_id=credential_id,
                                    control_code='C'
                                )
                            elif content == '\x04':  # CTRL+D
                                logger.info(f"收到CTRL+D，发送EOF信号到设备: {device.name}")
                                # 此处实现CTRL+D处理逻辑
                                await connection_manager.send_control_command(
                                    device_id=device_id,
                                    credential_id=credential_id,
                                    control_code='D'
                                )
                            else:
                                # 普通命令
                                result, error = await connection_manager.send_command(
                                    device_id=device_id,
                                    credential_id=credential_id,
                                    command=content.strip('\r\n'),
                                    timeout=30
                                )
                                
                                if result:
                                    # 发送输出到客户端
                                    if result.output:
                                        # 规范化输出格式
                                        normalized_output = result.output
                                        
                                        # 先将所有不同类型的换行符统一为\n
                                        normalized_output = normalized_output.replace('\r\n', '\n').replace('\r', '\n')
                                        # 确保输出正确结束，但不强制添加换行符
                                        # 如果有提示符，我们需要保留它在同一行
                                        
                                        await websocket.send_json({
                                            "type": "output",
                                            "content": normalized_output
                                        })
                                else:
                                    logger.error(f"命令执行错误: {error}")
                                    await websocket.send_json({
                                        "type": "error",
                                        "message": f"命令执行错误: {error}"
                                    })
                        except Exception as cmd_error:
                            logger.error(f"命令执行异常: {str(cmd_error)}")
                            logger.error(traceback.format_exc())
                            await websocket.send_json({
                                "type": "error",
                                "message": f"命令执行异常: {str(cmd_error)}"
                            })
            except json.JSONDecodeError:
                # 非JSON消息，可能是直接的文本输入
                logger.warning(f"收到非JSON格式消息: {data}")
                continue
            except Exception as loop_error:
                logger.error(f"消息处理错误: {str(loop_error)}")
                logger.error(traceback.format_exc())
                await websocket.send_json({
                    "type": "error",
                    "message": f"消息处理错误: {str(loop_error)}"
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket断开连接: {terminal_key}")
    except Exception as e:
        logger.error(f"终端WebSocket错误: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        # 清理连接
        if terminal_key in active_terminals:
            del active_terminals[terminal_key]
        
        # 断开设备连接
        try:
            await connection_manager.disconnect_device(device_id, credential_id)
        except Exception as e:
            logger.error(f"断开设备连接错误: {str(e)}")
            logger.error(traceback.format_exc())

# 主页路由 - 使用新的index.html（必须放在所有API路由之后）
@app.get("/{path:path}", response_class=HTMLResponse)
async def spa_handler(request: Request, path: str = ""):
    """提供单页应用入口点"""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "NetBrain MCP - 网络设备管理与MCP协议平台"}
    )

# 在凭据API之后添加拓扑API
# 拓扑发现API路由
@app.get("/api/topology")
async def get_topology():
    """获取当前网络拓扑"""
    try:
        topology = topology_discovery.get_topology()
        return {
            "success": True,
            "topology": topology.to_dict()
        }
    except Exception as e:
        logger.error(f"获取拓扑失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取拓扑失败: {str(e)}")

@app.post("/api/topology/discover")
async def discover_topology(device_ids: List[str]):
    """从指定设备开始发现网络拓扑"""
    try:
        if not device_ids:
            raise HTTPException(status_code=400, detail="请提供至少一个设备ID")
        
        logger.info(f"Web API拓扑发现，设备列表: {device_ids}")
        
        # 验证设备是否存在
        valid_devices = []
        for device_id in device_ids:
            device = device_manager.get_device(device_id)
            if device:
                valid_devices.append(device_id)
            else:
                logger.warning(f"设备不存在: {device_id}")
        
        if not valid_devices:
            raise HTTPException(status_code=400, detail="没有找到有效的设备")
        
        # 开始拓扑发现
        topology = await topology_discovery.discover_topology_from_devices(valid_devices)
        
        return {
            "success": True,
            "message": f"拓扑发现完成，发现{len(topology.nodes)}个节点，{len(topology.links)}条链路",
            "topology": topology.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"拓扑发现失败: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"拓扑发现失败: {str(e)}")

@app.delete("/api/topology")
async def clear_topology():
    """清空拓扑数据"""
    try:
        topology_discovery.clear_topology()
        return {"success": True, "message": "拓扑数据已清空"}
    except Exception as e:
        logger.error(f"清空拓扑失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空拓扑失败: {str(e)}")

@app.get("/api/topology/statistics")
async def get_topology_statistics():
    """获取拓扑统计信息"""
    try:
        topology = topology_discovery.get_topology()
        
        # 统计不同协议的链路数量
        protocol_stats = {}
        for link in topology.links:
            protocol = link.protocol.value
            protocol_stats[protocol] = protocol_stats.get(protocol, 0) + 1
        
        # 统计不同厂商的设备数量
        vendor_stats = {}
        for node in topology.nodes.values():
            vendor = node.vendor
            vendor_stats[vendor] = vendor_stats.get(vendor, 0) + 1
        
        return {
            "success": True,
            "total_nodes": len(topology.nodes),
            "total_links": len(topology.links),
            "protocol_distribution": protocol_stats,
            "vendor_distribution": vendor_stats,
            "last_discovery": topology.last_discovery.isoformat() if topology.last_discovery else None,
            "discovery_scope": topology.discovery_scope
        }
    except Exception as e:
        logger.error(f"获取拓扑统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取拓扑统计失败: {str(e)}")

@app.get("/api/devices/{device_id}/neighbors")
async def get_device_neighbors(device_id: str):
    """获取指定设备的邻居设备"""
    try:
        topology = topology_discovery.get_topology()
        neighbors = topology.get_device_neighbors(device_id)
        
        # 获取邻居设备的详细信息
        neighbor_details = []
        for neighbor_id in neighbors:
            device = device_manager.get_device(neighbor_id)
            if device:
                neighbor_details.append(device.to_dict())
        
        return {
            "success": True,
            "device_id": device_id,
            "neighbors": neighbor_details
        }
    except Exception as e:
        logger.error(f"获取设备邻居失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取设备邻居失败: {str(e)}")

@app.post("/api/devices/{device_id}/discover-neighbors")
async def discover_device_neighbors(device_id: str):
    """发现单个设备的邻居（实时发现）"""
    try:
        device = device_manager.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="设备未找到")
        
        logger.info(f"Web API开始发现设备 {device.name} 的邻居")
        
        # 发现设备邻居
        neighbors, interfaces = await topology_discovery.discover_device_neighbors(device)
        
        return {
            "success": True,
            "device_id": device_id,
            "device_name": device.name,
            "neighbors": neighbors,
            "interfaces": [iface.to_dict() for iface in interfaces],
            "neighbor_count": len(neighbors),
            "interface_count": len(interfaces)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发现设备邻居失败: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"发现设备邻居失败: {str(e)}")

# 网络扫描API路由
@app.post("/api/scan/network")
async def scan_network_range_api(request: dict):
    """扫描网络范围"""
    try:
        network = request.get("network")
        if not network:
            raise HTTPException(status_code=400, detail="请提供网络范围参数")
        
        # 扫描配置参数
        timeout = request.get("timeout", 3.0)
        max_concurrent = request.get("max_concurrent", 50)
        ping_enabled = request.get("ping_enabled", True)
        port_scan_enabled = request.get("port_scan_enabled", True)
        snmp_enabled = request.get("snmp_enabled", True)
        auto_create_devices = request.get("auto_create_devices", False)
        
        logger.info(f"Web API网络扫描，网络范围: {network}")
        
        from network_scanner import ScanConfiguration
        
        # 创建扫描配置
        config = ScanConfiguration(
            timeout=timeout,
            max_concurrent=max_concurrent,
            ping_enabled=ping_enabled,
            port_scan_enabled=port_scan_enabled,
            snmp_enabled=snmp_enabled
        )
        
        # 执行网络扫描
        scan_results = await network_scanner.scan_network_range(network, config)
        
        # 如果启用自动创建设备，则创建发现的设备
        discovered_devices = []
        if auto_create_devices:
            discovered_devices = await network_scanner.discover_devices_from_scan(scan_results, auto_create=True)
        
        return {
            "success": True,
            "message": f"网络扫描完成，发现 {len(scan_results)} 个活跃主机",
            "network_range": network,
            "alive_hosts": len(scan_results),
            "scan_results": [result.to_dict() for result in scan_results],
            "auto_created_devices": len(discovered_devices),
            "discovered_devices": [device.to_dict() for device in discovered_devices]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"网络扫描失败: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"网络扫描失败: {str(e)}")

@app.post("/api/scan/host")
async def scan_single_host_api(request: dict):
    """扫描单个主机"""
    try:
        ip_address = request.get("ip_address")
        if not ip_address:
            raise HTTPException(status_code=400, detail="请提供IP地址参数")
        
        # 扫描配置参数
        timeout = request.get("timeout", 3.0)
        port_scan_enabled = request.get("port_scan_enabled", True)
        snmp_enabled = request.get("snmp_enabled", True)
        
        logger.info(f"Web API扫描单个主机: {ip_address}")
        
        from network_scanner import ScanConfiguration
        
        # 创建扫描配置
        config = ScanConfiguration(
            timeout=timeout,
            port_scan_enabled=port_scan_enabled,
            snmp_enabled=snmp_enabled
        )
        
        # 执行单个主机扫描
        scan_result = await network_scanner.scan_single_host(ip_address, config)
        
        # 保存到扫描结果
        network_scanner.scan_results[ip_address] = scan_result
        network_scanner.save_scan_results()
        
        return {
            "success": True,
            "message": f"主机扫描完成: {ip_address}",
            "is_alive": scan_result.is_alive,
            "scan_result": scan_result.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"扫描单个主机失败: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"扫描单个主机失败: {str(e)}")

@app.get("/api/scan/results")
async def get_scan_results_api(ip_address: Optional[str] = None, alive_only: bool = True):
    """获取扫描结果"""
    try:
        if ip_address:
            # 获取特定IP的扫描结果
            result = network_scanner.scan_results.get(ip_address)
            if result:
                return {
                    "success": True,
                    "scan_result": result.to_dict()
                }
            else:
                raise HTTPException(status_code=404, detail=f"未找到IP {ip_address} 的扫描结果")
        else:
            # 获取所有扫描结果
            results = list(network_scanner.scan_results.values())
            if alive_only:
                results = [r for r in results if r.is_alive]
            
            return {
                "success": True,
                "total_results": len(results),
                "scan_results": [result.to_dict() for result in results]
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取扫描结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取扫描结果失败: {str(e)}")

@app.get("/api/scan/statistics")
async def get_scan_statistics_api():
    """获取扫描统计信息"""
    try:
        stats = network_scanner.get_scan_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"获取扫描统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取扫描统计失败: {str(e)}")

@app.post("/api/scan/discover-devices")
async def discover_devices_from_scan_api(request: dict):
    """从扫描结果中发现并创建设备"""
    try:
        # 过滤参数
        min_response_time = request.get("min_response_time")
        required_ports = request.get("required_ports", "")
        vendor_filter = request.get("vendor_filter")
        device_type_filter = request.get("device_type_filter")
        
        # 获取所有活跃的扫描结果
        all_results = [r for r in network_scanner.scan_results.values() if r.is_alive]
        
        # 应用过滤条件
        filtered_results = []
        for result in all_results:
            # 响应时间过滤
            if min_response_time and result.response_time and result.response_time > min_response_time:
                continue
            
            # 端口过滤
            if required_ports:
                required_port_list = [int(p.strip()) for p in required_ports.split(',') if p.strip().isdigit()]
                if not all(port in result.open_ports for port in required_port_list):
                    continue
            
            # 厂商过滤
            if vendor_filter and result.vendor:
                if vendor_filter.lower() not in result.vendor.lower():
                    continue
            
            # 设备类型过滤
            if device_type_filter and result.device_type:
                if device_type_filter.lower() not in result.device_type.lower():
                    continue
            
            filtered_results.append(result)
        
        # 从过滤后的结果创建设备
        discovered_devices = await network_scanner.discover_devices_from_scan(filtered_results, auto_create=True)
        
        return {
            "success": True,
            "message": f"从 {len(filtered_results)} 个扫描结果中创建了 {len(discovered_devices)} 个设备",
            "filtered_results_count": len(filtered_results),
            "created_devices_count": len(discovered_devices),
            "created_devices": [device.to_dict() for device in discovered_devices]
        }
    except Exception as e:
        logger.error(f"从扫描结果创建设备失败: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"从扫描结果创建设备失败: {str(e)}")

@app.delete("/api/scan/results")
async def clear_scan_results_api():
    """清空扫描结果"""
    try:
        network_scanner.clear_scan_results()
        return {"success": True, "message": "扫描结果已清空"}
    except Exception as e:
        logger.error(f"清空扫描结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空扫描结果失败: {str(e)}")

# 在其他API路由之后添加修复API

def standardize_platform_info(platform: str, device_name: str = "") -> str:
    """标准化平台信息为简洁的平台代码"""
    if not platform:
        return "unknown"
        
    platform_lower = platform.lower()
    device_name_lower = device_name.lower()
    
    # 华为设备平台标准化
    if "huawei" in platform_lower or "vrp" in platform_lower:
        if "s5700" in platform_lower or "s5700" in device_name_lower:
            return "huawei_s5700"
        elif "s6720" in platform_lower or "s6720" in device_name_lower:
            return "huawei_s6720"
        elif "s3700" in platform_lower or "s3700" in device_name_lower:
            return "huawei_s3700"
        elif "ce" in device_name_lower:
            return "huawei_ce"
        else:
            return "huawei_vrp"
    
    # Cisco设备平台标准化
    elif "cisco" in platform_lower:
        if "catalyst" in platform_lower:
            return "cisco_catalyst"
        elif "nexus" in platform_lower:
            return "cisco_nexus"
        elif "asr" in platform_lower:
            return "cisco_asr"
        elif "isr" in platform_lower:
            return "cisco_isr"
        else:
            return "cisco_ios"
    
    # H3C设备平台标准化
    elif "h3c" in platform_lower or "comware" in platform_lower:
        if "s5120" in platform_lower:
            return "h3c_s5120"
        elif "s5130" in platform_lower:
            return "h3c_s5130"
        else:
            return "h3c_comware"
    
    # Juniper设备平台标准化
    elif "juniper" in platform_lower or "junos" in platform_lower:
        return "juniper_junos"
    
    # 其他设备
    else:
        # 尝试从原始平台信息中提取关键型号信息
        import re
        model_match = re.search(r'(s\d+[a-z]*-?\d*[a-z]*)', platform_lower)
        if model_match:
            return f"unknown_{model_match.group(1)}"
        
        return "unknown"

@app.post("/api/devices/fix-platforms")
async def fix_device_platforms():
    """修复所有设备的平台信息"""
    try:
        devices = device_manager.list_devices()
        updated_devices = []
        
        for device in devices:
            original_platform = device.platform
            
            # 如果平台信息很长（超过30个字符），可能需要标准化
            if len(original_platform) > 30 or any(keyword in original_platform.lower() 
                                                  for keyword in ["software", "version", "copyright", "platform"]):
                new_platform = standardize_platform_info(original_platform, device.name)
                
                if new_platform != original_platform:
                    # 更新设备平台信息
                    updated_device = device_manager.update_device(device.id, platform=new_platform)
                    if updated_device:
                        updated_devices.append({
                            "device_name": device.name,
                            "original_platform": original_platform,
                            "new_platform": new_platform
                        })
        
        return {
            "success": True,
            "message": f"修复了 {len(updated_devices)} 个设备的平台信息",
            "updated_devices": updated_devices
        }
    except Exception as e:
        logger.error(f"修复设备平台信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"修复设备平台信息失败: {str(e)}")

# 运行应用
if __name__ == "__main__":
    # 注意: 此代码块不会被server.py调用
    # 仅在直接运行此文件时使用
    uvicorn.run("web.app:app", host="0.0.0.0", port=8088, reload=True) 