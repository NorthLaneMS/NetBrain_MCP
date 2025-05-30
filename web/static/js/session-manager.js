/**
 * 会话管理器模块
 * 
 * 负责管理设备连接会话，包括保存会话配置、加载会话和会话组管理
 */

class SessionManager {
    constructor() {
        this.activeSessions = {}; // 当前活跃会话
        this.savedSessions = {}; // 保存的会话配置
        this.sessionGroups = {}; // 会话组
        
        // 从本地存储加载保存的会话配置
        this.loadFromStorage();
    }
    
    /**
     * 将会话配置保存到本地存储
     */
    saveToStorage() {
        localStorage.setItem('netbrain_saved_sessions', JSON.stringify(this.savedSessions));
        localStorage.setItem('netbrain_session_groups', JSON.stringify(this.sessionGroups));
    }
    
    /**
     * 从本地存储加载会话配置
     */
    loadFromStorage() {
        try {
            const savedSessions = localStorage.getItem('netbrain_saved_sessions');
            const sessionGroups = localStorage.getItem('netbrain_session_groups');
            
            if (savedSessions) {
                this.savedSessions = JSON.parse(savedSessions);
            }
            
            if (sessionGroups) {
                this.sessionGroups = JSON.parse(sessionGroups);
            }
        } catch (error) {
            console.error('加载会话配置失败:', error);
        }
    }
    
    /**
     * 注册活跃会话
     * @param {string} sessionId 会话ID
     * @param {Object} sessionInfo 会话信息对象
     */
    registerActiveSession(sessionId, sessionInfo) {
        // 检查是否已存在相同的会话
        // 防止重复注册同一个设备和凭据的会话
        if (sessionInfo.deviceId && sessionInfo.credentialId) {
            const existingSessionIds = Object.keys(this.activeSessions);
            
            for (const existingId of existingSessionIds) {
                const existingSession = this.activeSessions[existingId];
                
                // 如果发现相同设备和凭据的活跃会话，则移除旧会话
                if (existingSession.deviceId === sessionInfo.deviceId && 
                    existingSession.credentialId === sessionInfo.credentialId &&
                    existingId !== sessionId) {
                    
                    console.log(`发现重复会话，正在移除旧会话 ${existingId}`);
                    delete this.activeSessions[existingId];
                }
            }
        }
        
        // 注册新会话
        this.activeSessions[sessionId] = {
            ...sessionInfo,
            startTime: sessionInfo.startTime || new Date(),
            status: sessionInfo.status || 'active'
        };
        
        // 输出调试信息
        console.log(`注册会话: ${sessionId}, 当前活跃会话数: ${Object.keys(this.activeSessions).length}`);
        
        this.notifySessionListeners();
    }
    
    /**
     * 注销活跃会话
     * @param {string} sessionId 会话ID
     */
    unregisterActiveSession(sessionId) {
        if (this.activeSessions[sessionId]) {
            delete this.activeSessions[sessionId];
            this.notifySessionListeners();
        }
    }
    
    /**
     * 更新会话状态
     * @param {string} sessionId 会话ID
     * @param {string} status 状态
     */
    updateSessionStatus(sessionId, status) {
        if (this.activeSessions[sessionId]) {
            this.activeSessions[sessionId].status = status;
            this.notifySessionListeners();
        }
    }
    
    /**
     * 保存会话配置
     * @param {string} name 会话名称
     * @param {Object} config 会话配置
     */
    saveSession(name, config) {
        this.savedSessions[name] = {
            ...config,
            createdAt: new Date().toISOString()
        };
        
        this.saveToStorage();
        this.notifySessionListeners();
        return true;
    }
    
    /**
     * 删除保存的会话配置
     * @param {string} name 会话名称
     */
    deleteSession(name) {
        if (this.savedSessions[name]) {
            delete this.savedSessions[name];
            
            // 同时从会话组中移除
            for (const groupName in this.sessionGroups) {
                const group = this.sessionGroups[groupName];
                const index = group.sessions.indexOf(name);
                if (index !== -1) {
                    group.sessions.splice(index, 1);
                }
            }
            
            this.saveToStorage();
            this.notifySessionListeners();
            return true;
        }
        return false;
    }
    
    /**
     * 创建会话组
     * @param {string} groupName 组名称
     * @param {Array} sessions 会话列表
     */
    createSessionGroup(groupName, sessions = []) {
        this.sessionGroups[groupName] = {
            name: groupName,
            sessions: sessions,
            createdAt: new Date().toISOString()
        };
        
        this.saveToStorage();
        this.notifySessionListeners();
        return true;
    }
    
    /**
     * 更新会话组
     * @param {string} groupName 组名称
     * @param {Array} sessions 会话列表
     */
    updateSessionGroup(groupName, sessions) {
        if (this.sessionGroups[groupName]) {
            this.sessionGroups[groupName].sessions = sessions;
            this.saveToStorage();
            this.notifySessionListeners();
            return true;
        }
        return false;
    }
    
    /**
     * 删除会话组
     * @param {string} groupName 组名称
     */
    deleteSessionGroup(groupName) {
        if (this.sessionGroups[groupName]) {
            delete this.sessionGroups[groupName];
            this.saveToStorage();
            this.notifySessionListeners();
            return true;
        }
        return false;
    }
    
    /**
     * 获取所有活跃会话
     * @returns {Object} 活跃会话对象
     */
    getActiveSessions() {
        return this.activeSessions;
    }
    
    /**
     * 获取所有保存的会话配置
     * @returns {Object} 保存的会话配置
     */
    getSavedSessions() {
        return this.savedSessions;
    }
    
    /**
     * 获取所有会话组
     * @returns {Object} 会话组对象
     */
    getSessionGroups() {
        return this.sessionGroups;
    }
    
    // 会话变更监听器列表
    sessionListeners = [];
    
    /**
     * 添加会话变更监听器
     * @param {Function} listener 监听器函数
     */
    addSessionListener(listener) {
        this.sessionListeners.push(listener);
    }
    
    /**
     * 移除会话变更监听器
     * @param {Function} listener 监听器函数
     */
    removeSessionListener(listener) {
        const index = this.sessionListeners.indexOf(listener);
        if (index !== -1) {
            this.sessionListeners.splice(index, 1);
        }
    }
    
    /**
     * 通知所有会话监听器
     */
    notifySessionListeners() {
        const data = {
            activeSessions: this.activeSessions,
            savedSessions: this.savedSessions,
            sessionGroups: this.sessionGroups
        };
        
        this.sessionListeners.forEach(listener => {
            try {
                listener(data);
            } catch (error) {
                console.error('会话监听器执行错误:', error);
            }
        });
    }
    
    /**
     * 连接到设备
     * @param {string} deviceId 设备ID
     * @param {string} credentialId 凭据ID
     * @param {string} name 会话名称
     * @returns {Object} 连接信息
     */
    async connectToDevice(deviceId, credentialId, name) {
        // 会话ID使用设备ID和凭据ID组合
        const sessionId = `${deviceId}_${credentialId}_${Date.now()}`;
        
        // 创建会话记录
        const sessionInfo = {
            id: sessionId,
            name: name,
            deviceId: deviceId,
            credentialId: credentialId,
            startTime: new Date(),
            status: 'connecting'
        };
        
        // 注册活跃会话
        this.registerActiveSession(sessionId, sessionInfo);
        
        return sessionInfo;
    }
}

/**
 * 会话管理UI类
 * 
 * 处理会话管理相关的UI交互
 */
class SessionManagerUI {
    constructor() {
        // 获取DOM元素
        this.activeSessionsList = document.getElementById('active-sessions-list');
        this.savedSessionsList = document.getElementById('saved-sessions-list');
        this.sessionGroupsList = document.getElementById('session-groups-list');
        
        // 获取会话操作按钮
        this.newSessionBtn = document.getElementById('new-session-btn');
        this.saveSessionBtn = document.getElementById('save-session-btn');
        this.manageGroupsBtn = document.getElementById('manage-groups-btn');
        
        // 绑定按钮事件
        if (this.newSessionBtn) {
            this.newSessionBtn.addEventListener('click', () => {
                // 显示连接对话框
                window.terminalManager.showConnectDialog();
            });
        }
        
        if (this.saveSessionBtn) {
            this.saveSessionBtn.addEventListener('click', () => {
                this.showSaveSessionDialog();
            });
        }
        
        if (this.manageGroupsBtn) {
            this.manageGroupsBtn.addEventListener('click', () => {
                this.showManageGroupsDialog();
            });
        }
        
        // 绑定保存会话表单提交事件
        const saveSessionForm = document.getElementById('save-session-form');
        if (saveSessionForm) {
            saveSessionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSession();
            });
        }
        
        // 绑定创建组按钮事件
        const createGroupBtn = document.getElementById('create-group-btn');
        if (createGroupBtn) {
            createGroupBtn.addEventListener('click', () => {
                this.createSessionGroup();
            });
        }
        
        // 绑定对话框关闭按钮事件
        document.querySelectorAll('.modal .close, .modal .close-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.modal').forEach(modal => {
                    modal.style.display = 'none';
                });
            });
        });
        
        // 添加会话变更监听器
        if (window.sessionManager) {
            window.sessionManager.addSessionListener(this.updateUI.bind(this));
        }
        
        // 初始化UI
        this.updateUI({
            activeSessions: window.sessionManager?.getActiveSessions() || {},
            savedSessions: window.sessionManager?.getSavedSessions() || {},
            sessionGroups: window.sessionManager?.getSessionGroups() || {}
        });
    }
    
    // 更新UI
    updateUI(data) {
        const { activeSessions, savedSessions, sessionGroups } = data;
        
        // 更新活跃会话列表
        this.updateActiveSessionsList(activeSessions);
        
        // 更新保存的会话列表
        this.updateSavedSessionsList(savedSessions);
        
        // 更新会话组列表
        this.updateSessionGroupsList(sessionGroups, savedSessions);
    }
    
    // 更新活跃会话列表
    updateActiveSessionsList(activeSessions) {
        if (!this.activeSessionsList) return;
        
        this.activeSessionsList.innerHTML = '';
        
        const sessionIds = Object.keys(activeSessions);
        
        if (sessionIds.length === 0) {
            this.activeSessionsList.innerHTML = '<div class="session-empty">暂无活跃会话</div>';
            return;
        }
        
        // 使用Set避免重复会话
        const processedSessions = new Set();
        
        sessionIds.forEach(sessionId => {
            // 避免重复显示会话
            if (processedSessions.has(sessionId)) {
                console.warn(`会话ID ${sessionId} 已存在，避免重复显示`);
                return;
            }
            
            processedSessions.add(sessionId);
            
            const session = activeSessions[sessionId];
            const sessionItem = document.createElement('div');
            sessionItem.className = 'session-item';
            sessionItem.dataset.sessionId = sessionId; // 添加会话ID作为数据属性
            
            // 状态指示灯
            let statusClass = '';
            
            switch (session.status) {
                case 'active':
                    statusClass = 'status-active';
                    break;
                case 'connecting':
                    statusClass = 'status-connecting';
                    break;
                case 'disconnected':
                    statusClass = 'status-disconnected';
                    break;
                case 'error':
                    statusClass = 'status-error';
                    break;
                default:
                    statusClass = 'status-connecting';
                    break;
            }
            
            sessionItem.innerHTML = `
                <div class="session-item-content">
                    <div class="session-item-title">
                        <span class="status-indicator ${statusClass}"></span>
                        ${session.name}
                    </div>
                    <div class="session-item-details">
                        ${new Date(session.startTime).toLocaleTimeString()}
                    </div>
                </div>
                <div class="session-item-actions">
                    <button class="session-item-action save-session" title="保存会话">
                        <i class="fas fa-save"></i>
                    </button>
                    <button class="session-item-action close-session" title="关闭会话" data-session-id="${sessionId}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            // 保存会话按钮
            sessionItem.querySelector('.save-session').addEventListener('click', () => {
                this.showSaveSessionDialog(session);
            });
            
            // 关闭会话按钮 - 修复关闭逻辑
            sessionItem.querySelector('.close-session').addEventListener('click', (event) => {
                const clickedSessionId = event.currentTarget.dataset.sessionId;
                console.log(`关闭会话: ${clickedSessionId}`);
                
                const termInfo = window.terminalManager.getTerminalById(clickedSessionId);
                if (termInfo) {
                    window.terminalManager.closeTerminal(clickedSessionId);
                } else {
                    // 如果没有找到对应的终端，直接注销会话
                    window.sessionManager.unregisterActiveSession(clickedSessionId);
                    // 手动更新UI
                    this.updateActiveSessionsList(window.sessionManager.getActiveSessions());
                }
            });
            
            this.activeSessionsList.appendChild(sessionItem);
        });
    }
    
    // 更新保存的会话列表
    updateSavedSessionsList(savedSessions) {
        if (!this.savedSessionsList) return;
        
        this.savedSessionsList.innerHTML = '';
        
        const sessionNames = Object.keys(savedSessions);
        
        if (sessionNames.length === 0) {
            this.savedSessionsList.innerHTML = '<div class="session-empty">暂无保存的会话</div>';
            return;
        }
        
        sessionNames.forEach(sessionName => {
            const session = savedSessions[sessionName];
            const sessionItem = document.createElement('div');
            sessionItem.className = 'session-item';
            
            sessionItem.innerHTML = `
                <div class="session-item-content">
                    <div class="session-item-title">${sessionName}</div>
                    <div class="session-item-details">
                        ${session.description || ''}
                    </div>
                </div>
                <div class="session-item-actions">
                    <button class="session-item-action connect-session" title="连接会话">
                        <i class="fas fa-plug"></i>
                    </button>
                    <button class="session-item-action delete-session" title="删除会话">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            // 连接会话按钮
            sessionItem.querySelector('.connect-session').addEventListener('click', () => {
                if (session.deviceId && session.credentialId) {
                    // 创建连接
                    window.terminalManager.createTerminal(
                        sessionName, 
                        session.deviceId, 
                        session.credentialId
                    );
                } else {
                    alert('无法连接会话：缺少设备ID或凭据ID');
                }
            });
            
            // 删除会话按钮
            sessionItem.querySelector('.delete-session').addEventListener('click', () => {
                if (confirm(`确定要删除保存的会话"${sessionName}"吗？`)) {
                    window.sessionManager.deleteSession(sessionName);
                }
            });
            
            this.savedSessionsList.appendChild(sessionItem);
        });
    }
    
    // 更新会话组列表
    updateSessionGroupsList(sessionGroups, savedSessions) {
        if (!this.sessionGroupsList) return;
        
        this.sessionGroupsList.innerHTML = '';
        
        const groupNames = Object.keys(sessionGroups);
        
        if (groupNames.length === 0) {
            this.sessionGroupsList.innerHTML = '<div class="session-empty">暂无会话组</div>';
            return;
        }
        
        groupNames.forEach(groupName => {
            const group = sessionGroups[groupName];
            const groupItem = document.createElement('div');
            groupItem.className = 'session-group-item';
            
            // 组标题
            const groupHeader = document.createElement('div');
            groupHeader.className = 'session-group-header';
            groupHeader.innerHTML = `
                <div class="session-item-title">
                    <i class="fas fa-folder"></i> ${groupName}
                </div>
                <div class="session-item-actions">
                    <button class="session-item-action toggle-group">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
            `;
            
            // 组内容
            const groupContent = document.createElement('div');
            groupContent.className = 'session-group-content';
            
            // 添加组内会话
            if (group.sessions.length === 0) {
                groupContent.innerHTML = '<div class="session-empty">此组中没有会话</div>';
            } else {
                group.sessions.forEach(sessionName => {
                    if (savedSessions[sessionName]) {
                        const session = savedSessions[sessionName];
                        const sessionItem = document.createElement('div');
                        sessionItem.className = 'session-item';
                        
                        sessionItem.innerHTML = `
                            <div class="session-item-content">
                                <div class="session-item-title">${sessionName}</div>
                            </div>
                            <div class="session-item-actions">
                                <button class="session-item-action connect-session" title="连接会话">
                                    <i class="fas fa-plug"></i>
                                </button>
                            </div>
                        `;
                        
                        // 连接会话按钮
                        sessionItem.querySelector('.connect-session').addEventListener('click', () => {
                            if (session.deviceId && session.credentialId) {
                                // 创建连接
                                window.terminalManager.createTerminal(
                                    sessionName, 
                                    session.deviceId, 
                                    session.credentialId
                                );
                            } else {
                                alert('无法连接会话：缺少设备ID或凭据ID');
                            }
                        });
                        
                        groupContent.appendChild(sessionItem);
                    }
                });
            }
            
            // 切换组展开/折叠
            groupHeader.querySelector('.toggle-group').addEventListener('click', () => {
                groupContent.classList.toggle('active');
                const icon = groupHeader.querySelector('.toggle-group i');
                if (groupContent.classList.contains('active')) {
                    icon.className = 'fas fa-chevron-up';
                } else {
                    icon.className = 'fas fa-chevron-down';
                }
            });
            
            groupItem.appendChild(groupHeader);
            groupItem.appendChild(groupContent);
            this.sessionGroupsList.appendChild(groupItem);
        });
    }
    
    // 显示保存会话对话框
    showSaveSessionDialog(session) {
        const modal = document.getElementById('save-session-modal');
        modal.style.display = 'block';
        
        // 加载活跃会话列表到下拉框
        const activeSessionSelect = document.getElementById('active-session-select');
        if (activeSessionSelect) {
            activeSessionSelect.innerHTML = '<option value="">-- 请选择会话 --</option>';
            
            const activeSessions = window.sessionManager.getActiveSessions();
            for (const sessionId in activeSessions) {
                const s = activeSessions[sessionId];
                const option = document.createElement('option');
                option.value = sessionId;
                option.textContent = s.name;
                activeSessionSelect.appendChild(option);
                
                // 如果有指定的会话，则选中它
                if (session && sessionId === session.id) {
                    option.selected = true;
                }
            }
        }
        
        // 加载会话组列表到下拉框
        const sessionGroupSelect = document.getElementById('session-group');
        if (sessionGroupSelect) {
            sessionGroupSelect.innerHTML = '<option value="">-- 无分组 --</option>';
            
            const sessionGroups = window.sessionManager.getSessionGroups();
            for (const groupName in sessionGroups) {
                const option = document.createElement('option');
                option.value = groupName;
                option.textContent = groupName;
                sessionGroupSelect.appendChild(option);
            }
        }
        
        // 设置表单默认值
        if (session) {
            const sessionNameInput = document.getElementById('session-name');
            if (sessionNameInput) {
                sessionNameInput.value = session.name;
            }
        }
    }
    
    // 显示管理会话组对话框
    showManageGroupsDialog() {
        const modal = document.getElementById('manage-groups-modal');
        modal.style.display = 'block';
        
        this.updateGroupsManagerUI();
    }
    
    // 更新管理会话组对话框内容
    updateGroupsManagerUI() {
        const groupsList = document.getElementById('manage-groups-list');
        if (!groupsList) return;
        
        groupsList.innerHTML = '';
        
        const sessionGroups = window.sessionManager.getSessionGroups();
        const groupNames = Object.keys(sessionGroups);
        
        if (groupNames.length === 0) {
            groupsList.innerHTML = '<div class="group-empty">暂无会话组</div>';
            return;
        }
        
        groupNames.forEach(groupName => {
            const group = sessionGroups[groupName];
            const groupItem = document.createElement('div');
            groupItem.className = 'group-item';
            groupItem.innerHTML = `
                <div class="group-item-name">${groupName}</div>
                <div class="group-item-actions">
                    <button class="session-item-action edit-group" title="编辑组">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="session-item-action delete-group" title="删除组">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            // 编辑组按钮
            groupItem.querySelector('.edit-group').addEventListener('click', () => {
                this.showEditGroupDialog(groupName, group);
            });
            
            // 删除组按钮
            groupItem.querySelector('.delete-group').addEventListener('click', () => {
                if (confirm(`确定要删除会话组"${groupName}"吗？`)) {
                    window.sessionManager.deleteSessionGroup(groupName);
                    this.updateGroupsManagerUI();
                }
            });
            
            groupsList.appendChild(groupItem);
        });
    }
    
    // 显示编辑会话组对话框
    showEditGroupDialog(groupName, group) {
        // 实现编辑会话组功能
        alert(`编辑会话组功能开发中: ${groupName}`);
    }
    
    // 创建会话组
    createSessionGroup() {
        const groupNameInput = document.getElementById('new-group-name');
        if (!groupNameInput) return;
        
        const groupName = groupNameInput.value.trim();
        
        if (!groupName) {
            alert('请输入组名称');
            return;
        }
        
        if (window.sessionManager.getSessionGroups()[groupName]) {
            alert('已存在同名会话组');
            return;
        }
        
        window.sessionManager.createSessionGroup(groupName);
        groupNameInput.value = '';
        this.updateGroupsManagerUI();
    }
    
    // 保存会话
    saveSession() {
        const sessionId = document.getElementById('active-session-select')?.value;
        const sessionName = document.getElementById('session-name')?.value.trim();
        const sessionDesc = document.getElementById('session-description')?.value.trim();
        const groupName = document.getElementById('session-group')?.value;
        
        if (!sessionId || !sessionName) {
            alert('请选择会话并输入会话名称');
            return;
        }
        
        const activeSessions = window.sessionManager.getActiveSessions();
        const sessionInfo = activeSessions[sessionId];
        
        if (!sessionInfo) {
            alert('所选会话不存在');
            return;
        }
        
        // 保存会话配置
        const config = {
            name: sessionName,
            description: sessionDesc,
            deviceId: sessionInfo.deviceId,
            credentialId: sessionInfo.credentialId,
            originalId: sessionId
        };
        
        window.sessionManager.saveSession(sessionName, config);
        
        // 如果指定了会话组，添加到组
        if (groupName) {
            const groups = window.sessionManager.getSessionGroups();
            if (groups[groupName]) {
                const sessions = [...groups[groupName].sessions];
                if (!sessions.includes(sessionName)) {
                    sessions.push(sessionName);
                    window.sessionManager.updateSessionGroup(groupName, sessions);
                }
            }
        }
        
        // 关闭对话框
        document.getElementById('save-session-modal').style.display = 'none';
        
        // 重置表单
        document.getElementById('save-session-form')?.reset();
    }
}

// 原本在这里自动创建实例的代码已移除，改为在页面加载时统一创建 