# __main__.py - 程序入口

import sys

from easycheck_manager import WebDriverManager
from auto_audit_visitor_review.core import VisitorReviewAutomation


def main():
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


if __name__ == "__main__":
    main()
