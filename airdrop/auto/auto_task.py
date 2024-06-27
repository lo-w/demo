#-*- coding:utf-8 -*-
'''
required lib:
pip install pyyaml
pip install pyperclip
pip install pyautogui
pip install pillow
pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple

'''
import os
import time
import yaml
import random
import platform
import webbrowser
import pyperclip
import pyautogui
import logging
from logging import handlers
from configparser import ConfigParser


class InitConf():
    def __init__(self) -> None:
        self.pf         = platform.system()
        self.MINS       = 1.0
        self.MAXS       = 2.0
        self.confidence = 0.9

        self.cur_dir    = os.path.dirname(os.path.abspath(__file__))
        self.log_level  = logging.INFO
        self.log_dir    = os.path.join(self.cur_dir, "./logs/")
        self.log_name   = os.path.splitext(os.path.basename(__file__))[0]
        self.log_ext    = ".log"
        self.conf       = self.load_config()
        self.check_path(self.log_dir)
        self.logger     = self.get_logger()

    def check_path(self, c_path):
        if not os.path.isdir(c_path):
            os.makedirs(c_path)

    def get_cur_path(self, file_name):
        return os.path.join(self.cur_dir, file_name)

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

    def get_chrome_path(self, chrome):
        pf = platform.system()
        cpath = ""
        if "MacOS" in pf:
            cpath = '/Applications/Google Chrome.app'
            return 'open -a %s' % cpath + ' %s' if os.path.exists(cpath) else None
        elif "Windows" in pf:
            if chrome:
                cpath = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
            else:
                cpath = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
        elif "Linux" in pf:
            if chrome:
                cpath = '/usr/bin/google-chrome'
            else:
                cpath = '/usr/bin/microsoft-edge-stable'
        return cpath + ' %s' if os.path.exists(cpath) else None

    def open_url(self, cpath, url):
        self.logger.info('start open url: %s' % url)
        webbrowser.get(cpath).open(url)
        self.sleep(3)
        self.logger.info('finish open url')

    def sleep(self, sec=1):
        time.sleep(sec)

    def get_round(self, mi, mx, decimal_places=2):
        return round(random.uniform(float(mi), float(mx)), decimal_places)

    def get_offset(self):
        ### x: width
        ### y: height
        return {"x": self.get_round(-10, 10), "y": self.get_round(-10, 10)}

    def wait_input(self):
        self.sleep(self.get_round(self.MINS, self.MAXS))

    def load_config(self, filename='auto.ini', section='auto'):
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


class MouseTask(InitConf):
    def __init__(self) -> None:
        super().__init__()

    def mouse(self, lo, o):
        ct = 1
        lr = "left"
        dura = self.get_round(self.MINS, self.MAXS)
        offset = self.get_offset()
        if o == 2:
            ct = 2
        elif o == 3:
            lr = "right"

        x = lo.x + offset.get('x')
        y = lo.y + offset.get('y')
        if o == 6:
            pyautogui.moveTo(x=x, y=y, duration=dura)  # Move the mouse to the specified location.
        else:
            pyautogui.click(x, y, clicks=ct, interval=dura, duration=dura, button=lr)  # Perform a mouse click.
        self.sleep(1)

    def validate_step(self, o, v):
        if isinstance(o, int):
            if o == 0:
                return True
            elif 0 < o < 4:
                return True if os.path.exists(os.path.join(self.cur_dir, v)) else False
            elif o == 4:
                return True if isinstance(v, int) else False
            elif o == 5:
                return True if isinstance(v, str) else False
            elif  o == 6 or o == 7:
                return True
        return False

    def get_location(self, v, r, s):
        retry_times = r if r else 4
        for _ in range(retry_times):
            try:
                location = pyautogui.locateCenterOnScreen(os.path.join(self.cur_dir, v), confidence=self.confidence)
                return location
            except:
                self.sleep(2)
        if not s:
            self.logger.error("cannot get image location")
        return None

    def execute_step(self, o, v, s, r):
        if o == 0:
            # print("sleep for %s seconds" % v)
            mi = v-2 if v >2 else 0
            self.sleep(self.get_round(mi, v))
        elif 0 < o < 4 or o == 6:
            location = self.get_location(v, r, s)
            if location:
                self.mouse(location, o)
                return True
            return True if s else False
        elif o == 4:
            # print("scroll %s..." % v)
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

    def execute_repeat_task(self, ets):
        self.logger.info("start repeat tasks...")
        rep = ets.get('rep')
        repeat_times = ets.get("ett")
        failed_count = 10
        while True:
            result = self.execute_mouse_task(rep)
            if not result:
                self.logger.error("repeat task failed...")
                failed_count = failed_count - 1
                if failed_count < 1:
                    self.logger.error("too many failed try...")
                    return False
                failed_task = rep.get('fail')
                if failed_task:
                    self.execute_mouse_task(failed_task)
                continue
            repeat_times = repeat_times - 1
            self.logger.info("left %s times" % str(repeat_times))
            if repeat_times < 1:
                break
            self.sleep(2)
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
            es = ets.get(i)
            if not es:
                self.logger.error("get execute task failed...")
                return False
            o = es.get('o')
            v = es.get('v')
            s = es.get('s')
            r = es.get('r')
            vs = self.validate_step(o, v)
            if not vs:
                self.logger.error("validate failed...")
                return False
            self.logger.info("start step: %s" % es)
            result = self.execute_step(o, v, s, r)
            if not result:
                return False
            # print("finish step...")

        if rep:
            return self.execute_repeat_task(ets)
        return True

    def perform_tasks(self, tasks):
        for task in tasks:
            if task.get("skip"):
                continue
            name = task.get("name")
            et = task.get("type")
            ets = task.get("ets")
            self.logger.info("started the task: %s" % name)
            if et:
                cpath = self.get_chrome_path(task.get("chrome"))
                if not cpath:
                    self.logger.error("no chrome/edge found in system, try next task!")
                    continue
                url = task.get("url")
                self.open_url(cpath, url)

            result = self.execute_mouse_task(ets)
            if not result:
                self.logger.error("execute task: %s failed, try next task!" % name)
                continue

            if et:
                self.logger.info("closing the tab...")
                pyautogui.hotkey('ctrl', 'w')

            self.logger.info("finished the task: %s" % name)

    def get_tasks(self, task_yaml):
        task_yaml = task_yaml if task_yaml else "task.yml"
        tasks = {}
        task_file_path = os.path.join(self.cur_dir, task_yaml)
        if os.path.exists(task_file_path):
            with open(task_file_path, 'r', encoding='UTF-8') as f:
                task_text = f.read()
                tasks = yaml.load(task_text, Loader=yaml.FullLoader)
        return tasks.get("tasks")


if __name__ == '__main__':
    mt = MouseTask()
    tasks_tmp = mt.conf.get('tasks')
    if tasks_tmp:
        tasks = tasks_tmp.split(';')
        for task in tasks:
            # print(mt.get_tasks(task))
            mt.perform_tasks(mt.get_tasks(task))
