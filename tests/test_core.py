# test_core.py - VisitorReviewAutomation 单元测试

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from unittest.mock import patch, MagicMock
import pytest

from auto_audit_visitor_review.core import VisitorReviewAutomation


class TestVisitorReviewAutomation:
    """测试 VisitorReviewAutomation 类"""

    # ------------------------------------------------------------------
    # 基础 & 工具方法
    # ------------------------------------------------------------------

    def test_init(self):
        """测试初始化 - driver 应为 None"""
        automation = VisitorReviewAutomation()
        assert automation.driver is None

    def test_constants(self):
        """测试类常量"""
        automation = VisitorReviewAutomation()
        assert "peoplego.vankeservice.com" in automation.URL
        assert "phone=18208475905" in automation.URL
        assert automation._SELECTOR_TAB_2 == "div.van-tab:nth-child(2)"
        assert automation._SELECTOR_TAB_1 == "div.van-tab:nth-child(1)"
        assert automation._SELECTOR_PRIMARY_BTN == "button.van-button--primary"
        assert automation._SELECTOR_DIALOG_CONFIRM == "button.van-dialog__confirm"

    @patch("auto_audit_visitor_review.core.webdriver")
    def test_create_driver(self, mock_webdriver):
        """测试 _create_driver 创建 Edge driver"""
        mock_driver = MagicMock()
        mock_webdriver.Edge.return_value = mock_driver

        automation = VisitorReviewAutomation()
        automation._create_driver()

        mock_webdriver.Edge.assert_called_once()
        assert automation.driver is not None
        mock_driver.set_page_load_timeout.assert_called_once_with(30)

    def test_safe_quit_driver_noop_when_none(self):
        """测试 _safe_quit_driver 当 driver 为 None 时不报错"""
        automation = VisitorReviewAutomation()
        automation.driver = None
        automation._safe_quit_driver()

    def test_stop_noop_when_none(self):
        """测试 stop 当 driver 为 None 时不报错"""
        automation = VisitorReviewAutomation()
        automation.stop()

    # ------------------------------------------------------------------
    # _safe_wait_click
    # ------------------------------------------------------------------

    @patch("auto_audit_visitor_review.core.WebDriverWait")
    def test_safe_wait_click_success(self, mock_wait):
        """测试 _safe_wait_click 成功点击"""
        mock_element = MagicMock()
        mock_wait.return_value.until.return_value = mock_element

        automation = VisitorReviewAutomation()
        automation.driver = MagicMock()
        result = automation._safe_wait_click("div.test", wait_ms=1000, delay_ms=0)

        assert result is True
        mock_element.click.assert_called_once()

    @patch("auto_audit_visitor_review.core.WebDriverWait")
    def test_safe_wait_click_failure(self, mock_wait):
        """测试 _safe_wait_click 超时返回 False"""
        from selenium.common.exceptions import TimeoutException
        mock_wait.return_value.until.side_effect = TimeoutException()

        automation = VisitorReviewAutomation()
        automation.driver = MagicMock()
        result = automation._safe_wait_click("div.test", wait_ms=1000)

        assert result is False

    # ------------------------------------------------------------------
    # _element_exists
    # ------------------------------------------------------------------

    @patch("auto_audit_visitor_review.core.WebDriverWait")
    def test_element_exists_true(self, mock_wait):
        """测试 _element_exists 元素存在"""
        mock_wait.return_value.until.return_value = MagicMock()

        automation = VisitorReviewAutomation()
        automation.driver = MagicMock()
        result = automation._element_exists("div.test", timeout_ms=1000)

        assert result is True

    @patch("auto_audit_visitor_review.core.WebDriverWait")
    def test_element_exists_false(self, mock_wait):
        """测试 _element_exists 元素不存在"""
        from selenium.common.exceptions import TimeoutException
        mock_wait.return_value.until.side_effect = TimeoutException()

        automation = VisitorReviewAutomation()
        automation.driver = MagicMock()
        result = automation._element_exists("div.test", timeout_ms=1000)

        assert result is False

    # ------------------------------------------------------------------
    # run_cycle —— 流程编排（核心）
    #
    #   run_cycle() 控制 flow：
    #     step1 → step2(切已审核) → step3(切待审核) → ?
    #        ├── step4=True  → step5 → step6 → step7
    #        └── step4=False → step7
    #   step1/2/3 任一失败也走 step7
    #
    #   注：step6 里面才有 "审核成功" 日志的 _log.info()，
    #       这取决于当天是否有待审核单子，不在测试范围内。
    # ------------------------------------------------------------------

    def test_run_cycle_full_success_with_primary(self):
        """[flow] 有单：tab切换 + 同意 + 确认 + 关闭"""
        automation = VisitorReviewAutomation()
        with (
            patch.object(automation, "_step_1_open_url", return_value=True) as s1,
            patch.object(automation, "_step_2_click_tab2", return_value=True) as s2,
            patch.object(automation, "_step_3_click_tab1", return_value=True) as s3,
            patch.object(automation, "_step_4_check_primary", return_value=True) as s4,
            patch.object(automation, "_step_5_click_primary", return_value=True) as s5,
            patch.object(automation, "_step_6_click_confirm", return_value=True) as s6,
            patch.object(automation, "_step_7_close_tab") as s7,
        ):
            automation.run_cycle()

        s1.assert_called_once()
        s2.assert_called_once()
        s3.assert_called_once()
        s4.assert_called_once()
        s5.assert_called_once()
        s6.assert_called_once()
        s7.assert_called_once()

    def test_run_cycle_tab_switching_no_pending(self):
        """[flow] 无单：tab切换 → 无同意按钮 → 跳过点击直接关闭"""
        automation = VisitorReviewAutomation()
        with (
            patch.object(automation, "_step_1_open_url", return_value=True) as s1,
            patch.object(automation, "_step_2_click_tab2", return_value=True) as s2,
            patch.object(automation, "_step_3_click_tab1", return_value=True) as s3,
            patch.object(automation, "_step_4_check_primary", return_value=False) as s4,
            patch.object(automation, "_step_5_click_primary") as s5,
            patch.object(automation, "_step_6_click_confirm") as s6,
            patch.object(automation, "_step_7_close_tab") as s7,
        ):
            automation.run_cycle()

        # tab 切换必须执行
        s1.assert_called_once()
        s2.assert_called_once()
        s3.assert_called_once()
        s4.assert_called_once()
        # 无单 → 不点击
        s5.assert_not_called()
        s6.assert_not_called()
        # 直接关闭
        s7.assert_called_once()

    def test_run_cycle_step1_failure_stops(self):
        """[flow] step1 打开页面失败 → 仅执行 step7"""
        automation = VisitorReviewAutomation()
        with (
            patch.object(automation, "_step_1_open_url", return_value=False) as s1,
            patch.object(automation, "_step_2_click_tab2") as s2,
            patch.object(automation, "_step_3_click_tab1") as s3,
            patch.object(automation, "_step_4_check_primary") as s4,
            patch.object(automation, "_step_5_click_primary") as s5,
            patch.object(automation, "_step_6_click_confirm") as s6,
            patch.object(automation, "_step_7_close_tab") as s7,
        ):
            automation.run_cycle()

        s1.assert_called_once()
        s2.assert_not_called()
        s3.assert_not_called()
        s4.assert_not_called()
        s5.assert_not_called()
        s6.assert_not_called()
        s7.assert_called_once()

    def test_run_cycle_step2_failure_stops(self):
        """[flow] 切已审核(tab2)失败 → 跳过后续关闭"""
        automation = VisitorReviewAutomation()
        with (
            patch.object(automation, "_step_1_open_url", return_value=True) as s1,
            patch.object(automation, "_step_2_click_tab2", return_value=False) as s2,
            patch.object(automation, "_step_3_click_tab1") as s3,
            patch.object(automation, "_step_4_check_primary") as s4,
            patch.object(automation, "_step_5_click_primary") as s5,
            patch.object(automation, "_step_6_click_confirm") as s6,
            patch.object(automation, "_step_7_close_tab") as s7,
        ):
            automation.run_cycle()

        s1.assert_called_once()
        s2.assert_called_once()
        s3.assert_not_called()
        s4.assert_not_called()
        s5.assert_not_called()
        s6.assert_not_called()
        s7.assert_called_once()

    def test_run_cycle_step3_failure_stops(self):
        """[flow] 切待审核(tab1)失败 → 跳过后续关闭"""
        automation = VisitorReviewAutomation()
        with (
            patch.object(automation, "_step_1_open_url", return_value=True) as s1,
            patch.object(automation, "_step_2_click_tab2", return_value=True) as s2,
            patch.object(automation, "_step_3_click_tab1", return_value=False) as s3,
            patch.object(automation, "_step_4_check_primary") as s4,
            patch.object(automation, "_step_5_click_primary") as s5,
            patch.object(automation, "_step_6_click_confirm") as s6,
            patch.object(automation, "_step_7_close_tab") as s7,
        ):
            automation.run_cycle()

        s1.assert_called_once()
        s2.assert_called_once()
        s3.assert_called_once()
        s4.assert_not_called()
        s5.assert_not_called()
        s6.assert_not_called()
        s7.assert_called_once()

    def test_run_cycle_step5_failure_stops(self):
        """[flow] 有单但点击同意失败 → 关闭"""
        automation = VisitorReviewAutomation()
        with (
            patch.object(automation, "_step_1_open_url", return_value=True) as s1,
            patch.object(automation, "_step_2_click_tab2", return_value=True) as s2,
            patch.object(automation, "_step_3_click_tab1", return_value=True) as s3,
            patch.object(automation, "_step_4_check_primary", return_value=True) as s4,
            patch.object(automation, "_step_5_click_primary", return_value=False) as s5,
            patch.object(automation, "_step_6_click_confirm") as s6,
            patch.object(automation, "_step_7_close_tab") as s7,
        ):
            automation.run_cycle()

        s1.assert_called_once()
        s2.assert_called_once()
        s3.assert_called_once()
        s4.assert_called_once()
        s5.assert_called_once()
        s6.assert_not_called()
        s7.assert_called_once()

    def test_run_cycle_step6_failure_stops(self):
        """[flow] 有单但确认弹窗失败 → 关闭"""
        automation = VisitorReviewAutomation()
        with (
            patch.object(automation, "_step_1_open_url", return_value=True) as s1,
            patch.object(automation, "_step_2_click_tab2", return_value=True) as s2,
            patch.object(automation, "_step_3_click_tab1", return_value=True) as s3,
            patch.object(automation, "_step_4_check_primary", return_value=True) as s4,
            patch.object(automation, "_step_5_click_primary", return_value=True) as s5,
            patch.object(automation, "_step_6_click_confirm", return_value=False) as s6,
            patch.object(automation, "_step_7_close_tab") as s7,
        ):
            automation.run_cycle()

        s1.assert_called_once()
        s2.assert_called_once()
        s3.assert_called_once()
        s4.assert_called_once()
        s5.assert_called_once()
        s6.assert_called_once()
        s7.assert_called_once()

    # ------------------------------------------------------------------
    # _step_6 日志写入验证
    # ------------------------------------------------------------------

    def test_step6_logs_success(self):
        """step6 成功时写入 '审核成功' 到日志"""
        automation = VisitorReviewAutomation()
        automation.driver = MagicMock()

        with patch.object(automation, "_safe_wait_click", return_value=True):
            automation._step_6_click_confirm()

        automation._log.info.assert_any_call("审核成功")

    def test_step6_does_not_log_on_failure(self):
        """step6 失败时 info 不写入 ('审核成功' 不会出现)"""
        automation = VisitorReviewAutomation()
        automation.driver = MagicMock()

        with patch.object(automation, "_safe_wait_click", return_value=False):
            automation._step_6_click_confirm()

        automation._log.info.assert_not_called()
