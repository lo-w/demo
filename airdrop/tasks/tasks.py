
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


profiles_select_sql     =  "SELECT * FROM profiles;"
profile_select_sql      =  "SELECT * FROM profiles where profile=%s;"
extensions_select_sql   =  "SELECT * FROM extensions;"
# tasks_select_sql      =  "SELECT distinct name      FROM tasks;"
tasks_select_sql        =  "SELECT distinct name FROM tasks where name not in ('metamask','unisat','keplr','fallback');"
# task_sub_select_sql   =  "SELECT name,subtask,times FROM tasks where name=%s order by id;"
task_sub_select_sql     =  '''
                            SELECT 
                                t.id        id,
                                t.name      name,
                                t.subtask   subtask,
                                t.times     times,
                                t.findby    findby,
                                t.findvalue findvalue,
                                t.operation operation,
                                i.task      task,
                                i.profile   profile,
                                i.val       val,
                                i.retry     retry
                            FROM tasks t left join inputs i on t.id=i.task and (i.profile=%s or i.profile is null) where t."name"=%s order by t.id;
                        '''
# task_sub_select_sql     = 'SELECT * FROM tasks t left join inputs i on t.id=i.task and (i.profile=%s or i.profile is null) where t."name"=%s order by t.id;'
fallback_select_sql     = 'SELECT * FROM tasks t where name=%s and subtask=%s order by t.id;'
wallet_steps_select_sql = 'SELECT * FROM tasks t left join inputs i on t.id=i.task left join extensions e on t."name"=e."name" where e.id=%s and t.subtask=%s order by t.id;'

class InitConf():
    def __init__(self) -> None:
        self.pf = platform.system()

        self.RLIST            = [",", "-"]
        self.JSON_ID          = '{"id": "%s"}'
        self.WEB_PAGE_TIMEOUT = 30
        self.INPUT_TIME       = 0.1
        self.MINS             = 1.0
        self.MAXS             = 2.0
        self.wait_time        = 10
        self.wait_handle      = 15
        self.CHROME_EXTENSION = "chrome-extension://%s/%s.html"
        self.position         = ["0,0","%s,0" % str(int(self.getMWH()[0]/2))]
        self.log_level        = logging.INFO
        self.cur_dir          = os.path.dirname(os.path.abspath(__file__))
        self.log_dir          = self.get_cur_path("./logs/")
        self.log_name         = os.path.splitext(os.path.basename(__file__))[0]
        self.log_ext          = ".log"
        self.check_path(self.log_dir)
        self.logger = self.get_logger()

    def get_cur_path(self, file_name):
        return os.path.join(self.cur_dir, file_name)

    def check_path(self, c_path):
        if not os.path.isdir(c_path):
            os.makedirs(c_path)

    def get_logger(self):
        log_handler = handlers.TimedRotatingFileHandler(filename=self.log_dir + self.log_name + self.log_ext, backupCount=5)
        log_handler.suffix = "%Y%m%d"
        formatter = logging.Formatter(
            '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
            '%a, %d %b %Y %H:%M:%S'
        )
        log_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(log_handler)
        logger.setLevel(self.log_level)
        return logger

    def get_otp(self, secret):
        # secret = 'MDANW36JHNV3EOBM'
        totp = pyotp.TOTP(secret)
        return totp.now()

    def sleep(self, sec=1):
        time.sleep(sec)

    def get_round(self, mi, mx, decimal_places=2):
        return round(random.uniform(float(mi), float(mx)), decimal_places)

    def get_random_from_range(self, spl, val_string):
        val = val_string
        if spl in val_string:
            val_list = val_string.split(spl)
            val = self.get_round(val_list[0], val_list[-1])
        return val

    def wait_input(self, mi=None, mx=None):
        self.sleep(self.get_round(mi, mx)) if mx else self.sleep(self.get_round(self.MINS, self.MAXS))

    def wait_wallet(self):
        self.logger.debug("wait wallet operation load...")
        self.wait_input(3, 5)

    def wait_page_load(self):
        self.logger.debug("wait page   operation load...")
        self.wait_input(5, 8)

    def get_random_items(self, items):
        return random.sample(items, len(items))

    def get_offset(self):
        ### x: width
        ### y: height
        return {"x": self.get_round(-10, 10), "y": self.get_round(-10, 10)}

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

    def get_position(self):
        index = random.randint(0, len(self.position) - 1)
        return self.position.pop(index)


class PostGressDB(InitConf):
    def __init__(self) -> None:
        super().__init__()
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

    def get_tasks(self):
        return self.sql_info(tasks_select_sql)

    def get_extensions(self):
        return self.sql_info(extensions_select_sql)

    def get_profile(self):
        profile_item = self.sql_info(profile_select_sql, (self.profile_id,))
        return profile_item[0] or None

class BitBrowser(InitConf):
    def __init__(self) -> None:
        super().__init__()
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

    def pre_check(self):
        return self.check_bit_browser()



class ChromeBrowser(InitConf):
    def __init__(self) -> None:
        super().__init__()

    def get_profiles(self):
        return [
            {
                "id": "8daa7a1341634a1db8bb2e3fd3aa8289",
                "path": "C:/Users/lo/AppData/Local/Google/Chrome/User Data/Profile 1"
            }
        ]

class MouseTask(InitConf):
    def __init__(self) -> None:
        super().__init__()
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
        offset = self.get_offset()
        # Perform the mouse operation based on the given operation type.
        if o == 2:
            ct = 2  # Double click.
        elif o == 3:
            lr = "right"  # Right click.
        if o == 6:
            pyautogui.moveTo(x=lo.x + offset.get('x'), y=lo.y + offset.get('y'), duration=dura)  # Move the mouse to the specified location.
        else:
            pyautogui.click(lo.x, lo.y, clicks=ct, interval=dura, duration=dura, button=lr)  # Perform a mouse click.
        self.wait_input()

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
                self.wait_input()
        self.logger.error("cannot get image location")
        return None

    def execute_step(self, o, v, s, r):
        if o == 0:
            mi = v-2 if v > 2 else 0
            self.wait_input(mi, v)
            # self.sleep(self.get_round(mi, v))
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
            return
        return True

    def execute_task_step(self, es):
        o = es.get('o')
        v = es.get('v')
        s = es.get('s')
        r = es.get('r')
        if str(v).startswith("meta_"):
            v = "wallets/%s" % v
        vs = self.validate_step(o, v)
        if not vs:
            self.logger.error("validate failed...")
            return
        self.logger.info("start  mouse step: %s" % es)
        result = self.execute_step(o, v, s, r)
        if not result:
            return
        self.logger.info("finish mouse step: %s" % es)
        return True

    def execute_repeat_task(self, ets):
        self.logger.info("start repeat tasks...")
        rep = ets.get('rep')
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
            self.wait_input()
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
            res = self.execute_task_step(es)
            if not res:
                return
        return self.execute_repeat_task(ets) if rep else True

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

class SeleniumTask(PostGressDB):
    def __init__(self) -> None:
        super().__init__()
        self.driver      = None
        self.wait        = None
        self.action      = None
        self.profile_id  = ""
        self.wallet_pass = ""
        self.orig_handle = ""
        self.task_handle = ""
        self.wall_handle = ""
        self.last_net    = ""
        self.know_handle = []
        self.know_titles = ["MetaMask","https://testnet.zulunetwork.io"]
        self.wallet_operation_list = ["confirm", "cancel","signpay", "sign"]

    def get_xpath_ele(self, ele):
        if ele:
            val = str(ele[0])
            if "(" in val:
                val = val.split("(")[0]
            for c in self.RLIST:
                val = val.replace(c, "")
            return unicodedata.normalize('NFKD', val).strip()
        return ""

    def wait_for_element(self, findby, findvalue, rt, eles=False):
        for _ in range(rt):
            try:
                # if operation == "click":
                #     return self.wait.until(EC.element_to_be_clickable((findby, findvalue)))
                # return self.driver.find_elements(findby, findvalue) if eles else self.wait.until(EC.presence_of_element_located((findby, findvalue)))
                return self.driver.find_elements(findby, findvalue) if eles else self.wait.until(EC.element_to_be_clickable((findby, findvalue)))
            except Exception as e:
                self.logger.debug("retry get value again: %s" % findvalue)
                self.logger.debug("error message: %s" % e)
                self.wait_input()
        self.logger.error("cannot find the element with value: %s" % findvalue)
        return

    def get_proxy_by_profile(self, profile_id):
        return "socks://192.168.1.13:10808"
    
    def save_page_to_local(self, file_name):
        with codecs.open(self.get_cur_path(file_name), "w", "utf-8") as hf:
            hf.write(self.driver.page_source)

class Wallets(MouseTask, SeleniumTask):
    ### https://stackoverflow.com/questions/76252205/runtime-callfunctionon-threw-exception-error-lavamoat-property-proxy-of-gl
    ### https://github.com/MetaMask/metamask-extension
    ### https://github.com/LavaMoat/LavaMoat/pull/360#issuecomment-1547726986
    ### https://pypi.org/project/auto-metamask/
    ### https://dev.to/ltmenezes/automated-dapps-scrapping-with-selenium-and-metamask-2ae9
    ### https://github.com/MetaMask/metamask-extension/issues/19018

    def __init__(self) -> None:
        super().__init__()

    def get_tasks_by_id(self, ext_id):
        val = "y:KHF~Mu2*3#^c>G"
        if self.profile_id == "8daa7a1341634a1db8bb2e3fd3aa8289":
            val = "vXzx}@^Sm#{7g-'W"

        if ext_id == "nkbihfbeogaeaoehlefnkodbefgpgknn":
            return [{"name":"meta","ets":{"0":{"o":1,"v":"meta_pass.png"},"1":{"o":5,"v":val},"2":{"o":1,"v":"meta_login.png"}}}]
        elif ext_id == "ppbibelpcjmhbdihakflkdcoccbgbkpo":
            return [{"name":"meta","ets":{"0":{"o":1,"v":"unisat_pass.png"},"1":{"o":5,"v":val},"2":{"o":1,"v":"unisat_login.png"}}}]

    def get_handle(self, handle_title):
        for handle in self.driver.window_handles:
            if handle in self.know_handle:
                continue
            self.sleep(self.INPUT_TIME)
            self.driver.switch_to.window(handle)
            cur_title = self.driver.title
            self.logger.debug("current handle: %s, title %s" % (handle, cur_title))
            if cur_title == handle_title or (not handle_title and cur_title not in self.know_titles):
                return handle
        return False

    def get_new_handle(self):
        ### running task in new tab
        self.driver.execute_script('''window.open("%s", "%s");''' % ('https://www.google.com', '_blank'))
        self.wait_input()
        return self.get_handle("Google")

    def login_wallet_task(self, extension):
        ext_id = extension.get("id")
        self.logger.info("login to wallet: %s..." % ext_id)
        login_steps = self.sql_info(wallet_steps_select_sql, (ext_id, 'login'))
        return self.exe_steps(login_steps)

    def login_wallets(self, extensions):
        wall_handle = self.get_new_handle()
        self.logger.debug("new wallet handle is: %s" % wall_handle)

        for extension in extensions:
            # if extension.get("id") != "nkbihfbeogaeaoehlefnkodbefgpgknn":
            #     continue
            res = self.login_wallet_task(extension)
            if not res:
                return
        ### close login tab then switch back to origin tab...
        self.driver.close()
        self.driver.switch_to.window(self.orig_handle)
        return True

        # with codecs.open("./2.html", "w", "utf-8") as hf:
        #     hf.write(self.driver.page_source)
    def handle_mouse(self, step):
        findby    = step.get('findby')
        findvalue = step.get('findvalue')
        if findby == "replace":
            subtask = step.get('subtask')
            val     = step.get('val')
            if not val and subtask == "login":
                val = self.wallet_pass
                findvalue = findvalue % val
        self.logger.debug("execute mouse task step: %s" % findvalue)
        return self.execute_task_step(json.loads(findvalue))

    def handle_wallet(self, step):
        wallet_operation = step.get('findby')
        wallet_id        = step.get('findvalue')
        wallet_task_steps = self.sql_info(wallet_steps_select_sql, (wallet_id, wallet_operation))

        self.logger.info("wait for a moment to switch handle: %s..." % wallet_operation)
        handle_res = None
        if wallet_operation in self.wallet_operation_list:
            wallet_val = wallet_task_steps[-1].get('val')
            self.wait_wallet()
            for _ in range(self.wait_handle):
                handle_res = self.get_handle(wallet_val)
                if handle_res:
                    self.logger.debug("succeed switch to wallet: %s handle..." % wallet_val)
                    break
                self.wait_input()
        elif wallet_operation == "switch":
            wallet_val    = step.get('val')
            if self.last_net == wallet_val:
                self.logger.info("wallet network already switched, no need to switch...")
                return True
            self.last_net = wallet_val
            handle_res    = self.get_new_handle()

            ### replace the val for switch
            switch_search  = wallet_task_steps[-1]['findvalue'] % ("switch/%s" % wallet_val)
            wallet_task_steps[-1]['findvalue'] = switch_search
            switch_task    = wallet_task_steps[-2]['findvalue'] % wallet_val
            wallet_task_steps[-2]['findvalue'] = switch_task

        if not handle_res:
            self.logger.error("failed switch to wallet: %s handle..." % wallet_val)
            return

        res = self.exe_steps(wallet_task_steps)
        if not res:
            return

        if wallet_operation == "switch":
            self.driver.close()

        self.logger.info("wait for a moment let transaction finished then switch back to task tab...")
        self.wait_wallet()
        self.driver.switch_to.window(self.task_handle)
        return True


class WebTask(BitBrowser, Wallets):
    def __init__(self) -> None:
        super().__init__()

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

    def login_social(self):
        ### login to twitter & discord...
        return True

    def handle_task_elements(self, task_eles, step):
        fall_back_steps = self.sql_info(fallback_select_sql, ("fallback", str(step.get('id'))))
        # self.save_page_to_local("eles.html")
        for task_ele in task_eles:
            try:
                task_ele.click()
                self.wait_input()
            except Exception as e:
                ### to do check fall back task, if exist perform fall back task
                self.logger.error(e)
                self.wait_page_load()

            res = self.exe_steps(fall_back_steps)
            if not res:
                return
            self.wait_input()
        return True

    def exe_step(self, step):
        findby    = step.get('findby')
        findvalue = step.get('findvalue')
        operation = step.get('operation')
        subtask   = step.get('subtask')
        val       = step.get('val')
        retry_tmp = step.get('retry')
        retry     = retry_tmp if retry_tmp else 4

        if operation == 'url':
            for _ in range(4):
                try:
                    self.driver.get(findvalue)
                    break
                except Exception as e:
                    self.logger.error("failed to open url: %s..." % findvalue)
            self.logger.info("wait for a moment to let url: %s load..." % findvalue)
            self.wait_page_load()
            return True
        elif operation == 'wallet':
            return self.handle_wallet(step)
        elif operation == 'mouse':
            return self.handle_mouse(step)
        elif operation == "eles":
            task_eles = self.wait_for_element(findby, findvalue, retry, eles=True)
            if not task_eles:
                return True if val == "skip" else False
            return self.handle_task_elements(task_eles, step)
        elif operation == "sleep":
            wait_time = self.get_random_from_range(",", findvalue)
            self.sleep(wait_time)
            return True
        elif operation == "close":
            new_handle = self.get_handle(None)
            if not new_handle:
                return
            self.driver.close()
            self.driver.switch_to.window(self.task_handle)
            return True
        elif operation == "scroll":
            self.driver.execute_script('window.scrollBy(0, %s)' % findvalue)
            return True

        task_ele = self.wait_for_element(findby, findvalue, retry)

        if not task_ele:
            return True if val == "skip" else False

        if operation == 'click':
            try:
                task_ele.click()
                self.wait_input()
            except Exception as e:
                ### to do check fall back task, if exist perform fall back task
                self.logger.error(e)
                self.wait_page_load()

        elif operation == 'clear':
            task_ele.clear()
        elif operation == 'input':
            if subtask == "login":
                val = self.wallet_pass
            elif ';;' in val:
                val = self.get_random_from_range(";;", val)
            for v in str(val):
                task_ele.send_keys(v)
                self.sleep(self.INPUT_TIME)
            self.wait_input()
        elif operation == 'select':
            for op in task_ele.find_elements(By.TAG_NAME, 'option'):
                if val.lower() in op.text.lower():
                    op.click()
        elif operation == 'action':
            self.action.move_to_element(task_ele).click().perform()
        elif operation == 'iframe':
            self.driver.switch_to.frame(task_ele)
        else:
            self.logger.error("running step:%s failed with unsupported operation: %s" % (self.profile_id, operation))
            return

        self.wait_input()
        self.logger.info("finish step: %s" % findvalue)
        return True

    def exe_steps(self, steps):
        ### need to switch to tasks tab, already change it in wallet
        for step in steps:
            res = self.exe_step(step)
            if not res:
                self.logger.error("execute step: %s failed..." % step)
                return
        self.logger.info("all steps finished...")
        return True

    def handle_sub_tasks(self, other_sub_exe_task, sub_task):
        ### get times list
        times_list = list({oset["times"] for oset in other_sub_exe_task})
        self.logger.info("get times list for sub task: %s, times list: %s" % (sub_task, times_list))

        for times in times_list:
            self.logger.info("get specific steps for specific sub task: %s, times: %s" % (sub_task, times))
            exe_times_list = [oset for oset in other_sub_exe_task if oset["times"] == times]
            for _ in range(times):
                res = self.exe_steps(exe_times_list)
                if not res:
                    return
        return True

    def exe_sub_tasks(self, task_name):
        task_sub_steps = self.sql_info(task_sub_select_sql, (self.profile_id, task_name))
        self.logger.debug("exe_sub_tasks: %s" % task_sub_steps)

        pre_sub_task = []
        oth_sub_task = []
        for st in task_sub_steps:
            if st.get('times') == 0:
                pre_sub_task.append(st)
            else:
                oth_sub_task.append(st)

        ### execute pre sub task
        self.logger.info("execute task: %s, pre task: %s" % (task_name, pre_sub_task))
        res = self.exe_steps(pre_sub_task)
        if not res:
            self.logger.error("failed execute task: %s, pre task: %s" % (task_name, pre_sub_task))
            return

        ### execute oth sub task, shuffle the sub task, random select one of it
        other_list = list({ost["subtask"] for ost in oth_sub_task})
        self.logger.info("task: %s other taks list: %s" % (task_name, other_list))
        for ost in self.get_random_items(other_list):
            # if ost != "finance":
            #     continue
            self.logger.info("start  execute task: %s, other task: %s" % (task_name, ost))
            other_sub_exe_task = []

            for tss in task_sub_steps:
                if tss.get('subtask') == ost:
                    other_sub_exe_task.append(tss)

            self.logger.debug("other  task list: %s" % other_sub_exe_task)
            res = self.handle_sub_tasks(other_sub_exe_task, ost)

            if not res:
                self.logger.error("failed execute task: %s, other task: %s" % (task_name, ost))
                return

            self.logger.info("finish execute task: %s, other task: %s" % (task_name, ost))
        return True

    def run_tasks_by_profile(self, tasks):
        ### shuffle the task
        for task in self.get_random_items(tasks):
            task_name = task.get('name')
            # if task_name != "ZULU":
            #     continue
            self.logger.info("start  profile: %s, task: %s" % (self.profile_id, task_name))
            res = self.exe_sub_tasks(task_name)
            if not res:
                self.logger.info("failed task: %s, try next one..." % task_name)
                ### update DB let other profile skip this failed task
                continue
            self.logger.info("finish profile: %s, task: %s" % (self.profile_id, task_name))

        self.logger.info("all tasks finished for profile: %s" % self.profile_id)
        self.driver.close()

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
            ### TODO using multi thread to running profile
            self.profile_id = profile.get('id')
            # if self.profile_id != '156665546fe14caf894d1f01565c862a':
            #     continue
            self.logger.info("start  profile: %s" % self.profile_id)
            # profile_path = profile.get('path')
            # profile_extensions = ",".join([os.path.join(profile_path,"Extensions",extension) for extension in extensions])
            # proxy = get_proxy_by_profile(profile_id)

            res = self.open_browser(self.profile_id)
            if not res['success']:
                self.logger.error("open profile: %s failed..." % self.profile_id)
                ### need to update the DB status which profile is failed
                continue
            chrome_options = Options()
            # position = self.get_position()
            # chrome_options.add_argument("--window-position=%s" % position)
            chrome_options.add_experimental_option("debuggerAddress", res['data']['http'])
            self.driver = webdriver.Chrome(service=Service(executable_path=res['data']['driver']), options=chrome_options)

            # chrome_options.add_argument("--window-size=1280,720")
            # chrome_options.add_argument("--disable-component-update")
            # chrome_options.add_argument("--no-first-run")
            # chrome_options.add_argument("--no-default-browser-check")
            # chrome_options.add_argument("--password-store=basic")
            # chrome_options.add_argument("--user-data-dir=%s" % profile_path)
            # # chrome_options.add_argument("--fingerprint-config=%s" % profile_path)
            # chrome_options.add_argument("--load-extension=%s" % profile_extensions)
            # chrome_options.add_argument("--proxy-server=%s" % proxy)
            # profile_driver = webdriver.Chrome(service=Service(executable_path=executable_path), options=chrome_options)

            self.wait   = WebDriverWait(self.driver, self.wait_time)
            self.action = ActionChains(self.driver)

            self.orig_handle = self.driver.current_window_handle
            self.logger.debug("original window is: %s" % self.orig_handle)
            self.know_handle.append(self.orig_handle)

            profile_item = self.get_profile()
            self.wallet_pass = profile_item.get('pass')

            ### login to wallets first...
            log_wallet = self.login_wallets(extensions)
            if not log_wallet:
                self.logger.error("login wallet failed, try next profile...")
                continue
            self.logger.info("login to wallets successfully...")

            ### create new tab for login & running tasks
            self.task_handle = self.get_new_handle()
            self.know_handle.append(self.task_handle)
            self.logger.info("new  tasks handle is: %s" % self.task_handle)

            ### login to social account(twitter & discord...)
            # log_social = login_social()
            # if not log_social:
            #     print("login social failed")
            #     continue

            self.run_tasks_by_profile(tasks)

            ### all task finished for current profile, close the browser
            self.logger.info("finish profile: %s" % self.profile_id)
            self.last_net    = ""
            # self.position.append(position)
            self.close_browser(self.profile_id)

    def run_web_task(self):
        if not self.pre_check():
            raise Exception(f"web3 pre check failed")
        self.start_web()

def main():
    st = WebTask()
    st.run_web_task()
    # st.profile_id = "156665546fe14caf894d1f01565c862a"
    # print(st.get_profile())
    # print(st.get_extensions())
    # res = st.sql_info(input_select_sql,('8daa7a1341634a1db8bb2e3fd3aa8289', 6))
    # print(res)

if __name__ == '__main__':
    main()
