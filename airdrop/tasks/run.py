#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   run.py
@Author  :   renjun

required lib:
pip install pytz
'''

import pytz
import threading
from datetime import datetime
# from zoneinfo import ZoneInfo
from airdrop.tasks.tasks import WebTask


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    def __init__(self):
        self.head = None
        self.size = 0
        self.node_count = 50
        self.logger = None

    def search(self, data):
        current = self.head
        profile_id = data.get('profile')
        schedule_task = data.get('schedule_task')
        task_name = data.get('task')
        sub_task_name = data.get('subtask')
        while current:
            current_id = current.data.get('profile')
            current_schedule = current.data.get('schedule_task')
            if schedule_task:
                current_task = current.data.get('task')
                current_sub_task = current.data.get('subtask')
                if profile_id == current_id and schedule_task == current_schedule and task_name == current_task and sub_task_name == current_sub_task:
                    return True
            else:
                if profile_id == current_id and schedule_task == current_schedule:
                    return True
            current = current.next
        return False

    def add(self, data):
        # search node
        if self.size > self.node_count:
            return

        if self.search(data):
            # node already exist 
            return

        new_node = Node(data)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            profile_start = data.get('start_time')
            current_start = current.data.get('start_time')

            if profile_start <= current_start:
                # new added profile start time less than current start time
                new_node.next = self.head
                self.head = new_node
            else:
                while current.next:
                    next_profile_start = current.next.data.get('start_time')
                    if next_profile_start > profile_start:
                        # current.next = new_node
                        new_node.next = current.next
                        break
                    current = current.next
                current.next = new_node
        self.size += 1

    def get(self):
        return self.head

    def delete(self):
        current = self.head
        if current:
            # profile_id = current.data.get('profile')
            # schedule_task = current.data.get('schedule_task')
            # task_name = current.data.get('task')
            # sub_task_name = current.data.get('subtask')
            self.head = current.next
            self.size -= 1
            current = current.next
            return True
        return False

    def log_list(self):
        current = self.head
        while current:
            self.logger.info(f"{current.data} ->")
            # print(current.data, end=f" -> \n")
            current = current.next


class RunTasks(WebTask):
    def __init__(self) -> None:
        self._log_name = __file__
        super().__init__()
        self.ll = LinkedList()
        self.ll.logger = self.logger

    def update_tasks_list(self):
        while True:
            if self.profile_running:
                self.sleep(60)
                continue

            self.logger.info(f"update_tasks_list start")

            # current UTC time
            cur_time, cur_date = self.get_cur_time_date()
            run_time = datetime.strptime(f"{cur_date} 00:15:00", "%Y-%m-%d %H:%M:%S").astimezone(pytz.utc)
            profile_sort_list = []

            if cur_time < run_time:
                self.logger.info(f"timezone not in started UTC time: {run_time}")
                self.sleep(60)
                continue

            # az_list = self.get_azs()
            # az_sort_list = []
            # for azi in az_list:
            #     az = azi.get('timezone')
            #     # az = "America/Denver"
            #     # convert current UTC time to timezone time & date
            #     cur_az_time = cur_time.astimezone(ZoneInfo(az))
            #     cur_az_date = cur_az_time.date()
            #     # get started time
            #     naive_time = datetime.strptime(f"{cur_az_date} 06:00:00", "%Y-%m-%d %H:%M:%S")
            #     utc_dt = pytz.timezone(az).localize(naive_time, is_dst=None).astimezone(pytz.utc)
            #     az_sort_list.append([az, utc_dt, cur_az_time])

            # sorted_list = sorted(az_sort_list, key=lambda x:x[1])
            # for azs in sorted_list:
            #     run_az = azs[0]
            #     run_time = azs[1]
            #     cur_az_time = azs[2]
            #     if cur_time < run_time:
            #         self.logger.info(f"timezone not in started UTC time: {run_time}, local time: {cur_az_time} az: {run_az}")
            #         continue

            # current az can be running && get current az profile list
            #   profiles = self.get_profiles_by_az(run_az)
            profiles = self.get_profiles()
            for profile in self.get_random_items(profiles):
                # check if profile already added in running tasks & validate profile is running if not get a ramdom time to run
                profile_id = profile.get('profile')

                az = profile.get('timezone')
                # cur_az_time = cur_time.astimezone(ZoneInfo(az))
                naive_time = datetime.strptime(f"{cur_date} 00:00:00", "%Y-%m-%d %H:%M:%S")
                utc_dt = pytz.timezone(az).localize(naive_time, is_dst=None).astimezone(pytz.utc)
                if cur_time < utc_dt:
                    self.logger.info(f"timezone not in started UTC time: {utc_dt}, profile: {profile_id}, az: {az}")
                    continue

                self.logger.debug(f"start to check profile: {profile_id}")
                # get succeed scheduled tasks
                schedule_tasks = self.schedule_tasks_by_profile(profile_id)
                self.logger.info(f"profile: {profile_id}, schedule count: {len(schedule_tasks)} schedule tasks: {schedule_tasks}")
                for sd_profile in schedule_tasks:
                    ### schedule tasks added in list
                    sd_profile.update({"normal_check": False})
                    sd_profile.update({"schedule_task": True})
                    if self.ll.search(sd_profile):
                        self.logger.info(f"schedule task already added in LinkedList: {sd_profile}")
                        continue

                    ### schedule tasks running or not
                    res = self.profile_records_check(sd_profile)
                    if not res:
                        # profile normal tasks already running today
                        continue

                    last_update_time_db = sd_profile.get('update_time')
                    # last_update_hour = last_update_time_db.strftime("%H:%M:%S")
                    # last_update_time = datetime.strptime(f"{last_update_time_db}", "%Y-%m-%d %H:%M:%S").astimezone(pytz.utc)
                    last_update_time = last_update_time_db.astimezone(pytz.utc)

                    # get schedule hours from input
                    schedule_hours = self.get_schedule_hours(sd_profile)
                    start_time = self.gen_start_time(last_update_time, hours=schedule_hours, minutes=self.get_round(2, 5, 0), seconds=self.get_round(0, 59, 0))
                    sd_profile.update({"start_time": start_time})
                    #print(sd_profile)
                    self.logger.info(f"add schedule task in profile_sort_list started: {sd_profile}")
                    # not sure why added too many the same schedule task in list try using dict?
                    # task = sd_profile.get('task')
                    # subtask = sd_profile.get('subtask')
                    profile_sort_list.append(sd_profile)
                    self.logger.debug(f"add schedule task in profile_sort_list finished: {sd_profile}")

                ### for normal tasks
                profile.update({"normal_check": True})
                profile.update({"schedule_task": False})
                if self.ll.search(profile):
                    # profile normal tasks already added to LinkedList
                    continue

                # check normal task running or not
                res = self.profile_records_check(profile, True)
                if not res:
                    # profile normal tasks already running today
                    continue

                start_time = self.gen_start_time(utc_dt, hours=self.get_round(0, 4, 0), minutes=self.get_round(0, 59, 0), seconds=self.get_round(0, 59, 0))
                profile.update({"start_time": start_time})
                profile_sort_list.append(profile)
                self.sleep(5)

            #print('3'*20)
            #print(profile_sort_list)
            if profile_sort_list:
                sorted_profile_list = sorted(profile_sort_list, key=lambda x:x.get('start_time'))
                self.logger.info(f"start add profile to LinkedList {len(sorted_profile_list)}...")
                for sort_profile in sorted_profile_list:
                    if self.ll.size > self.ll.node_count:
                        self.logger.info(f"too many profile added to LinkedList...")
                        break
                    self.ll.add(sort_profile)
                    self.sleep()
                self.logger.debug(f"add profile to LinkedList: {sorted_profile_list}")
                self.ll.log_list()
            # self.update_tasks = False
            self.sleep(300)

    def run(self):
        # get task from tasks list
        self.sleep(10)
        while True:
            # print("run--------------------")
            # self.logger.debug(f"run start")

            profile_node = self.ll.get()
            if profile_node:
                # self.init_pyautogui()
                profile = profile_node.data
                task_time = profile.get('start_time')
                normal_check = profile.get('normal_check')
                schedule_task = profile.get('schedule_task')
                cur_time = datetime.now(pytz.utc)
                if cur_time > task_time:
                    res = self.profile_records_check(profile, normal_check)
                    if not res:
                        self.ll.delete()
                        continue
                    # running task
                    self.logger.info(f"running profile:")
                    self.logger.info(profile)
                    ### two types normal/schedule task
                    self.profile_running = True
                    self.run_profile(profile, normal_check, schedule_task)
                    self.close_browser()
                    self.profile_running = False
                    self.ll.delete()
                    self.logger.info(f"print LinkedList in running func...")
                    self.ll.log_list()
            # print("run2--------------------")
            self.sleep(20)

    def run_tasks(self):
        # multi thread update & running tasks
        t1 = threading.Thread(target=self.update_tasks_list)
        t2 = threading.Thread(target=self.run)
        t1.start()
        t2.start()
        t1.join()
        t2.join()


def main():
    rt = RunTasks()
    rt.run_tasks()


if __name__ == '__main__':
    main()




