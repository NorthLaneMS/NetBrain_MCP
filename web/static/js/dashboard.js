/**
 * 仪表盘功能模块
 * 提供主题切换、数据统计、系统状态监控等功能
 */

class DashboardManager {
    constructor() {
        this.refreshInterval = null;
        this.timeInterval = null;
        this.activities = [];
        this.lastDataSnapshot = null;
        
        this.init();
    }
    
    /**
     * 初始化仪表盘
     */
    init() {
        console.log('初始化仪表盘管理器...');
        
        // 初始化主题切换器
        this.initializeThemeSwitcher();
        
        // 更新当前时间
        this.updateCurrentTime();
        this.timeInterval = setInterval(() => this.updateCurrentTime(), 1000);
        
        // 加载仪表盘数据
        this.loadDashboardData();
        
        // 绑定仪表盘事件
        this.bindEvents();
        
        // 添加活动记录
        this.addActivity('仪表盘初始化成功', 'success');
        
        // 设置自动刷新（30秒）
        this.refreshInterval = setInterval(() => this.loadDashboardData(), 30000);
    }
    
    /**
     * 主题切换器初始化
     */
    initializeThemeSwitcher() {
        const themeToggle = document.getElementById('theme-toggle');
        if (!themeToggle) {
            console.warn('主题切换器元素未找到');
            return;
        }
        
        // 获取保存的主题或使用默认主题
        const currentTheme = localStorage.getItem('theme') || 'light';
        console.log('当前主题:', currentTheme);
        
        // 应用主题
        this.applyTheme(currentTheme);
        
        // 设置切换器状态
        themeToggle.checked = currentTheme === 'dark';
        
        // 监听主题切换事件
        themeToggle.addEventListener('change', (event) => {
            const newTheme = event.target.checked ? 'dark' : 'light';
            console.log('切换主题到:', newTheme);
            
            this.applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
            
            // 添加活动记录
            this.addActivity(`切换到${newTheme === 'dark' ? '暗色' : '明亮'}主题`, 'info');
        });
        
        console.log('主题切换器初始化完成');
    }
    
    /**
     * 应用主题
     */
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // 更新元标签以支持系统主题
        let themeColorMeta = document.querySelector('meta[name="theme-color"]');
        if (!themeColorMeta) {
            themeColorMeta = document.createElement('meta');
            themeColorMeta.name = 'theme-color';
            document.head.appendChild(themeColorMeta);
        }
        
        // 根据主题设置元标签颜色
        if (theme === 'dark') {
            themeColorMeta.content = '#1e293b';
        } else {
            themeColorMeta.content = '#ffffff';
        }
        
        console.log(`主题 ${theme} 已应用`);
    }
    
    /**
     * 更新当前时间
     */
    updateCurrentTime() {
        const now = new Date();
        const timeString = now.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const currentTimeElement = document.getElementById('current-time');
        if (currentTimeElement) {
            currentTimeElement.textContent = timeString;
        }
    }
    
    /**
     * 加载仪表盘数据
     */
    async loadDashboardData() {
        try {
            console.log('开始加载仪表盘数据...');
            
            // 显示加载状态
            this.setLoadingState(true);
            
            // 并行加载各种数据
            const [devices, topology, credentials, activeConnections, terminalSessions] = await Promise.all([
                this.fetchWithFallback('/api/devices', []),
                this.fetchWithFallback('/api/topology', { nodes: {}, links: [] }),
                this.fetchWithFallback('/api/credentials', []),
                this.getActiveSessions(),
                this.getTerminalSessions()
            ]);
            
            console.log('数据加载完成:', {
                devices: devices.length,
                topology: Object.keys(topology.nodes || {}).length,
                credentials: credentials.length,
                activeConnections: activeConnections.length,
                terminalSessions: terminalSessions.length
            });
            
            // 检测数据变化
            const currentSnapshot = {
                devicesCount: devices.length,
                topologyCount: Object.keys(topology.nodes || {}).length,
                credentialsCount: credentials.length,
                connectionsCount: activeConnections.length,
                sessionsCount: terminalSessions.length
            };
            
            // 如果有数据变化，记录活动
            if (this.lastDataSnapshot) {
                this.detectDataChanges(this.lastDataSnapshot, currentSnapshot);
            }
            
            this.lastDataSnapshot = currentSnapshot;
            
            // 更新统计数据
            this.updateDashboardStats(devices, topology, credentials, activeConnections, terminalSessions);
            
            // 更新设备概览
            this.updateDevicesOverview(devices);
            
            // 检查系统状态
            await this.checkSystemStatus();
            
        } catch (error) {
            console.error('加载仪表盘数据失败:', error);
            this.addActivity('加载仪表盘数据失败', 'error');
        } finally {
            this.setLoadingState(false);
        }
    }
    
    /**
     * 检测数据变化
     */
    detectDataChanges(oldSnapshot, newSnapshot) {
        if (newSnapshot.devicesCount !== oldSnapshot.devicesCount) {
            const change = newSnapshot.devicesCount - oldSnapshot.devicesCount;
            this.addActivity(`设备数量${change > 0 ? '增加' : '减少'}${Math.abs(change)}个`, change > 0 ? 'success' : 'warning');
        }
        
        if (newSnapshot.topologyCount !== oldSnapshot.topologyCount) {
            const change = newSnapshot.topologyCount - oldSnapshot.topologyCount;
            this.addActivity(`拓扑节点${change > 0 ? '增加' : '减少'}${Math.abs(change)}个`, 'info');
        }
        
        if (newSnapshot.credentialsCount !== oldSnapshot.credentialsCount) {
            const change = newSnapshot.credentialsCount - oldSnapshot.credentialsCount;
            this.addActivity(`凭据${change > 0 ? '增加' : '减少'}${Math.abs(change)}个`, 'info');
        }
        
        if (newSnapshot.connectionsCount !== oldSnapshot.connectionsCount) {
            const change = newSnapshot.connectionsCount - oldSnapshot.connectionsCount;
            this.addActivity(`活跃连接${change > 0 ? '增加' : '减少'}${Math.abs(change)}个`, change > 0 ? 'success' : 'info');
        }
        
        if (newSnapshot.sessionsCount !== oldSnapshot.sessionsCount) {
            const change = newSnapshot.sessionsCount - oldSnapshot.sessionsCount;
            this.addActivity(`终端会话${change > 0 ? '增加' : '减少'}${Math.abs(change)}个`, change > 0 ? 'success' : 'info');
        }
    }
    
    /**
     * 获取活跃会话数
     */
    async getActiveSessions() {
        try {
            // 首先尝试从后端API获取活跃连接
            const response = await fetch('/api/connections/active');
            if (response.ok) {
                const connections = await response.json();
                return connections || [];
            }
        } catch (error) {
            console.warn('无法从API获取活跃连接:', error);
        }
        
        // 从全局会话管理器获取活跃会话
        if (window.sessionManager && window.sessionManager.activeSessions) {
            return Object.keys(window.sessionManager.activeSessions);
        }
        
        // 从终端管理器获取
        if (window.terminalManager && window.terminalManager.terminals) {
            return Object.keys(window.terminalManager.terminals);
        }
        
        return [];
    }
    
    /**
     * 获取真正的终端会话数
     */
    async getTerminalSessions() {
        try {
            // 尝试从终端管理器获取
            if (window.terminalManager && window.terminalManager.terminals) {
                return Object.keys(window.terminalManager.terminals);
            }
            
            // 尝试从会话管理器获取
            if (window.sessionManager && window.sessionManager.activeSessions) {
                return Object.keys(window.sessionManager.activeSessions);
            }
            
            // 尝试从DOM获取终端标签页数量
            const terminalTabs = document.querySelectorAll('.terminal-tab');
            if (terminalTabs.length > 0) {
                return Array.from(terminalTabs).map((tab, index) => `terminal-${index}`);
            }
            
            return [];
        } catch (error) {
            console.warn('获取终端会话失败:', error);
            return [];
        }
    }
    
    /**
     * 带回退的网络请求
     */
    async fetchWithFallback(url, fallback) {
        try {
            const response = await fetch(url);
            if (response.ok) {
                const data = await response.json();
                console.log(`API ${url} 请求成功:`, data);
                return data;
            } else {
                console.warn(`API ${url} 请求失败 (${response.status}):`, response.statusText);
                return fallback;
            }
        } catch (error) {
            console.warn(`API ${url} 请求异常:`, error);
            return fallback;
        }
    }
    
    /**
     * 设置加载状态
     */
    setLoadingState(loading) {
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            if (loading) {
                refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 加载中';
                refreshBtn.disabled = true;
            } else {
                refreshBtn.innerHTML = '<i class="fas fa-sync"></i> 刷新';
                refreshBtn.disabled = false;
            }
        }
    }
    
    /**
     * 更新仪表盘统计数据
     */
    updateDashboardStats(devices, topology, credentials, activeConnections, terminalSessions) {
        // 设备数量
        const devicesCount = devices.length;
        this.updateStatCard('dashboard-devices-count', devicesCount);
        this.updateStatChange('dashboard-devices-change', `+${devicesCount}`);
        
        // 活跃连接数（会话数）
        const connectionsCount = activeConnections.length;
        this.updateStatCard('dashboard-connections-count', connectionsCount);
        this.updateStatChange('dashboard-connections-change', connectionsCount > 0 ? `+${connectionsCount}` : '0');
        
        // 拓扑节点数
        const topologyNodes = topology.nodes ? Object.keys(topology.nodes).length : 0;
        this.updateStatCard('dashboard-topology-nodes', topologyNodes);
        this.updateStatChange('dashboard-topology-change', `+${topologyNodes}`);
        
        // 终端会话数（修正：之前错误地显示凭据数量）
        const sessionsCount = terminalSessions.length;
        this.updateStatCard('dashboard-sessions-count', sessionsCount);
        this.updateStatChange('dashboard-sessions-change', `+${sessionsCount}`);
    }
    
    /**
     * 更新统计卡片的数值
     */
    updateStatCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            const currentValue = parseInt(element.textContent) || 0;
            const targetValue = parseInt(value) || 0;
            
            if (currentValue !== targetValue) {
                this.animateNumber(element, currentValue, targetValue, 500);
            }
        }
    }
    
    /**
     * 更新统计变化指示器
     */
    updateStatChange(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            
            // 根据值设置样式
            element.className = 'stat-change';
            if (value.startsWith('+') && value !== '+0') {
                element.classList.add('positive');
            } else if (value.startsWith('-')) {
                element.classList.add('negative');
            } else {
                element.classList.add('neutral');
            }
        }
    }
    
    /**
     * 数字动画效果
     */
    animateNumber(element, start, end, duration) {
        const startTime = performance.now();
        
        const updateNumber = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // 使用缓动函数
            const easedProgress = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (end - start) * easedProgress);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            }
        };
        
        requestAnimationFrame(updateNumber);
    }
    
    /**
     * 更新设备概览
     */
    updateDevicesOverview(devices) {
        const devicesOverview = document.getElementById('devices-overview');
        if (!devicesOverview) return;
        
        if (!devices || devices.length === 0) {
            devicesOverview.innerHTML = `
                <div class="no-devices">
                    <i class="fas fa-server"></i>
                    <p>暂无设备</p>
                    <button class="btn btn-sm" onclick="dashboardManager.goToDevices()">
                        <i class="fas fa-plus"></i> 添加设备
                    </button>
                </div>
            `;
            return;
        }
        
        // 显示前5个设备
        const displayDevices = devices.slice(0, 5);
        const deviceItems = displayDevices.map(device => `
            <div class="device-overview-item" onclick="dashboardManager.goToDevices('${device.id}')" title="点击查看设备详情">
                <div class="device-overview-icon">
                    <i class="fas fa-${this.getDeviceIcon(device.device_type)}"></i>
                </div>
                <div class="device-overview-info">
                    <div class="device-overview-name">${device.name}</div>
                    <div class="device-overview-details">${device.ip_address} • ${this.getVendorDisplayName(device.vendor)}</div>
                </div>
                <div class="device-overview-status ${device.status || 'unknown'}" title="状态: ${this.getStatusDisplayName(device.status)}"></div>
            </div>
        `).join('');
        
        devicesOverview.innerHTML = deviceItems;
        
        // 如果设备数量超过5个，显示"查看更多"
        if (devices.length > 5) {
            devicesOverview.innerHTML += `
                <div class="device-overview-item" onclick="dashboardManager.goToDevices()" style="cursor: pointer;" title="查看所有设备">
                    <div class="device-overview-icon">
                        <i class="fas fa-ellipsis-h"></i>
                    </div>
                    <div class="device-overview-info">
                        <div class="device-overview-name">查看更多</div>
                        <div class="device-overview-details">还有 ${devices.length - 5} 个设备</div>
                    </div>
                    <div class="device-overview-status more-indicator"></div>
                </div>
            `;
        }
    }
    
    /**
     * 获取设备图标
     */
    getDeviceIcon(deviceType) {
        const icons = {
            router: 'route',
            switch: 'network-wired',
            firewall: 'shield-alt',
            wireless_controller: 'wifi',
            access_point: 'broadcast-tower',
            load_balancer: 'balance-scale',
            server: 'server'
        };
        return icons[deviceType] || 'server';
    }
    
    /**
     * 获取厂商显示名称
     */
    getVendorDisplayName(vendor) {
        const vendorNames = {
            cisco: 'Cisco',
            huawei: '华为',
            h3c: 'H3C',
            juniper: 'Juniper',
            arista: 'Arista',
            fortinet: 'Fortinet',
            checkpoint: 'CheckPoint',
            other: '其他'
        };
        return vendorNames[vendor] || vendor;
    }
    
    /**
     * 获取状态显示名称
     */
    getStatusDisplayName(status) {
        const statusNames = {
            online: '在线',
            offline: '离线',
            unreachable: '不可达',
            maintenance: '维护中',
            unknown: '未知'
        };
        return statusNames[status] || '未知';
    }
    
    /**
     * 检查系统状态
     */
    async checkSystemStatus() {
        // 检查网络连接
        await this.checkNetworkStatus();
        
        // 检查数据库状态
        await this.checkDatabaseStatus();
    }
    
    /**
     * 检查网络状态
     */
    async checkNetworkStatus() {
        const statusIcon = document.getElementById('network-status');
        const statusText = document.getElementById('network-status-text');
        
        if (!statusIcon || !statusText) return;
        
        try {
            const response = await fetch('/api/devices', { 
                method: 'HEAD',
                signal: AbortSignal.timeout(5000) // 5秒超时
            });
            
            if (response.ok) {
                statusIcon.className = 'status-icon online';
                statusIcon.innerHTML = '<i class="fas fa-wifi"></i>';
                statusText.textContent = '连接正常';
            } else {
                statusIcon.className = 'status-icon warning';
                statusIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                statusText.textContent = '连接异常';
            }
        } catch (error) {
            statusIcon.className = 'status-icon offline';
            statusIcon.innerHTML = '<i class="fas fa-times-circle"></i>';
            statusText.textContent = '连接失败';
            console.error('网络状态检查失败:', error);
        }
    }
    
    /**
     * 检查数据库状态
     */
    async checkDatabaseStatus() {
        const statusIcon = document.getElementById('database-status');
        const statusText = document.getElementById('database-status-text');
        
        if (!statusIcon || !statusText) return;
        
        try {
            // 通过尝试加载设备列表来检查数据库状态
            const response = await fetch('/api/devices', {
                signal: AbortSignal.timeout(3000) // 3秒超时
            });
            
            if (response.ok) {
                statusIcon.className = 'status-icon online';
                statusIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
                statusText.textContent = '正常';
            } else {
                statusIcon.className = 'status-icon warning';
                statusIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                statusText.textContent = '异常';
            }
        } catch (error) {
            statusIcon.className = 'status-icon offline';
            statusIcon.innerHTML = '<i class="fas fa-times-circle"></i>';
            statusText.textContent = '错误';
            console.error('数据库状态检查失败:', error);
        }
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 刷新仪表盘按钮
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDashboardData();
                this.addActivity('手动刷新仪表盘数据', 'info');
            });
        }
    }
    
    /**
     * 添加活动记录
     */
    addActivity(text, type = 'info') {
        const activitiesList = document.getElementById('recent-activities');
        if (!activitiesList) return;
        
        const now = new Date();
        
        // 添加到内部数组
        this.activities.unshift({ text, type, time: now });
        
        // 限制活动数量
        if (this.activities.length > 50) {
            this.activities = this.activities.slice(0, 50);
        }
        
        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';
        activityItem.innerHTML = `
            <div class="activity-icon ${type}">
                <i class="fas fa-${this.getActivityIcon(type)}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-text">${text}</div>
                <div class="activity-time">${this.getRelativeTime(now)}</div>
            </div>
        `;
        
        // 插入到列表顶部
        activitiesList.insertBefore(activityItem, activitiesList.firstChild);
        
        // 限制显示的活动数量（最多保留10条显示）
        const displayedActivities = activitiesList.querySelectorAll('.activity-item');
        if (displayedActivities.length > 10) {
            activitiesList.removeChild(displayedActivities[displayedActivities.length - 1]);
        }
        
        // 定期更新活动时间
        setTimeout(() => this.updateActivityTimes(), 60000);
        
        console.log(`活动记录: ${text} (${type})`);
    }
    
    /**
     * 获取活动图标
     */
    getActivityIcon(type) {
        const icons = {
            info: 'info-circle',
            success: 'check-circle',
            warning: 'exclamation-triangle',
            error: 'times-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    /**
     * 获取相对时间
     */
    getRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (seconds < 60) return '刚刚';
        if (minutes < 60) return `${minutes}分钟前`;
        if (hours < 24) return `${hours}小时前`;
        if (days < 7) return `${days}天前`;
        return date.toLocaleDateString('zh-CN');
    }
    
    /**
     * 更新活动时间显示
     */
    updateActivityTimes() {
        const timeElements = document.querySelectorAll('.activity-time');
        timeElements.forEach((element, index) => {
            if (this.activities[index]) {
                element.textContent = this.getRelativeTime(this.activities[index].time);
            }
        });
    }
    
    /**
     * 导航到设备页面
     */
    goToDevices(deviceId = null) {
        const devicesLink = document.querySelector('.nav-link[data-page="devices"]');
        if (devicesLink) {
            devicesLink.click();
            
            // 如果指定了设备ID，在设备页面高亮该设备
            if (deviceId) {
                setTimeout(() => {
                    const deviceElement = document.getElementById(`device-${deviceId}`);
                    if (deviceElement) {
                        deviceElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        deviceElement.style.backgroundColor = 'var(--primary-color)';
                        deviceElement.style.color = 'white';
                        setTimeout(() => {
                            deviceElement.style.backgroundColor = '';
                            deviceElement.style.color = '';
                        }, 2000);
                    }
                }, 500);
            }
            
            this.addActivity('跳转到设备管理页面', 'info');
        }
    }
    
    /**
     * 刷新系统状态
     */
    refreshSystemStatus() {
        this.checkSystemStatus();
        this.addActivity('刷新系统状态', 'info');
    }
    
    /**
     * 刷新设备概览
     */
    refreshDevicesOverview() {
        this.loadDashboardData();
        this.addActivity('刷新设备概览', 'info');
    }
    
    /**
     * 清空活动记录
     */
    clearActivities() {
        this.activities = [];
        const activitiesList = document.getElementById('recent-activities');
        if (activitiesList) {
            activitiesList.innerHTML = `
                <div class="activity-item">
                    <div class="activity-icon info">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    <div class="activity-content">
                        <div class="activity-text">活动记录已清空</div>
                        <div class="activity-time">刚刚</div>
                    </div>
                </div>
            `;
        }
        console.log('活动记录已清空');
    }
    
    /**
     * 销毁函数
     */
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        if (this.timeInterval) {
            clearInterval(this.timeInterval);
            this.timeInterval = null;
        }
        console.log('仪表盘管理器已销毁');
    }
}

// 全局仪表盘管理器实例
let dashboardManager = null;

// 初始化仪表盘的全局函数
function initializeDashboard() {
    if (!dashboardManager) {
        dashboardManager = new DashboardManager();
        console.log('仪表盘管理器初始化完成');
    }
    return dashboardManager;
}

// 全局快捷函数
function goToDevices(deviceId = null) {
    if (dashboardManager) {
        dashboardManager.goToDevices(deviceId);
    }
}

function refreshSystemStatus() {
    if (dashboardManager) {
        dashboardManager.refreshSystemStatus();
    }
}

function refreshDevicesOverview() {
    if (dashboardManager) {
        dashboardManager.refreshDevicesOverview();
    }
}

function clearActivities() {
    if (dashboardManager) {
        dashboardManager.clearActivities();
    }
}

// 暴露到全局作用域
window.DashboardManager = DashboardManager;
window.initializeDashboard = initializeDashboard;
window.dashboardManager = dashboardManager;
window.goToDevices = goToDevices;
window.refreshSystemStatus = refreshSystemStatus;
window.refreshDevicesOverview = refreshDevicesOverview;
window.clearActivities = clearActivities;

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (dashboardManager) {
        dashboardManager.destroy();
    }
});

// 页面可见性变化时的处理
document.addEventListener('visibilitychange', () => {
    if (dashboardManager) {
        if (document.hidden) {
            console.log('页面隐藏，暂停定时器');
            if (dashboardManager.refreshInterval) {
                clearInterval(dashboardManager.refreshInterval);
                dashboardManager.refreshInterval = null;
            }
        } else {
            console.log('页面可见，恢复定时器');
            if (!dashboardManager.refreshInterval) {
                dashboardManager.refreshInterval = setInterval(() => dashboardManager.loadDashboardData(), 30000);
            }
            // 立即刷新一次数据
            dashboardManager.loadDashboardData();
        }
    }
});

console.log('仪表盘模块已加载'); 