
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


headers          = {'Content-Type': 'application/json'}
confidence       = 0.9

BIT_URL          = "http://127.0.0.1:54345"
RLIST            = [",", "-"]
JSON_ID          = '{"id": "%s"}'
WEB_PAGE_TIMEOUT = 30
INPUT_TIME       = 0.1
MINS             = 1.0
MAXS             = 2.0
CHROME_EXTENSION = "chrome-extension://%s/%s.html"

CUR_DIR          = os.path.dirname(os.path.abspath(__file__))




def get_cur_path(file_name):
    return os.path.join(CUR_DIR, file_name)

def check_path(c_path):
    if not os.path.isdir(c_path):
        os.makedirs(c_path)


CONFIG_DB_PATH   = get_cur_path("config.db")
LOG_DIR          = get_cur_path("./logs/")
LOG_NAME         = os.path.splitext(os.path.basename(__file__))[0]


# offer_check_sql  = "SELECT * FROM urls type='offer' limit 1;"
profiles_select_sql   = "SELECT * FROM profiles;"

extensions_select_sql = "SELECT * FROM extensions;"

tasks_select_sql      = "SELECT distinct name      FROM tasks;"
task_sub_select_sql   = "SELECT name,subtask,times FROM tasks where name=%s order by id;"
task_steps_sql        = "SELECT *                  FROM tasks where name=%s and subtask=%s and times=%s order by id;"
input_select_sql      = "select val from inputs where profile=%s and task=%s;"


check_path(LOG_DIR)
log_handler = handlers.TimedRotatingFileHandler(filename=LOG_DIR + LOG_NAME, backupCount=5)
log_handler.suffix = "%Y%m%d"
formatter = logging.Formatter(
    '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    '%a, %d %b %Y %H:%M:%S'
)
log_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

def sleep(sec=1):
    time.sleep(sec)

def get_round(mi, mx):
    return round(random.uniform(mi, mx), 2)

def wait_input():
    sleep(get_round(MINS, MAXS))

def wait_page_load():
    sleep(get_round(8, 10))

class PostGressDB():
    def __init__(self) -> None:
        conf = self.load_config()
        conn = self.connect(conf)
        self.cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def load_config(self, filename='database.ini', section='postgresql'):
        parser = ConfigParser()
        parser.read(get_cur_path(filename))
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
                logger.debug("success connected to the PostgreSQL server...")
                return conn
        except (psycopg2.DatabaseError, Exception) as error:
            print(error)

    def sql_info(self, sql, param=None, query=True):
        self.cur.execute(sql, param) if param else self.cur.execute(sql)
        return self.cur.fetchall() if query else self.cur.lastrowid

class MouseTask():
    pass


def getMWH(pf):
    if "Windows" in pf:
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    else:
        from subprocess import check_output
        if "Linux" in pf:
            # test in ubuntu
            command = "xrandr | awk -F' ' '/\*/{print $1}'"
        elif "MacOS" in pf:
            # test for python3 in catalina
            command = "system_profiler SPDisplaysDataType | awk -F' ' '/Resolution/{print $2 \"x\" $4}'"
        else:
            return 1920, 1080
    return check_output(command, shell=True, encoding="utf-8").strip().split("x")

def mouse(lo, o):
    ct = 1
    lr = "left"
    dura = get_round(MINS, MAXS)
    if o == 2:
        ct = 2
    elif o == 3:
        lr = "right"
    if o == 6:
        pyautogui.moveTo(x=lo.x, y=lo.y, duration=dura)
    else:
        pyautogui.click(lo.x,lo.y,clicks=ct,interval=dura,duration=dura,button=lr)
    sleep(1)

def validate_step(o, v):
    if isinstance(o, int):
        if o == 0:
            return True
        elif 0 < o < 4:
            return True if os.path.exists(get_cur_path(v)) else False
        elif o == 4:
            return True if isinstance(v, int) else False
        elif o == 5:
            return True if isinstance(v, str) else False
        elif  o == 6 or o == 7:
            return True
    return False

def get_location(v, r):
    retry_times = r if r else 4
    for _ in range(retry_times):
        try:
            location = pyautogui.locateCenterOnScreen(get_cur_path(v), confidence=confidence)
            return location
        except:
            sleep(2)
    logger.error("cannot get image location")
    return None

def execute_step(o, v, s, r):
    if o == 0:
        mi = v-2 if v > 2 else 0
        sleep(get_round(mi, v))
    elif 0 < o < 4 or o == 6:
        location = get_location(v, r)
        if location:
            mouse(location, o)
            return True
        return True if s else False
    elif o == 4:
        pyautogui.scroll(v)
    elif o == 5:
        pyperclip.copy(v)
        wait_input()
        pyautogui.hotkey('ctrl','v')
        wait_input()
    elif o == 7:
        pyautogui.hotkey(v)
    else:
        return False
    return True

def execute_mouse_task(ets):
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
            logger.error("get execute task failed...")
            return
        o = es.get('o')
        v = es.get('v')
        s = es.get('s')
        r = es.get('r')
        vs = validate_step(o, v)
        if not vs:
            logger.error("validate failed...")
            return
        logger.info("start step: ", es)
        result = execute_step(o, v, s, r)
        if not result:
            return
        logger.info("finish step...")

    if rep:
        print("start repeat tasks...")
        repeat_times = ets.get("ett")
        failed_count = 10
        while True:
            result = execute_mouse_task(rep)
            if not result:
                failed_count = failed_count - 1
                logger.info("repeat task failed, left %s..." % failed_count)
                if failed_count < 1:
                    logger.error("too many failed try...")
                    return False
                execute_mouse_task(rep.get('fail'))
                continue
            repeat_times = repeat_times - 1
            print("left %s times" % str(repeat_times))
            if repeat_times < 1:
                logger.info("repeat task finished...")
                break
            sleep(2)
    return True

def perform_mouse_tasks(tasks):
    for task in tasks:
        if task.get("skip"):
            continue
        name = task.get("name")
        ets = task.get("ets")
        print("started the task: ", name)
        result = execute_mouse_task(ets)
        if not result:
            print("execute task %s failed, try next task!" % name)
            return

        print("finished the task: ", name)
    return True



def get_proxy():
    proxy = {
        "socks5": "192.168.1.12:10808"
    }
    return proxy

def get_proxy_by_user(user):
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

def check_get_proxy():
    return True

def get_user_by_profile(profile_id):
    # twitter & telegram & discord & metamask etc.
    pass


def get_tasks_by_id(profile_id, ext_id):
    val = "y:KHF~Mu2*3#^c>G"
    if profile_id == "8daa7a1341634a1db8bb2e3fd3aa8289":
        val = "vXzx}@^Sm#{7g-'W"

    if ext_id == "nkbihfbeogaeaoehlefnkodbefgpgknn":
        return [{"name":"meta","ets":{"0":{"o":1,"v":"meta_pass.png"},"1":{"o":5,"v":val},"2":{"o":1,"v":"meta_login.png"}}}]
    elif ext_id == "ppbibelpcjmhbdihakflkdcoccbgbkpo":
        return [{"name":"meta","ets":{"0":{"o":1,"v":"unisat_pass.png"},"1":{"o":5,"v":val},"2":{"o":1,"v":"unisat_login.png"}}}]

class BitBrowser():
    def open_browser(self, id):    # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
        return requests.post(f"{BIT_URL}/browser/open", data=JSON_ID % id, headers=headers).json()

    def close_browser(self, id):   # 关闭窗口
        requests.post(f"{BIT_URL}/browser/close", data=JSON_ID % id, headers=headers).json()

    def get_bit_profiles(self):
        return requests.post(f"{BIT_URL}/browser/list", data=json.dumps({"page":0,"pageSize":10}), headers=headers).json()

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


class SeliniumTask():
    def __init__(self) -> None:
        self.pg = PostGressDB()
        self.bt = BitBrowser()
        self.cur = self.pg.cur
        self.driver = None
        self.wait = None
        self.profile_id = ""
        self.ori_window = ""
        self.new_window = ""

    def get_xpath_ele(self, ele):
        if ele:
            val = ele[0]
            if "(" in val:
                val = val.split("(")[0]
            for c in RLIST:
                val = val.replace(c, "")
            return unicodedata.normalize('NFKD', val).strip()
        return ""

    def wait_for_element(self, findby, findvalue, max_attempts=4):
        for _ in range(max_attempts):
            try:
                return self.driver.find_element(findby, findvalue)
            except Exception as e:
                logger.debug("retry get value again: %s" % findvalue)
                logger.info("error message: %s" % e)
                wait_input()
        raise Exception(f"cannot find the element with value: %s" % findvalue)

    def get_input(self, id):
        res =  self.pg.sql_info(input_select_sql,(self.profile_id, id))
        return res[0].get('val') or ""

    def exe_tasks(self, tasks):
        for task in tasks:
            findby = task.get('findby')
            findvalue = task.get('findvalue')
            operation = task.get('operation')
            ### need to switch to tasks windows
            self.driver.switch_to.window(self.new_window)

            if operation == 'url':
                self.driver.get(findvalue)
                wait_page_load()
                logger.info("wait for a moment to let %s: %s load..." % (operation,findvalue))
                continue
            elif operation == 'wallet':
                wait_page_load()
                logger.info("wait for a moment to let %s load..." % operation)
                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
                    print(self.driver.title)
                    if self.driver.title == 'MetaMask':
                        break

                # with codecs.open("./2.html", "w", "utf-8") as hf:
                #     hf.write(self.driver.page_source)

                operation = 'click'

            try:
                task_ele = self.wait_for_element(findby, findvalue)
            except Exception as e:
                logger.error(e)
                logger.error("ele not found for %s" % findvalue)
                return

            if operation == 'click':
                try:
                    task_ele.click()
                    wait_input()

                except Exception as e:
                    logger.error(e)
                    sleep(10)
                    # if "Other element would receive the click" in e:
                    #     with codecs.open("./error.html", "w", "utf-8") as hf:
                    #         hf.write(task_driver.page_source)
            elif operation == 'input':
                val = self.get_input(task.get('id'))
                for v in val:
                    task_ele.send_keys(v)
                    sleep(INPUT_TIME)
            elif operation == 'select':
                val = self.get_input(task.get('id'))
                for op in task_ele.find_elements(By.TAG_NAME, 'option'):
                    if val.lower() in op.text.lower():
                        op.click()
            else:
                logger.error("running task:%s failed with unsupported operation: %s" % (self.profile_id, operation))
                return
            logger.info("finish task: %s" % findvalue)
            sleep()

        return True

    def login_wallet_task(self, profile_id, extension):
        logger.info("login to wallet %s..." % extension)
        ### name id version
        ext_id = extension.get("id")
        ext_tasks = get_tasks_by_id(profile_id, ext_id)

        self.driver.get(CHROME_EXTENSION % (ext_id, extension.get("home")))
        sleep(4)
        task_resp = perform_mouse_tasks(ext_tasks)

        if not task_resp:
            return
        return True

    def login_wallet(self, extensions, profile_id):
        for extension in extensions:
            log_status = self.login_wallet_task(profile_id, extension)
            if not log_status:
                return
        return True

    def login_social(self):
        return True

    def get_tasks(self):
        return self.pg.sql_info(tasks_select_sql)

    def get_profiles(self):
        return [
            {
                "id": "8daa7a1341634a1db8bb2e3fd3aa8289",
                "path": "C:/Users/lo/AppData/Local/Google/Chrome/User Data/Profile 1"
            }
        ]

    def get_extensions(self):
        return self.pg.sql_info(extensions_select_sql)

    def get_proxy_by_profile(self, profile_id):
        return "socks://192.168.1.13:10808"

    def exe_sub_steps(self, task_sub_steps, task_name):
        sub_task = ''
        times = 1
        for st in task_sub_steps:
            logger.debug("exe_sub_steps: %s" % st)
            if st.get('subtask') == sub_task and st.get('times')==times:
                continue
            sub_task = st.get('subtask')
            times = st.get('times')
            task_steps = self.pg.sql_info(task_steps_sql, (task_name, sub_task, times))
            for _ in range(times):
                res = self.exe_tasks(task_steps)
                if not res:
                    return

    def run_tasks_by_profile(self, tasks):
        for task in tasks:
            task_name = task.get('name')
            logger.info("start task: %s" % task_name)
            task_sub_steps = self.pg.sql_info(task_sub_select_sql, (task_name,))
            logger.debug("run_tasks_by_profile %s" % task_sub_steps)
            res = self.exe_sub_steps(task_sub_steps, task_name)
            if not res:
                logger.info("failed task: %s, try next one..." % task_name)
                ### update DB let other profile skip this failed task
                continue

    def start_web(self):
        profile_resp = self.bt.get_bit_profiles()
        profiles = profile_resp.get('data').get('list')
        # profiles = get_profiles()
        extensions = self.get_extensions()
        # executable_path = "C:/others/dev/py/chromedriver-win64/chromedriver.exe"
        tasks = self.get_tasks()
        logger.debug("successfully get tasks: %s" % tasks)
        for profile in profiles:
            self.profile_id = profile.get('id')
            if self.profile_id == '156665546fe14caf894d1f01565c862a':
                continue
            # profile_path = profile.get('path')
            # profile_extensions = ",".join([os.path.join(profile_path,"Extensions",extension) for extension in extensions])
            # proxy = get_proxy_by_profile(profile_id)

            chrome_options = Options()
            res = self.bt.open_browser(self.profile_id)
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
            logger.debug("original window is: %s" % self.ori_window)

            ### running task in new tab
            self.driver.execute_script('''window.open("%s", "%s");''' % ('https://www.google.com', self.profile_id))
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if self.driver.title == "Google":
                    self.new_window = handle
                    break

            logger.debug("new tasks window is: %s" % self.new_window)
            # self.driver.switch_to.window(self.handle)
            # log_wallet = login_wallet(extensions, profile_id)
            # if not log_wallet:
            #     print("login wallet failed, try next profile...")
            #     continue
            # print("login to wallet successfully...")

            # log_social = login_social()
            # if not log_social:
            #     print("login social failed")
            #     continue

            self.run_tasks_by_profile(tasks)


    def pre_check(self):
        return self.bt.check_bit_browser()

    def run_web_task(self):
        # print(self.pre_check())
        if not self.pre_check():
            raise Exception(f"web3 pre check failed")
        self.start_web()

def main():
    st = SeliniumTask()
    st.run_web_task()
    # pg = PostGressDB()
    # res = pg.sql_info(input_select_sql,('8daa7a1341634a1db8bb2e3fd3aa8289', 6))
    # print(res)

if __name__ == '__main__':
    main()
