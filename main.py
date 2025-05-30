"""
NetBrain MCP 主模块
"""

import logging
import sys
from server import mcp

def main():
    """主函数，启动NetBrain MCP服务器"""
    # 设置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(stream=sys.stdout)
        ]
    )
    logger = logging.getLogger("netbrain_mcp")
    
    logger.info("正在启动NetBrain MCP服务器...")
    
    # 启动MCP服务器
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("收到中断信号，关闭服务器...")
    except Exception as e:
        logger.error(f"服务器运行时出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
