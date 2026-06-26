# conftest.py - pytest 共享 fixtures

import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))


@pytest.fixture(autouse=True)
def _mock_all():
    """自动 mock 日志 & 配置模块，避免测试时写文件和读取真实 config"""
    with patch(
        "auto_audit_visitor_review.core._get_logger",
        return_value=MagicMock(),
    ):
        with patch("auto_audit_visitor_review.core._log_success"):
            with patch("auto_audit_visitor_review.core._daily_maintenance"):
                with patch("auto_audit_visitor_review.core._finalize_prev_log"):
                    with patch("auto_audit_visitor_review.core._trim_old_entries"):
                        with patch(
                            "auto_audit_visitor_review.core.load_config",
                            return_value={
                                "phone": "18208475905",
                                "name": "花梦莲",
                                "uid": "2462900",
                                "project_code": "52010017",
                            },
                        ):
                            with patch(
                                "auto_audit_visitor_review.core.build_url",
                                return_value=(
                                    "https://peoplego.vankeservice.com/#/Embed"
                                    "/visitorReview/pending?phone=18208475905"
                                    "&name=%E8%8A%B1%E6%A2%A6%E8%8E%B2"
                                    "&id=2462900"
                                    "&projectCode=52010017"
                                ),
                            ):
                                yield
