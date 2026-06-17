# conftest.py - pytest 共享 fixtures

import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))


@pytest.fixture(autouse=True)
def _mock_logging():
    """自动 mock 日志模块，避免测试时写 log 文件"""
    with patch(
        "auto_audit_visitor_review.core._get_logger",
        return_value=MagicMock(),
    ):
        with patch("auto_audit_visitor_review.core._log_success"):
            with patch("auto_audit_visitor_review.core._daily_maintenance"):
                with patch("auto_audit_visitor_review.core._finalize_prev_log"):
                    with patch("auto_audit_visitor_review.core._trim_old_entries"):
                        yield
