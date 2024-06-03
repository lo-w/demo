
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
import sqlite3
import hashlib
import random
import logging
import requests
import platform
import unicodedata
import pyperclip
import pyautogui

from lxml import html
from logging import handlers
from datetime import datetime
from multiprocessing.pool import ThreadPool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains


headers          = {'Content-Type': 'application/json'}
confidence       = 0.95

BIT_URL          = "http://127.0.0.1:54345"
RLIST            = [",", "-"]
JSON_ID          = '{"id": "%s"}'
WEB_PAGE_TIMEOUT = 30
INPUT_TIME       = 0.1
MINS             = 0.5
MAXS             = 2.0
CHROME_EXTENSION = "chrome-extension://%s/%s.html"

CUR_DIR          = os.path.dirname(os.path.abspath(__file__))
CONFIG_DB_PATH   = os.path.join(CUR_DIR, "config.db")
LOG_DIR          = os.path.join(CUR_DIR, "./logs/")
LOG_NAME         = os.path.splitext(os.path.basename(__file__))[0]

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

def sleep(sec=1):
    time.sleep(sec)

def get_round(mi, mx):
    return round(random.uniform(mi, mx),2)

def get_sleep(mi, mx):
    return get_round(mi, mx)

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
    dura = get_round(0.5, 1)
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
        sleep(get_round(1, 2))
        pyautogui.hotkey('ctrl','v')
        sleep(get_round(1, 2))
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

def get_xpath_ele(ele):
    if ele:
        val = ele[0]
        if "(" in val:
            val = val.split("(")[0]
        for c in RLIST:
            val = val.replace(c, "")
        return unicodedata.normalize('NFKD', val).strip()
    return ""

def wait_for_element(driver, findby, findvalue, max_attempts=3, eles=False):
    for _ in range(max_attempts):
        try:
            return driver.find_element(findby, findvalue)
        except Exception:
            # logger.info("retry get value again: %s" % findvalue)
            time.sleep(get_sleep(MINS, MAXS))
    raise Exception(f"cannot find the element with value: %s" % findvalue)

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

def open_browser(id):    # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
    return requests.post(f"{BIT_URL}/browser/open", data=JSON_ID % id, headers=headers).json()

def close_browser(id):   # 关闭窗口
    requests.post(f"{BIT_URL}/browser/close", data=JSON_ID % id, headers=headers).json()

def get_bit_profiles():
    return requests.post(f"{BIT_URL}/browser/list", data=json.dumps({"page":0,"pageSize":10}), headers=headers).json()

def get_bit_url():
    url = "http://127.0.0.1:"
    for proc in psutil.process_iter():
        if proc.name() == '比特浏览器.exe':
            for x in proc.connections():
                if x.status == psutil.CONN_LISTEN:
                    url = url + str(x.laddr.port)
                    return url
    return None

def check_bit_browser():
    BIT_URL = get_bit_url()
    return True if BIT_URL else False
    # return True

def get_tasks_by_id(profile_id, ext_id):
    if profile_id == "8daa7a1341634a1db8bb2e3fd3aa8289":
        mapto = "vXzx}@^Sm#{7g-'W"
    else:
        mapto = "y:KHF~Mu2*3#^c>G"

    if ext_id == "nkbihfbeogaeaoehlefnkodbefgpgknn":
        return [{"name":"meta","ets":{"0":{"o":1,"v":"meta_pass.png"},"1":{"o":5,"v":mapto},"2":{"o":1,"v":"meta_login.png"}}}]
    elif ext_id == "ppbibelpcjmhbdihakflkdcoccbgbkpo":
        return [{"name":"meta","ets":{"0":{"o":1,"v":"unisat_pass.png"},"1":{"o":5,"v":mapto},"2":{"o":1,"v":"unisat_login.png"}}}]

def exe_tasks(task_driver, tasks, hc, extension, wallet=False):
    for task in tasks:
        findby = task.get('findby')
        findvalue = task.get('findvalue')
        operation = task.get('operation')




        task_ele = wait_for_element(task_driver, findby, findvalue)
        if not task_ele:
            print("ele not found for %s" % findvalue)
            # logger.error("running task:%s failed with get element failed, %s" % (offer_uuid, findvalue))
            return
        mapto = task.get('mapto')
        val = ""
        if mapto:
            val = mapto.strip()

        if operation == 'click':
            try:
                task_ele.click()
            except Exception as e:
                if wallet:
                    task_driver.switch_to.window(task_driver.window_handles[hc+1])
                    task_driver.get('chrome-extension://{}/popup.html'.format(extension))
                    sleep(5)
                    task_driver.execute_script("window.scrollBy(0, document.body.scrollHeight)")
                    task_driver.find_element_by_xpath('//*[@id="app-content"]/div/div[3]/div/div[4]/footer/button[1]').click()
                    sleep(5)
                # if "Other element would receive the click" in e:
                #     with codecs.open("./error.html", "w", "utf-8") as hf:
                #         hf.write(task_driver.page_source)
        elif operation == 'input':
            for v in val:
                task_ele.send_keys(v)
                time.sleep(INPUT_TIME)
        elif operation == 'select':
            for op in task_ele.find_elements(By.TAG_NAME, 'option'):
                if val.lower() in op.text.lower():
                    op.click()
        else:
            # logger.error("running offer:%s failed with unsupported operation: %s" % (offer_uuid, operation))
            return
        # logger.info("finish task: %s" % findvalue)
        time.sleep(MINS)

    return True

def login_wallet_task(task_driver, profile_id, extension):
    logger.info("login to wallet %s..." % extension)
    ### name id version
    ext_id = extension.get("id")
    ext_tasks = get_tasks_by_id(profile_id, ext_id)

    task_driver.get(CHROME_EXTENSION % (ext_id, extension.get("home")))
    sleep(4)
    task_resp = perform_mouse_tasks(ext_tasks)

    if not task_resp:
        return False
    return True

def login_wallet(task_driver, extensions, profile_id):
    for extension in extensions:
        log_status = login_wallet_task(task_driver, profile_id, extension)
        if not log_status:
            return False
    return True

def login_social():
    return True

def get_tasks():
    return [
        {
            "url": "https://adamdefi.io/swap",
            "extension": "nkbihfbeogaeaoehlefnkodbefgpgknn",
            "tasks": [
                {
                    "findby": "xpath",
                    "findvalue": '(//div[contains(@class, "items-center")]//span[contains(text(), "ZBTC")])[last()]',
                    "operation": "click"
                },
                {
                    "findby": "xpath",
                    "findvalue": '//*[@id="__nuxt"]//div/input[@placeholder=0]',
                    "operation": "input",
                    "mapto": "0.0001"
                },
                {
                    "findby": "xpath",
                    "findvalue": '//*[@id="__nuxt"]//div/button[contains(@class, "dex-button")]',
                    "operation": "click"
                }
            ]
        }
    ]

def get_profiles():
    return [
        {
            "id": "8daa7a1341634a1db8bb2e3fd3aa8289",
            "path": "C:/Users/lo/AppData/Local/Google/Chrome/User Data/Profile 1"
        }
    ]

def get_extensions():
    return [
        {"name":"metamask", "id":"nkbihfbeogaeaoehlefnkodbefgpgknn", "home":"home",  "version":"11.15.6_0"},
        # {"name":"okx",      "id":"mcohilncbfahbmgdjkbpemcciiolgcge", "home":"home",  "version":"2.96.0_0"},
        {"name":"unisat",   "id":"ppbibelpcjmhbdihakflkdcoccbgbkpo", "home":"index", "version":"1.3.3_0"},
        # {"name":"initia",   "id":"ffbceckpkpbcmgiaehlloocglmijnpmp", "home":"index", "version":"0.59.0_0"},
        # {"name":"keplr",    "id":"dmkamcknogkgcdfhhbddcghachkejeap", "home":"popup", "version":"0.12.95_0"},
    ]

def get_proxy_by_profile(profile_id):
    return "socks://192.168.1.13:10808"

def run_tasks_by_profile(task_driver, tasks, hc):
    for task in tasks:
        task_url = task.get('url')
        extension = task.get('extension')

        task_driver.get(task_url)
        task_driver.set_page_load_timeout(WEB_PAGE_TIMEOUT)
        # wait for the element load
        sleep(3)
        perform_mouse_tasks([{"name":"zulu","ets":{"0":{"o":1,"v":"zulu_select.png"}}}])
        # with codecs.open("./error.html", "w", "utf-8") as hf:
        #     hf.write(profile_driver.page_source)
        for _ in range(2):
            exe_tasks(task_driver, task.get('tasks'), hc, extension, True)
            # perform_mouse_tasks([{"name":"meta","ets":{"0":{"o":1,"v":"meta_confirm.png"}}}])
        time.sleep(2000)

def start_web():
    profile_resp = get_bit_profiles()
    profiles = profile_resp.get('data').get('list')
    # profiles = get_profiles()
    extensions =  get_extensions()
    # executable_path = "C:/others/dev/py/chromedriver-win64/chromedriver.exe"
    tasks = get_tasks()
    for profile in profiles:
        hc = 0
        profile_id = profile.get('id')
        # print(profile_id)
        # continue
        # profile_path = profile.get('path')
        # profile_extensions = ",".join([os.path.join(profile_path,"Extensions",extension) for extension in extensions])
        # proxy = get_proxy_by_profile(profile_id)
        chrome_options = Options()
        res = open_browser(profile_id)
        # print(res['data']['driver'])
        chrome_options.add_experimental_option("debuggerAddress", res['data']['http'])
        profile_driver = webdriver.Chrome(service=Service(executable_path=res['data']['driver']), options=chrome_options)

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

        hc += 1
        profile_driver.execute_script('''window.open("%s", "%s");''' % ('', profile_id))
        profile_driver.switch_to.window(profile_driver.window_handles[hc])

        # log_wallet = login_wallet(profile_driver, extensions, profile_id)
        # if not log_wallet:
        #     print("login wallet failed")
        #     continue
        # print("login to wallet successfully...")

        # log_social = login_social()
        # if not log_social:
        #     print("login social failed")
        #     continue
        run_tasks_by_profile(profile_driver, tasks, hc)


def pre_check():
    return check_bit_browser()

def run_web_task():
    if not pre_check():
        raise Exception(f"web3 pre check failed")
    start_web()

def main():
    run_web_task()

if __name__ == '__main__':
    main()
