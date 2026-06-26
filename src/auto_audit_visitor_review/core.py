# core.py - 访客审核自动化核心逻辑

import logging
import os
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from auto_audit_visitor_review.config_loader import load_config, build_url

# ---------------------------------------------------------------------------
# 日志子系统
#   aavr.log           —— 实时运行日志（所有操作），保留 48 小时
#   aavr_YYYYMMDD.log  —— 每日审核成功汇总，日终自动追加统计行
# ---------------------------------------------------------------------------

LOG_DIR = "log"
LOG_FILE = os.path.join(LOG_DIR, "aavr.log")
_logger = None
_daily_finalized_date = None  # 最后处理过的日期（YYYYMMDD）


def _get_logger():
    """获取 logger 实例，首次调用时初始化 aavr.log。"""
    global _logger
    if _logger is None:
        _logger = logging.getLogger("aavr")
        _logger.setLevel(logging.INFO)
        _logger.propagate = False
        _ensure_log()
    return _logger


def _ensure_log():
    """确保日志目录存在、aavr.log handler 已就绪。"""
    os.makedirs(LOG_DIR, exist_ok=True)
    for h in _logger.handlers[:]:
        h.close()
        _logger.removeHandler(h)
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    _logger.addHandler(handler)


def _log_success():
    """将 '审核成功' 追加到当日汇总文件 aavr_YYYYMMDD.log。"""
    log_file = os.path.join(LOG_DIR, f"aavr_{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 审核成功\n")


def _daily_maintenance():
    """跨日维护：汇总前一日日志 + 清理 aavr.log 旧条目。"""
    global _daily_finalized_date
    today = datetime.now().strftime("%Y%m%d")
    if today == _daily_finalized_date:
        return

    # 为前一天的日志文件追加汇总行
    if _daily_finalized_date is not None:
        _finalize_prev_log(_daily_finalized_date)

    _daily_finalized_date = today
    _trim_old_entries()


def _finalize_prev_log(date_str):
    """在指定日期的汇总日志文件开头插入当日统计行。"""
    log_file = os.path.join(LOG_DIR, f"aavr_{date_str}.log")
    if not os.path.exists(log_file):
        return
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    success_count = sum(1 for line in lines if "审核成功" in line)
    if success_count == 0:
        return

    date_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    summary = f"[{date_fmt}] 处理了 {success_count} 条人行助手审核\n\n"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(summary)
        f.writelines(lines)


def _trim_old_entries():
    """删除 aavr.log 中昨天以前（不含昨天）的日志条目。
    
    按"日期行 + 附属行"为一组整体判断：非日期行（如 stacktrace 等）
    跟随前一条日期行的保留策略，不会独立存活。
    """
    if not os.path.exists(LOG_FILE):
        return
    cutoff = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    kept = []
    in_range = False  # 当前条目是否在保留范围内

    for line in lines:
        # 判断是否为新的日志条目（以 YYYY-MM-DD 开头）
        is_new_entry = (
            len(line) >= 10
            and line[0:4].isdigit()
            and line[4] == "-"
        )
        if is_new_entry:
            in_range = line[:10] >= cutoff

        if in_range:
            kept.append(line)

    if len(kept) < len(lines):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(kept)


# ---------------------------------------------------------------------------
# 核心自动化类
# ---------------------------------------------------------------------------

class VisitorReviewAutomation:
    """访客审核自动化流程"""

    def __init__(self):
        self.driver = None
        self._log = _get_logger()
        self._config = load_config()
        self.URL = build_url(self._config)

    _SELECTOR_TAB_2 = "div.van-tab:nth-child(2)"
    _SELECTOR_TAB_1 = "div.van-tab:nth-child(1)"
    _SELECTOR_PRIMARY_BTN = "button.van-button--primary"
    _SELECTOR_DIALOG_CONFIRM = "button.van-dialog__confirm"

    def _create_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        service = Service()
        self.driver = webdriver.Edge(service=service, options=options)
        self.driver.set_page_load_timeout(30)

    def _safe_wait_click(self, selector, wait_ms=5000, delay_ms=0):
        try:
            element = WebDriverWait(self.driver, wait_ms / 1000).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            return True
        except (TimeoutException, WebDriverException):
            return False

    def _element_exists(self, selector, timeout_ms=5000):
        try:
            WebDriverWait(self.driver, timeout_ms / 1000).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except (TimeoutException, WebDriverException):
            return False

    def _step_1_open_url(self):
        try:
            handles = self.driver.window_handles
            for h in handles[:-1]:
                try:
                    self.driver.switch_to.window(h)
                    self.driver.close()
                except WebDriverException:
                    pass
            if self.driver.window_handles:
                self.driver.switch_to.window(self.driver.window_handles[0])
            self.driver.get(self.URL)
            time.sleep(1)
            self._log.info("  [Step1] 页面加载完成")
            return True
        except WebDriverException as e:
            self._log.error("  [Step1] 打开页面失败: %s", e)
            return False

    def _step_2_click_tab2(self):
        ok = self._safe_wait_click(self._SELECTOR_TAB_2, 5000, 800)
        if ok:
            self._log.info("  [Step2] 点击<已审核>标签页成功")
        else:
            self._log.warning("  [Step2] 点击<已审核>标签页失败")
        return ok

    def _step_3_click_tab1(self):
        ok = self._safe_wait_click(self._SELECTOR_TAB_1, 5000, 3000)
        if ok:
            self._log.info("  [Step3] 点击<待审核>标签页成功")
        else:
            self._log.warning("  [Step3] 点击<待审核>标签页失败")
        return ok

    def _step_4_check_primary(self):
        exists = self._element_exists(self._SELECTOR_PRIMARY_BTN, 3000)
        time.sleep(0.3)
        if exists:
            self._log.info("  [Step4] 检测到同意按钮")
        else:
            self._log.info("  [Step4] 未检测到同意按钮")
        return exists

    def _step_5_click_primary(self):
        ok = self._safe_wait_click(self._SELECTOR_PRIMARY_BTN, 5000, 400)
        if ok:
            self._log.info("  [Step5] 点击同意按钮成功")
        else:
            self._log.warning("  [Step5] 点击同意按钮失败")
        return ok

    def _step_6_click_confirm(self):
        ok = self._safe_wait_click(self._SELECTOR_DIALOG_CONFIRM, 5000, 3000)
        if ok:
            self._log.info("  [Step6] 点击弹窗确认按钮成功")
            self._log.info("审核成功")
            _log_success()
        else:
            self._log.warning("  [Step6] 点击弹窗确认按钮失败")
        return ok

    def _step_7_close_tab(self):
        try:
            handles = self.driver.window_handles
            for h in handles[:-1]:
                try:
                    self.driver.switch_to.window(h)
                    self.driver.close()
                except WebDriverException:
                    pass
            if self.driver.window_handles:
                self.driver.switch_to.window(self.driver.window_handles[0])
            self._log.info("  [Step7] 关闭标签页，准备下一轮")
        except WebDriverException as e:
            self._log.error("  [Step7] 关闭标签页时出错: %s", e)

    def run_cycle(self):
        """执行单轮审核流程"""
        if not self._step_1_open_url():
            self._step_7_close_tab()
            return
        if not self._step_2_click_tab2():
            self._step_7_close_tab()
            return
        if not self._step_3_click_tab1():
            self._step_7_close_tab()
            return
        if self._step_4_check_primary():
            if not self._step_5_click_primary():
                self._step_7_close_tab()
                return
            if not self._step_6_click_confirm():
                self._step_7_close_tab()
                return
        self._step_7_close_tab()

    def run(self):
        """主循环 - 7x24小时不间断运行"""
        while True:
            # 跨日维护：汇总前一日 + 清理 aavr.log
            _daily_maintenance()

            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"\n[{now}] 运行中...")
            try:
                if self.driver is None:
                    self._create_driver()
                self.run_cycle()
                time.sleep(1)
            except WebDriverException as e:
                print("  [主循环] WebDriver异常，正在重新创建驱动...")
                self._log.error("  [主循环] WebDriver异常: %s", e)
                self._safe_quit_driver()
                self.driver = None
                time.sleep(3)
            except Exception as e:
                print("  [主循环] 未知异常，3秒后自动重试...")
                self._log.error("  [主循环] 未知异常: %s", e)
                time.sleep(3)

    def _safe_quit_driver(self):
        if self.driver is None:
            return
        try:
            self.driver.quit()
        except Exception:
            pass

    def stop(self):
        """停止自动化流程"""
        if _daily_finalized_date is not None:
            _finalize_prev_log(_daily_finalized_date)
        self._safe_quit_driver()
