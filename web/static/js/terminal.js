/**
 * NetBrain MCP 终端管理器
 * 
 * 基于XTerm.js实现虚拟终端功能
 * 通过WebSocket与后端scrapli连接器通信
 */

class TerminalManager {
    constructor() {
        this.terminals = [];
        this.activeTerminalId = null;
        this.tabContainer = document.querySelector('.terminal-tabs');
        this.windowContainer = document.querySelector('.terminal-windows');
        this.nextId = 1;
        
        // 命令自动补全功能所需的通用命令列表
        this.commonCommands = {
            'cisco': [
                // 基本命令
                'show', 'configure', 'terminal', 'interface', 'ip', 'router', 'enable', 'disable',
                'exit', 'end', 'write', 'reload', 'ping', 'traceroute', 'telnet', 'ssh',
                'copy', 'delete', 'dir', 'more', 'no', 'clear', 'clock', 'hostname',
                
                // 配置命令
                'configure terminal', 'line console', 'line vty', 'access-list', 'banner',
                'logging', 'service', 'boot', 'cdp', 'lldp', 'vtp', 'spanning-tree',
                'username', 'password', 'enable secret', 'enable password', 'crypto',
                'aaa', 'tacacs', 'radius', 'ntp', 'snmp-server', 'ip http', 'ip domain',
                'ip name-server', 'ip ssh', 'ip access-list', 'ip route', 'vlan',
                'switchport', 'channel-group', 'port-channel', 'standby', 'vrf',
                'policy-map', 'class-map', 'route-map', 'ip nat', 'ip dhcp',
                
                // 显示命令
                'show running-config', 'show startup-config', 'show version', 'show ip interface brief',
                'show ip route', 'show vlan', 'show mac address-table', 'show cdp neighbors',
                'show interfaces status', 'show interfaces', 'show ip protocols',
                'show processes cpu', 'show processes memory', 'show environment',
                'show inventory', 'show tech-support', 'show logging', 'show users',
                'show clock', 'show vtp status', 'show spanning-tree', 'show standby',
                'show etherchannel summary', 'show ip ospf', 'show ip bgp',
                'show ip nat translations', 'show ip dhcp binding', 'show access-lists',
                'show controllers', 'show platform', 'show diagnostic', 'show power',
                'show module', 'show license', 'show switch', 'show stack',
                'show vrf', 'show mpls', 'show crypto', 'show aaa', 'show tacacs',
                'show radius', 'show ntp', 'show snmp', 'show ip ssh',
                
                // 接口命令
                'interface GigabitEthernet', 'interface FastEthernet', 'interface TenGigabitEthernet',
                'interface FortyGigabitEthernet', 'interface HundredGigE', 'interface Loopback',
                'interface Tunnel', 'interface Vlan', 'interface Port-channel',
                'interface GigabitEthernet0/0', 'interface GigabitEthernet0/0/0',
                'interface FastEthernet0/0', 'interface TenGigabitEthernet1/1',
                'interface Vlan1', 'interface Loopback0', 'interface Port-channel1',
                
                // 接口配置命令
                'switchport mode access', 'switchport mode trunk', 'switchport access vlan',
                'switchport trunk allowed vlan', 'switchport trunk encapsulation',
                'switchport nonegotiate', 'switchport port-security', 'spanning-tree portfast',
                'spanning-tree bpduguard', 'channel-group mode', 'ip address', 'ip helper-address',
                'duplex', 'speed', 'negotiation', 'mtu', 'bandwidth', 'delay',
                'shutdown', 'no shutdown', 'description', 'encapsulation', 'keepalive',
                'load-interval', 'carrier-delay', 'flow-control', 'mdix auto',
                
                // 路由协议命令
                'router ospf', 'router bgp', 'router eigrp', 'router isis', 'router rip',
                'network', 'area', 'passive-interface', 'default-information originate',
                'redistribute', 'neighbor', 'distance', 'maximum-paths', 'auto-cost',
                
                // 其他常用命令
                'do', 'debug', 'undebug', 'erase', 'archive', 'verify', 'test',
                'macro', 'monitor', 'diagnostic', 'license', 'platform', 'redundancy'
            ],
            'huawei': [
                // 基本系统命令
                'display', 'system-view', 'interface', 'ip', 'quit', 'return', 'save',
                'reboot', 'ping', 'tracert', 'telnet', 'ssh', 'copy', 'delete',
                'dir', 'more', 'undo', 'sysname', 'header', 'clock', 'debugging',
                
                // 系统视图命令
                'aaa', 'acl', 'user-interface', 'user', 'super', 'password', 'role',
                'snmp-agent', 'vlan', 'vlan batch', 'port-group', 'diffserv', 'domain',
                'stp', 'lacp', 'ntp', 'info-center', 'arp', 'ospf', 'isis', 'bgp',
                'route-policy', 'ip route-static', 'mpls', 'mpls lsp', 'qos', 'traffic',
                'radius-server', 'hwtacacs-server', 'local-user', 'ssh user', 'ftp',
                'version', 'stelnet', 'public-key', 'rsa', 'dsa', 'license', 'patch',
                
                // 详细配置命令
                'ospf 1', 'area', 'network', 'vrrp vrid', 'track', 'dhcp enable',
                'dhcp server', 'dhcp pool', 'gateway-list', 'dns-list', 'interface vlanif',
                'nat', 'nat server', 'nat outbound', 'port link-type', 'port trunk allow-pass',
                'port hybrid', 'port access', 'loopback', 'description', 'shutdown',
                'undo shutdown', 'mtu', 'speed', 'duplex', 'flow-control', 'portswitch',
                
                // 诊断和排障命令
                'display ip routing-table', 'display ip interface brief',
                'display current-configuration', 'display saved-configuration',
                'display version', 'display device', 'display device interface',
                'display arp', 'display mac-address', 'display cpu-usage', 'display memory-usage',
                'display vlan', 'display port vlan', 'display port', 'display logbuffer',
                'display diagnostic-information', 'display fan', 'display power',
                'display temperature', 'display clock', 'display environment',
                'display ntp status', 'display ntp session', 'display interface',
                'display ip interface', 'display users', 'display ssh user-information',
                'display tcp status', 'display ip socket', 'display ip statistics',
                
                // 更多显示命令组合
                'display interface brief', 'display ospf peer', 'display ospf lsdb',
                'display ospf routing', 'display bgp peer', 'display bgp routing-table',
                'display acl all', 'display acl resource', 'display traffic-policy',
                'display qos-profile', 'display queue-statistics', 'display traffic classifier',
                'display traffic behavior', 'display traffic-policy statistics',
                'display ip vpn-instance', 'display ip vpn-instance interface',
                'display mac-address blackhole', 'display mac-address dynamic',
                'display mac-address static', 'display lldp neighbor', 'display lldp statistics',
                'display device manuinfo', 'display device manuinfo fan',
                'display device manuinfo power', 'display stack', 'display esn',
                'display patch-information', 'display patch-status', 'display elabel',
                'display transceiver', 'display transceiver verbose', 'display transceiver alarm',
                'display transceiver diagnosis', 'display startup', 'display boot-loader',
                'display dhcp server', 'display dhcp client', 'display dhcp pool',
                'display license', 'display license feature', 'display license authorization',
                'display mirror', 'display alarm', 'display alarm statistics',
                'display sflow', 'display dldp', 'display nqa', 'display info-center',
                'display link-aggregation', 'display port trunk', 'display port-security',
                'display error-down', 'display interface counters', 'display interface statistics',
                
                // 接口特定命令
                'interface GigabitEthernet', 'interface XGigabitEthernet',
                'interface 10GE', 'interface 40GE', 'interface 100GE',
                'interface Eth-Trunk', 'interface LoopBack', 'interface MEth',
                'interface Tunnel', 'interface NULL', 'interface Vlanif',
                'interface GigabitEthernet0/0/1', 'interface XGigabitEthernet0/0/1',
                'interface 10GE1/0/1', 'interface 40GE1/0/1', 'interface Eth-Trunk1',
                'interface Vlanif100', 'interface LoopBack0', 'interface NULL0',
                'interface Tunnel0/0/0',
                
                // 接口详细配置命令
                'portswitch', 'jumboframe enable', 'mdix auto', 'loopback',
                'port link-type access', 'port link-type trunk', 'port link-type hybrid',
                'port default vlan', 'port trunk allow-pass vlan', 'port hybrid tagged vlan',
                'port hybrid untagged vlan', 'port hybrid pvid vlan', 'stp',
                'stp edged-port enable', 'stp bpdu-protection', 'stp root-protection',
                'stp loop-protection', 'port-security enable', 'port-security max-mac-num',
                'port-security port-mode', 'port-security mac-address sticky',
                'lldp enable', 'lldp transmit', 'lldp receive', 'undo negotiation auto',
                'speed 1000', 'speed auto', 'duplex full', 'duplex auto',
                'trust dscp', 'trust 8021p', 'traffic-filter', 'traffic-policy',
                'qos-profile', 'mirroring-group', 'monitor-link group', 'ip binding vpn-instance',
                'statistic enable', 'flow-control', 'flow-control receive',
                
                // 调试命令
                'debugging ip packet', 'debugging dhcp', 'debugging ssh', 'debugging ntp',
                'debugging ospf packet', 'debugging bgp', 'debugging igmp', 'debugging pim',
                
                // 安全与访问控制命令
                'acl number', 'acl name', 'rule', 'firewall', 'security-policy',
                'ike', 'ipsec', 'ssl', 'pki', 'ca', 'certificate', 'aaa',
                
                // 特定撤销命令
                'undo ip address', 'undo vlan', 'undo interface', 'undo acl', 'undo stp',
                'undo dhcp', 'undo nat', 'undo ip route-static', 'undo ospf',
                'undo bgp', 'undo snmp-agent', 'undo ssh user', 'undo user-interface',
                'undo local-user', 'undo mirroring-group', 'undo traffic-policy',
                'undo qos-profile', 'undo port trunk', 'undo port hybrid',
                'undo port link-type', 'undo port default vlan', 'undo stp enable',
                'undo lldp enable', 'undo info-center', 'undo ntp-service',
                'undo ip vpn-instance', 'undo sysname', 'undo license',
                
                // 配置保存和重启命令
                'save', 'save force', 'save safely', 'reboot', 'reboot fast',
                'startup saved-configuration', 'reset saved-configuration',
                'reset recycle-bin', 'reset counters interface', 'reset logbuffer',
                
                // VPN和MPLS相关命令
                'ip vpn-instance', 'ipv4-family', 'ipv6-family', 'route-distinguisher',
                'vpn-target', 'mpls lsr-id', 'mpls', 'mpls ldp', 'mpls te',
                'mpls rsvp-te', 'tunnel-protocol', 'mpls l2vc', 'mpls l3vpn',
                
                // 特定场景配置命令
                'smart-link group', 'smart-link flush enable', 'monitor-link group',
                'vrrp vrid', 'vrrp authentication-mode', 'vrrp preempt-mode',
                'vrrp track', 'track', 'track nqa', 'track interface',
                'hrp enable', 'hrp interface', 'dfs-group', 'stack', 
                'issu', 'issu load', 'issu run', 'issu accept', 'issu commit',
                'issu set', 'patch', 'patch active', 'patch deactive', 'patch delete',
                'patch install', 'patch rollback', 'patch running', 'startup patch',
                
                // 常用缩写命令
                'dis', 'int', 'sys', 'sa', 'qu', 'ret', 'conf', 'cl', 'un'
            ],
            'common': [
                'ls', 'cd', 'pwd', 'cat', 'clear', 'help', 'exit', 'quit'
            ]
        };
        
        // 绑定事件处理程序
        document.getElementById('reconnect-terminal')?.addEventListener('click', () => this.reconnectActiveTerminal());
        document.getElementById('connect-device')?.addEventListener('click', () => this.showConnectDialog());
        
        // 绑定连接对话框事件
        document.getElementById('connect-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleDeviceConnect();
        });

        // 绑定窗口调整大小事件
        window.addEventListener('resize', () => {
            this.resizeActiveTerminal();
        });
        
        // 初始化连接对话框关闭按钮
        const closeButtons = document.querySelectorAll('.modal .close, .modal .close-btn');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.modal').forEach(modal => {
                    modal.style.display = 'none';
                });
            });
        });
    }
    
    // 创建新终端
    createTerminal(name, deviceId = null, credentialId = null) {
        const terminalId = `terminal-${this.nextId++}`;
        
        // 创建标签页
        const tab = document.createElement('div');
        tab.className = 'terminal-tab';
        tab.dataset.target = terminalId;
        tab.innerHTML = `
            <span>${name}</span>
            <span class="terminal-tab-close">&times;</span>
        `;
        this.tabContainer.appendChild(tab);

        // 创建终端窗口
        const termWindow = document.createElement('div');
        termWindow.className = 'terminal-instance';
        termWindow.id = terminalId;
        this.windowContainer.appendChild(termWindow);

        // 初始化xterm.js终端
        const terminal = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            theme: {
                background: '#1a1a1a',
                foreground: '#f8f8f8'
            },
            allowTransparency: true,
            scrollback: 5000, // 增大滚动缓冲区
            lineHeight: 1.2,  // 增加行间距
            rendererType: 'canvas', // 使用canvas渲染器提升性能
            convertEol: true, // 确保回车时换行
            letterSpacing: 0, // 调整字间距
            tabStopWidth: 8   // Tab宽度
        });

        // 使用FitAddon来自适应终端大小
        const fitAddon = new FitAddon.FitAddon();
        terminal.loadAddon(fitAddon);
        
        // 使用WebLinksAddon自动识别链接
        const webLinksAddon = new WebLinksAddon.WebLinksAddon();
        terminal.loadAddon(webLinksAddon);

        // 打开终端并适配大小
        terminal.open(termWindow);
        setTimeout(() => fitAddon.fit(), 100);

        // 保存终端信息
        const terminalInfo = {
            id: terminalId,
            name: name,
            terminal: terminal,
            fitAddon: fitAddon,
            deviceId: deviceId,
            credentialId: credentialId,
            socket: null,
            commandBuffer: '',
            cursorPosition: 0,      // 跟踪光标在命令中的位置
            inputActive: false, // 标记终端是否正在接收用户输入
            sessionRegistered: false, // 会话注册标记
            commandHistory: [],     // 命令历史数组
            historyIndex: -1,       // 历史命令索引
            currentCommand: ''      // 当前未提交的命令
        };
        
        this.terminals.push(terminalInfo);
        
        // 设置事件监听
        // 点击标签页激活对应终端
        tab.addEventListener('click', (e) => {
            if (!e.target.classList.contains('terminal-tab-close')) {
                this.activateTerminal(terminalId);
            }
        });
        
        // 点击关闭按钮
        tab.querySelector('.terminal-tab-close').addEventListener('click', () => {
            this.closeTerminal(terminalId);
        });
        
        // 激活新创建的终端
        this.activateTerminal(terminalId);
        
        // 如果提供了设备ID和凭据ID，则连接到设备
        if (deviceId && credentialId) {
            this.connectToDevice(terminalInfo, deviceId, credentialId);
            
            // 注册会话 - 使用terminalId作为会话ID
            if (window.sessionManager) {
                const deviceName = this._getDeviceName(deviceId);
                window.sessionManager.registerActiveSession(terminalId, {
                    name: name || `${deviceName || '设备'}-会话`,
                    deviceId: deviceId,
                    credentialId: credentialId
                });
                
                // 记录注册的会话ID，以防重复注册
                terminalInfo.sessionRegistered = true;
            }
        } else {
            // 否则，显示本地终端提示
            terminal.writeln('\r\n欢迎使用 NetBrain MCP 终端\r\n');
            terminal.writeln('这是一个本地终端会话。要连接到网络设备，请点击"连接设备"按钮。\r\n');
            
            // 创建简单的本地echo会话
            terminalInfo.promptText = '[MCP]>';
            terminal.write(`${terminalInfo.promptText}`);
            terminalInfo.inputActive = true;
            terminalInfo.cursorPosition = 0;  // 初始化光标位置
            terminalInfo.vendorType = 'common'; // 本地终端使用通用命令
            
            terminal.onData(data => {
                // 模拟简单的本地shell行为
                // 处理上下箭头键
                if (data === '\x1b[A') {  // 上箭头
                    this.navigateHistory(terminalInfo, 'up');
                    return;
                } else if (data === '\x1b[B') {  // 下箭头
                    this.navigateHistory(terminalInfo, 'down');
                    return;
                } else if (data === '\x1b[C') {  // 右箭头
                    this.moveCursor(terminalInfo, 'right');
                    return;
                } else if (data === '\x1b[D') {  // 左箭头
                    this.moveCursor(terminalInfo, 'left');
                    return;
                } else if (data === '\t') {  // Tab键 - 处理自动补全
                    this.handleTabCompletion(terminalInfo);
                    return;
                } else if (data === '\r') {  // 回车
                    // 重置Tab补全状态
                    terminalInfo.tabMatches = null;
                    terminalInfo.tabIndex = undefined;
                    
                    const command = terminalInfo.commandBuffer.trim();
                    
                    // 添加到历史记录
                    if (command && (terminalInfo.commandHistory.length === 0 || 
                                   terminalInfo.commandHistory[terminalInfo.commandHistory.length - 1] !== command)) {
                        terminalInfo.commandHistory.push(command);
                        // 限制历史记录长度
                        if (terminalInfo.commandHistory.length > 100) {
                            terminalInfo.commandHistory.shift();
                        }
                    }
                    // 重置历史索引和光标位置
                    terminalInfo.historyIndex = -1;
                    terminalInfo.cursorPosition = 0;
                    
                    terminalInfo.commandBuffer = '';
                    terminal.writeln('');
                    
                    // 简单的命令处理
                    if (command === 'clear') {
                        terminal.clear();
                    } else if (command === 'help') {
                        terminal.writeln('可用命令:');
                        terminal.writeln('  clear   - 清屏');
                        terminal.writeln('  help    - 显示帮助');
                        terminal.writeln('  exit    - 关闭终端');
                        terminal.writeln('  connect - 连接到设备');
                        terminal.writeln('  tab键   - 自动补全命令');
                        terminal.writeln('  sysname - 修改终端名称 (例如: sysname Router1)');
                    } else if (command === 'exit') {
                        this.closeTerminal(terminalId);
                        return;
                    } else if (command === 'connect') {
                        this.showConnectDialog();
                    } else if (command.startsWith('sysname ')) {
                        const newName = command.substring(8).trim();
                        if (newName) {
                            terminalInfo.promptText = `[${newName}]>`;
                            terminal.writeln(`终端名称已修改为: ${newName}`);
                        } else {
                            terminal.writeln('请提供终端名称');
                        }
                    } else if (command) {
                        terminal.writeln(`未知命令: ${command}`);
                    }
                    
                    terminal.write(`${terminalInfo.promptText}`);
                } else if (data === '\u007f') {  // 退格键
                    if (terminalInfo.commandBuffer.length > 0 && terminalInfo.cursorPosition > 0) {
                        // 重置Tab补全状态
                        terminalInfo.tabMatches = null;
                        terminalInfo.tabIndex = undefined;
                        
                        // 在光标位置删除字符
                        const before = terminalInfo.commandBuffer.substring(0, terminalInfo.cursorPosition - 1);
                        const after = terminalInfo.commandBuffer.substring(terminalInfo.cursorPosition);
                        terminalInfo.commandBuffer = before + after;
                        terminalInfo.cursorPosition--;
                        
                        // 重新绘制整行
                        terminal.write('\b \b'); // 删除光标前的字符
                        
                        // 如果光标不在行尾，需要重新绘制整个命令
                        if (terminalInfo.cursorPosition < terminalInfo.commandBuffer.length) {
                            // 将光标移回行首
                            terminal.write('\b'.repeat(terminalInfo.cursorPosition));
                            
                            // 清空整行
                            terminal.write(' '.repeat(terminalInfo.commandBuffer.length + 1));
                            terminal.write('\b'.repeat(terminalInfo.commandBuffer.length + 1));
                            
                            // 写入新命令
                            terminal.write(terminalInfo.commandBuffer);
                            
                            // 将光标移动到新位置
                            terminal.write('\b'.repeat(terminalInfo.commandBuffer.length - terminalInfo.cursorPosition));
                        }
                    }
                } else {
                    // 输入了新字符，重置Tab补全状态
                    terminalInfo.tabMatches = null;
                    terminalInfo.tabIndex = undefined;
                    
                    // 在光标位置插入字符
                    const before = terminalInfo.commandBuffer.substring(0, terminalInfo.cursorPosition);
                    const after = terminalInfo.commandBuffer.substring(terminalInfo.cursorPosition);
                    terminalInfo.commandBuffer = before + data + after;
                    terminalInfo.cursorPosition++;
                    
                    // 如果光标在行尾，直接写入字符
                    if (terminalInfo.cursorPosition === terminalInfo.commandBuffer.length) {
                        terminal.write(data);
                    } else {
                        // 否则，需要重新绘制整行
                        terminal.write(data + after);
                        
                        // 将光标移回到正确位置
                        terminal.write('\b'.repeat(after.length));
                    }
                }
            });
        }
        
        return terminalInfo;
    }
    
    // 移动光标
    moveCursor(terminalInfo, direction) {
        const terminal = terminalInfo.terminal;
        
        if (direction === 'left') {
            // 光标向左移动，但不能超出命令范围
            if (terminalInfo.cursorPosition > 0) {
                terminalInfo.cursorPosition--;
                terminal.write('\x1b[D'); // 向左移动光标
            }
        } else if (direction === 'right') {
            // 光标向右移动，但不能超出命令末尾
            if (terminalInfo.cursorPosition < terminalInfo.commandBuffer.length) {
                terminalInfo.cursorPosition++;
                terminal.write('\x1b[C'); // 向右移动光标
            }
        }
    }
    
    // 清除输入行
    clearInputLine(terminalInfo) {
        const terminal = terminalInfo.terminal;
        const currentLength = terminalInfo.commandBuffer.length;
        
        if (currentLength > 0) {
            // 先将光标移到行尾，然后再清除整行
            if (terminalInfo.cursorPosition < currentLength) {
                terminal.write('\x1b[C'.repeat(currentLength - terminalInfo.cursorPosition));
            }
            terminal.write('\b'.repeat(currentLength) + ' '.repeat(currentLength) + '\b'.repeat(currentLength));
        }
    }
    
    // 导航命令历史功能
    navigateHistory(terminalInfo, direction) {
        const terminal = terminalInfo.terminal;
        const history = terminalInfo.commandHistory;
        
        if (history.length === 0) return;
        
        // 处理上箭头
        if (direction === 'up') {
            // 第一次按上箭头时，保存当前输入
            if (terminalInfo.historyIndex === -1) {
                terminalInfo.currentCommand = terminalInfo.commandBuffer;
            }
            
            // 确保不超出历史记录范围
            if (terminalInfo.historyIndex < history.length - 1) {
                terminalInfo.historyIndex++;
                
                // 清除当前行
                this.clearInputLine(terminalInfo);
                
                // 显示历史命令
                const historyCommand = history[history.length - 1 - terminalInfo.historyIndex];
                terminal.write(historyCommand);
                terminalInfo.commandBuffer = historyCommand;
                terminalInfo.cursorPosition = historyCommand.length; // 更新光标位置到行尾
            }
        } 
        // 处理下箭头
        else if (direction === 'down') {
            if (terminalInfo.historyIndex > -1) {
                terminalInfo.historyIndex--;
                
                // 清除当前行
                this.clearInputLine(terminalInfo);
                
                // 如果回到初始状态，显示未提交的命令
                if (terminalInfo.historyIndex === -1) {
                    terminal.write(terminalInfo.currentCommand);
                    terminalInfo.commandBuffer = terminalInfo.currentCommand;
                    terminalInfo.cursorPosition = terminalInfo.currentCommand.length; // 更新光标位置到行尾
                } else {
                    // 否则显示较新的历史命令
                    const historyCommand = history[history.length - 1 - terminalInfo.historyIndex];
                    terminal.write(historyCommand);
                    terminalInfo.commandBuffer = historyCommand;
                    terminalInfo.cursorPosition = historyCommand.length; // 更新光标位置到行尾
                }
            }
        }
    }
    
    // 获取设备名称
    _getDeviceName(deviceId) {
        const cachedDevices = window.cachedDevices || [];
        const device = cachedDevices.find(d => d.id === deviceId);
        return device ? device.name : null;
    }
    
    // 激活终端
    activateTerminal(terminalId) {
        // 取消激活所有终端
        document.querySelectorAll('.terminal-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.terminal-instance').forEach(inst => {
            inst.classList.remove('active');
        });
        
        // 激活选定的终端
        const tab = document.querySelector(`.terminal-tab[data-target="${terminalId}"]`);
        const instance = document.getElementById(terminalId);
        
        if (tab && instance) {
            tab.classList.add('active');
            instance.classList.add('active');
            this.activeTerminalId = terminalId;
            
            // 获取终端对象并重新适应大小
            this.resizeActiveTerminal();
        }
    }
    
    // 调整活动终端大小
    resizeActiveTerminal() {
        if (this.activeTerminalId) {
            const termInfo = this.getTerminalById(this.activeTerminalId);
            if (termInfo && termInfo.fitAddon) {
                setTimeout(() => termInfo.fitAddon.fit(), 10);
            }
        }
    }
    
    // 关闭终端
    closeTerminal(terminalId) {
        // 获取终端信息
        const termIndex = this.terminals.findIndex(t => t.id === terminalId);
        if (termIndex === -1) return;
        
        const termInfo = this.terminals[termIndex];
        
        // 标记为手动关闭，防止自动重连
        termInfo.manualClosed = true;
        termInfo.needReconnect = false;
        
        // 清除任何重连或超时计时器
        if (termInfo.reconnectTimer) {
            clearTimeout(termInfo.reconnectTimer);
            termInfo.reconnectTimer = null;
        }
        
        if (termInfo.inputTimeoutId) {
            clearTimeout(termInfo.inputTimeoutId);
            termInfo.inputTimeoutId = null;
        }
        
        // 关闭WebSocket连接
        if (termInfo.socket && termInfo.socket.readyState === WebSocket.OPEN) {
            termInfo.socket.close();
        }
        
        // 从DOM移除元素
        const tab = document.querySelector(`.terminal-tab[data-target="${terminalId}"]`);
        const instance = document.getElementById(terminalId);
        
        if (tab) tab.remove();
        if (instance) instance.remove();
        
        // 销毁终端实例
        termInfo.terminal.dispose();
        
        // 从数组中移除
        this.terminals.splice(termIndex, 1);
        
        // 如果关闭的是当前激活的终端，则激活另一个终端
        if (this.activeTerminalId === terminalId && this.terminals.length > 0) {
            this.activateTerminal(this.terminals[0].id);
        } else if (this.terminals.length === 0) {
            this.activeTerminalId = null;
        }
        
        // 注销会话
        if (window.sessionManager && termInfo.sessionRegistered) {
            window.sessionManager.unregisterActiveSession(terminalId);
        }
    }
    
    // 通过ID获取终端信息
    getTerminalById(terminalId) {
        return this.terminals.find(t => t.id === terminalId);
    }
    
    // 显示连接设备对话框
    showConnectDialog() {
        // 显示模态框
        const modal = document.getElementById('device-connect-modal');
        modal.style.display = 'block';
        
        const deviceSelect = document.getElementById('device-select');
        const credentialSelect = document.getElementById('credential-select');
        
        // 清空下拉列表并显示加载中状态
        deviceSelect.innerHTML = '<option value="">-- 正在加载设备列表... --</option>';
        credentialSelect.innerHTML = '<option value="">-- 正在加载凭据列表... --</option>';
        
        // 如果有缓存数据，优先使用缓存
        if (window.cachedDevices && window.cachedDevices.length > 0) {
            this.updateDeviceSelectOptions(deviceSelect, window.cachedDevices);
        }
        
        if (window.cachedCredentials && window.cachedCredentials.length > 0) {
            this.updateCredentialSelectOptions(credentialSelect, window.cachedCredentials);
        }
        
        // 无论是否有缓存，都重新请求最新数据
        // 加载设备列表
        console.log('正在加载设备列表...');
        fetch('/api/devices')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP错误 ${response.status}`);
                }
                return response.json();
            })
            .then(devices => {
                console.log('设备列表加载成功:', devices);
                window.cachedDevices = devices; // 更新缓存
                this.updateDeviceSelectOptions(deviceSelect, devices);
            })
            .catch(error => {
                console.error('加载设备列表失败:', error);
                if (!window.cachedDevices || window.cachedDevices.length === 0) {
                    deviceSelect.innerHTML = '<option value="">-- 加载设备列表失败 --</option>';
                    alert('加载设备列表失败: ' + error.message);
                }
            });
        
        // 加载凭据列表
        console.log('正在加载凭据列表...');
        fetch('/api/credentials')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP错误 ${response.status}`);
                }
                return response.json();
            })
            .then(credentials => {
                console.log('凭据列表加载成功:', credentials);
                window.cachedCredentials = credentials; // 更新缓存
                this.updateCredentialSelectOptions(credentialSelect, credentials);
            })
            .catch(error => {
                console.error('加载凭据列表失败:', error);
                if (!window.cachedCredentials || window.cachedCredentials.length === 0) {
                    credentialSelect.innerHTML = '<option value="">-- 加载凭据列表失败 --</option>';
                    alert('加载凭据列表失败: ' + error.message);
                }
            });
        
        // 设备选择变化时更新终端名称默认值
        deviceSelect.addEventListener('change', () => {
            const selectedOption = deviceSelect.selectedOptions[0];
            const terminalNameInput = document.getElementById('terminal-name');
            
            if (selectedOption && selectedOption.value) {
                const deviceName = selectedOption.textContent.split(' ')[0];
                terminalNameInput.value = `${deviceName}-会话`;
            }
        });
    }
    
    // 更新设备选择下拉列表
    updateDeviceSelectOptions(deviceSelect, devices) {
        deviceSelect.innerHTML = '<option value="">-- 请选择设备 --</option>';
        
        if (!devices || devices.length === 0) {
            deviceSelect.innerHTML = '<option value="">-- 没有可用设备 --</option>';
            console.log('没有可用设备');
            return;
        }
        
        devices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.id;
            option.textContent = `${device.name} (${device.ip_address})`;
            deviceSelect.appendChild(option);
        });
    }
    
    // 更新凭据选择下拉列表
    updateCredentialSelectOptions(credentialSelect, credentials) {
        credentialSelect.innerHTML = '<option value="">-- 请选择凭据 --</option>';
        
        if (!credentials || credentials.length === 0) {
            credentialSelect.innerHTML = '<option value="">-- 没有可用凭据 --</option>';
            console.log('没有可用凭据');
            return;
        }
        
        credentials.forEach(credential => {
            const option = document.createElement('option');
            option.value = credential.id;
            option.textContent = `${credential.name} (${credential.username}@${credential.protocol})`;
            credentialSelect.appendChild(option);
        });
    }
    
    // 处理连接设备表单提交
    handleDeviceConnect() {
        const deviceId = document.getElementById('device-select').value;
        const credentialId = document.getElementById('credential-select').value;
        const terminalName = document.getElementById('terminal-name').value;
        
        // 验证表单
        if (!deviceId) {
            alert('请选择设备');
            return;
        }
        
        if (!credentialId) {
            alert('请选择凭据');
            return;
        }
        
        if (!terminalName) {
            alert('请输入终端会话名称');
            return;
        }
        
        // 创建唯一终端ID，确保不重复
        const uniqueId = `terminal-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
        
        // 创建新终端并连接
        const terminalInfo = this.createTerminal(terminalName, deviceId, credentialId);
        
        // 隐藏对话框
        document.getElementById('device-connect-modal').style.display = 'none';
        
        return terminalInfo;
    }
    
    // 连接到设备
    connectToDevice(terminalInfo, deviceId, credentialId) {
        const terminal = terminalInfo.terminal;
        
        // 显示连接中状态
        terminal.writeln('\r\n正在连接到设备，请稍候...\r\n');
        
        // 创建WebSocket连接
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/terminal/${deviceId}/${credentialId}`;
        
        console.log(`连接到WebSocket: ${wsUrl}`);
        
        const socket = new WebSocket(wsUrl);
        terminalInfo.socket = socket;
        terminalInfo.manualClosed = false; // 初始化为非手动关闭
        
        // 确保终端有命令历史相关属性
        if (!terminalInfo.commandHistory) {
            terminalInfo.commandHistory = [];
        }
        if (terminalInfo.historyIndex === undefined) {
            terminalInfo.historyIndex = -1;
        }
        if (!terminalInfo.currentCommand) {
            terminalInfo.currentCommand = '';
        }
        if (terminalInfo.cursorPosition === undefined) {
            terminalInfo.cursorPosition = 0;
        }
        
        // 尝试获取设备类型用于命令补全
        if (deviceId && window.cachedDevices) {
            const deviceInfo = window.cachedDevices.find(d => d.id === deviceId);
            if (deviceInfo && deviceInfo.vendor) {
                terminalInfo.vendorType = deviceInfo.vendor.toLowerCase();
                console.log(`设备厂商类型: ${terminalInfo.vendorType}`);
            }
        }
        
        // 设置WebSocket事件处理器
        this.setupSocketHandlers(terminalInfo, deviceId, credentialId);
        
        // 保存设备连接的信息，用于可能的重连
        terminalInfo.deviceId = deviceId;
        terminalInfo.credentialId = credentialId;
    }
    
    // 设置WebSocket事件处理器（用于初始连接和重连）
    setupSocketHandlers(terminalInfo, deviceId, credentialId) {
        const terminal = terminalInfo.terminal;
        const socket = terminalInfo.socket;
        
        socket.onopen = () => {
            terminal.writeln('WebSocket连接已建立，等待设备响应...\r\n');
            terminalInfo.needReconnect = false; // 连接成功，重置重连标志
            
            // 重置输入状态
            terminalInfo.commandBuffer = '';
            terminalInfo.cursorPosition = 0;
            // 注意：此处不设置inputActive=true，等待收到设备响应后再激活输入
        };
        
        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('收到WebSocket消息:', data.type);
                
                if (data.type === 'output') {
                    // 处理和格式化设备返回的内容
                    let content = data.content || '';

                    // 确保内容有正确的换行格式
                    // 替换所有可能的换行符组合为标准的\r\n
                    content = content.replace(/\r\n|\n\r|\n|\r/g, '\r\n');

                    // 尝试从设备输出中提取提示符
                    // 支持华为设备<xxx>、思科设备xxx#、xxx>等多种格式
                    const promptRegex = /((?:\<[\w\-\u4e00-\u9fa5\s]+\>)|(?:\[[\w\-\u4e00-\u9fa5\s]+\])|(?:[\w\-\u4e00-\u9fa5]+[#>]))(?:\s*)$/;
                    const promptMatch = content.match(promptRegex);
                    if (promptMatch && promptMatch[1]) {
                        // 更新提示符为设备返回的真实提示符
                        terminalInfo.promptText = promptMatch[1];
                        console.log('从设备输出提取提示符:', terminalInfo.promptText);
                    }

                    // 直接输出设备返回的内容，确保不会丢失任何字符
                    terminal.write(content);
                    
                    // 再次激活终端输入
                    terminalInfo.inputActive = true;
                    
                    // 默认光标位置应该在用户输入的末尾
                    terminalInfo.cursorPosition = terminalInfo.commandBuffer.length;
                    console.log('终端输入已激活，命令缓冲区长度:', terminalInfo.commandBuffer.length, '光标位置:', terminalInfo.cursorPosition);
                    
                    // 清除输入超时计时器
                    if (terminalInfo.inputTimeoutId) {
                        clearTimeout(terminalInfo.inputTimeoutId);
                        terminalInfo.inputTimeoutId = null;
                    }
                    
                    // 如果会话管理器存在，更新状态为活跃
                    if (window.sessionManager) {
                        window.sessionManager.updateSessionStatus(terminalInfo.id, 'active');
                    }
                } else if (data.type === 'status') {
                    if (data.connected) {
                        terminal.writeln(`\r\n已连接到设备: ${data.device_name}\r\n`);
                        
                        // 如果后端返回了设备厂商信息，更新用于命令补全
                        if (data.vendor) {
                            terminalInfo.vendorType = data.vendor.toLowerCase();
                            console.log(`从服务器获取设备厂商类型: ${terminalInfo.vendorType}`);
                        }
                        
                        // 设置默认提示符，等待设备输出中提取真实提示符
                        if (data.vendor && data.vendor.toLowerCase() === 'huawei') {
                            terminalInfo.promptText = '<' + data.device_name + '>';
                        } else if (data.vendor && data.vendor.toLowerCase() === 'cisco') {
                            terminalInfo.promptText = data.device_name + '#';
                        } else {
                            // 默认提示符格式
                            terminalInfo.promptText = '<' + data.device_name + '>';
                        }
                        
                        terminalInfo.inputActive = true;
                        terminalInfo.commandBuffer = '';
                        terminalInfo.cursorPosition = 0;
                        console.log('设备已连接，重置命令缓冲区和光标位置');
                        
                        // 移除可能存在的旧输入处理器以避免重复绑定
                        if (terminalInfo.inputHandler) {
                            console.log('重置旧的输入处理器');
                            terminal.onData(() => {}); // 清除旧的处理函数
                        }
                        
                        // 设置终端输入监听
                        terminalInfo.inputHandler = (input) => {
                            if (!terminalInfo.inputActive || socket.readyState !== WebSocket.OPEN) {
                                return;
                            }
                            
                            // 处理上下箭头键
                            if (input === '\x1b[A') {  // 上箭头
                                this.navigateHistory(terminalInfo, 'up');
                                return;
                            } else if (input === '\x1b[B') {  // 下箭头
                                this.navigateHistory(terminalInfo, 'down');
                                return;
                            } else if (input === '\x1b[C') {  // 右箭头
                                this.moveCursor(terminalInfo, 'right');
                                return;
                            } else if (input === '\x1b[D') {  // 左箭头
                                this.moveCursor(terminalInfo, 'left');
                                return;
                            } else if (input === '\t') {  // Tab键 - 处理自动补全
                                this.handleTabCompletion(terminalInfo);
                                return;
                            }
                            
                            // 回车键处理 - 发送完整命令
                            if (input === '\r') {
                                // 重置Tab补全状态
                                terminalInfo.tabMatches = null;
                                terminalInfo.tabIndex = undefined;
                                
                                const command = terminalInfo.commandBuffer;
                                
                                // 添加到历史记录
                                if (command && (terminalInfo.commandHistory.length === 0 || 
                                               terminalInfo.commandHistory[terminalInfo.commandHistory.length - 1] !== command)) {
                                    terminalInfo.commandHistory.push(command);
                                    // 限制历史记录长度
                                    if (terminalInfo.commandHistory.length > 100) {
                                        terminalInfo.commandHistory.shift();
                                    }
                                }
                                // 重置历史索引
                                terminalInfo.historyIndex = -1;
                                terminalInfo.currentCommand = '';
                                terminalInfo.cursorPosition = 0;
                                
                                // 发送当前缓冲区的命令并清空缓冲区
                                socket.send(JSON.stringify({
                                    type: 'input',
                                    content: terminalInfo.commandBuffer + '\n'
                                }));
                                
                                // 写入换行符，但不再写入提示符，后端会发送提示符
                                terminal.write('\r\n');
                                
                                // 清空命令缓冲区
                                terminalInfo.commandBuffer = '';
                                
                                // 暂时禁用输入，直到收到新的数据
                                terminalInfo.inputActive = false;
                                
                                // 添加超时自动重新激活输入
                                if (terminalInfo.inputTimeoutId) {
                                    clearTimeout(terminalInfo.inputTimeoutId);
                                }
                                
                                terminalInfo.inputTimeoutId = setTimeout(() => {
                                    if (!terminalInfo.inputActive && socket.readyState === WebSocket.OPEN) {
                                        console.log('命令输入超时未收到响应，自动激活输入');
                                        terminalInfo.inputActive = true;
                                    }
                                }, 10000);
                            } 
                            // 退格键处理
                            else if (input === '\x7F') {
                                if (terminalInfo.commandBuffer.length > 0 && terminalInfo.cursorPosition > 0) {
                                    // 重置Tab补全状态
                                    terminalInfo.tabMatches = null;
                                    terminalInfo.tabIndex = undefined;
                                    
                                    // 在光标位置删除字符
                                    const before = terminalInfo.commandBuffer.substring(0, terminalInfo.cursorPosition - 1);
                                    const after = terminalInfo.commandBuffer.substring(terminalInfo.cursorPosition);
                                    terminalInfo.commandBuffer = before + after;
                                    terminalInfo.cursorPosition--;
                                    
                                    // 重新绘制整行
                                    terminal.write('\b \b'); // 删除光标前的字符
                                    
                                    // 如果光标不在行尾，需要重新绘制整个命令
                                    if (terminalInfo.cursorPosition < terminalInfo.commandBuffer.length) {
                                        // 将光标移回行首
                                        terminal.write('\b'.repeat(terminalInfo.cursorPosition));
                                        
                                        // 清空整行
                                        terminal.write(' '.repeat(terminalInfo.commandBuffer.length + 1));
                                        terminal.write('\b'.repeat(terminalInfo.commandBuffer.length + 1));
                                        
                                        // 写入新命令
                                        terminal.write(terminalInfo.commandBuffer);
                                        
                                        // 将光标移动到新位置
                                        terminal.write('\b'.repeat(terminalInfo.commandBuffer.length - terminalInfo.cursorPosition));
                                    }
                                }
                            }
                            // CTRL+C 处理
                            else if (input === '\x03') {
                                terminal.write('^C');
                                socket.send(JSON.stringify({
                                    type: 'input',
                                    content: '\x03'
                                }));
                                terminalInfo.commandBuffer = '';
                                terminalInfo.cursorPosition = 0;  // 重置光标位置
                            }
                            // CTRL+D 处理
                            else if (input === '\x04') {
                                socket.send(JSON.stringify({
                                    type: 'input',
                                    content: '\x04'
                                }));
                            }
                            // 普通字符处理
                            else {
                                // 重置Tab补全状态
                                terminalInfo.tabMatches = null;
                                terminalInfo.tabIndex = undefined;
                                
                                // 在光标位置插入字符
                                const before = terminalInfo.commandBuffer.substring(0, terminalInfo.cursorPosition);
                                const after = terminalInfo.commandBuffer.substring(terminalInfo.cursorPosition);
                                terminalInfo.commandBuffer = before + input + after;
                                terminalInfo.cursorPosition++;
                                
                                // 如果光标在行尾，直接写入字符
                                if (terminalInfo.cursorPosition === terminalInfo.commandBuffer.length) {
                                    terminal.write(input); // 回显输入的字符
                                } else {
                                    // 否则，需要重新绘制光标后的所有字符
                                    terminal.write(input + after);
                                    
                                    // 将光标移回到正确位置
                                    terminal.write('\b'.repeat(after.length));
                                }
                            }
                        };
                        terminal.onData(terminalInfo.inputHandler);
                    } else {
                        terminal.writeln(`\r\n连接状态: ${data.message || '未知'}\r\n`);
                    }
                } else if (data.type === 'error') {
                    terminal.writeln(`\r\n错误: ${data.message}\r\n`);
                    
                    // 如果是连接错误，可以考虑激活输入，避免终端卡死
                    if (data.message.includes('连接断开') || data.message.includes('ScrapliConnectionNotOpened')) {
                        terminal.writeln('检测到连接问题，服务器正在尝试重新连接...\r\n');
                        terminalInfo.inputActive = false;
                    }
                    
                    // 如果会话管理器存在，更新状态为错误
                    if (window.sessionManager) {
                        window.sessionManager.updateSessionStatus(terminalInfo.id, 'error');
                    }
                }
            } catch (e) {
                // 如果不是JSON格式，确保直接输出也有正确的换行
                let output = event.data;
                if (typeof output === 'string') {
                    output = output.replace(/\r\n|\n\r|\n|\r/g, '\r\n');
                }
                terminal.write(output);
            }
        };
        
        socket.onclose = (event) => {
            console.log(`WebSocket连接关闭，代码: ${event.code}，原因: ${event.reason || '未提供'}`);
            terminal.writeln('\r\n连接已关闭\r\n');
            terminalInfo.inputActive = false;
            
            // 如果会话管理器存在，更新状态为断开
            if (window.sessionManager) {
                window.sessionManager.updateSessionStatus(terminalInfo.id, 'disconnected');
            }
            
            // 设置标志，表示需要重新连接
            terminalInfo.needReconnect = true;
            
            // 如果不是用户主动关闭，尝试自动重连
            if (!terminalInfo.manualClosed) {
                terminal.writeln('将在5秒后尝试重新连接...\r\n');
                
                // 清除之前的重连定时器
                if (terminalInfo.reconnectTimer) {
                    clearTimeout(terminalInfo.reconnectTimer);
                }
                
                // 设置延迟重连
                terminalInfo.reconnectTimer = setTimeout(() => {
                    if (terminalInfo.needReconnect) {
                        terminal.writeln('正在尝试重新连接...\r\n');
                        // 重新创建WebSocket连接
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        const wsUrl = `${protocol}//${window.location.host}/ws/terminal/${deviceId}/${credentialId}`;
                        terminalInfo.socket = new WebSocket(wsUrl);
                        
                        // 重新绑定事件处理器
                        this.setupSocketHandlers(terminalInfo, deviceId, credentialId);
                    }
                }, 5000);
            }
        };
        
        socket.onerror = (error) => {
            terminal.writeln(`\r\n连接错误: ${error.message || '未知错误'}\r\n`);
            console.error('WebSocket错误:', error);
            terminalInfo.inputActive = false;
            
            // 如果会话管理器存在，更新状态为错误
            if (window.sessionManager) {
                window.sessionManager.updateSessionStatus(terminalInfo.id, 'error');
            }
        };
    }

    // 手动重新连接当前活动终端
    reconnectActiveTerminal() {
        if (!this.activeTerminalId) {
            console.log('没有活动的终端会话');
            return;
        }

        const terminalInfo = this.getTerminalById(this.activeTerminalId);
        if (!terminalInfo) {
            console.log('找不到活动终端信息');
            return;
        }

        // 检查终端是否已连接到设备
        if (!terminalInfo.deviceId || !terminalInfo.credentialId) {
            console.log('此终端未连接到任何设备');
            terminalInfo.terminal.writeln('\r\n请先使用"连接设备"按钮连接到网络设备\r\n');
            return;
        }

        // 关闭现有WebSocket连接
        if (terminalInfo.socket) {
            // 标记为手动重连，不是手动关闭
            terminalInfo.manualClosed = false;
            terminalInfo.needReconnect = true;
            
            // 关闭现有连接
            if (terminalInfo.socket.readyState === WebSocket.OPEN || 
                terminalInfo.socket.readyState === WebSocket.CONNECTING) {
                terminalInfo.socket.close();
            }
        }

        // 清除所有计时器
        if (terminalInfo.reconnectTimer) {
            clearTimeout(terminalInfo.reconnectTimer);
            terminalInfo.reconnectTimer = null;
        }
        
        if (terminalInfo.inputTimeoutId) {
            clearTimeout(terminalInfo.inputTimeoutId);
            terminalInfo.inputTimeoutId = null;
        }

        // 重置终端状态
        terminalInfo.commandBuffer = '';
        terminalInfo.cursorPosition = 0;
        terminalInfo.inputActive = false; // 初始状态设为不接收输入，连接成功后会自动激活

        // 向用户显示正在重新连接的消息
        terminalInfo.terminal.writeln('\r\n正在手动重新连接设备...\r\n');

        // 重新连接到设备
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/terminal/${terminalInfo.deviceId}/${terminalInfo.credentialId}`;
        
        console.log(`正在重新连接WebSocket: ${wsUrl}`);
        
        // 创建新的WebSocket连接
        const newSocket = new WebSocket(wsUrl);
        terminalInfo.socket = newSocket;
        
        // 备份当前对象的引用
        const self = this;
        const terminal = terminalInfo.terminal;
        
        // 为新连接设置事件处理器
        newSocket.onopen = function() {
            console.log('重新连接成功，等待设备响应');
            terminal.writeln('\r\n重新连接成功，等待设备响应...\r\n');
            terminalInfo.needReconnect = false;
            
            // 初始化状态
            terminalInfo.inputActive = false;
            terminalInfo.commandBuffer = '';
            terminalInfo.cursorPosition = 0;
            
            // 给设备响应一些时间，然后手动激活输入
            setTimeout(() => {
                terminalInfo.inputActive = true;
                console.log('手动激活输入状态');
                terminal.writeln('\r\n输入已激活，可以开始输入命令\r\n');
            }, 2000);
        };
        
        newSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('收到消息类型:', data.type);
                
                if (data.type === 'output') {
                    // 处理和格式化设备返回的内容
                    let content = data.content || '';
                    content = content.replace(/\r\n|\n\r|\n|\r/g, '\r\n');
                    terminal.write(content);
                    
                    // 激活输入
                    terminalInfo.inputActive = true;
                    terminalInfo.cursorPosition = terminalInfo.commandBuffer.length;
                    
                } else if (data.type === 'status') {
                    if (data.connected) {
                        terminal.writeln(`\r\n已连接到设备: ${data.device_name}\r\n`);
                        terminalInfo.inputActive = true;
                        
                        // 如果没有输入处理函数，则设置一个
                        if (!terminalInfo.inputHandler) {
                            self.setupInputHandler(terminalInfo);
                        }
                    } else {
                        terminal.writeln(`\r\n连接状态: ${data.message || '未知'}\r\n`);
                    }
                } else if (data.type === 'error') {
                    terminal.writeln(`\r\n错误: ${data.message}\r\n`);
                }
            } catch (e) {
                // 如果不是JSON格式，直接输出
                let output = event.data;
                if (typeof output === 'string') {
                    output = output.replace(/\r\n|\n\r|\n|\r/g, '\r\n');
                }
                terminal.write(output);
            }
        };
        
        newSocket.onclose = (event) => {
            console.log(`WebSocket连接关闭，代码: ${event.code}`);
            terminal.writeln('\r\n连接已关闭\r\n');
            terminalInfo.inputActive = false;
            
            // 如果会话管理器存在，更新状态为断开
            if (window.sessionManager) {
                window.sessionManager.updateSessionStatus(terminalInfo.id, 'disconnected');
            }
        };
        
        newSocket.onerror = (error) => {
            terminal.writeln(`\r\n连接错误\r\n`);
            console.error('WebSocket错误:', error);
            terminalInfo.inputActive = false;
        };
        
        // 确保有输入处理函数
        this.setupInputHandler(terminalInfo);
        
        // 如果会话管理器存在，更新状态为连接中
        if (window.sessionManager) {
            window.sessionManager.updateSessionStatus(terminalInfo.id, 'connecting');
        }
    }
    
    // 设置输入处理函数
    setupInputHandler(terminalInfo) {
        if (!terminalInfo || !terminalInfo.terminal) return;
        
        const terminal = terminalInfo.terminal;
        const socket = terminalInfo.socket;
        
        // 先移除可能存在的旧处理函数
        terminal.onData(() => {});
        
        // 设置新的输入处理函数
        terminalInfo.inputHandler = (input) => {
            if (!terminalInfo.inputActive || (socket && socket.readyState !== WebSocket.OPEN)) {
                return;
            }
            
            // 处理上下箭头键
            if (input === '\x1b[A') {  // 上箭头
                this.navigateHistory(terminalInfo, 'up');
                return;
            } else if (input === '\x1b[B') {  // 下箭头
                this.navigateHistory(terminalInfo, 'down');
                return;
            } else if (input === '\x1b[C') {  // 右箭头
                this.moveCursor(terminalInfo, 'right');
                return;
            } else if (input === '\x1b[D') {  // 左箭头
                this.moveCursor(terminalInfo, 'left');
                return;
            } else if (input === '\t') {  // Tab键 - 处理自动补全
                this.handleTabCompletion(terminalInfo);
                return;
            }
            
            // 回车键处理
            if (input === '\r') {
                // 重置Tab补全状态
                terminalInfo.tabMatches = null;
                terminalInfo.tabIndex = undefined;
                
                const command = terminalInfo.commandBuffer;
                
                // 添加到历史记录
                if (command && (terminalInfo.commandHistory.length === 0 || 
                               terminalInfo.commandHistory[terminalInfo.commandHistory.length - 1] !== command)) {
                    terminalInfo.commandHistory.push(command);
                    if (terminalInfo.commandHistory.length > 100) {
                        terminalInfo.commandHistory.shift();
                    }
                }
                
                // 重置状态
                terminalInfo.historyIndex = -1;
                terminalInfo.currentCommand = '';
                terminalInfo.cursorPosition = 0;
                
                // 发送命令
                socket.send(JSON.stringify({
                    type: 'input',
                    content: command + '\n'
                }));
                
                // 写入换行并禁用输入直到收到响应
                terminal.write('\r\n');
                terminalInfo.commandBuffer = '';
                terminalInfo.inputActive = false;
                
                // 防止超时
                if (terminalInfo.inputTimeoutId) {
                    clearTimeout(terminalInfo.inputTimeoutId);
                }
                
                terminalInfo.inputTimeoutId = setTimeout(() => {
                    if (!terminalInfo.inputActive && socket.readyState === WebSocket.OPEN) {
                        terminalInfo.inputActive = true;
                    }
                }, 10000);
                
                return;
            }
            
            // 退格键处理
            if (input === '\x7F') {
                if (terminalInfo.commandBuffer.length > 0 && terminalInfo.cursorPosition > 0) {
                    // 重置Tab补全状态
                    terminalInfo.tabMatches = null;
                    terminalInfo.tabIndex = undefined;
                    
                    // 在光标位置删除字符
                    const before = terminalInfo.commandBuffer.substring(0, terminalInfo.cursorPosition - 1);
                    const after = terminalInfo.commandBuffer.substring(terminalInfo.cursorPosition);
                    terminalInfo.commandBuffer = before + after;
                    terminalInfo.cursorPosition--;
                    
                    // 重新绘制整行
                    terminal.write('\b \b'); // 删除光标前的字符
                    
                    // 如果光标不在行尾，重绘命令
                    if (terminalInfo.cursorPosition < terminalInfo.commandBuffer.length) {
                        terminal.write('\b'.repeat(terminalInfo.cursorPosition));
                        terminal.write(' '.repeat(terminalInfo.commandBuffer.length + 1));
                        terminal.write('\b'.repeat(terminalInfo.commandBuffer.length + 1));
                        terminal.write(terminalInfo.commandBuffer);
                        terminal.write('\b'.repeat(terminalInfo.commandBuffer.length - terminalInfo.cursorPosition));
                    }
                }
                return;
            }
            
            // CTRL+C 处理
            if (input === '\x03') {
                // 重置Tab补全状态
                terminalInfo.tabMatches = null;
                terminalInfo.tabIndex = undefined;
                
                terminal.write('^C');
                socket.send(JSON.stringify({
                    type: 'input',
                    content: '\x03'
                }));
                terminalInfo.commandBuffer = '';
                terminalInfo.cursorPosition = 0;
                return;
            }
            
            // CTRL+D 处理
            if (input === '\x04') {
                // 重置Tab补全状态
                terminalInfo.tabMatches = null;
                terminalInfo.tabIndex = undefined;
                
                socket.send(JSON.stringify({
                    type: 'input',
                    content: '\x04'
                }));
                return;
            }
            
            // 普通字符处理
            // 重置Tab补全状态
            terminalInfo.tabMatches = null;
            terminalInfo.tabIndex = undefined;
            
            const before = terminalInfo.commandBuffer.substring(0, terminalInfo.cursorPosition);
            const after = terminalInfo.commandBuffer.substring(terminalInfo.cursorPosition);
            terminalInfo.commandBuffer = before + input + after;
            terminalInfo.cursorPosition++;
            
            // 如果光标在行尾，直接写入
            if (terminalInfo.cursorPosition === terminalInfo.commandBuffer.length) {
                terminal.write(input);
            } else {
                // 否则重绘光标后的内容
                terminal.write(input + after);
                terminal.write('\b'.repeat(after.length));
            }
        };
        
        // 绑定处理函数
        terminal.onData(terminalInfo.inputHandler);
        console.log('已设置终端输入处理函数，包含命令自动补全功能');
    }
    
    // 自动补全相关方法
    
    // 根据当前输入查找匹配的命令
    findMatchingCommands(terminalInfo, input) {
        const vendorType = terminalInfo.vendorType || 'common';
        let commandList = [];
        
        // 基于设备类型选择命令列表
        if (vendorType === 'cisco') {
            commandList = [...this.commonCommands.cisco, ...this.commonCommands.common];
        } else if (vendorType === 'huawei') {
            commandList = [...this.commonCommands.huawei, ...this.commonCommands.common];
        } else {
            commandList = this.commonCommands.common;
        }
        
        // 查找匹配的命令
        if (input) {
            return commandList.filter(cmd => cmd.startsWith(input));
        } else {
            return [];
        }
    }
    
    // 处理Tab键自动补全
    handleTabCompletion(terminalInfo) {
        const terminal = terminalInfo.terminal;
        const input = terminalInfo.commandBuffer;
        
        // 如果已经有匹配列表并再次按Tab，则循环选择下一个
        if (terminalInfo.tabMatches && terminalInfo.tabMatches.length > 1 && terminalInfo.tabIndex !== undefined) {
            // 移到下一个匹配项，如果到末尾则循环到开头
            terminalInfo.tabIndex = (terminalInfo.tabIndex + 1) % terminalInfo.tabMatches.length;
            
            // 清除当前输入并显示新选择的命令
            const newCommand = terminalInfo.tabMatches[terminalInfo.tabIndex];
            
            // 计算需要退格的数量 - 当前缓冲区长度
            const backspaces = terminalInfo.commandBuffer.length;
            
            if (backspaces > 0) {
                // 清除当前行
                terminal.write('\b'.repeat(backspaces) + ' '.repeat(backspaces) + '\b'.repeat(backspaces));
            }
            
            // 写入新命令
            terminal.write(newCommand);
            terminalInfo.commandBuffer = newCommand;
            terminalInfo.cursorPosition = newCommand.length;
            
            return;
        }
        
        // 第一次按Tab键或没有匹配列表时执行初始匹配
        const matches = this.findMatchingCommands(terminalInfo, input);
        
        if (matches.length === 0) {
            // 没有匹配项，不做任何操作
            return;
        } else if (matches.length === 1) {
            // 只有一个匹配项，直接补全
            const completion = matches[0].substring(input.length);
            if (completion) {
                // 更新命令缓冲区和光标位置
                terminalInfo.commandBuffer = matches[0];
                terminalInfo.cursorPosition = matches[0].length;
                
                // 更新显示
                terminal.write(completion);
            }
            
            // 清除任何现有的tab匹配状态
            terminalInfo.tabMatches = null;
            terminalInfo.tabIndex = undefined;
        } else {
            // 多个匹配项，显示所有可能性
            terminal.writeln('');
            
            // 计算最长命令的长度，用于格式化输出
            const maxLength = Math.max(...matches.map(cmd => cmd.length)) + 2;
            const termWidth = terminal.cols;
            const itemsPerRow = Math.floor(termWidth / maxLength) || 1;
            
            // 分行显示匹配项
            let line = '';
            for (let i = 0; i < matches.length; i++) {
                const paddedCommand = matches[i].padEnd(maxLength);
                line += paddedCommand;
                
                if ((i + 1) % itemsPerRow === 0 || i === matches.length - 1) {
                    terminal.writeln(line);
                    line = '';
                }
            }
            
            // 保存匹配列表，并设置当前索引为0（选择第一个匹配项）
            terminalInfo.tabMatches = matches;
            terminalInfo.tabIndex = 0;
            
            // 清除旧命令并显示第一个匹配项
            const firstMatch = matches[0];
            
            // 重新显示提示符 - 使用设备提供的提示符或默认提示符
            const promptText = terminalInfo.promptText || '[MCP]>';
            terminal.write(promptText);
            
            // 写入第一个匹配项作为新命令
            terminal.write(firstMatch);
            terminalInfo.commandBuffer = firstMatch;
            terminalInfo.cursorPosition = firstMatch.length;
        }
    }
}

// 原本在这里自动创建实例的代码已移除，改为在页面加载时统一创建 