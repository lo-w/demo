# import codecs
# import csv
import psutil
import requests
import win32gui
import win32con
import win32api
import win32com.client
from ctypes import windll

# def my_is_integer(n):
#     try:
#         float(n)
#     except ValueError:
#         return False
#     else:
#         return float(n).is_integer()

# with codecs.open("./cred.xlsx", "r", "utf-8") as r:
#     csvreader = csv.reader(r, delimiter=',')
#     for line in csvreader:
#         if not my_is_integer(line[0]):
#             continue
#         print(line)


# def win_enum_handler(hwnd, top_windows):
#     """
#         get all window append it to a list
#     """
#     top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))


# def printClasses(childHwnd, lparam):
#     print(win32gui.GetClassName(childHwnd), win32gui.GetWindowText(childHwnd))

def callback(hwnd, controls):
    controls.append(hwnd)


def check_bit_api(url):

    bwindow = win32gui.FindWindow(None, '比特浏览器')
    win32gui.ShowWindow(bwindow, 5)
    win32gui.SetForegroundWindow(bwindow)
    btnHnd= win32gui.FindWindowEx(bwindow, 0 , "Button", "")


    # HWND = win32gui.GetDlgItem(hDlg, )
    print(btnHnd)
    # controls = []
    # win32gui.EnumChildWindows(bwindow, callback, controls)
    # for control in controls:
    #     print(control)
    # win32gui.EnumChildWindows(bwindow, printClasses, None)
    # tid = win32gui.FindWindowEx(bwindow, 0, "Button", None)
    # print(tid)
    # win32gui.PostMessage(tid, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
    return url


def get_bit_url():
    url = "http://127.0.0.1:"
    # print(psutil.pids())
    for proc in psutil.process_iter():
        # print(proc.info)
        # print(proc.name())
        if proc.name() == '比特浏览器.exe':
            for x in proc.connections():
                if x.status == psutil.CONN_LISTEN:
                    url = url + str(x.laddr.port)
                    return check_bit_api(url)
    return None


# get_bit_url()

import os
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DB_PATH = os.path.join(CUR_DIR, "config.db")
print(CONFIG_DB_PATH)


import requests
from lxml import html
import random
RLIST = [",", "-"]

def get_xpath_ele(ele):
    return ele[0].replace(",","").strip() if ele else ""

USER_URL = "https://www.fakepersongenerator.com/"
# USER_URL = "https://www.shenfendaquan.com/"

proxy = {
    "http": "www-proxy.ericsson.se:8080"
}

etree = html.etree
res=requests.get(USER_URL)
# res=requests.get(USER_URL, proxies=proxy)

user_xpath = etree.HTML(res.text)

name = get_xpath_ele(user_xpath.xpath('//div[@class="basic-face"]//p[contains(@class, "name")]/b/text()'))
address = get_xpath_ele(user_xpath.xpath('//div[@class="basic-face"]//p[4]/b/text()'))
city = get_xpath_ele(user_xpath.xpath('//div[@class="basic-face"]//p[5]/b/a[1]/text()'))
state = get_xpath_ele(user_xpath.xpath('//div[@class="basic-face"]//p[5]/b/text()'))
post = get_xpath_ele(user_xpath.xpath('//div[@class="basic-face"]//p[5]/b/a[2]/text()'))
phone = get_xpath_ele(user_xpath.xpath('//div[@class="basic-face"]//p[6]/b/text()'))
mail = get_xpath_ele(user_xpath.xpath('//div[contains(@class,"row")]//div[2]/input/@value'))

# mlist = [
#     "@gmail.com",
#     "@outlook.com",
#     "@hotmail.com",
#     "@foxmail.com"
# ]
# name = get_xpath_ele(user_xpath.xpath('//div[@class="main-right"]//div[2]/div[2]/input/@value'))
# address = get_xpath_ele(user_xpath.xpath('//div[@class="main-right"]//div[6]/div[2]/input/@value'))
# city = get_xpath_ele(user_xpath.xpath('//div[@class="main-right"]//div[7]/div[2]/input/@value'))
# state = get_xpath_ele(user_xpath.xpath('//div[@class="main-right"]//div[8]/div[4]/input/@value'))
# post = get_xpath_ele(user_xpath.xpath('//div[@class="main-right"]//div[8]/div[2]/input/@value'))
# phone = get_xpath_ele(user_xpath.xpath('//div[@class="main-right"]//div[7]/div[4]/input/@value'))
# mail = name.replace(" ", ".").lower() + random.choice(mlist)

user = {
    "name": name,
    "address": address,
    "city": city,
    "state": state,
    "post": post,
    "phone": phone,
    "mail": mail,
}

print(user)