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
import yaml
import pyautogui


import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))

from airdrop.utils.utils import MouseTask


class AutoTask(MouseTask):
    def __init__(self) -> None:
        super().__init__()
        # self.logger = self.get_logger(self.get_log_name(__file__))
        self.cur_dir = self.get_cur_dir(__file__)
        self.conf = self.load_config(self.get_cur_path("auto.ini"), "auto")

    def perform_tasks(self, tasks):
        for task in tasks:
            if task.get("skip"):
                continue
            name = task.get("name")
            et = task.get("type")
            ets = task.get("ets")
            # print(self.log_dir)
            self.logger.info("started the task: %s" % name)
            if et:
                self.browser = task.get("chrome")
                cpath = self.get_chrome_path(self.browser)

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
    at = AutoTask()
    tasks_tmp = at.conf.get('tasks')
    # print(tasks_tmp)
    if tasks_tmp:
        tasks = tasks_tmp.split(';')
        for task in tasks:
            # print(at.get_tasks(task))
            at.perform_tasks(at.get_tasks(task))
