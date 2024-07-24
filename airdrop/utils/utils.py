#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   utils.py
@Author  :   renjun
'''
import os
import time
import pyotp
import ctypes
import psutil
import random
import logging
import platform
import unicodedata
import pyperclip
import pyautogui
import psycopg2
import webbrowser
import psycopg2.extras
import threading

from os import path
from logging import handlers
from datetime import datetime
from configparser import ConfigParser


profile_select_sql      =  "SELECT * FROM profiles where profile=%s;"
extensions_select_sql   =  "SELECT * FROM extensions;"
tasks_select_sql        =  "SELECT distinct name FROM tasks where name not in ('metamask','unisat','keplr','fallback');"


class InitConf():
    def __init__(self) -> None:
        self.pf               = platform.system()
        self.google_url       = "https://www.google.com"

        self.log_level        = logging.INFO
        self.log_ext          = ".log"
        self.cur_dir          = self.get_cur_dir(__file__)
        self.log_dir          = self.get_log_path("./logs/")
        self.logger           = self.get_logger(self.get_log_name(__file__))

        self.MINS             = 1.0
        self.MAXS             = 2.0
        self.INPUT_TIME       = 0.1
        self.wait_time        = 10
        self.wait_handle      = 15
        self.WEB_PAGE_TIMEOUT = 30

        self.confidence       = 0.9
        self.r                = 4

        self.wallets_pre      = ["meta_", "okx_"]
        self.wallets_not      = ["wallets", "switch"]
        self.RLIST            = [",", "-"]
        self.JSON_ID          = '{"id": "%s"}'

        self.CHROME_EXTENSION = "chrome-extension://%s/%s.html"
        self.position         = ["0,0","%s,0" % str(int(self.getMWH()[0])/2)]
        self.browser          = None

    def get_cur_dir(self, file_name):
        return os.path.dirname(os.path.abspath(file_name))

    def get_cur_path(self, file_name):
        return os.path.join(self.cur_dir, file_name)

    def get_log_name(self, file_name):
        return os.path.splitext(os.path.basename(file_name))[0]

    def get_log_path(self, file_name):
        return os.path.join(path.dirname(self.cur_dir), file_name)

    def check_path(self, c_path):
        if not os.path.isdir(c_path):
            os.makedirs(c_path)

    def get_logger(self, log_name):
        self.check_path(self.log_dir)
        log_handler = handlers.TimedRotatingFileHandler(filename=self.log_dir + log_name + self.log_ext, backupCount=5)
        log_handler.suffix = "%Y%m%d"
        formatter = logging.Formatter(
            '%(asctime)s,%(msecs)03d %(levelname)-5s [%(filename)-12s:%(lineno)03d] %(message)s',
            '%Y-%m-%d %H:%M:%S'
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
            val_list = str(val_string).split(spl)
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
        return {"x": self.get_round(-10, 10), "y": self.get_round(-6, 6)}

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

    def load_config(self, filename=None, section=None):
        if not filename or not section:
            return
        parser = ConfigParser()
        parser.read(filename)
        if not parser.has_section(section):
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))
        # get section, default to postgresql
        config = {}
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
        return config

    def if_process_is_running_by_exename(self, exename='chrome'):
        ### chrome, msedge
        for proc in psutil.process_iter(['pid', 'name']):
            # This will check if there exists any process running with executable name
            if proc.info['name'] == exename:
                return True
        return False

    def get_chrome_path(self, chrome):
        cpath = ""
        self.browser_name = "chrome" if chrome else "msedge"

        if "MacOS" in self.pf:
            cpath = '/Applications/Google Chrome.app'
            return 'open -a %s' % cpath + ' %s' if os.path.exists(cpath) else None
        elif "Windows" in self.pf:
            cpath = 'C:/Program Files/Google/Chrome/Application/chrome.exe' if chrome else 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
            self.browser_name += ".exe"
            self.browser_close = "taskkill /f /im " + self.browser_name
        elif "Linux" in self.pf:
            cpath = '/usr/bin/google-chrome' if chrome else '/usr/bin/microsoft-edge-stable'
            self.browser_close = "pkill " + self.browser_name
        return cpath + ' %s' if os.path.exists(cpath) else None

    def open_url(self, cpath, url):
        self.logger.info('start  open url: %s' % url)
        browser_running = self.if_process_is_running_by_exename(self.browser_name)

        if not browser_running:
            x=lambda: webbrowser.get(cpath).open(self.google_url)
            threading.Thread(target=x).start()
            self.sleep(2)

        webbrowser.get(cpath).open(url)
        self.sleep(3)
        self.logger.info('finish open url')

    def close_browser(self):
        if self.browser_close:
            os.system(self.browser_close)

class MouseTask(InitConf):
    def __init__(self) -> None:
        super().__init__()

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

        x = lo.x + offset.get('x')
        y = lo.y + offset.get('y')
        tween = pyautogui.easeInOutSine

        if o == 6:
            pyautogui.moveTo(x, y, duration=dura,tween=tween)  # Move the mouse to the specified location.
        else:
            pyautogui.click(x, y, clicks=ct, interval=dura, duration=dura, button=lr, tween=tween)  # Perform a mouse click.
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

    def get_location(self, v, r, s):
        retry_times = r or self.r
        for _ in range(retry_times):
            try:
                location = pyautogui.locateCenterOnScreen(self.get_cur_path(v), confidence=self.confidence)
                return location
            except:
                self.wait_input()
        if not s:
            self.logger.error("cannot get image location")
        return None

    def execute_step(self, o, v, s, r):
        if o == 0:
            mi = v-2 if v > 2 else 0
            self.wait_input(mi, v)
            # self.sleep(self.get_round(mi, v))
        elif 0 < o < 4 or o == 6:
            location = self.get_location(v, r, s)
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

        for wallet_pre in self.wallets_pre:
            if str(v).startswith(wallet_pre):
                v = "wallets/%s" % v

        if str(v).startswith("task_"):
            v = "tasks/%s" % v

        vs = self.validate_step(o, v)
        if not vs:
            self.logger.error("validate failed...")
            return
        self.logger.info("start  mouse step: %s" % es)
        result = self.execute_step(o, v, s, r)
        if not result:
            return
        self.logger.debug("finish mouse step: %s" % es)
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
            es = ets.get(i) if isinstance(next(iter(ets)), int) else ets.get(str(i))
            if not es:
                self.logger.error("get execute task failed...")
                return
            res = self.execute_task_step(es)
            if not res:
                return
        return self.execute_repeat_task(ets) if rep else True


class PostGressDB(InitConf):
    def __init__(self) -> None:
        super().__init__()
        self.cur_dir = self.get_cur_dir(__file__)
        dbconf = self.load_config(self.get_cur_path("database.ini"), "postgresql")
        conn = self.connect(dbconf)
        self.cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) if conn else None

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

