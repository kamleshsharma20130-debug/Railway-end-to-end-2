import os
import sys
import time
import random
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException
)

# =========================================================
#               RAILWAY REAL-TIME LOGGING FIX
# =========================================================
os.environ["PYTHONUNBUFFERED"] = "1"

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

logger = logging.getLogger("railway")

def log(msg=""):
    logger.info(msg)

def clear_screen():
    pass

def success(msg):
    log(f"[SUCCESS] {msg}")

def error(msg):
    log(f"[ERROR] {msg}")

def info(msg):
    log(f"[INFO] {msg}")

def get_current_time():

    ist = ZoneInfo("Asia/Kolkata")

    return datetime.now(ist).strftime(
        "%d-%m-%Y %I:%M:%S %p IST"
    )
    
# =========================================================
#                   MAIN CLASS
# =========================================================
class FacebookMessenger:

    def __init__(self):

        self.driver = None
        self.wait = None

        self.cookie_str = ""
        self.target_uid = ""
        self.messages = []

        self.haters_name = ""
        self.delay = 10

        # MEMORY CLEANUP INTERVAL
        self.cleanup_interval = 5
        
        # DRIVER RESTART TRACKER
        self.restart_count = 0
        self.max_restart = 999999

    # =====================================================
    #               SAFE WAIT FUNCTION
    # =====================================================
    def safe_wait(self, condition, timeout=60):

        try:
            return WebDriverWait(
                self.driver,
                timeout,
                poll_frequency=0.5
            ).until(condition)

        except TimeoutException:
            return False

    # =====================================================
    #               DRIVER HEALTH CHECK
    # =====================================================
    def driver_alive(self):

        try:

            self.driver.execute_script(
                "return 1"
            )

            return True

        except Exception as e:

            error(f"DRIVER DEAD : {e}")

            return False

    # =====================================================
    #               FULL DRIVER RECOVERY
    # =====================================================
    def recover_driver(self):

        try:

            info("STARTING DRIVER RECOVERY")

            self.restart_count += 1

            try:
                self.driver.quit()
            except:
                pass

            time.sleep(5)

            # NEW DRIVER
            if not self.setup_driver():
                raise Exception("NEW DRIVER FAILED")

            # LOGIN AGAIN
            if not self.login_with_cookies():
                raise Exception("RE-LOGIN FAILED")

            # OPEN CHAT AGAIN
            self.driver.get(
                f"https://www.facebook.com/messages/e2ee/t/{self.target_uid}"
            )

            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                120
            )

            if not loaded:
                raise Exception("CHAT LOAD FAILED")

            ready = self.safe_wait(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@contenteditable='true']"
                    )
                ),
                120
            )

            if not ready:
                raise Exception("CHAT BOX FAILED")

            success(
                f"DRIVER RECOVERY SUCCESS | RESTART #{self.restart_count}"
            )

            return True

        except Exception as e:

            error(f"RECOVERY FAILED : {e}")

            return False

    # =====================================================
    #               SOFT RESET TAB
    # =====================================================
    def soft_refresh_chat(self):

        try:

            info("SOFT RESETTING TAB")

            # DESTROY OLD HEAVY TAB
            self.driver.get("about:blank")

            time.sleep(2)

            # REOPEN SAME SESSION CHAT
            self.driver.get(
                f"https://www.facebook.com/messages/e2ee/t/{self.target_uid}"
            )

            # WAIT FULL LOAD
            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                120
            )

            if not loaded:
                raise Exception("CHAT PAGE LOAD FAILED")

            # WAIT MESSAGE BOX
            ready = self.safe_wait(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@contenteditable='true']"
                    )
                ),
                120
            )

            if not ready:
                raise Exception("CHAT BOX LOAD FAILED")

            success("TAB SOFT RESET COMPLETE")

            return True

        except Exception as e:

            error(f"SOFT RESET FAILED : {e}")

            return False

    # =====================================================
    #                   AUTO LOAD
    # =====================================================
    def auto_load(self):

        try:

            self.cookie_str = open(
                "cookies.txt",
                "r",
                encoding="utf-8"
            ).read().strip()

            self.target_uid = open(
                "target_uid.txt",
                "r",
                encoding="utf-8"
            ).read().strip()

            self.messages = [
                x.strip()
                for x in open(
                    "messages.txt",
                    "r",
                    encoding="utf-8"
                )
                if x.strip()
            ]

            if os.path.exists("hatersname.txt"):

                self.haters_name = open(
                    "hatersname.txt",
                    "r",
                    encoding="utf-8"
                ).read().strip()

            if os.path.exists("time.txt"):

                self.delay = int(
                    open("time.txt").read().strip()
                )

            if (
                not self.cookie_str
                or not self.target_uid
                or not self.messages
            ):
                raise Exception("FILES EMPTY OR MISSING")

            success("ALL FILES AUTO-LOADED SUCCESSFULLY")

            log(
                f"[CONFIG] "
                f"[TARGET: {self.target_uid}] "
                f"[TOTAL_MSGS: {len(self.messages)}] "
                f"[DELAY: {self.delay}s]"
            )

            return True

        except Exception as e:

            error(f"AUTO LOAD FAILED : {e}")

            return False

    # =====================================================
    #                   DRIVER SETUP
    # =====================================================
    def setup_driver(self):

        try:

            options = Options()

            # =================================================
            #           HEADLESS + STABLE MODE
            # =================================================

            options.add_argument("--headless=old")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            options.page_load_strategy = "eager"

            # =================================================
            #               MEMORY OPTIMIZATION
            # =================================================

            options.add_argument("--max_old_space_size=128")

            options.add_argument(
                "--disable-renderer-backgrounding"
            )

            options.add_argument(
                "--disable-background-timer-throttling"
            )

            options.add_argument(
                "--disable-backgrounding-occluded-windows"
            )

            options.add_argument("--disable-gpu")

            options.add_argument(
                "--disable-features=CalculateNativeWinOcclusion"
            )

            options.add_argument("--disable-breakpad")

            options.add_argument(
                "--disable-component-update"
            )

            # =================================================
            #               IMAGE DISABLE
            # =================================================            
            options.add_argument(
                "--blink-settings=imagesEnabled=false"
            )

            # =================================================
            #               EXTRA PERFORMANCE
            # =================================================

            options.add_argument("--disable-extensions")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-infobars")

            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--disable-default-apps")
            
            # =================================================
            #               CRASH PREVENTION
            # =================================================

            options.add_argument("--memory-pressure-off")

            options.add_argument(
                "--disable-ipc-flooding-protection"
            )

            options.add_argument(
                "--renderer-process-limit=1"
            )

            options.add_argument("--single-process")

            options.add_argument("--window-size=1280,720")

            # =================================================
            #               CHROME LOG REDUCTION
            # =================================================

            options.add_argument("--log-level=3")

            options.add_experimental_option(
                "excludeSwitches",
                ["enable-logging"]
            )

            service = Service(
                "/usr/bin/chromedriver"
            )

            self.driver = webdriver.Chrome(
                service=service,
                options=options
            )

            self.wait = WebDriverWait(
                self.driver,
                40
            )

            success("CHROME DRIVER STARTED")
            success("LOW MEMORY MODE ENABLED")
            success("RAILWAY LOGGING FIX ENABLED")

            return True

        except Exception as e:

            error(f"DRIVER ERROR : {e}")

            return False

    # =====================================================
    #           LOGIN USING COOKIES (STABLE)
    # =====================================================
    def login_with_cookies(self):

        try:

            info("OPENING FACEBOOK")

            self.driver.get(
                "https://www.facebook.com"
            )

            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                60
            )

            if not loaded:
                raise Exception("FACEBOO.LOAD FAILED")

            cookies = self.cookie_str.split(";")

            added = 0

            for cookie in cookies:

                if "=" in cookie:

                    name, value = cookie.strip().split(
                        "=",
                        1
                    )

                    try:

                        self.driver.add_cookie({
                            "name": name,
                            "value": value,
                            "domain": ".facebook.com"
                        })

                        added += 1

                    except:
                        pass

            success(f"COOKIES LOADED : {added}")

            # SAME SESSION LOGIN
            self.driver.get(
                "https://www.facebook.com/messages"
            )

            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                60
            )

            if not loaded:
                raise Exception("MESSENGER LOAD FAILED")

            ready = self.safe_wait(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[@role='navigation']"
                    )
                ),
                60
            )

            if not ready:
                raise Exception("MESSENGER UI LOAD FAILED")

            success("LOGIN SUCCESSFUL")

            return True

        except Exception as e:

            error(f"COOKIE LOGIN FAILED : {e}")

            return False

    # =====================================================
    #                   GET MESSAGE BOX
    # =====================================================
    def get_message_box(self):

        return self.safe_wait(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[@contenteditable='true']"
                )
            ),
            120
        )

    # =====================================================
    #                   SEND MESSAGE
    # =====================================================
    def send_message(self, text):

        try:

            if not self.driver_alive():
                return False

            # =================================================
            #               PAGE READY
            # =================================================

            loaded = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                120
            )

            if not loaded:
                raise Exception("PAGE LOAD TIMEOUT")

            # =================================================
            #               GET FRESH BOX
            # =================================================

            box = self.get_message_box()

            if not box:
                raise Exception("MESSAGE BOX NOT FOUND")

            # =================================================
            #               SCROLL + FOCUS
            # =================================================

            self.driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    block: 'center'
                });
                """,
                box
            )

            self.driver.execute_script(
                "arguments[0].focus();",
                box
            )

            focused = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.activeElement === arguments[0]",
                    box
                ),
                30
            )

            if not focused:
                raise Exception("BOX FOCUS FAILED")

            # =================================================
            #               FINAL MESSAGE
            # =================================================

            final_msg = (
                f"{self.haters_name} {text}"
            ).strip()

            # =================================================
            #               CLEAR OLD TEXT
            # =================================================

            box.send_keys(
                Keys.CONTROL,
                "a"
            )

            box.send_keys(Keys.BACKSPACE)

            time.sleep(1)

            # =================================================
            #               RE-GET BOX
            # =================================================

            box = self.driver.find_element(
                By.XPATH,
                "//div[@contenteditable='true']"
            )

            # =================================================
            #               TYPE MESSAGE
            # =================================================

            box.send_keys(final_msg)

            time.sleep(1.5)

            # =================================================
            #               RANDOM STABILITY DELAY
            # =================================================

            time.sleep(
                random.uniform(1.5, 3.5)
            )

            # =================================================
            #               SEND MESSAGE
            # =================================================

            box.send_keys(Keys.ENTER)

            # =================================================
            #               SEND CONFIRM
            # =================================================

            sent = self.safe_wait(
                lambda d: box.text.strip() == "",
                60
            )

            if not sent:
                raise Exception("MESSAGE SEND FAILED")

            # =================================================
            #               EXTRA STABILITY
            # =================================================

            stable = self.safe_wait(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) == "complete",
                30
            )

            if not stable:
                raise Exception("POST SEND STABILITY FAILED")

            time.sleep(
                random.uniform(1.5, 2.5)
            )

            return True

        except (
            TimeoutException,
            StaleElementReferenceException,
            WebDriverException,
            Exception
        ) as e:

            error(f"SEND FAILED : {e}")

            try:

                self.soft_refresh_chat()

            except:
                pass

            return False

    # =====================================================
    #                       START
    # =====================================================
    def start(self):

        clear_screen()

        info("LOADING CONFIGURATION")

        if not self.auto_load():
            return

        if not self.setup_driver():
            return

        if not self.login_with_cookies():
            return

        info("OPENING E2EE CHAT")

        self.driver.get(
            f"https://www.facebook.com/messages/e2ee/t/{self.target_uid}"
        )

        loaded = self.safe_wait(
            lambda d: d.execute_script(
                "return document.readyState"
            ) == "complete",
            60
        )

        if not loaded:

            error("CHAT PAGE LOAD FAILED")

            return

        chat_ready = self.safe_wait(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[@contenteditable='true']"
                )
            ),
            60
        )

        if not chat_ready:

            error("CHAT FAILED TO OPEN")

            return

        success("MESSAGE SENDING STARTED")

        count = 0

        while True:

            for msg in self.messages:

                # DRIVER CHECK
                if not self.driver_alive():

                    error("DRIVER CRASH DETECTED")

                    recovered = self.recover_driver()

                    if not recovered:
                        error("RECOVERY FAILED")
                        return

                    continue

                current_time = get_current_time()

                sent = self.send_message(msg)

                count += 1

                # =================================================
                #         FULL DRIVER RESTART FOR STABILITY
                # =================================================

                if count % 30 == 0:

                    info("FULL DRIVER RESTART FOR STABILITY")

                    if not self.recover_driver():
                        return

                elif count % self.cleanup_interval == 0:

                    self.soft_refresh_chat()

                short_msg = (
                    msg[:60] + "..."
                    if len(msg) > 60
                    else msg
                )

                status = (
                    "SUCCESS"
                    if sent
                    else "FAILED"
                )

                # =================================================
                #               STABLE LOGS
                # =================================================

                log(
                    f"[MSG #{count}] "
                    f"[TARGET: {self.target_uid}] "
                    f"[TIME: {current_time}] "
                    f"[STATUS: {status}] "
                    f"[MESSAGE: {short_msg}]"
                )

                log(
                    f"[ALIVE] BOT RUNNING | "
                    f"MSG #{count} | "
                    f"{current_time}"
                )

                log(
                    "───────────────────────────────────────────────────────────────"
                )

                # =================================================
                #               SAFE DELAY LOOP
                # =================================================

                for _ in range(self.delay):

                    time.sleep(1)

                    if not self.driver_alive():

                        error("DRIVER CRASH DETECTED DURING DELAY")

                        recovered = self.recover_driver()

                        if not recovered:
                            error("RECOVERY FAILED")
                            return

                        break


# =========================================================
#                       RUN SCRIPT
# =========================================================
if __name__ == "__main__":
    bot = FacebookMessenger()
    bot.start()