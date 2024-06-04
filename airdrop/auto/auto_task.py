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

CUR_DIR             = os.path.dirname(os.path.abspath(__file__))
LOG_DIR             = os.path.join(CUR_DIR, "./logs/")
LOG_NAME            = os.path.splitext(os.path.basename(__file__))[0]
confidence          = 0.9

def check_path(c_path):
    if not os.path.isdir(c_path):
        os.makedirs(c_path)

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


def get_chrome_path(chrome):
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

def open_url(cpath, url):
    print('start open url: ', url)
    webbrowser.get(cpath).open(url)
    sleep(3)
    print('finish open url')

def sleep(sec=1):
    time.sleep(sec)

def mouse(lo, o):
    ct = 1
    lr = "left"
    dura = round(random.uniform(0.5, 1),2)
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
            return True if os.path.exists(os.path.join(CUR_DIR, v)) else False
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
            location = pyautogui.locateCenterOnScreen(os.path.join(CUR_DIR, v), confidence=confidence)
            return location
        except:
            sleep(2)
    logger.error("cannot get image location")
    return None

def execute_step(o, v, s, r):
    if o == 0:
        # print("sleep for %s seconds" % v)
        mi = v-2 if v >2 else 0
        sleep(round(random.uniform(mi, v),2))
    elif 0 < o < 4 or o == 6:
        location = get_location(v, r)
        if location:
            mouse(location, o)
            return True
        return True if s else False
    elif o == 4:
        # print("scroll %s..." % v)
        pyautogui.scroll(v)
    elif o == 5:
        pyperclip.copy(v)
        sleep(round(random.uniform(1, 2),2))
        pyautogui.hotkey('ctrl','v')
        sleep(round(random.uniform(1, 2),2))
    elif o == 7:
        pyautogui.hotkey(v)
    else:
        return False
    return True

def execute_task(ets):
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
            logger.error("get execute task failed...")
            return False
        o = es.get('o')
        v = es.get('v')
        s = es.get('s')
        r = es.get('r')
        vs = validate_step(o, v)
        if not vs:
            logger.error("validate failed...")
            return False
        logger.info("start step: %s" % es)
        result = execute_step(o, v, s, r)
        if not result:
            return False
        # print("finish step...")

    if rep:
        print("start repeat tasks...")
        repeat_times = ets.get("ett")
        failed_count = 10
        while True:
            result = execute_task(rep)
            if not result:
                logger.error("repeat task failed...")
                failed_count = failed_count - 1
                if failed_count < 1:
                    logger.error("too many failed try...")
                    return False
                execute_task(rep.get('fail'))
                continue
            repeat_times = repeat_times - 1
            logger.info("left %s times" % str(repeat_times))
            if repeat_times < 1:
                break
            sleep(2)
    return True

def perform_tasks(tasks):
    for task in tasks:
        if task.get("skip"):
            continue
        name = task.get("name")
        et = task.get("type")
        ets = task.get("ets")
        print("started the task: ", name)
        if et:
            cpath = get_chrome_path(task.get("chrome"))
            if not cpath:
                logger.error("no chrome/edge found in system, try next task!")
                continue
            url = task.get("url")
            open_url(cpath, url)

        result = execute_task(ets)
        if not result:
            logger.error("execute task: %s failed, try next task!" % name)
            continue

        if et:
            logger.info("closing the tab...")
            pyautogui.hotkey('ctrl', 'w')

        logger.info("finished the task: ", name)

def get_tasks(task_yaml):
    task_yaml = task_yaml if task_yaml else "task.yml"
    tasks = {}
    task_file_path = os.path.join(CUR_DIR, task_yaml)
    if os.path.exists(task_file_path):
        with open(task_file_path, 'r', encoding='UTF-8') as f:
            task_text = f.read()
            tasks = yaml.load(task_text, Loader=yaml.FullLoader)
    return tasks.get("tasks")


if __name__ == '__main__':
    tasks = get_tasks("")
    if tasks:
        # import json
        # print(json.dumps(tasks))
        perform_tasks(tasks)
    else:
        logger.error("no task need to execute, exit!")
