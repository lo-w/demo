#!/usr/bin/python
# -*- coding: utf-8 -*-
# ============================
# @Author  : stone wu
# @Time    : 18-7-19 下午1:22
# @File    : t2web
# @Software: PyCharm
# ============================
import time
import win32ui
import win32con
import win32gui
import win32com.client

from flask import Flask, jsonify, make_response
from flask_cors import CORS
from multiprocessing.pool import ThreadPool


app = Flask(__name__)
CORS(app, supports_credentials=True)


def windowEnumerationHandler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))


def create_window(dlg):
    flag = dlg.DoModal()
    return flag, dlg


def pop_up(w_name):
    time.sleep(0.1)
    top_windows = []
    win32gui.EnumWindows(windowEnumerationHandler, top_windows)
    for i in top_windows:
        if w_name in i[1]:
            # print(i)
            # print("-"*50)
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')
            win32gui.ShowWindow(i[0], 5)
            win32gui.SetForegroundWindow(i[0])
            # print("+"*50)
            break

@app.route('/test', methods=['GET'])
def test():
    save_code = 1

    # open_flags = win32con.GMDI_GOINTOPOPUPS
    open_flags=win32con.OFN_OVERWRITEPROMPT
    filter_file = "Text File (*.txt)|*.txt|All Files (*.*)|*.*|"
    dlg = win32ui.CreateFileDialog(1, "", "test.txt", open_flags, filter_file)
    dlg.SetOFNInitialDir("C:")
    dlg.SetOFNTitle("save")

    pool = ThreadPool(processes=1)
    print("1"*40)
    async_result1 = pool.apply_async(create_window, (dlg, ))
    # async_result2 = pool.apply_async(pop_up, ("save",))
    print("2"*40)
    pop_up("save")
    print("3"*40)
    flag, dlg = async_result1.get()
    print("4"*40)
    # r = async_result2.get()
    # flag = dlg.DoModal()

    if flag == 1:
        path = dlg.GetPathName()
        save_code = 0
        print(path)

    v = {"code": save_code}
    return make_response(jsonify(v))


if __name__ == '__main__':
    app.run(host='0.0.0.0')


