#-*- coding:utf-8 -*-
'''
required lib:
pip install pyyaml

'''
import os
import yaml

from airdrop.utils.utils import MouseTask


class AutoTask(MouseTask):
    def __init__(self) -> None:
        self._log_name = __file__
        super().__init__()
        self.cur_dir = self.get_cur_dir(__file__)
        self.conf = self.load_config(self.get_cur_path("auto.ini"), "auto")

    def perform_mouse_tasks(self, tasks):
        for task in tasks:
            if task.get("skip"):
                continue
            name = task.get("name")
            ets = task.get("ets")
            # print(self.log_dir)
            self.browser = task.get("browser")
            self.logger.info("started  the task: %s" % name)
            if self.browser:
                self.cpath = self.get_browser_path()
                if not self.cpath:
                    self.logger.error("browser cannot be found in system, try next task!")
                    continue

            result = self.execute_mouse_task(ets)
            if not result:
                self.logger.error("execute task: %s failed, try next task!" % name)
                continue

            if self.browser:
                self.logger.info("closing  the tab...")
                self.execute_task_step({"o":7,"v":["ctrl","w"]})

            self.logger.info("finished the task: %s" % name)
        self.close_webbrowser()

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
            at.perform_mouse_tasks(at.get_tasks(task))
