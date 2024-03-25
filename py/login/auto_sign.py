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
import platform
import webbrowser
import yaml
import pyperclip
import pyautogui


def get_chrome_path():
    pf = platform.system()
    cpath = ""
    if "MacOS" in pf:
        cpath = '/Applications/Google Chrome.app'
        return 'open -a %s' % cpath + ' %s' if os.path.exists(cpath) else None
    elif "Windows" in pf:
        cpath = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
    elif "Linux" in pf:
        cpath = '/usr/bin/google-chrome'
    return cpath + ' %s' if os.path.exists(cpath) else None

def open_url(cpath, url):
    print('start open url: ', url)
    webbrowser.get(cpath).open(url)
    sleep(6)
    print('finish open url')

def sleep(sec=1):
    time.sleep(sec)

def mouse(lo, o):
    ct = 1
    lr = "left"
    if o == 2:
        ct = 2
    elif o == 3:
        lr = "right"
    pyautogui.click(lo.x,lo.y,clicks=ct,interval=0.2,duration=0.2,button=lr)
    sleep(2)

def validate_step(o, v):
    if isinstance(o, int):
        if o == 0:
            return True if isinstance(v, int) else False
        elif 0 < o < 4:
            return True if os.path.exists(v) else False
        elif o == 4:
            return True if isinstance(v, int) else False
        elif o == 5:
            return True if isinstance(v, str) else False
    return False

def execute_step(o, v, s, rt=3):
    if o == 0:
        sleep(v)
    elif 0 < o < 4:
        for _ in range(0, rt):
            location = pyautogui.locateCenterOnScreen(v, confidence=0.8)
            if location:
                mouse(location, o)
                return True
        return True if s else False
    elif o == 4:
        pyautogui.scroll(v)
    elif o == 5:
        pyperclip.copy(v)
        pyautogui.hotkey('ctrl','v')
    else:
        return False
    return True

def execute_task(ets):
    for i in range (len(ets.keys())):
        es = ets.get(i)
        if es:
            o = es.get('o')
            v = es.get('v')
            s = es.get('s')
            vs = validate_step(o, v)
            if vs:
                print("start step: ", es)
                result = execute_step(o, v, s)
                if not result:
                    return False
                print("finish step...")
            else:
                print("validate failed...")
                return False
        else:
            return False
    return True

def perform_tasks(tasks):
    cpath = get_chrome_path()
    if cpath:
        for task in tasks:
            name = task.get("name")
            et = task.get("type")
            ets = task.get("ets")

            print("started the task: ", name)
            if et:
                url = task.get("url")
                open_url(cpath, url)
                result = execute_task(ets)
                pyautogui.hotkey('ctrl', 'w')
            else:
                result = execute_task(ets)
            if result:
                print("finished the task: ", name)
            else:
                print("skip task: ", name)
    else:
        print("no chrome found in system, exit!")

def get_tasks(task_yaml):
    task_yaml = task_yaml if task_yaml else "task.yml"
    tasks = {}
    if os.path.exists(task_yaml):
        with open(task_yaml, 'r', encoding='UTF-8') as f:
            task_text = f.read()
            tasks = yaml.load(task_text, Loader=yaml.FullLoader)
    return tasks.get("tasks")


if __name__ == '__main__':
    tasks = get_tasks("")
    if tasks:
        perform_tasks(tasks)
    else:
        print("no task need to execute, exit!")
