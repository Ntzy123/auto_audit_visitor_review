# run.py

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.webdriver_manager import WebDriverManager
from lib.automation import VisitorReviewAutomation


if __name__ == "__main__":
    print("=" * 55)
    print("  EdgeDriver 环境检查")
    print("=" * 55)
    manager = WebDriverManager()
    manager.start()

    print("\n" + "=" * 55)
    print("  开始自动化审核流程")
    print("=" * 55)
    automation = VisitorReviewAutomation()
    try:
        automation.run()
    except KeyboardInterrupt:
        print("\n  收到中断信号，正在退出...")
        automation.stop()
        sys.exit(0)
