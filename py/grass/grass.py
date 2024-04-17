# -*- coding: utf-8 -*-
'''
@File    :   grass.py
@Time    :   2024/04/12
@Author  :   renjun
'''

import os
import time
import codecs
import random
from flask import Flask
from selenium import webdriver

app              = Flask(__name__)
MINS             = 0.5
MAXS             = 2.0
INPUT_TIME       = 0.1

def sleep(sec=10):
    time.sleep(sec)

def get_sleep(mi, mx):
    return random.uniform(mi, mx)

def get_path(f_path):
    return os.path.join(workdir, f_path)

def get_param():
    try:
        user = os.environ['GRASS_USER']
        passwd = os.environ['GRASS_PASS']
        workdir = os.environ['WORKDIR']
        extensionid = os.environ['EXTENSIONID']
    except:
        raise Exception(f'please set GRASS_USER and GRASS_PASS')
    return {"user":user,"password":passwd,"extensionid":extensionid,"workdir":workdir}

user_args        = get_param()
workdir          = user_args.get('workdir')
extensionid      = user_args.get('extensionid')

op = webdriver.ChromeOptions()
op.add_argument("--headless=new")
op.add_argument("--no-sandbox")
op.add_argument("--disable-dev-shm-usage")
# op.add_argument("--load-extension=%s" % get_path("grass.crx"))
# alpine 3.15 cannot load extension hence using 3.19
op.add_extension(get_path("grass.crx"))

print("LOAD EXTENSION")
driver =  webdriver.Chrome(options=op)
print("START GRASS")

def save_log(driver):
    print("SAVE LOG TO LOCAL")
    driver.save_screenshot(get_path('logs/error.png'))
    with codecs.open(get_path("logs/connect.html"), "w", "utf-8") as hf:
        hf.write(driver.page_source)
    logs = driver.get_log('browser')
    with codecs.open(get_path('logs/error.log'), "a", "utf-8") as f:
        for log in logs:
            f.write(str(log)+'\n')

def wait_for_element(driver, findby, findvalue, max_attempts=10):
    for _ in range(max_attempts):
        try:
            return driver.find_element(findby, findvalue)
        except:
            sleep(get_sleep(MINS, MAXS))
    raise Exception(f"cannot find the element with value: %s" % findvalue)

def check_extension(driver, extensionid):
    driver.get('chrome-extension://%s/index.html' % extensionid)
    try:
        wait_for_element(driver, 'xpath', '//div/a[@href="https://app.getgrass.io"]')
    except:
        raise Exception(f"load exennsion failed")

def execute_task(driver, task_list):
    for task in task_list:
        findby = task.get('findby')
        findvalue = task.get('findvalue')
        task_ele = wait_for_element(driver, findby, findvalue)
        if not task_ele:
            raise Exception(f"get element failed, %s" % findvalue)
        operation = task.get('operation')
        mapto = task.get('mapto')
        val = ""
        if mapto:
            val = user_args.get(mapto)
        if operation == 'click':
            task_ele.click()
        elif operation == 'input':
            for v in val:
                task_ele.send_keys(v)
                sleep(INPUT_TIME)
        elif operation == 'get':
            pass

def try_login(driver):
    login_task = [
        {"step":"1","findby":"xpath","findvalue":'//input[@name="user"]',    "operation":"input","mapto":"user"},
        {"step":"2","findby":"xpath","findvalue":'//input[@name="password"]',"operation":"input","mapto":"password"},
        {"step":"3","findby":"xpath","findvalue":'//button[@type="submit"]', "operation":"click"}
    ]
    execute_task(driver, login_task)
    wait_for_element(driver, 'xpath', '//div/a[@href="/dashboard"]', 30)
    print("LOGIN SUCCEED")

def open_dashboard(driver):
    for i in range(30):
        try:
            wait_for_element(driver, 'xpath', '//*[contains(text(), "Open dashboard")]', 3)
            print("OPEN DASHBOARD SUCCEED")
            break
        except:
            print("TRY OPEN %d times" % i)

def try_connect(driver):
    connect_task = [
        {"step":"1","findby":"xpath","findvalue":'//button[contains(@id, "menu-button")]', "operation":"click"},
        {"step":"2","findby":"xpath","findvalue":'//button[contains(@id, "menu-list")]', "operation":"click"}
    ]
    execute_task(driver, connect_task)

def start_grass():
    # check_extension(driver, extensionid)
    print("TRY TO GET RESP")
    driver.get('https://app.getgrass.io/')

    print("TRY TO LOGIN")
    try_login(driver)

    ### OPEN DASHBOARD TAB
    print("OPEN DASHBOARD")
    driver.get('chrome-extension://%s/index.html' % extensionid)
    open_dashboard(driver)

    print("WAIT TO CONNECT")

@app.route('/')
def get():
    connect = None
    net_qua = None
    try:
        connect_ele = wait_for_element(driver, 'xpath','//div[contains(@class, "chakra-stack")]/span[contains(@class, "chakra-badge")]//p[contains(@class,"chakra-text")]/text()')
        if connect_ele:
            connect = connect_ele[0] 

        network_quality_ele = wait_for_element(driver, 'xpath','//div[contains(@class, "chakra-stack")]/div[contains(@class, "chakra-skeleton")]/p[contains(@class,"chakra-text")]/text()')
        for ele in network_quality_ele:
            if "network quality:" in ele.lower():
                net_qua = ele.split(':')[-1].strip()
                break
    except:
        save_log(driver)
    return {"connect":connect, "network_quality": net_qua}

if __name__ == '__main__':
    print("START")
    start_grass()
    app.run(host='localhost',port=3000, debug=False)
    driver.quit()
