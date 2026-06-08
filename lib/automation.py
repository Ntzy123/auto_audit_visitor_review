# automation.py

import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class VisitorReviewAutomation:
    def __init__(self):
        self.driver = None

    def _create_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("detach", True)
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
    # Step implementations

    URL = (
        "https://peoplego.vankeservice.com/#/Embed/visitorReview/pending"
        "?phone=18208475905"
        "&name=%E8%8A%B1%E6%A2%A6%E8%8E%B2"
        "&id=2462900"
        "&projectCode=52010017"
    )

    SELECTOR_TAB_2 = "div.van-tab:nth-child(2)"
    SELECTOR_TAB_1 = "div.van-tab:nth-child(1)"
    SELECTOR_PRIMARY_BTN = "button.van-button--primary"
    SELECTOR_DIALOG_CONFIRM = "button.van-dialog__confirm"

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
            print("  [Step1] 页面加载完成")
            return True
        except WebDriverException as e:
            print(f"  [Step1] 打开页面失败: {e}")
            return False

    def _step_2_click_tab2(self):
        ok = self._safe_wait_click(self.SELECTOR_TAB_2, 5000, 800)
        if ok:
            print("  [Step2] 点击<已审核>标签页成功")
        else:
            print("  [Step2] 点击<已审核>标签页失败")
        return ok

    def _step_3_click_tab1(self):
        ok = self._safe_wait_click(self.SELECTOR_TAB_1, 5000, 3000)
        if ok:
            print("  [Step3] 点击<待审核>标签页成功")
        else:
            print("  [Step3] 点击<待审核>标签页失败")
        return ok

    def _step_4_check_primary(self):
        exists = self._element_exists(self.SELECTOR_PRIMARY_BTN, 3000)
        time.sleep(0.3)
        if exists:
            print("  [Step4] 检测到同意按钮")
        else:
            print("  [Step4] 未检测到同意按钮")
        return exists

    def _step_5_click_primary(self):
        ok = self._safe_wait_click(self.SELECTOR_PRIMARY_BTN, 5000, 400)
        if ok:
            print("  [Step5] 点击同意按钮成功")
        else:
            print("  [Step5] 点击同意按钮失败")
        return ok

    def _step_6_click_confirm(self):
        ok = self._safe_wait_click(self.SELECTOR_DIALOG_CONFIRM, 5000, 3000)
        if ok:
            print("  [Step6] 点击弹窗确认按钮成功")
        else:
            print("  [Step6] 点击弹窗确认按钮失败")
        return ok

    def _step_7_close_tab(self):
        print("  [Step7] 关闭标签页，准备下一轮")
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
        except WebDriverException as e:
            print(f"  [Step7] 关闭标签页时出错: {e}")

    # Cycle and main loop

    def run_cycle(self):
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
        while True:
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"\n")
            print(f"[{now}]")
            #print(f"{'='*45}")
            try:
                if self.driver is None:
                    self._create_driver()
                self.run_cycle()
                time.sleep(1)
            except WebDriverException as e:
                print(f"  [主循环] WebDriver异常: {e}")
                print("  [主循环] 正在重新创建驱动...")
                self._safe_quit_driver()
                self.driver = None
                time.sleep(3)
            except Exception as e:
                print(f"  [主循环] 未知异常: {e}")
                print("  [主循环] 3秒后自动重试...")
                time.sleep(3)

    def _safe_quit_driver(self):
        if self.driver is None:
            return
        try:
            self.driver.quit()
        except Exception:
            pass

    def stop(self):
        self._safe_quit_driver()
