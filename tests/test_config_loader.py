# test_config_loader.py - config_loader 单元测试

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import os.path

from unittest.mock import patch, MagicMock
import pytest

from auto_audit_visitor_review.config_loader import build_url, ensure_config, load_config


class TestBuildUrl:
    """测试 build_url"""

    def test_build_url_with_chinese_name(self):
        """中文名应被 URL 编码"""
        config = {
            "phone": "18208475905",
            "name": "花梦莲",
            "uid": "2462900",
            "project_code": "52010017",
        }
        url = build_url(config)
        assert "peoplego.vankeservice.com" in url
        assert "phone=18208475905" in url
        assert "%E8%8A%B1%E6%A2%A6%E8%8E%B2" in url  # URL-encoded 花梦莲
        assert "id=2462900" in url
        assert "projectCode=52010017" in url

    def test_build_url_with_ascii_name(self):
        """纯英文名不需要编码"""
        config = {
            "phone": "18085009482",
            "name": "libo",
            "uid": "1702071",
            "project_code": "52010017",
        }
        url = build_url(config)
        assert "name=libo" in url


class TestEnsureConfig:
    """测试 ensure_config"""

    @patch("auto_audit_visitor_review.config_loader._project_root")
    @patch("auto_audit_visitor_review.config_loader.os.path.exists")
    def test_ensure_config_exists(self, mock_exists, mock_root):
        """config 已存在时直接返回路径"""
        mock_root.return_value = os.path.join("", "fake", "root")
        mock_exists.return_value = True

        path = ensure_config()
        assert path == os.path.join("", "fake", "root", "config.toml")

    @patch("auto_audit_visitor_review.config_loader._project_root")
    @patch("auto_audit_visitor_review.config_loader.os.path.exists")
    @patch("auto_audit_visitor_review.config_loader.open")
    def test_ensure_config_creates_default(self, mock_open, mock_exists, mock_root):
        """config 不存在时生成默认配置"""
        mock_root.return_value = os.path.join("", "fake", "root")
        mock_exists.return_value = False

        path = ensure_config()
        expected = os.path.join("", "fake", "root", "config.toml")
        mock_open.assert_called_once_with(expected, "w", encoding="utf-8")
        assert path == expected
