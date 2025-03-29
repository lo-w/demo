#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   utils.py
@Author  :   renjun

required lib:
pip install pyotp
pip install psutil
pip install pyperclip
pip install pyautogui
pip install pillow
pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install psycopg2-binary

for linux:
apt install xclip

'''
import os
import time
import pyotp
import ctypes
import psutil
import random
import logging
import platform
import pyperclip
import threading
import webbrowser
import subprocess
import psycopg2
import psycopg2.extras

from datetime import datetime, timezone

from os import path
from logging import handlers
from configparser import ConfigParser
from abc import abstractmethod
from subprocess import check_output


profiles_select_sql       = "SELECT * FROM profiles;"
profile_select_sql        = "SELECT * FROM profiles where profile=%s;"
records_select_by_profile = "SELECT * FROM records  where profile=%s order by update_time desc limit 1;"
extensions_select_sql     = "SELECT * FROM extensions where login is True;"
tasks_select_sql          = "SELECT distinct name FROM tasks where name not in ('metamask','unisat','keplr','fallback');"


class InitConf():
    def __init__(self) -> None:
        self.pf               = platform.system()
        # self.new_title      = "Version"
        self.open_page        = "chrome://version/"
        self.new_url          = "https://www.bing.com"
        self.new_title        = "Bing"

        self.log_level        = logging.INFO
        self.log_ext          = ".log"
        self.cur_dir          = self.get_cur_dir(__file__)
        self.log_dir          = self.get_log_path("./logs/")
        self.logger           = self.get_logger(self.get_log_name())

        self.MINS             = 0.8
        self.MAXS             = 1.5
        self.INPUT_TIME       = 0.1
        self.wait_time        = 5
        self.wait_handle      = 10
        self.WEB_PAGE_TIMEOUT = 30

        self.confidence       = 0.9 if self.pf == "Windows" else 0.8
        self.r                = 4

        self.split_str        = ";;"
        self.wallets_pre      = ["meta_", "okx_"]
        self.wallets_not      = ["wallets", "switch"]

        self.known_titles     = ["SwitchyOmega", "MetaMask Offscreen", "https://testnet.zulunetwork.io"]
        self.known_handles    = []
        self.extensions       = []
        self.tasks            = []
        self.orig_handle      = ""
        self.task_handle      = ""
        self.wall_handle      = ""
        self.wallet_pass      = ""
        self.last_net         = ""
        self.profile_id       = ""
        self.wallet_operation_list = ["confirm", "cancel", "switchnet", "signpay", "sign"]
        self.RLIST            = [",", "-"]
        self.JSON_ID          = '{"id": "%s"}'
        self.background       = True
        self.init_pyautogui()
        self.position         = ["0,0","%s,0" % str(int(self.getMWH()[0])/2)]
        self.browser          = "chrome"
        self.browser_close    = ""
        self.tweens           = []

    def get_cur_dir(self, file_name):
        return os.path.dirname(os.path.abspath(file_name))

    def get_cur_path(self, file_name):
        return os.path.join(self.cur_dir, file_name)

    def get_log_name(self):
        if not self._log_name:
            self._log_name = __file__
        return os.path.splitext(os.path.basename(self._log_name))[0]

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
        if not logger.handlers:
            logger.addHandler(log_handler)
        logger.setLevel(self.log_level)
        return logger

    def handle_function(self, parameter, *args, **kwargs):
        call_func = 'handle_' + parameter
        if hasattr(self, call_func):
            self.logger.debug(f"perfrom handle function: {call_func}")
            res = getattr(self, call_func)(*args, **kwargs)
            return res
        else:
            self.logger.error(f"handle function not exist: {call_func}")

    def get_otp(self, secret):
        # secret = 'MDANW36JHNV3EOBM'
        totp = pyotp.TOTP(secret)
        return totp.now()

    def sleep(self, sec=1):
        time.sleep(sec)

    def get_round(self, mi, mx, decimal_places=2):
        return round(random.uniform(float(mi), float(mx)), int(decimal_places))

    def get_random_from_range(self, spl, val_string):
        val = val_string
        if spl in val_string:
            val_list = str(val_string).split(spl)
            if len(val_list) > 2:
                val = self.get_round(val_list[0], val_list[-1], val_list[-2])
            else:
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

    def choose_item_from_list(self, items):
        return random.choice(items)

    def get_offset(self):
        ### x: width
        ### y: height
        return {"x": self.get_round(-10, 10), "y": self.get_round(-6, 6)}

    def exe_shell(self, command):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
        stdout, stderr = process.communicate()
        self.exit_code = process.returncode
        return stdout.rstrip("\n"), stderr

    def init_pyautogui(self):
        if self.background:
            import Xlib.display # type: ignore
            from pyvirtualdisplay.display import Display
            # export DISPLAY=:99 && Xvfb :99 -ac &
            os.environ["DISPLAY"] = ":99"
            self.exe_shell("Xvfb :99 -ac &")
            disp = Display(visible=True, size=(2560, 1440), backend="xvfb", use_xauth=True, extra_args=[":99"])
            disp.start()

        import pyautogui
        self.tweens = [pyautogui.easeInOutQuart, pyautogui.easeInOutQuint, pyautogui.easeInOutSine, pyautogui.easeInOutExpo]
        self._pyautogui = pyautogui
        # pyautogui._pyautogui_x11._display = Xlib.display.Display(os.environ['DISPLAY'])

    def getMWH(self):
        if self.background:
            return 2560, 1440

        match self.pf:
            case "Windows":
                user32 = ctypes.windll.user32
                self.driver_path   = "C:/others/dev/py/chromedriver-win64/chromedriver.exe"
                self.user_data_dir = "C:/others/dev/chromedata/"
                return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            case "Linux":
                command = "xrandr | awk -F'[ ]+|,' '/current/{print $9 $10 $11}'"
                self.driver_path = "/home/lo/chromedata/chromedriver-linux64/chromedriver"
                self.user_data_dir = "/home/lo/chromedata"
            case "MacOS":
                command = "system_profiler SPDisplaysDataType | awk -F' ' '/Resolution/{print $2 \"x\" $4}'"
            case _:
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
            raise Exception(f'Section {section} not found in the {filename} file')
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

    def get_browser_path(self):
        cpath = ""
        match self.pf:
            case "MacOS":
                match self.browser:
                    case "chrome":
                        cpath = '/Applications/Google Chrome.app'
                    case "msedge":
                        cpath = '/Applications/Microsoft Edge.app'
                self.browser_close = ""
                return 'open -a %s' % cpath + ' %s' if os.path.exists(cpath) else None
            case "Windows":
                match self.browser:
                    case "chrome":
                        cpath = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
                    case "msedge":
                        cpath = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
                self.browser_close = f"taskkill /f /im {self.browser}.exe"
            case "Linux":
                match self.browser:
                    case "chrome":
                        cpath = '/usr/bin/chrome'
                    case "msedge":
                        cpath = '/usr/bin/microsoft-edge-stable'
                self.browser_close = f"pkill {self.browser}"
            case _:
                return
        return cpath + ' %s' if os.path.exists(cpath) else None

    def open_url(self, cpath, url):
        self.logger.info(f'start  open url: {url}')
        browser_running = self.if_process_is_running_by_exename(self.browser_name)

        if not browser_running:
            x=lambda: webbrowser.get(cpath).open(self.new_url)
            threading.Thread(target=x).start()
            self.sleep(2)

        webbrowser.get(cpath).open(url)
        self.sleep(3)
        self.logger.info('finish open url')

    @abstractmethod
    def exe_profile(self):
        pass

    @abstractmethod
    def get_driver(self):
        pass

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
        tween = self.choose_item_from_list(self.tweens)

        if o == 6:
            self._pyautogui.moveTo(x, y, duration=dura,tween=tween)  # Move the mouse to the specified location.
        else:
            self._pyautogui.click(x, y, clicks=ct, interval=dura, duration=dura, button=lr, tween=tween)  # Perform a mouse click.
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
            elif  5 < o < 10:
                return True
        return False

    def get_location(self, v, r, s):
        retry_times = r or self.r
        for _ in range(retry_times):
            try:
                location = self._pyautogui.locateCenterOnScreen(self.get_cur_path(v), confidence=self.confidence)
                return location
            except:
                self.wait_input()
        if not s:
            self.logger.info(f"cannot get image location with path: {v}")
        return None

    def execute_step(self, o, v, s, r, u):
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
            self._pyautogui.scroll(v)
        elif o == 5:
            pyperclip.copy(v)
            self.wait_input()
            self._pyautogui.hotkey('ctrl','v')
            self.wait_input()
        elif o == 7:
            self._pyautogui.hotkey(v)
        elif o == 9:
            if u:
                self.cpath = " ".join((self.cpath, f"--user-data-dir={u}"))
            self.open_url(self.cpath, v)
        else:
            return
        return True

    def execute_task_step(self, es):
        o = es.get('o')
        v = es.get('v')
        s = es.get('s')
        r = es.get('r')
        u = es.get('u')
        for wallet_pre in self.wallets_pre:
            if str(v).startswith(wallet_pre):
                v = f"wallets/{v}"

        if str(v).startswith("task_"):
            v = f"tasks/{v}"

        vs = self.validate_step(o, v)
        if not vs:
            self.logger.error("validate failed...")
            return
        self.logger.debug(f"start  mouse step: {es}")
        result = self.execute_step(o, v, s, r, u)
        if not result:
            return
        self.logger.debug(f"finish mouse step: {es}")
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
                self.logger.info(f"repeat task failed, left {failed_count}...")
                if failed_count < 1:
                    self.logger.error("too many failed try...")
                    return False
                self.execute_mouse_task(rep.get('fail'))
                continue
            repeat_times = repeat_times - 1
            self.logger.info(f"left {str(repeat_times)} times")
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

    def close_webbrowser(self):
        if self.browser_close:
            os.system(self.browser_close)


class PostGressDB(InitConf):
    def __init__(self) -> None:
        super().__init__()
        self.cur_dir = self.get_cur_dir(__file__)
        dbconf = self.load_config(self.get_cur_path("database.ini"), "postgresql")
        conn = self.connect(dbconf)
        conn.set_session(autocommit=True)
        self.cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) if conn else None

    def connect(self, config):
        """ Connect to the PostgreSQL database server """
        try:
            # connecting to the PostgreSQL server
            with psycopg2.connect(**config) as conn:
                self.logger.debug("success connected to the PostgreSQL server...")
                return conn
        except (psycopg2.DatabaseError, Exception) as e:
            self.logger.error(f"failed connect to DB with error: {e}")
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

    def get_profiles(self):
        return self.sql_info(profiles_select_sql)

    def get_profile(self, profile_id):
        profile_item = self.sql_info(profile_select_sql, (profile_id,))
        return profile_item[0] or None

    def get_records(self, records_sql, params):
        res = self.sql_info(records_sql, params)
        return res[0] if res else None

    def update_records(self, update_record, params):
        return self.sql_info(update_record, params, False)

    def check_profile(self):
        res = self.get_records(records_select_by_profile, (self.profile_id,))
        if res:
            update_time = res.get('update_time')
            update_date = update_time.date()
            if self.current_date == update_date:
                self.logger.info(f"profile: {self.profile_id} already running today")
                return
        return True

    def profile_pre_check(self, profile_check=True):
        self.current_time = datetime.now(timezone.utc)
        self.current_date = self.current_time.date()
        if profile_check:
            res = self.check_profile()
            if not res:
                return
        if not self.extensions:
            self.extensions = self.get_extensions()

        if not self.tasks:
            ### get tasks
            self.tasks = self.get_tasks()
            self.logger.debug(f"successfully get tasks: {self.tasks}")
        return True

