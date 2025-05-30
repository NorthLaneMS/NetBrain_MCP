/**
 * 网络拓扑可视化模块
 * 基于D3.js实现网络拓扑图的可视化和交互
 */

class TopologyVisualization {
    constructor() {
        // 初始化变量
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.selectedNode = null;
        this.selectedLink = null;
        this.transform = d3.zoomIdentity;
        this.width = 0;
        this.height = 0;
        
        // UI元素
        this.elements = {};
        
        // 厂商颜色映射
        this.vendorColors = {
            cisco: '#1e40af',
            huawei: '#dc2626',
            h3c: '#059669',
            juniper: '#7c3aed',
            other: '#6b7280'
        };
        
        // 初始化
        this.init();
    }
    
    /**
     * 初始化拓扑可视化
     */
    init() {
        console.log('初始化网络拓扑可视化模块');
        
        // 缓存DOM元素
        this.cacheElements();
        
        // 初始化SVG
        this.initSVG();
        
        // 绑定事件
        this.bindEvents();
        
        // 加载初始拓扑数据
        this.loadTopology();
    }
    
    /**
     * 缓存DOM元素
     */
    cacheElements() {
        this.elements = {
            // 主要容器
            topologyContent: document.getElementById('topology-content'),
            topologyCanvas: document.getElementById('topology-canvas'),
            topologySvg: document.getElementById('topology-svg'),
            topologyLoading: document.getElementById('topology-loading'),
            topologyEmpty: document.getElementById('topology-empty'),
            
            // 工具栏按钮
            discoverBtn: document.getElementById('discover-topology-btn'),
            refreshBtn: document.getElementById('refresh-topology-btn'),
            clearBtn: document.getElementById('clear-topology-btn'),
            fitBtn: document.getElementById('fit-topology-btn'),
            zoomInBtn: document.getElementById('zoom-in-btn'),
            zoomOutBtn: document.getElementById('zoom-out-btn'),
            centerBtn: document.getElementById('center-topology-btn'),
            
            // 过滤器
            vendorFilter: document.getElementById('vendor-filter'),
            deviceTypeFilter: document.getElementById('device-type-filter'),
            applyFilterBtn: document.getElementById('apply-filter-btn'),
            
            // 统计元素
            statNodes: document.getElementById('stat-nodes'),
            statLinks: document.getElementById('stat-links'),
            statProtocols: document.getElementById('stat-protocols'),
            statVendors: document.getElementById('stat-vendors'),
            
            // 详情面板
            nodeDetails: document.getElementById('node-details'),
            linkDetails: document.getElementById('link-details'),
            
            // 操作按钮
            connectBtn: document.getElementById('connect-to-device-btn'),
            pingBtn: document.getElementById('ping-device-btn'),
            discoverNeighborsBtn: document.getElementById('discover-neighbors-btn'),
            propertiesBtn: document.getElementById('device-properties-btn'),
            
            // 对话框
            discoverModal: document.getElementById('topology-discover-modal'),
            discoverForm: document.getElementById('topology-discover-form'),
            seedDevicesList: document.getElementById('seed-devices-list'),
            discoveryProgress: document.getElementById('discovery-progress'),
            discoveryStatus: document.getElementById('discovery-status'),
            discoveryProgressBar: document.getElementById('discovery-progress-bar'),
            
            // 其他
            gotoDevicesBtn: document.getElementById('goto-devices-btn')
        };
    }
    
    /**
     * 初始化SVG
     */
    initSVG() {
        const container = this.elements.topologyCanvas;
        this.width = container.clientWidth;
        this.height = container.clientHeight;
        
        this.svg = d3.select('#topology-svg')
            .attr('width', this.width)
            .attr('height', this.height);
            
        // 创建主要的图形组
        this.g = this.svg.select('#topology-graph');
        this.linkGroup = this.svg.select('#links-group');
        this.nodeGroup = this.svg.select('#nodes-group');
        this.labelGroup = this.svg.select('#labels-group');
        
        // 获取或创建defs元素
        let defs = this.svg.select('defs');
        if (defs.empty()) {
            defs = this.svg.append('defs');
        }
        
        // 添加渐变定义
        this.createGradients(defs);
        
        // 添加阴影滤镜
        this.createShadowFilter(defs);
        
        // 设置缩放行为
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.transform = event.transform;
                this.g.attr('transform', this.transform);
            });
            
        this.svg.call(zoom);
        
        // 初始化力仿真
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(30)); // 从25增加到30，适应更大的图标
    }
    
    /**
     * 创建渐变定义
     */
    createGradients(defs) {
        const vendors = ['cisco', 'huawei', 'h3c', 'juniper', 'other'];
        
        vendors.forEach(vendor => {
            const gradient = defs.append('radialGradient')
                .attr('id', `gradient-${vendor}`)
                .attr('cx', '30%')
                .attr('cy', '30%')
                .attr('r', '70%');
            
            const baseColor = this.vendorColors[vendor];
            
            gradient.append('stop')
                .attr('offset', '0%')
                .attr('stop-color', this.lightenColor(baseColor, 0.3));
                
            gradient.append('stop')
                .attr('offset', '100%')
                .attr('stop-color', baseColor);
        });
    }
    
    /**
     * 创建阴影滤镜
     */
    createShadowFilter(defs) {
        const filter = defs.append('filter')
            .attr('id', 'drop-shadow')
            .attr('x', '-50%')
            .attr('y', '-50%')
            .attr('width', '200%')
            .attr('height', '200%');
            
        filter.append('feDropShadow')
            .attr('dx', 2)
            .attr('dy', 2)
            .attr('stdDeviation', 3)
            .attr('flood-color', '#000')
            .attr('flood-opacity', 0.3);
    }
    
    /**
     * 调亮颜色
     */
    lightenColor(color, percent) {
        const num = parseInt(color.replace("#",""), 16);
        const amt = Math.round(2.55 * percent * 100);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 工具栏事件
        this.elements.discoverBtn?.addEventListener('click', () => this.showDiscoverDialog());
        this.elements.refreshBtn?.addEventListener('click', () => this.loadTopology());
        this.elements.clearBtn?.addEventListener('click', () => this.clearTopology());
        this.elements.fitBtn?.addEventListener('click', () => this.fitToView());
        this.elements.zoomInBtn?.addEventListener('click', () => this.zoomIn());
        this.elements.zoomOutBtn?.addEventListener('click', () => this.zoomOut());
        this.elements.centerBtn?.addEventListener('click', () => this.centerView());
        this.elements.applyFilterBtn?.addEventListener('click', () => this.applyFilters());
        
        // 操作按钮事件
        this.elements.connectBtn?.addEventListener('click', () => this.connectToDevice());
        this.elements.pingBtn?.addEventListener('click', () => this.pingDevice());
        this.elements.discoverNeighborsBtn?.addEventListener('click', () => this.discoverNeighbors());
        this.elements.propertiesBtn?.addEventListener('click', () => this.showDeviceProperties());
        
        // 其他事件
        this.elements.gotoDevicesBtn?.addEventListener('click', () => this.gotoDevicesPage());
        
        // 发现对话框事件
        this.elements.discoverForm?.addEventListener('submit', (e) => this.handleDiscoverSubmit(e));
        
        // 窗口大小改变事件
        window.addEventListener('resize', () => this.handleResize());
        
        // SVG点击事件（取消选择和隐藏菜单）
        this.svg?.on('click', (event) => {
            if (event.target === this.svg.node()) {
                this.clearSelection();
                this.hideContextMenu();
            }
        });
        
        // 全局点击事件（隐藏上下文菜单）
        document.addEventListener('click', (event) => {
            // 如果点击的不是菜单内容，则隐藏菜单
            const menu = document.getElementById('topology-context-menu');
            if (menu && !menu.contains(event.target)) {
                this.hideContextMenu();
            }
        });
        
        // 全局ESC键事件（隐藏上下文菜单）
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.hideContextMenu();
            }
        });
    }
    
    /**
     * 加载拓扑数据
     */
    async loadTopology() {
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/topology');
            const data = await response.json();
            
            if (data.success && data.topology) {
                this.updateTopology(data.topology);
                this.showEmpty(false);
            } else {
                this.showEmpty(true);
            }
        } catch (error) {
            console.error('加载拓扑数据失败:', error);
            this.showEmpty(true);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * 更新拓扑数据
     */
    updateTopology(topology) {
        // 转换节点数据
        this.nodes = Object.values(topology.nodes || {}).map(node => ({
            id: node.device_id,
            name: node.name,
            ip: node.ip_address,
            vendor: node.vendor || 'other',
            deviceType: node.device_type || 'other',
            status: node.status || 'unknown',
            interfaces: node.interfaces || [],
            interface_count: node.interface_count || (node.interfaces ? node.interfaces.length : 0), // 添加接口数字段
            // D3需要的位置信息
            x: Math.random() * this.width,
            y: Math.random() * this.height
        }));
        
        // 转换链路数据
        this.links = topology.links?.map(link => ({
            id: `${link.source_device_id}-${link.target_device_id}`,
            source: link.source_device_id,
            target: link.target_device_id,
            sourceInterface: link.source_interface,
            targetInterface: link.target_interface,
            protocol: link.protocol || 'unknown'
        })) || [];
        
        // 更新可视化
        this.renderTopology();
        
        // 更新统计信息
        this.updateStatistics();
    }
    
    /**
     * 渲染拓扑图
     */
    renderTopology() {
        // 更新仿真数据
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);
        
        // 渲染链路
        this.renderLinks();
        
        // 渲染节点
        this.renderNodes();
        
        // 渲染标签
        this.renderLabels();
        
        // 重启仿真
        this.simulation.alpha(1).restart();
        
        // 显示SVG并隐藏空状态
        this.elements.topologySvg.style.display = 'block';
        
        // 根据节点数量决定是否显示空状态
        if (this.nodes.length > 0) {
            this.showEmpty(false);
        } else {
            this.showEmpty(true);
        }
    }
    
    /**
     * 渲染链路
     */
    renderLinks() {
        const links = this.linkGroup.selectAll('.topology-link')
            .data(this.links, d => d.id);
            
        links.exit().remove();
        
        const linkEnter = links.enter()
            .append('line')
            .attr('class', d => `topology-link ${d.protocol}`)
            .attr('stroke-width', 2)
            .on('click', (event, d) => this.selectLink(event, d));
            
        const linkUpdate = linkEnter.merge(links);
        
        // 更新链路位置（在仿真tick中处理）
        this.simulation.on('tick', () => {
            linkUpdate
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
                
            this.updateNodePositions();
            this.updateLabelPositions();
        });
    }
    
    /**
     * 渲染节点
     */
    renderNodes() {
        const nodes = this.nodeGroup.selectAll('.topology-node-group')
            .data(this.nodes, d => d.id);
            
        nodes.exit().remove();
        
        // 创建节点组
        const nodeEnter = nodes.enter()
            .append('g')
            .attr('class', d => `topology-node-group ${d.vendor}`)
            .call(this.createDragBehavior());
        
        // 绑定点击和双击事件
        this.bindNodeEvents(nodeEnter);
        
        // 添加主节点圆圈（修改为完全透明）
        nodeEnter.append('circle')
            .attr('class', 'node-main-circle')
            .attr('r', 18)
            .attr('stroke', 'transparent')  // 边框透明
            .attr('stroke-width', 0)        // 边框宽度为0
            .style('fill', 'transparent')   // 填充透明
            .style('filter', 'none');       // 移除阴影效果
        
        // 添加设备类型SVG图标（进一步增大尺寸）
        const iconGroup = nodeEnter.append('g')
            .attr('class', 'node-icon-group')
            .attr('transform', 'translate(-20, -20)');  // 调整位置以适应更大的图标
        
        // 根据设备类型添加不同的SVG图标
        iconGroup.each(function(d) {
            const group = d3.select(this);
            const iconSvg = window.topologyVisualization.createDeviceIcon(d.deviceType, true);  // 传递黑色参数
            group.node().innerHTML = iconSvg;
        });
        
        // 添加状态指示器
        nodeEnter.append('circle')
            .attr('class', 'node-status-indicator')
            .attr('r', 5)
            .attr('cx', 18)  // 调整位置以适应更大的图标
            .attr('cy', -18)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .style('fill', d => this.getStatusColor(d.status));
        
        // 添加厂商徽章
        nodeEnter.append('circle')
            .attr('class', 'node-vendor-badge')
            .attr('r', 6)
            .attr('cx', -18)  // 调整位置以适应更大的图标
            .attr('cy', -18)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .style('fill', d => this.vendorColors[d.vendor] || this.vendorColors.other);
        
        // 添加厂商徽章文字
        nodeEnter.append('text')
            .attr('class', 'node-vendor-text')
            .attr('x', -18)  // 调整位置以适应更大的图标
            .attr('y', -15)
            .attr('text-anchor', 'middle')
            .style('font-size', '7px')
            .style('font-weight', 'bold')
            .style('fill', '#fff')
            .style('pointer-events', 'none')
            .text(d => this.getVendorBadgeText(d.vendor));
        
        // 更新现有节点
        const nodeUpdate = nodeEnter.merge(nodes);
        
        // 更新事件绑定
        this.bindNodeEvents(nodeUpdate);
        
        // 更新主圆圈样式
        nodeUpdate.select('.node-main-circle')
            .attr('r', 18)
            .style('fill', 'transparent');
        
        // 更新状态指示器颜色
        nodeUpdate.select('.node-status-indicator')
            .style('fill', d => this.getStatusColor(d.status));
        
        // 更新图标
        nodeUpdate.select('.node-icon-group')
            .each(function(d) {
                const group = d3.select(this);
                const iconSvg = window.topologyVisualization.createDeviceIcon(d.deviceType, true);
                group.node().innerHTML = iconSvg;
            });
        
        // 添加选择效果
        nodeUpdate.classed('selected', d => d === this.selectedNode);
    }
    
    /**
     * 绑定节点事件（单击选择，双击菜单）
     */
    bindNodeEvents(selection) {
        let clickTimeout = null;
        
        selection
            .on('click', (event, d) => {
                event.stopPropagation();
                
                // 清除之前的延迟
                if (clickTimeout) {
                    clearTimeout(clickTimeout);
                    clickTimeout = null;
                }
                
                // 延迟执行单击，以区分双击
                clickTimeout = setTimeout(() => {
                    this.selectNode(event, d);
                    clickTimeout = null;
                }, 250);
            })
            .on('dblclick', (event, d) => {
                event.stopPropagation();
                
                // 取消单击延迟
                if (clickTimeout) {
                    clearTimeout(clickTimeout);
                    clickTimeout = null;
                }
                
                // 先选择节点
                this.selectNode(event, d);
                
                // 显示上下文菜单
                this.showContextMenu(event, d);
            });
    }
    
    /**
     * 显示上下文菜单
     */
    showContextMenu(event, node) {
        // 隐藏已存在的菜单
        this.hideContextMenu();
        
        // 创建菜单容器
        const menu = document.createElement('div');
        menu.className = 'topology-context-menu';
        menu.id = 'topology-context-menu';
        
        // 菜单项配置
        const menuItems = [
            {
                icon: 'fas fa-terminal',
                text: '连接终端',
                action: () => this.connectToDevice(),
                disabled: false
            },
            {
                icon: 'fas fa-satellite-dish',
                text: 'Ping测试',
                action: () => this.pingDevice(),
                disabled: false
            },
            {
                icon: 'fas fa-search',
                text: '发现邻居',
                action: () => this.discoverNeighbors(),
                disabled: false
            },
            {
                type: 'divider'
            },
            {
                icon: 'fas fa-cog',
                text: '设备属性',
                action: () => this.showDeviceProperties(),
                disabled: false
            },
            {
                icon: 'fas fa-copy',
                text: '复制IP地址',
                action: () => this.copyIPAddress(node),
                disabled: false
            },
            {
                type: 'divider'
            },
            {
                icon: 'fas fa-expand-arrows-alt',
                text: '居中到此设备',
                action: () => this.centerToNode(node),
                disabled: false
            }
        ];
        
        // 创建菜单项
        menuItems.forEach(item => {
            if (item.type === 'divider') {
                const divider = document.createElement('div');
                divider.className = 'context-menu-divider';
                menu.appendChild(divider);
            } else {
                const menuItem = document.createElement('div');
                menuItem.className = `context-menu-item ${item.disabled ? 'disabled' : ''}`;
                
                menuItem.innerHTML = `
                    <i class="${item.icon}"></i>
                    <span>${item.text}</span>
                `;
                
                if (!item.disabled) {
                    menuItem.addEventListener('click', (e) => {
                        e.stopPropagation();
                        item.action();
                        this.hideContextMenu();
                    });
                }
                
                menu.appendChild(menuItem);
            }
        });
        
        // 添加到页面
        document.body.appendChild(menu);
        
        // 计算位置（确保菜单不超出视窗）
        const rect = this.elements.topologyCanvas.getBoundingClientRect();
        const menuRect = menu.getBoundingClientRect();
        
        let x = event.clientX;
        let y = event.clientY;
        
        // 防止菜单超出右边界
        if (x + menuRect.width > window.innerWidth) {
            x = window.innerWidth - menuRect.width - 10;
        }
        
        // 防止菜单超出下边界
        if (y + menuRect.height > window.innerHeight) {
            y = window.innerHeight - menuRect.height - 10;
        }
        
        // 设置位置
        menu.style.left = `${x}px`;
        menu.style.top = `${y}px`;
        
        // 添加动画效果
        menu.style.opacity = '0';
        menu.style.transform = 'scale(0.8)';
        
        requestAnimationFrame(() => {
            menu.style.opacity = '1';
            menu.style.transform = 'scale(1)';
        });
        
        // 存储当前菜单节点
        this.contextMenuNode = node;
    }
    
    /**
     * 隐藏上下文菜单
     */
    hideContextMenu() {
        const existingMenu = document.getElementById('topology-context-menu');
        if (existingMenu) {
            existingMenu.remove();
        }
        this.contextMenuNode = null;
    }
    
    /**
     * 复制IP地址到剪贴板
     */
    async copyIPAddress(node) {
        try {
            await navigator.clipboard.writeText(node.ip);
            this.showNotification(`IP地址已复制: ${node.ip}`, 'success');
        } catch (error) {
            console.error('复制失败:', error);
            this.showNotification('复制失败，请手动复制', 'error');
        }
    }
    
    /**
     * 居中到指定节点
     */
    centerToNode(node) {
        if (!node) return;
        
        const scale = this.transform.k || 1;
        const translateX = this.width / 2 - node.x * scale;
        const translateY = this.height / 2 - node.y * scale;
        
        this.svg.transition()
            .duration(750)
            .call(d3.zoom().transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
    }
    
    /**
     * 显示通知消息
     */
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `topology-notification ${type}`;
        notification.textContent = message;
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 设置初始样式
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '10000';
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        notification.style.transition = 'all 0.3s ease';
        
        // 显示动画
        requestAnimationFrame(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        });
        
        // 自动隐藏
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    /**
     * 渲染标签
     */
    renderLabels() {
        const labels = this.labelGroup.selectAll('.node-label')
            .data(this.nodes, d => d.id);
            
        labels.exit().remove();
        
        const labelEnter = labels.enter()
            .append('text')
            .attr('class', 'node-label')
            .attr('dy', 35)  // 调整标签位置，从25改回35
            .text(d => d.name);
            
        const labelUpdate = labelEnter.merge(labels);
    }
    
    /**
     * 更新节点位置 - 优化版，支持拖拽时的实时更新
     */
    updateNodePositions() {
        this.nodeGroup.selectAll('.topology-node-group')
            .attr('transform', d => {
                // 优先使用固定位置（拖拽时设置的fx, fy），否则使用模拟位置
                const x = d.fx !== undefined ? d.fx : d.x;
                const y = d.fy !== undefined ? d.fy : d.y;
                return `translate(${x},${y})`;
            });
    }
    
    /**
     * 更新标签位置
     */
    updateLabelPositions() {
        this.labelGroup.selectAll('.node-label')
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    }
    
    /**
     * 创建拖拽行为 - 优化版，只移动当前设备，其他设备保持固定
     */
    createDragBehavior() {
        return d3.drag()
            .on('start', (event, d) => {
                // 固定所有其他节点
                this.nodes.forEach(node => {
                    if (node !== d) {
                        node.fx = node.x;
                        node.fy = node.y;
                    }
                });
                
                // 设置当前节点为拖拽状态
                d.fx = d.x;
                d.fy = d.y;
                
                // 提升被拖拽节点的层级
                d3.select(event.sourceEvent.currentTarget.parentNode)
                    .raise()
                    .classed('dragging', true);
                
                // 暂停力模拟或设置很低的alpha值
                this.simulation.alphaTarget(0.01).restart();
            })
            .on('drag', (event, d) => {
                // 实时更新当前节点位置
                d.fx = event.x;
                d.fy = event.y;
                
                // 立即更新节点位置
                const nodeGroup = d3.select(event.sourceEvent.currentTarget.parentNode);
                nodeGroup.attr('transform', `translate(${d.fx},${d.fy})`);
                
                // 立即更新相关链路
                this.linkGroup.selectAll('.topology-link')
                    .filter(link => link.source === d || link.target === d)
                    .attr('x1', link => link.source.fx || link.source.x)
                    .attr('y1', link => link.source.fy || link.source.y)
                    .attr('x2', link => link.target.fx || link.target.x)
                    .attr('y2', link => link.target.fy || link.target.y);
                
                // 立即更新标签位置
                this.labelGroup.selectAll('.node-label')
                    .filter(node => node === d)
                    .attr('x', d.fx)
                    .attr('y', d.fy + 35); // 调整标签位置，从25改回35
            })
            .on('end', (event, d) => {
                // 拖拽结束，停止力模拟
                this.simulation.alphaTarget(0);
                
                // 移除拖拽状态
                d3.select(event.sourceEvent.currentTarget.parentNode)
                    .classed('dragging', false);
                
                // 保持当前节点在拖拽结束位置（固定位置）
                // 保持其他节点的固定位置不变
                // 注意：不释放fx, fy，这样所有节点都保持在固定位置
            });
    }
    
    /**
     * 选择节点
     */
    selectNode(event, node) {
        event.stopPropagation();
        
        // 清除之前的选择
        this.clearSelection();
        
        // 设置新选择
        this.selectedNode = node;
        this.selectedLink = null;
        
        // 更新UI
        this.updateNodeSelection();
        this.showNodeDetails(node);
        this.updateActionButtons();
    }
    
    /**
     * 选择链路
     */
    selectLink(event, link) {
        event.stopPropagation();
        
        // 清除之前的选择
        this.clearSelection();
        
        // 设置新选择
        this.selectedLink = link;
        this.selectedNode = null;
        
        // 更新UI
        this.updateLinkSelection();
        this.showLinkDetails(link);
        this.updateActionButtons();
    }
    
    /**
     * 清除选择
     */
    clearSelection() {
        this.selectedNode = null;
        this.selectedLink = null;
        
        // 更新UI
        this.updateNodeSelection();
        this.updateLinkSelection();
        this.showDefaultDetails();
        this.updateActionButtons();
    }
    
    /**
     * 更新节点选择状态
     */
    updateNodeSelection() {
        this.nodeGroup.selectAll('.topology-node-group')
            .classed('selected', d => d === this.selectedNode);
            
        this.labelGroup.selectAll('.node-label')
            .classed('selected', d => d === this.selectedNode);
    }
    
    /**
     * 更新链路选择状态
     */
    updateLinkSelection() {
        this.linkGroup.selectAll('.topology-link')
            .classed('selected', d => d === this.selectedLink);
    }
    
    /**
     * 显示节点详情
     */
    showNodeDetails(node) {
        // 获取接口数，优先级：直接接口数据 > 连接数推测 > 显示未知
        let interfaceCount;
        if (node.interfaces && Array.isArray(node.interfaces) && node.interfaces.length > 0) {
            // 有实际接口数据
            interfaceCount = node.interfaces.length;
        } else if (node.interface_count && node.interface_count > 0) {
            // 有接口数字段
            interfaceCount = node.interface_count;
        } else {
            // 尝试从连接的链路数推测
            const connectedLinks = this.links.filter(link => 
                (link.source.id || link.source) === node.id || 
                (link.target.id || link.target) === node.id
            );
            if (connectedLinks.length > 0) {
                interfaceCount = `${connectedLinks.length}+ (推测)`;
            } else {
                interfaceCount = '未知';
            }
        }
        
        const detailsHtml = `
            <div class="device-info">
                <div class="device-name">${node.name}</div>
                <div class="device-details">
                    <div class="detail-item">
                        <span class="detail-label">IP地址:</span>
                        <span>${node.ip}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">厂商:</span>
                        <span>${this.getVendorDisplayName(node.vendor)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">类型:</span>
                        <span>${this.getDeviceTypeDisplayName(node.deviceType)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">状态:</span>
                        <span class="device-status-indicator ${node.status}"></span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">接口数:</span>
                        <span>${interfaceCount}</span>
                    </div>
                </div>
            </div>
        `;
        
        this.elements.nodeDetails.innerHTML = detailsHtml;
    }
    
    /**
     * 显示链路详情
     */
    showLinkDetails(link) {
        const sourceNode = this.nodes.find(n => n.id === link.source.id || n.id === link.source);
        const targetNode = this.nodes.find(n => n.id === link.target.id || n.id === link.target);
        
        const detailsHtml = `
            <div class="link-info">
                <div class="link-endpoints">
                    ${sourceNode?.name || 'Unknown'} ↔ ${targetNode?.name || 'Unknown'}
                </div>
                <div class="link-details-info">
                    <div class="detail-item">
                        <span class="detail-label">协议:</span>
                        <span class="protocol-badge ${link.protocol}">${link.protocol.toUpperCase()}</span>
                    </div>
                    ${link.sourceInterface ? `
                    <div class="detail-item">
                        <span class="detail-label">源接口:</span>
                        <span>${link.sourceInterface}</span>
                    </div>
                    ` : ''}
                    ${link.targetInterface ? `
                    <div class="detail-item">
                        <span class="detail-label">目标接口:</span>
                        <span>${link.targetInterface}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        this.elements.linkDetails.innerHTML = detailsHtml;
    }
    
    /**
     * 显示默认详情
     */
    showDefaultDetails() {
        this.elements.nodeDetails.innerHTML = `
            <div class="no-selection">
                <i class="fas fa-mouse-pointer"></i>
                <span>点击节点查看详细信息</span>
            </div>
        `;
        
        this.elements.linkDetails.innerHTML = `
            <div class="no-selection">
                <i class="fas fa-mouse-pointer"></i>
                <span>点击链路查看连接信息</span>
            </div>
        `;
    }
    
    /**
     * 更新操作按钮状态
     */
    updateActionButtons() {
        const hasSelection = this.selectedNode !== null;
        
        if (this.elements.connectBtn) this.elements.connectBtn.disabled = !hasSelection;
        if (this.elements.pingBtn) this.elements.pingBtn.disabled = !hasSelection;
        if (this.elements.discoverNeighborsBtn) this.elements.discoverNeighborsBtn.disabled = !hasSelection;
        if (this.elements.propertiesBtn) this.elements.propertiesBtn.disabled = !hasSelection;
    }
    
    /**
     * 更新统计信息
     */
    updateStatistics() {
        // 计算协议数量
        const protocols = new Set(this.links.map(l => l.protocol));
        const vendors = new Set(this.nodes.map(n => n.vendor));
        
        if (this.elements.statNodes) this.elements.statNodes.textContent = this.nodes.length;
        if (this.elements.statLinks) this.elements.statLinks.textContent = this.links.length;
        if (this.elements.statProtocols) this.elements.statProtocols.textContent = protocols.size;
        if (this.elements.statVendors) this.elements.statVendors.textContent = vendors.size;
    }
    
    /**
     * 显示发现对话框
     */
    async showDiscoverDialog() {
        try {
            // 加载可用设备
            const response = await fetch('/api/devices');
            const devices = await response.json();
            
            this.populateDeviceList(devices);
            this.showModal(this.elements.discoverModal);
        } catch (error) {
            console.error('加载设备列表失败:', error);
        }
    }
    
    /**
     * 填充设备列表
     */
    populateDeviceList(devices) {
        const container = this.elements.seedDevicesList;
        
        if (!devices || devices.length === 0) {
            container.innerHTML = `
                <div class="no-devices">
                    <p>没有可用的设备。请先在设备管理页面添加设备。</p>
                </div>
            `;
            return;
        }
        
        const deviceListHtml = devices.map(device => `
            <label class="checkbox-label">
                <input type="checkbox" value="${device.id}" data-device-name="${device.name}">
                <div class="device-checkbox-item">
                    <span class="device-checkbox-name">${device.name}</span>
                    <span class="device-checkbox-info">${device.ip_address} (${device.vendor})</span>
                </div>
            </label>
        `).join('');
        
        container.innerHTML = deviceListHtml;
    }
    
    /**
     * 处理发现表单提交
     */
    async handleDiscoverSubmit(event) {
        event.preventDefault();
        
        // 获取选中的设备
        const selectedDevices = Array.from(this.elements.seedDevicesList.querySelectorAll('input[type="checkbox"]:checked'))
            .map(cb => cb.value);
            
        if (selectedDevices.length === 0) {
            alert('请至少选择一个种子设备');
            return;
        }
        
        // 显示进度
        this.showDiscoveryProgress(true);
        
        try {
            // 调用发现API
            const response = await fetch('/api/topology/discover', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(selectedDevices)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 发现成功，更新拓扑
                this.updateTopology(result.topology);
                this.hideModal(this.elements.discoverModal);
                this.showDiscoveryProgress(false);
            } else {
                throw new Error(result.message || '拓扑发现失败');
            }
        } catch (error) {
            console.error('拓扑发现失败:', error);
            alert('拓扑发现失败: ' + error.message);
            this.showDiscoveryProgress(false);
        }
    }
    
    /**
     * 显示/隐藏发现进度
     */
    showDiscoveryProgress(show) {
        if (this.elements.discoveryProgress) {
            this.elements.discoveryProgress.style.display = show ? 'block' : 'none';
        }
        
        if (this.elements.discoverForm) {
            this.elements.discoverForm.style.display = show ? 'none' : 'block';
        }
    }
    
    /**
     * 清空拓扑
     */
    async clearTopology() {
        if (!confirm('确定要清空拓扑数据吗？')) {
            return;
        }
        
        try {
            const response = await fetch('/api/topology', {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.nodes = [];
                this.links = [];
                this.clearSelection();
                this.renderTopology();
                this.updateStatistics();
                this.showEmpty(true);
            }
        } catch (error) {
            console.error('清空拓扑失败:', error);
        }
    }
    
    /**
     * 缩放控制
     */
    fitToView() {
        if (this.nodes.length === 0) return;
        
        const bounds = this.getTopologyBounds();
        const fullWidth = this.width;
        const fullHeight = this.height;
        const width = bounds.x[1] - bounds.x[0];
        const height = bounds.y[1] - bounds.y[0];
        const midX = (bounds.x[0] + bounds.x[1]) / 2;
        const midY = (bounds.y[0] + bounds.y[1]) / 2;
        
        if (width === 0 || height === 0) return;
        
        const scale = Math.min(fullWidth / width, fullHeight / height) * 0.8;
        const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY];
        
        this.svg.transition()
            .duration(750)
            .call(d3.zoom().transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
    }
    
    zoomIn() {
        this.svg.transition()
            .duration(300)
            .call(d3.zoom().scaleBy, 1.5);
    }
    
    zoomOut() {
        this.svg.transition()
            .duration(300)
            .call(d3.zoom().scaleBy, 1 / 1.5);
    }
    
    centerView() {
        this.svg.transition()
            .duration(750)
            .call(d3.zoom().transform, d3.zoomIdentity);
    }
    
    /**
     * 获取拓扑边界
     */
    getTopologyBounds() {
        const xs = this.nodes.map(d => d.x);
        const ys = this.nodes.map(d => d.y);
        
        return {
            x: [Math.min(...xs) - 50, Math.max(...xs) + 50],
            y: [Math.min(...ys) - 50, Math.max(...ys) + 50]
        };
    }
    
    /**
     * 应用过滤器
     */
    applyFilters() {
        const vendorFilter = this.elements.vendorFilter?.value;
        const deviceTypeFilter = this.elements.deviceTypeFilter?.value;
        
        // 应用节点过滤
        this.nodeGroup.selectAll('.topology-node-group')
            .style('opacity', d => {
                let visible = true;
                if (vendorFilter && d.vendor !== vendorFilter) visible = false;
                if (deviceTypeFilter && d.deviceType !== deviceTypeFilter) visible = false;
                return visible ? 1 : 0.2;
            });
            
        // 应用标签过滤
        this.labelGroup.selectAll('.node-label')
            .style('opacity', d => {
                let visible = true;
                if (vendorFilter && d.vendor !== vendorFilter) visible = false;
                if (deviceTypeFilter && d.deviceType !== deviceTypeFilter) visible = false;
                return visible ? 1 : 0.2;
            });
    }
    
    /**
     * 操作按钮功能
     */
    connectToDevice() {
        if (!this.selectedNode) return;
        
        // 切换到终端页面并连接设备
        this.gotoTerminalPage();
        
        // 触发设备连接（需要集成到终端模块）
        setTimeout(() => {
            const event = new CustomEvent('connectDevice', {
                detail: { deviceId: this.selectedNode.id }
            });
            document.dispatchEvent(event);
        }, 100);
    }
    
    async pingDevice() {
        if (!this.selectedNode) return;
        
        alert(`Ping功能待实现: ${this.selectedNode.ip}`);
    }
    
    async discoverNeighbors() {
        if (!this.selectedNode) return;
        
        try {
            // 显示加载状态
            this.showLoading(true);
            
            const response = await fetch(`/api/devices/${this.selectedNode.id}/discover-neighbors`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 发现成功，重新加载拓扑但保持当前状态
                await this.loadTopologyData();
                
                // 显示成功消息
                alert(`发现邻居成功，找到 ${result.neighbor_count} 个邻居`);
                
                // 如果有数据，确保不显示空状态
                if (this.nodes.length > 0) {
                    this.showEmpty(false);
                }
            } else {
                throw new Error(result.message || '发现邻居失败');
            }
        } catch (error) {
            console.error('发现邻居失败:', error);
            alert('发现邻居失败: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * 加载拓扑数据（不改变UI状态）
     */
    async loadTopologyData() {
        try {
            const response = await fetch('/api/topology');
            const data = await response.json();
            
            if (data.success && data.topology) {
                this.updateTopology(data.topology);
                return true;
            } else {
                return false;
            }
        } catch (error) {
            console.error('加载拓扑数据失败:', error);
            return false;
        }
    }
    
    showDeviceProperties() {
        if (!this.selectedNode) return;
        
        // 切换到设备管理页面并高亮选中的设备
        this.gotoDevicesPage();
        
        setTimeout(() => {
            const event = new CustomEvent('highlightDevice', {
                detail: { deviceId: this.selectedNode.id }
            });
            document.dispatchEvent(event);
        }, 100);
    }
    
    /**
     * 页面导航
     */
    gotoDevicesPage() {
        const devicesNavLink = document.querySelector('.nav-link[data-page="devices"]');
        if (devicesNavLink) {
            devicesNavLink.click();
        }
    }
    
    gotoTerminalPage() {
        const terminalNavLink = document.querySelector('.nav-link[data-page="terminal"]');
        if (terminalNavLink) {
            terminalNavLink.click();
        }
    }
    
    /**
     * 工具函数
     */
    getVendorDisplayName(vendor) {
        const vendorNames = {
            cisco: 'Cisco',
            huawei: '华为',
            h3c: 'H3C',
            juniper: 'Juniper',
            other: '其他'
        };
        return vendorNames[vendor] || vendor;
    }
    
    getDeviceTypeDisplayName(deviceType) {
        const typeNames = {
            router: '路由器',
            switch: '交换机',
            firewall: '防火墙',
            wireless_controller: '无线控制器',
            access_point: '接入点',
            load_balancer: '负载均衡器',
            other: '其他'
        };
        return typeNames[deviceType] || deviceType;
    }
    
    getStatusDisplayName(status) {
        const statusNames = {
            online: '在线',
            offline: '离线',
            unreachable: '不可达',
            maintenance: '维护中',
            unknown: '未知'
        };
        return statusNames[status] || status;
    }
    
    /**
     * 获取状态颜色
     */
    getStatusColor(status) {
        const statusColors = {
            online: '#10b981',     // 绿色
            offline: '#ef4444',    // 红色
            unreachable: '#f59e0b', // 橙色
            maintenance: '#3b82f6', // 蓝色
            unknown: '#6b7280'     // 灰色
        };
        return statusColors[status] || statusColors.unknown;
    }
    
    /**
     * 获取厂商徽章文字
     */
    getVendorBadgeText(vendor) {
        const vendorTexts = {
            cisco: 'C',
            huawei: '华',
            h3c: 'H',
            juniper: 'J',
            other: '?'
        };
        return vendorTexts[vendor] || vendorTexts.other;
    }
    
    /**
     * 创建设备类型图标 (SVG) - 升级版本，更具设备特征
     */
    createDeviceIcon(deviceType, black = false) {
        const iconSize = 40; // 从32进一步增大到40
        const iconColor = black ? '#000000' : '#ffffff';
        const shadowColor = 'rgba(0,0,0,0.15)';
        
        const icons = {
            router: `
                <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" style="pointer-events: none;">
                    <defs>
                        <linearGradient id="routerGrad${black ? 'Black' : ''}" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:${iconColor};stop-opacity:0.9"/>
                            <stop offset="100%" style="stop-color:${black ? '#333333' : '#e5e7eb'};stop-opacity:0.8"/>
                        </linearGradient>
                        <filter id="routerShadow${black ? 'Black' : ''}">
                            <feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="${shadowColor}"/>
                        </filter>
                    </defs>
                    <g filter="url(#routerShadow${black ? 'Black' : ''})">
                        <!-- 路由器主机箱 -->
                        <rect x="2" y="8" width="20" height="8" rx="2" fill="url(#routerGrad${black ? 'Black' : ''})" stroke="${iconColor}" stroke-width="0.5"/>
                        <rect x="3" y="9" width="18" height="6" rx="1" fill="rgba(${black ? '255,255,255' : '0,0,0'},0.1)"/>
                        
                        <!-- 前面板指示灯 -->
                        <circle cx="5" cy="12" r="1" fill="#10b981"/>
                        <circle cx="7.5" cy="12" r="1" fill="#f59e0b"/>
                        <circle cx="10" cy="12" r="1" fill="#ef4444"/>
                        
                        <!-- 以太网端口 -->
                        <rect x="14" y="10.5" width="6" height="3" rx="0.5" fill="rgba(${black ? '255,255,255' : '0,0,0'},0.3)"/>
                        <rect x="14.5" y="11" width="1" height="2" rx="0.2" fill="${iconColor}"/>
                        <rect x="16" y="11" width="1" height="2" rx="0.2" fill="${iconColor}"/>
                        <rect x="17.5" y="11" width="1" height="2" rx="0.2" fill="${iconColor}"/>
                        <rect x="19" y="11" width="1" height="2" rx="0.2" fill="${iconColor}"/>
                        
                        <!-- WiFi天线 -->
                        <rect x="5" y="5" width="1.5" height="3" rx="0.5" fill="${iconColor}"/>
                        <rect x="8" y="4" width="1.5" height="4" rx="0.5" fill="${iconColor}"/>
                        <rect x="11" y="3" width="1.5" height="5" rx="0.5" fill="${iconColor}"/>
                        <rect x="14" y="4" width="1.5" height="4" rx="0.5" fill="${iconColor}"/>
                        <rect x="17" y="5" width="1.5" height="3" rx="0.5" fill="${iconColor}"/>
                        
                        <!-- 天线顶部 -->
                        <circle cx="5.75" cy="4.5" r="0.5" fill="#fbbf24"/>
                        <circle cx="8.75" cy="3.5" r="0.5" fill="#fbbf24"/>
                        <circle cx="11.75" cy="2.5" r="0.5" fill="#fbbf24"/>
                        <circle cx="14.75" cy="3.5" r="0.5" fill="#fbbf24"/>
                        <circle cx="17.75" cy="4.5" r="0.5" fill="#fbbf24"/>
                    </g>
                </svg>`,
            
            switch: `
                <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" style="pointer-events: none;">
                    <defs>
                        <linearGradient id="switchGrad${black ? 'Black' : ''}" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:${iconColor};stop-opacity:0.9"/>
                            <stop offset="100%" style="stop-color:${black ? '#333333' : '#e5e7eb'};stop-opacity:0.8"/>
                        </linearGradient>
                        <filter id="switchShadow${black ? 'Black' : ''}">
                            <feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="${shadowColor}"/>
                        </filter>
                    </defs>
                    <g filter="url(#switchShadow${black ? 'Black' : ''})">
                        <!-- 交换机主体 -->
                        <rect x="1" y="7" width="22" height="10" rx="2" fill="url(#switchGrad${black ? 'Black' : ''})" stroke="${iconColor}" stroke-width="0.5"/>
                        <rect x="2" y="8" width="20" height="8" rx="1" fill="rgba(${black ? '255,255,255' : '0,0,0'},0.1)"/>
                        
                        <!-- 前面板 -->
                        <rect x="2.5" y="8.5" width="19" height="7" rx="0.5" fill="rgba(${black ? '255,255,255' : '0,0,0'},0.05)"/>
                        
                        <!-- 端口灯光指示器 -->
                        <rect x="3" y="9.5" width="17" height="1" rx="0.5" fill="rgba(16,185,129,0.3)"/>
                        <rect x="3" y="11" width="17" height="1" rx="0.5" fill="rgba(245,158,11,0.3)"/>
                        
                        <!-- 网络端口组 1 -->
                        <rect x="3" y="13" width="1.8" height="1.5" rx="0.3" fill="${iconColor}" stroke="rgba(${black ? '255,255,255' : '0,0,0'},0.2)" stroke-width="0.3"/>
                        <rect x="5.2" y="13" width="1.8" height="1.5" rx="0.3" fill="${iconColor}" stroke="rgba(${black ? '255,255,255' : '0,0,0'},0.2)" stroke-width="0.3"/>
                        <rect x="7.4" y="13" width="1.8" height="1.5" rx="0.3" fill="${iconColor}" stroke="rgba(${black ? '255,255,255' : '0,0,0'},0.2)" stroke-width="0.3"/>
                        <rect x="9.6" y="13" width="1.8" height="1.5" rx="0.3" fill="${iconColor}" stroke="rgba(${black ? '255,255,255' : '0,0,0'},0.2)" stroke-width="0.3"/>
                        <rect x="11.8" y="13" width="1.8" height="1.5" rx="0.3" fill="${iconColor}" stroke="rgba(${black ? '255,255,255' : '0,0,0'},0.2)" stroke-width="0.3"/>
                        <rect x="14" y="13" width="1.8" height="1.5" rx="0.3" fill="${iconColor}" stroke="rgba(${black ? '255,255,255' : '0,0,0'},0.2)" stroke-width="0.3"/>
                        <rect x="16.2" y="13" width="1.8" height="1.5" rx="0.3" fill="${iconColor}" stroke="rgba(${black ? '255,255,255' : '0,0,0'},0.2)" stroke-width="0.3"/>
                        <rect x="18.4" y="13" width="1.8" height="1.5" rx="0.3" fill="${iconColor}" stroke="rgba(${black ? '255,255,255' : '0,0,0'},0.2)" stroke-width="0.3"/>
                        
                        <!-- 千兆上行端口 -->
                        <rect x="17" y="9" width="2.5" height="2" rx="0.3" fill="#3b82f6" stroke="${iconColor}" stroke-width="0.3"/>
                        <text x="18.25" y="10.5" text-anchor="middle" font-size="3" fill="${iconColor}" font-weight="bold">G</text>
                        
                        <!-- 状态LED -->
                        <circle cx="4" cy="10.5" r="0.4" fill="#10b981"/>
                        <circle cx="6" cy="10.5" r="0.4" fill="#10b981"/>
                        <circle cx="8" cy="10.5" r="0.4" fill="#f59e0b"/>
                        <circle cx="10" cy="10.5" r="0.4" fill="#10b981"/>
                        <circle cx="12" cy="10.5" r="0.4" fill="#10b981"/>
                    </g>
                </svg>`,
            
            firewall: `
                <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" style="pointer-events: none;">
                    <defs>
                        <linearGradient id="firewallGrad${black ? 'Black' : ''}" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:${black ? '#000000' : '#ef4444'};stop-opacity:0.9"/>
                            <stop offset="100%" style="stop-color:${black ? '#333333' : '#dc2626'};stop-opacity:0.8"/>
                        </linearGradient>
                        <filter id="firewallShadow${black ? 'Black' : ''}">
                            <feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="${shadowColor}"/>
                        </filter>
                    </defs>
                    <g filter="url(#firewallShadow${black ? 'Black' : ''})">
                        <!-- 盾牌外形 -->
                        <path d="M12 2L3 6v6c0 6.55 4.03 12.74 9 14 4.97-1.26 9-7.45 9-14V6l-9-4z" fill="url(#firewallGrad${black ? 'Black' : ''})" stroke="${iconColor}" stroke-width="0.5"/>
                        
                        <!-- 内部盾牌 -->
                        <path d="M12 3.5L4.5 7v5.5c0 5.8 3.5 10.6 7.5 11.8 4-1.2 7.5-6 7.5-11.8V7L12 3.5z" fill="rgba(${black ? '255,255,255' : '0,0,0'},0.1)"/>
                        
                        <!-- 防火墙图标 -->
                        <rect x="7" y="8" width="10" height="1" rx="0.5" fill="${iconColor}"/>
                        <rect x="7" y="10" width="10" height="1" rx="0.5" fill="${iconColor}"/>
                        <rect x="7" y="12" width="10" height="1" rx="0.5" fill="${iconColor}"/>
                        <rect x="7" y="14" width="10" height="1" rx="0.5" fill="${iconColor}"/>
                        
                        <!-- 中心锁 -->
                        <rect x="10" y="9.5" width="4" height="3.5" rx="0.5" fill="${iconColor}"/>
                        <rect x="10.5" y="10" width="3" height="2.5" rx="0.3" fill="${black ? '#000000' : '#ef4444'}"/>
                        <path d="M11.5 9.5v-1c0-0.8 0.7-1.5 1.5-1.5s1.5 0.7 1.5 1.5v1" stroke="${iconColor}" stroke-width="0.8" fill="none"/>
                        
                        <!-- 安全指示器 -->
                        <circle cx="8" cy="16" r="0.8" fill="#10b981"/>
                        <circle cx="12" cy="16" r="0.8" fill="#f59e0b"/>
                        <circle cx="16" cy="16" r="0.8" fill="#ef4444"/>
                    </g>
                </svg>`,
            
            wireless_controller: `
                <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" style="pointer-events: none;">
                    <defs>
                        <linearGradient id="wifiGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.9"/>
                            <stop offset="100%" style="stop-color:#1d4ed8;stop-opacity:0.8"/>
                        </linearGradient>
                        <filter id="wifiShadow">
                            <feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="${shadowColor}"/>
                        </filter>
                    </defs>
                    <g filter="url(#wifiShadow)">
                        <!-- 控制器主体 -->
                        <rect x="2" y="12" width="20" height="6" rx="2" fill="url(#wifiGrad)" stroke="${iconColor}" stroke-width="0.5"/>
                        <rect x="3" y="13" width="18" height="4" rx="1" fill="rgba(0,0,0,0.1)"/>
                        
                        <!-- WiFi信号波纹（大范围） -->
                        <path d="M12 9c-4 0-7.5 1.6-10 4.2L3.4 12C6.2 9.9 9 8.5 12 8.5s5.8 1.4 8.6 3.5L19.6 13.2C17.5 10.6 14 9 12 9z" fill="${iconColor}" opacity="0.3"/>
                        <path d="M12 6c-5.5 0-10.5 2.2-14 5.8L-0.6 10.4C3.3 6.4 7.5 4.5 12 4.5s8.7 1.9 12.6 5.9L23.4 11.8C19.5 8.2 14.5 6 12 6z" fill="${iconColor}" opacity="0.2"/>
                        
                        <!-- 中等信号波 -->
                        <path d="M12 11c-2.2 0-4.2 0.9-5.7 2.4l1.4 1.4c1-1 2.4-1.6 3.8-1.6s2.8 0.6 3.8 1.6l1.4-1.4C16.2 11.9 14.2 11 12 11z" fill="${iconColor}" opacity="0.6"/>
                        
                        <!-- 小信号波 -->
                        <circle cx="12" cy="15.5" r="1.5" fill="${iconColor}"/>
                        
                        <!-- 天线 -->
                        <rect x="6" y="9" width="1" height="3" rx="0.5" fill="${iconColor}"/>
                        <rect x="17" y="9" width="1" height="3" rx="0.5" fill="${iconColor}"/>
                        
                        <!-- 天线顶部 -->
                        <circle cx="6.5" cy="8.5" r="0.8" fill="#10b981"/>
                        <circle cx="17.5" cy="8.5" r="0.8" fill="#10b981"/>
                        
                        <!-- 前面板LED -->
                        <rect x="4" y="14.5" width="2" height="1" rx="0.3" fill="#10b981"/>
                        <rect x="7" y="14.5" width="2" height="1" rx="0.3" fill="#f59e0b"/>
                        <rect x="10" y="14.5" width="2" height="1" rx="0.3" fill="#ef4444"/>
                        
                        <!-- 接入点管理指示 -->
                        <text x="18" y="15.8" text-anchor="middle" font-size="3" fill="${iconColor}" font-weight="bold">AP</text>
                    </g>
                </svg>`,
            
            access_point: `
                <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" style="pointer-events: none;">
                    <defs>
                        <radialGradient id="apGrad" cx="50%" cy="50%" r="50%">
                            <stop offset="0%" style="stop-color:#ffffff;stop-opacity:0.9"/>
                            <stop offset="100%" style="stop-color:#d1d5db;stop-opacity:0.8"/>
                        </radialGradient>
                        <filter id="apShadow">
                            <feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="${shadowColor}"/>
                        </filter>
                    </defs>
                    <g filter="url(#apShadow)">
                        <!-- AP圆形外壳 -->
                        <circle cx="12" cy="15" r="7" fill="url(#apGrad)" stroke="${iconColor}" stroke-width="0.5"/>
                        <circle cx="12" cy="15" r="5.5" fill="rgba(0,0,0,0.05)"/>
                        
                        <!-- WiFi波纹效果 -->
                        <circle cx="12" cy="15" r="2" fill="none" stroke="#3b82f6" stroke-width="1.5" opacity="0.8"/>
                        <circle cx="12" cy="15" r="3.5" fill="none" stroke="#3b82f6" stroke-width="1" opacity="0.5"/>
                        <circle cx="12" cy="15" r="5" fill="none" stroke="#3b82f6" stroke-width="0.8" opacity="0.3"/>
                        
                        <!-- 中心发射点 -->
                        <circle cx="12" cy="15" r="1.2" fill="#3b82f6"/>
                        <circle cx="12" cy="15" r="0.6" fill="${iconColor}"/>
                        
                        <!-- 天线基座 -->
                        <rect x="11" y="7" width="2" height="8" rx="1" fill="${iconColor}" stroke="rgba(0,0,0,0.2)" stroke-width="0.3"/>
                        
                        <!-- 安装支架 -->
                        <rect x="9" y="6.5" width="6" height="2" rx="1" fill="${iconColor}" stroke="rgba(0,0,0,0.2)" stroke-width="0.3"/>
                        <rect x="10" y="5.5" width="4" height="1" rx="0.5" fill="rgba(0,0,0,0.1)"/>
                        
                        <!-- 状态指示灯 -->
                        <circle cx="12" cy="11" r="0.8" fill="#10b981"/>
                        
                        <!-- AP标识 -->
                        <text x="12" y="19" text-anchor="middle" font-size="3" fill="#6b7280" font-weight="bold">WiFi</text>
                    </g>
                </svg>`,
            
            load_balancer: `
                <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" style="pointer-events: none;">
                    <defs>
                        <linearGradient id="lbGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:0.9"/>
                            <stop offset="100%" style="stop-color:#7c3aed;stop-opacity:0.8"/>
                        </linearGradient>
                        <filter id="lbShadow">
                            <feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="${shadowColor}"/>
                        </filter>
                    </defs>
                    <g filter="url(#lbShadow)">
                        <!-- 负载均衡器主体 -->
                        <rect x="2" y="9" width="20" height="6" rx="2" fill="url(#lbGrad)" stroke="${iconColor}" stroke-width="0.5"/>
                        <rect x="3" y="10" width="18" height="4" rx="1" fill="rgba(0,0,0,0.1)"/>
                        
                        <!-- 负载均衡核心 -->
                        <circle cx="12" cy="12" r="2.5" fill="${iconColor}" stroke="rgba(0,0,0,0.2)" stroke-width="0.5"/>
                        <circle cx="12" cy="12" r="1.5" fill="#8b5cf6"/>
                        
                        <!-- 负载分配箭头 -->
                        <path d="M9 8l3 2 3-2" stroke="${iconColor}" stroke-width="1.5" fill="none" marker-end="url(#arrowhead)"/>
                        <path d="M9 16l3-2 3 2" stroke="${iconColor}" stroke-width="1.5" fill="none" marker-end="url(#arrowhead)"/>
                        
                        <!-- 连接线 -->
                        <line x1="5" y1="12" x2="9.5" y2="12" stroke="${iconColor}" stroke-width="2"/>
                        <line x1="14.5" y1="12" x2="19" y2="12" stroke="${iconColor}" stroke-width="2"/>
                        
                        <!-- 输入输出端点 -->
                        <circle cx="4" cy="12" r="1.5" fill="#10b981" stroke="${iconColor}" stroke-width="0.5"/>
                        <circle cx="20" cy="12" r="1.5" fill="#10b981" stroke="${iconColor}" stroke-width="0.5"/>
                        
                        <!-- 多个后端连接 -->
                        <circle cx="20" cy="9" r="0.8" fill="#3b82f6"/>
                        <circle cx="20" cy="12" r="0.8" fill="#10b981"/>
                        <circle cx="20" cy="15" r="0.8" fill="#f59e0b"/>
                        
                        <!-- LB标识 -->
                        <text x="12" y="12.8" text-anchor="middle" font-size="3" fill="${iconColor}" font-weight="bold">LB</text>
                        
                        <!-- 状态指示 -->
                        <circle cx="6" cy="10.5" r="0.5" fill="#10b981"/>
                        <circle cx="18" cy="10.5" r="0.5" fill="#10b981"/>
                    </g>
                </svg>`,
            
            server: `
                <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" style="pointer-events: none;">
                    <defs>
                        <linearGradient id="serverGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#6b7280;stop-opacity:0.9"/>
                            <stop offset="100%" style="stop-color:#4b5563;stop-opacity:0.8"/>
                        </linearGradient>
                        <filter id="serverShadow">
                            <feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="${shadowColor}"/>
                        </filter>
                    </defs>
                    <g filter="url(#serverShadow)">
                        <!-- 服务器机箱 -->
                        <rect x="4" y="3" width="16" height="18" rx="2" fill="url(#serverGrad)" stroke="${iconColor}" stroke-width="0.5"/>
                        <rect x="5" y="4" width="14" height="16" rx="1" fill="rgba(0,0,0,0.1)"/>
                        
                        <!-- 服务器单元 1 -->
                        <rect x="6" y="5" width="12" height="3" rx="0.5" fill="${iconColor}" stroke="rgba(0,0,0,0.2)" stroke-width="0.3"/>
                        <circle cx="7.5" cy="6.5" r="0.5" fill="#10b981"/>
                        <circle cx="9" cy="6.5" r="0.5" fill="#10b981"/>
                        <rect x="15" y="6" width="2" height="1" rx="0.2" fill="rgba(0,0,0,0.3)"/>
                        
                        <!-- 服务器单元 2 -->
                        <rect x="6" y="9" width="12" height="3" rx="0.5" fill="${iconColor}" stroke="rgba(0,0,0,0.2)" stroke-width="0.3"/>
                        <circle cx="7.5" cy="10.5" r="0.5" fill="#10b981"/>
                        <circle cx="9" cy="10.5" r="0.5" fill="#f59e0b"/>
                        <rect x="15" y="10" width="2" height="1" rx="0.2" fill="rgba(0,0,0,0.3)"/>
                        
                        <!-- 服务器单元 3 -->
                        <rect x="6" y="13" width="12" height="3" rx="0.5" fill="${iconColor}" stroke="rgba(0,0,0,0.2)" stroke-width="0.3"/>
                        <circle cx="7.5" cy="14.5" r="0.5" fill="#ef4444"/>
                        <circle cx="9" cy="14.5" r="0.5" fill="#6b7280"/>
                        <rect x="15" y="14" width="2" height="1" rx="0.2" fill="rgba(0,0,0,0.3)"/>
                        
                        <!-- 底部电源/连接部分 -->
                        <rect x="6" y="17" width="12" height="2" rx="0.5" fill="rgba(0,0,0,0.2)"/>
                        <rect x="7" y="17.5" width="2" height="1" rx="0.2" fill="#10b981"/>
                        <rect x="10" y="17.5" width="2" height="1" rx="0.2" fill="#3b82f6"/>
                        <rect x="13" y="17.5" width="2" height="1" rx="0.2" fill="#f59e0b"/>
                        <rect x="16" y="17.5" width="1" height="1" rx="0.2" fill="#ef4444"/>
                        
                        <!-- 散热孔 -->
                        <rect x="11" y="6" width="0.5" height="1" fill="rgba(0,0,0,0.3)"/>
                        <rect x="12.5" y="6" width="0.5" height="1" fill="rgba(0,0,0,0.3)"/>
                        <rect x="11" y="10" width="0.5" height="1" fill="rgba(0,0,0,0.3)"/>
                        <rect x="12.5" y="10" width="0.5" height="1" fill="rgba(0,0,0,0.3)"/>
                        <rect x="11" y="14" width="0.5" height="1" fill="rgba(0,0,0,0.3)"/>
                        <rect x="12.5" y="14" width="0.5" height="1" fill="rgba(0,0,0,0.3)"/>
                    </g>
                </svg>`,
            
            other: `
                <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" style="pointer-events: none;">
                    <defs>
                        <linearGradient id="otherGrad${black ? 'Black' : ''}" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:${iconColor};stop-opacity:0.9"/>
                            <stop offset="100%" style="stop-color:${black ? '#333333' : '#6b7280'};stop-opacity:0.8"/>
                        </linearGradient>
                        <filter id="otherShadow${black ? 'Black' : ''}">
                            <feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="${shadowColor}"/>
                        </filter>
                    </defs>
                    <g filter="url(#otherShadow${black ? 'Black' : ''})">
                        <!-- 通用网络设备外壳 -->
                        <rect x="3" y="8" width="18" height="8" rx="2" fill="url(#otherGrad${black ? 'Black' : ''})" stroke="${iconColor}" stroke-width="0.5"/>
                        <rect x="4" y="9" width="16" height="6" rx="1" fill="rgba(${black ? '255,255,255' : '0,0,0'},0.1)"/>
                        
                        <!-- 网络连接图标 -->
                        <circle cx="8" cy="12" r="2.5" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
                        <circle cx="16" cy="12" r="2.5" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
                        
                        <!-- 连接线 -->
                        <line x1="10.5" y1="12" x2="13.5" y2="12" stroke="${iconColor}" stroke-width="2"/>
                        
                        <!-- 数据流动指示 -->
                        <circle cx="11" cy="12" r="0.5" fill="#3b82f6"/>
                        <circle cx="12" cy="12" r="0.5" fill="#10b981"/>
                        <circle cx="13" cy="12" r="0.5" fill="#f59e0b"/>
                        
                        <!-- 状态指示灯 -->
                        <circle cx="5" cy="10" r="0.8" fill="#10b981"/>
                        <circle cx="19" cy="10" r="0.8" fill="#f59e0b"/>
                        <circle cx="5" cy="14" r="0.8" fill="#3b82f6"/>
                        <circle cx="19" cy="14" r="0.8" fill="#ef4444"/>
                        
                        <!-- 设备标识 -->
                        <text x="12" y="10.5" text-anchor="middle" font-size="2.5" fill="${iconColor}" font-weight="bold">NET</text>
                    </g>
                </svg>`
        };
        
        return icons[deviceType] || icons.other;
    }
    
    /**
     * 显示/隐藏状态
     */
    showLoading(show) {
        if (this.elements.topologyLoading) {
            this.elements.topologyLoading.style.display = show ? 'block' : 'none';
        }
    }
    
    showEmpty(show) {
        if (this.elements.topologyEmpty) {
            this.elements.topologyEmpty.style.display = show ? 'block' : 'none';
        }
        if (this.elements.topologySvg) {
            this.elements.topologySvg.style.display = show ? 'none' : 'block';
        }
    }
    
    /**
     * 模态框控制
     */
    showModal(modal) {
        if (modal) {
            modal.style.display = 'block';
        }
    }
    
    hideModal(modal) {
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    /**
     * 窗口大小改变处理
     */
    handleResize() {
        const container = this.elements.topologyCanvas;
        if (container) {
            this.width = container.clientWidth;
            this.height = container.clientHeight;
            
            this.svg
                .attr('width', this.width)
                .attr('height', this.height);
                
            this.simulation
                .force('center', d3.forceCenter(this.width / 2, this.height / 2))
                .alpha(0.3)
                .restart();
        }
    }
}

// 全局变量
let topologyVisualization = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('拓扑模块JavaScript已加载');
    
    // 将TopologyVisualization类暴露到全局作用域，供其他模块使用
    window.TopologyVisualization = TopologyVisualization;
    
    // 检查拓扑页面是否当前可见，如果是则立即初始化
    const topologyContent = document.getElementById('topology-content');
    if (topologyContent && topologyContent.style.display === 'block') {
        console.log('拓扑页面当前可见，立即初始化');
        try {
            topologyVisualization = new TopologyVisualization();
            window.topologyVisualization = topologyVisualization;
            console.log('拓扑可视化模块初始化成功');
        } catch (error) {
            console.error('拓扑可视化模块初始化失败:', error);
        }
    }
});

// 导出模块（如果需要）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TopologyVisualization;
} 