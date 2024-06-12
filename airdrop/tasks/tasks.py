
#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   tasks.py
@Author  :   renjun
'''

import os
import json
import time
import uuid
import pyotp
import codecs
import ctypes
import psutil
import hashlib
import random
import logging
import requests
import platform
import unicodedata
import pyperclip
import pyautogui
import psycopg2
import psycopg2.extras

from lxml import html
from logging import handlers
from datetime import datetime
from configparser import ConfigParser
from multiprocessing.pool import ThreadPool

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from auto_metamask import setupWebdriver




# offer_check_sql  = "SELECT * FROM urls type='offer' limit 1;"
profiles_select_sql   = "SELECT * FROM profiles;"

extensions_select_sql = "SELECT * FROM extensions;"

tasks_select_sql      = "SELECT distinct name      FROM tasks;"
task_sub_select_sql   = "SELECT name,subtask,times FROM tasks where name=%s order by id;"
task_pre_steps_sql    = "SELECT *                  FROM tasks where name=%s and times=0 order by id;"
task_steps_sql        = "SELECT *                  FROM tasks where name=%s and subtask=%s order by id;"
input_select_sql      = "select val from inputs where profile=%s and task=%s;"


class InitConf():
    def __init__(self) -> None:
        self.pf = platform.system()

        self.RLIST            = [",", "-"]
        self.JSON_ID          = '{"id": "%s"}'
        self.WEB_PAGE_TIMEOUT = 30
        self.INPUT_TIME       = 0.1
        self.MINS             = 1.0
        self.MAXS             = 2.0
        self.CHROME_EXTENSION = "chrome-extension://%s/%s.html"

        self.CUR_DIR          = os.path.dirname(os.path.abspath(__file__))
        self.LOG_DIR          = self.get_cur_path("./logs/")
        self.LOG_NAME         = os.path.splitext(os.path.basename(__file__))[0]
        self.check_path(self.LOG_DIR)
        self.logger = self.get_logger()

    def get_cur_path(self, file_name):
        return os.path.join(self.CUR_DIR, file_name)

    def check_path(self, c_path):
        if not os.path.isdir(c_path):
            os.makedirs(c_path)

    def get_logger(self):
        log_handler = handlers.TimedRotatingFileHandler(filename=self.LOG_DIR + self.LOG_NAME, backupCount=5)
        log_handler.suffix = "%Y%m%d"
        formatter = logging.Formatter(
            '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
            '%a, %d %b %Y %H:%M:%S'
        )
        log_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(log_handler)
        logger.setLevel(logging.INFO)
        return logger

    def get_otp(self, secret):
        # secret = 'MDANW36JHNV3EOBM'
        totp = pyotp.TOTP(secret)
        return totp.now()

    def sleep(self, sec=1):
        time.sleep(sec)

    def get_round(self, mi, mx):
        return round(random.uniform(mi, mx), 2)

    def wait_input(self):
        self.sleep(self.get_round(self.MINS, self.MAXS))

    def wait_page_load(self):
        self.sleep(self.get_round(8, 10))

    def getMWH(self):
        if "Windows" in self.pf:
            user32 = ctypes.windll.user32
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        else:
            from subprocess import check_output
            if "Linux" in self.pf:
                # test in ubuntu
                command = "xrandr | awk -F' ' '/\*/{print $1}'"
            elif "MacOS" in self.pf:
                # test for python3 in catalina
                command = "system_profiler SPDisplaysDataType | awk -F' ' '/Resolution/{print $2 \"x\" $4}'"
            else:
                return 1920, 1080
        return check_output(command, shell=True, encoding="utf-8").strip().split("x")

class PostGressDB(InitConf):
    def __init__(self) -> None:
        conf = self.load_config()
        conn = self.connect(conf)
        self.cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) if conn else None

    def load_config(self, filename='database.ini', section='postgresql'):
        parser = ConfigParser()
        parser.read(self.get_cur_path(filename))
        if not parser.has_section(section):
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))

        # get section, default to postgresql
        config = {}
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
        return config

    def connect(self, config):
        """ Connect to the PostgreSQL database server """
        try:
            # connecting to the PostgreSQL server
            with psycopg2.connect(**config) as conn:
                self.logger.debug("success connected to the PostgreSQL server...")
                return conn
        except (psycopg2.DatabaseError, Exception) as e:
            self.logger.error("failed connect to DB with error: %s" % e)
            return

    def sql_info(self, sql, param=None, query=True):
        """
        Execute SQL query and return the result.

        Args:
            sql (str): The SQL query to execute.
            param (tuple, optional): The parameters to pass to the query.
            query (bool, optional): Whether the query should return multiple rows.

        Returns:
            list or int: If query is True, returns a list of tuples containing the results. If query is False, returns the last inserted row id.
        """
        # execute the SQL query with the given parameters
        self.cur.execute(sql, param) if param else self.cur.execute(sql)

        # if the query is meant to return multiple rows,
        # fetch all the rows and return them as a list
        if query:
            return self.cur.fetchall()
        else:
            # if the query is meant to return only the last inserted row id,
            # return that value
            return self.cur.lastrowid

class MouseTask(InitConf):
    def __init__(self) -> None:
        self.r          = 4
        self.confidence = 0.9

    def mouse(self, lo, o):
        """
        Perform mouse operation based on the given parameters.

        Args:
            lo (pyautogui.Point): The location on the screen where the mouse operation should be performed.
            o (int): The type of mouse operation to perform.

                0: Wait for a specified duration.
                1: Perform a left single click.
                2: Perform a left double click.
                3: Perform a right single click.
                4: Scroll the screen.
                5: Input a value.
                6: Move the mouse to a specified location.

        Returns:
            None
        """
        # Initialize the number of clicks and the mouse button.
        ct = 1
        lr = "left"
        dura = self.get_round(self.MINS, self.MAXS)  # Get a random duration between MINS and MAXS.

        # Perform the mouse operation based on the given operation type.
        if o == 2:
            ct = 2  # Double click.
        elif o == 3:
            lr = "right"  # Right click.
        if o == 6:
            pyautogui.moveTo(x=lo.x, y=lo.y, duration=dura)  # Move the mouse to the specified location.
        else:
            pyautogui.click(lo.x, lo.y, clicks=ct, interval=dura, duration=dura, button=lr)  # Perform a mouse click.
        self.sleep(1)  # Wait for 1 second.

    def validate_step(self, o, v):
        if isinstance(o, int):
            if o == 0:
                return True
            elif 0 < o < 4:
                return True if os.path.exists(self.get_cur_path(v)) else False
            elif o == 4:
                return True if isinstance(v, int) else False
            elif o == 5:
                return True if isinstance(v, str) else False
            elif  o == 6 or o == 7:
                return True
        return False

    def get_location(self, v, r):
        retry_times = r or self.r
        for _ in range(retry_times):
            try:
                location = pyautogui.locateCenterOnScreen(self.get_cur_path(v), confidence=self.confidence)
                return location
            except:
                self.sleep(2)
        self.logger.error("cannot get image location")
        return None

    def execute_step(self, o, v, s, r):
        if o == 0:
            mi = v-2 if v > 2 else 0
            self.sleep(self.get_round(mi, v))
        elif 0 < o < 4 or o == 6:
            location = self.get_location(v, r)
            if location:
                self.mouse(location, o)
                return True
            return True if s else False
        elif o == 4:
            pyautogui.scroll(v)
        elif o == 5:
            pyperclip.copy(v)
            self.wait_input()
            pyautogui.hotkey('ctrl','v')
            self.wait_input()
        elif o == 7:
            pyautogui.hotkey(v)
        else:
            return False
        return True

    def execute_mouse_task(self, ets):
        tc = len(ets.keys()) if ets else 1
        rep = ets.get('rep')
        fail = ets.get("fail")
        if rep:
            tc = tc - 2
        if fail:
            tc = tc - 1
        for i in range (tc):
            es = ets.get(str(i))
            if not es:
                self.logger.error("get execute task failed...")
                return
            o = es.get('o')
            v = es.get('v')
            s = es.get('s')
            r = es.get('r')
            vs = self.validate_step(o, v)
            if not vs:
                self.logger.error("validate failed...")
                return
            self.logger.info("start step: ", es)
            result = self.execute_step(o, v, s, r)
            if not result:
                return
            self.logger.info("finish step...")

        if rep:
            print("start repeat tasks...")
            repeat_times = ets.get("ett")
            failed_count = 10
            while True:
                result = self.execute_mouse_task(rep)
                if not result:
                    failed_count = failed_count - 1
                    self.logger.info("repeat task failed, left %s..." % failed_count)
                    if failed_count < 1:
                        self.logger.error("too many failed try...")
                        return False
                    self.execute_mouse_task(rep.get('fail'))
                    continue
                repeat_times = repeat_times - 1
                self.logger.info("left %s times" % str(repeat_times))
                if repeat_times < 1:
                    self.logger.info("repeat task finished...")
                    break
                self.sleep(2)
        return True

    def perform_mouse_tasks(self, tasks):
        for task in tasks:
            if task.get("skip"):
                continue
            name = task.get("name")
            ets = task.get("ets")
            self.logger.info("started the task: ", name)
            result = self.execute_mouse_task(ets)
            if not result:
                self.logger.error("execute task %s failed, try next task!" % name)
                return

            self.logger.info("finished the task: ", name)
        return True


class BitBrowser(InitConf):
    def __init__(self) -> None:
        self.headers = {'Content-Type': 'application/json'}
        self.BIT_URL = "http://127.0.0.1:54345"

    def open_browser(self, id):    # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
        return requests.post(f"{self.BIT_URL}/browser/open", data=self.JSON_ID % id, headers=self.headers).json()

    def close_browser(self, id):   # 关闭窗口
        requests.post(f"{self.BIT_URL}/browser/close", data=self.JSON_ID % id, headers=self.headers).json()

    def get_bit_profiles(self):
        return requests.post(f"{self.BIT_URL}/browser/list", data=json.dumps({"page":0,"pageSize":10}), headers=self.headers).json()

    def get_bit_url(self):
        url = "http://127.0.0.1:"
        for proc in psutil.process_iter():
            if proc.name() == '比特浏览器.exe':
                for x in proc.connections():
                    if x.status == psutil.CONN_LISTEN:
                        url = url + str(x.laddr.port)
                        return url
        return None

    def check_bit_browser(self):
        BIT_URL = self.get_bit_url()
        return BIT_URL or False

class ChromeBrowser(InitConf):
    def get_profiles(self):
        return [
            {
                "id": "8daa7a1341634a1db8bb2e3fd3aa8289",
                "path": "C:/Users/lo/AppData/Local/Google/Chrome/User Data/Profile 1"
            }
        ]


class Wallets(MouseTask):
    ### https://stackoverflow.com/questions/76252205/runtime-callfunctionon-threw-exception-error-lavamoat-property-proxy-of-gl
    ### https://github.com/MetaMask/metamask-extension
    ### https://github.com/LavaMoat/LavaMoat/pull/360#issuecomment-1547726986
    ### https://pypi.org/project/auto-metamask/
    ### https://dev.to/ltmenezes/automated-dapps-scrapping-with-selenium-and-metamask-2ae9
    ### https://github.com/MetaMask/metamask-extension/issues/19018

    def __init__(self) -> None:
        self.driver = None
        self.wait = None
        self.profile_id = ""
        self.ori_window = ""
        self.new_window = ""

    def get_tasks_by_id(self, profile_id, ext_id):
        val = "y:KHF~Mu2*3#^c>G"
        if profile_id == "8daa7a1341634a1db8bb2e3fd3aa8289":
            val = "vXzx}@^Sm#{7g-'W"

        if ext_id == "nkbihfbeogaeaoehlefnkodbefgpgknn":
            return [{"name":"meta","ets":{"0":{"o":1,"v":"meta_pass.png"},"1":{"o":5,"v":val},"2":{"o":1,"v":"meta_login.png"}}}]
        elif ext_id == "ppbibelpcjmhbdihakflkdcoccbgbkpo":
            return [{"name":"meta","ets":{"0":{"o":1,"v":"unisat_pass.png"},"1":{"o":5,"v":val},"2":{"o":1,"v":"unisat_login.png"}}}]


    def login_wallet_task(self, profile_id, extension):
        self.logger.info("login to wallet %s..." % extension)
        ### name id version
        ext_id = extension.get("id")
        ext_tasks = self.get_tasks_by_id(profile_id, ext_id)

        self.driver.get(self.CHROME_EXTENSION % (ext_id, extension.get("home")))
        self.sleep(4)
        task_resp = self.perform_mouse_tasks(ext_tasks)

        if not task_resp:
            return
        return True

    def login_wallet(self, extensions, profile_id):
        for extension in extensions:
            log_status = self.login_wallet_task(profile_id, extension)
            if not log_status:
                return
        return True

    def get_confirm_handle(self):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            self.logger.info("current handle: %s, title %s" % (handle, self.driver.title))
            if self.driver.title == 'MetaMask':
                break

    def handle_wallet(self, step):
        wallet_operation = step.get('findby')
        wallet_id = step.get('findvalue')
        # self.logger.info("wait for a moment to let %s load..." % operation)
        if wallet_operation == "confirm":
            self.get_confirm_handle()
        elif wallet_operation == "sign":
            pass
        elif wallet_operation == "switch":
            pass
        
        self.logger.info("switch back to task tab...")
        self.driver.switch_to.window(self.new_window)


        # with codecs.open("./2.html", "w", "utf-8") as hf:
        #     hf.write(self.driver.page_source)


class SeliniumTask(PostGressDB, BitBrowser, Wallets):
    def __init__(self) -> None:
        self.driver = None
        self.wait = None
        self.profile_id = ""
        self.ori_window = ""
        self.new_window = ""

    def get_proxy_by_user(self, user):
        city = user.get("city")
        state = user.get("state")
        proxy = {
            "type": "socks5",
            "host" : "192.168.1.9",
            "port": 7890,
            "country": "US",
            "ip" : "103.114.163.234"
        }
        return proxy

    def check_get_proxy(self):
        return True

    def get_user_by_profile(self, profile_id):
        # twitter & telegram & discord & metamask etc.
        pass

    def get_proxy(self):
        proxy = {
            "socks5": "192.168.1.12:10808"
        }
        return proxy

    def get_xpath_ele(self, ele):
        if ele:
            val = str(ele[0])
            if "(" in val:
                val = val.split("(")[0]
            for c in self.RLIST:
                val = val.replace(c, "")
            return unicodedata.normalize('NFKD', val).strip()
        return ""

    def wait_for_element(self, findby, findvalue, max_attempts=4, eles=False):
        for _ in range(max_attempts):
            try:
                return self.driver.find_elements(findby, findvalue) if eles else self.driver.find_element(findby, findvalue)
            except Exception as e:
                self.logger.debug("retry get value again: %s" % findvalue)
                self.logger.info("error message: %s" % e)
                self.wait_input()
        raise Exception(f"cannot find the element with value: %s" % findvalue)

    def get_input(self, id):
        res =  self.sql_info(input_select_sql,(self.profile_id, id))
        return res[0].get('val') or ""


    def login_social(self):
        ### login to twitter & discord...
        return True

    def get_tasks(self):
        """
        Get the tasks from the tasks table

        Returns:
            list: The tasks to be executed except the wallet & social task
        """
        return self.sql_info(tasks_select_sql)

    def get_extensions(self):
        return self.sql_info(extensions_select_sql)

    def get_proxy_by_profile(self, profile_id):
        return "socks://192.168.1.13:10808"

    def get_random_items(self, items):
        return random.sample(items, len(items))

    def exe_step(self, step):
        findby = step.get('findby')
        findvalue = step.get('findvalue')
        operation = step.get('operation')
        ### need to switch to tasks windows

        if operation == 'url':
            self.driver.get(findvalue)
            self.logger.info("wait for a moment to let %s: %s load..." % (operation, findvalue))
            self.wait_page_load()
            return True
        elif operation == 'wallet':
            res = self.handle_wallet(step)
            if not res:
                return
            return True

        try:
            task_ele = self.wait_for_element(findby, findvalue)
        except Exception as e:
            self.logger.error(e)
            self.logger.error("ele not found for %s" % findvalue)
            return

        if operation == 'click':
            try:
                task_ele.click()
                self.wait_input()
            except Exception as e:
                ### to do check fall back task, if exist perform fall back task
                self.logger.error(e)
                self.wait_page_load()
                # if "Other element would receive the click" in e:
                #     with codecs.open("./error.html", "w", "utf-8") as hf:
                #         hf.write(task_driver.page_source)
        elif operation == 'input':
            val = self.get_input(step.get('id'))
            for v in val:
                task_ele.send_keys(v)
                self.sleep(self.INPUT_TIME)
        elif operation == 'select':
            val = self.get_input(step.get('id'))
            for op in task_ele.find_elements(By.TAG_NAME, 'option'):
                if val.lower() in op.text.lower():
                    op.click()
        else:
            self.logger.error("running step:%s failed with unsupported operation: %s" % (self.profile_id, operation))
            return

        self.logger.info("finish step: %s" % findvalue)
        self.sleep()
        return True

    def exe_steps(self, steps):
        for step in steps:
            res = self.exe_step(step)
            if not res:
                self.logger.error("execute step: %s failed...")
                return
        self.logger.info("all steps finished...")
        return True

    def exe_sub_tasks(self, task_sub_steps, task_name):
        ### to do shuffle sub task
        ### zulu index 0
        ### zulu swap  4
        ### zulu add   1
        sub_task = ''
        times = 0

        sub_list = []
        for st in task_sub_steps:
            if st.get('subtask') == sub_task or st.get('times')==0:
                continue
            sub_task = st.get('subtask')
            self.logger.info("add subtask to list" % st)
            sub_list.append((task_name, sub_task))

        ### execute pre task
        pre_sub_task = self.sql_info(task_steps_sql, (task_name,))
        res = self.exe_steps(pre_sub_task)

        ### 
        for nst in self.get_random_items(sub_list):
            task_steps = self.sql_info(task_steps_sql, nst)
            for ts in task_steps:
                sub_task = ts.get('subtask')
                times = ts.get('times')
                task_steps = self.sql_info(task_steps_sql, (task_name, sub_task, times))

        # for st in task_sub_steps:
        #     self.logger.debug("exe_sub_steps: %s" % st)
        #     if st.get('subtask') == sub_task and st.get('times')==times:
        #         continue
        #     sub_task = st.get('subtask')
        #     times = st.get('times')
        #     task_steps = self.sql_info(task_steps_sql, (task_name, sub_task, times))
        #     for _ in range(times):
        #         res = self.exe_steps(task_steps)
        #         if not res:
        #             return

    def run_tasks_by_profile(self, tasks):
        ### random select task to execute
        for task in self.get_random_items(tasks):
            task_name = task.get('name')
            self.logger.info("start task: %s" % task_name)
            task_sub_steps = self.sql_info(task_sub_select_sql, (task_name,))
            self.logger.debug("run_tasks_by_profile %s" % task_sub_steps)
            res = self.exe_sub_tasks(task_sub_steps, task_name)
            if not res:
                self.logger.info("failed task: %s, try next one..." % task_name)
                ### update DB let other profile skip this failed task
                continue

    def start_web(self):
        profile_resp = self.get_bit_profiles()
        profiles = profile_resp.get('data').get('list')
        # profiles = get_profiles()
        extensions = self.get_extensions()
        # executable_path = "C:/others/dev/py/chromedriver-win64/chromedriver.exe"

        ### get tasks
        tasks = self.get_tasks()
        self.logger.debug("successfully get tasks: %s" % tasks)

        ### random select profile to execute
        for profile in self.get_random_items(profiles):
            ### to do using multi thread to running profile
            self.profile_id = profile.get('id')
            print(self.profile_id)
            if self.profile_id == '156665546fe14caf894d1f01565c862a':
                continue

            # profile_path = profile.get('path')
            # profile_extensions = ",".join([os.path.join(profile_path,"Extensions",extension) for extension in extensions])
            # proxy = get_proxy_by_profile(profile_id)

            chrome_options = Options()
            res = self.open_browser(self.profile_id)
            chrome_options.add_experimental_option("debuggerAddress", res['data']['http'])
            self.driver = webdriver.Chrome(service=Service(executable_path=res['data']['driver']), options=chrome_options)

            # chrome_options.add_argument("--window-size=1280,720")
            # chrome_options.add_argument("--window-position=0,0")
            # chrome_options.add_argument("--disable-component-update")
            # chrome_options.add_argument("--no-first-run")
            # chrome_options.add_argument("--no-default-browser-check")
            # chrome_options.add_argument("--password-store=basic")
            # chrome_options.add_argument("--user-data-dir=%s" % profile_path)
            # # chrome_options.add_argument("--fingerprint-config=%s" % profile_path)
            # chrome_options.add_argument("--load-extension=%s" % profile_extensions)
            # chrome_options.add_argument("--proxy-server=%s" % proxy)
            # profile_driver = webdriver.Chrome(service=Service(executable_path=executable_path), options=chrome_options)

            self.wait = WebDriverWait(self.driver, 20)
            self.ori_window = self.driver.current_window_handle
            self.logger.debug("original window is: %s" % self.ori_window)

            ### running task in new tab
            self.driver.execute_script('''window.open("%s", "%s");''' % ('https://www.google.com', self.profile_id))
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if self.driver.title == "Google":
                    self.new_window = handle
                    break

            self.logger.debug("new tasks window is: %s" % self.new_window)

            ### login to wallet first...
            # log_wallet = login_wallet(extensions, profile_id)
            # if not log_wallet:
            #     print("login wallet failed, try next profile...")
            #     continue
            # print("login to wallet successfully...")

            ### login to social account(twitter & discord...)
            # log_social = login_social()
            # if not log_social:
            #     print("login social failed")
            #     continue

            self.run_tasks_by_profile(tasks)
            ### all task finished for current profile, close the browser
            self.logger.info("finished profile: %s" % self.profile_id)
            # self.close_browser(self.profile_id)

    def pre_check(self):
        return self.check_bit_browser()

    def run_web_task(self):
        # print(self.pre_check())
        if not self.pre_check():
            raise Exception(f"web3 pre check failed")
        self.start_web()

def main():
    st = SeliniumTask()
    st.run_web_task()
    # res = st.sql_info(input_select_sql,('8daa7a1341634a1db8bb2e3fd3aa8289', 6))
    # print(res)

if __name__ == '__main__':
    main()
