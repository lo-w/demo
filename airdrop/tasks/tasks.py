#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   tasks.py
@Author  :   renjun

required lib:
pip install requests
pip install selenium
'''

import os
import json
import codecs
import psutil
import requests
import unicodedata

from datetime import datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

from airdrop.utils.utils import MouseTask, PostGressDB



profiles_select_sql     =   'SELECT * FROM profiles;'
task_sub_select_sql     =   '''
                            SELECT 
                                t.id        id,
                                t.name      name,
                                t.subtask   subtask,
                                t.times     times,
                                t.findby    findby,
                                t.findvalue findvalue,
                                t.operation operation,
                                i.task      task,
                                i.profile   profile,
                                i.val       val,
                                i.retry     retry,
                                i.fallback  fallback
                            FROM tasks t left join inputs i on t.id=i.task and (i.profile=%s or i.profile is null) where t."name"=%s order by t.id;
                            '''
tasks_select_sql        =   '''
                            SELECT 
                                t.id        id,
                                t.name      name,
                                t.subtask   subtask,
                                t.times     times,
                                t.findby    findby,
                                t.findvalue findvalue,
                                t.operation operation,
                                i.task      task,
                                i.profile   profile,
                                i.val       val,
                                i.retry     retry,
                                i.fallback  fallback
                            FROM tasks t left join inputs i on t.id=i.task where name=%s and subtask=%s order by t.id;
                            '''
wallet_steps_select_sql   = 'SELECT * FROM tasks t left join inputs i on t.id=i.task left join extensions e on t."name"=e."name" where e.id=%s and t.subtask=%s order by t.id;'

records_finish_by_task    = "UPDATE records set status=true  where profile=%s and task=%s and subtask is null;"
records_finish_by_subtask = "UPDATE records set status=true  where profile=%s and task=%s and subtask=%s;"
records_failed_by_task    = "UPDATE records set status=false where profile=%s and task=%s and subtask is null;"
records_failed_by_subtask = "UPDATE records set status=false where profile=%s and task=%s and subtask=%s;"



class ChromeBrowser(PostGressDB):
    def __init__(self) -> None:
        """
        chromedriver: https://googlechromelabs.github.io/chrome-for-testing/#stable
        """
        super().__init__()

    def check_browser(self):
        return True

    def open_browser(self):
        self.driver.get(self.open_page)
        return self.driver

    def close_browser(self):
        if self.driver:
            self.driver.quit()

    def check_get_proxy(self):
        return True

    def get_proxy(self):
        proxy = {
            "socks5": "192.168.1.9:10000"
        }
        return proxy

    def get_proxy_by_profile(self, profile_id):
        return "socks://192.168.1.13:10808"

    def run_profile(self, profile, normal_check=False, schedule_task=False):
        # profile.update({"task":"taker","schedule_task":True})
        self.profile_id = profile.get('profile')
        self.schedule_task = profile.get('schedule_task')
        # self.schedule_task = True
        res = self.profile_records_check(profile, normal_check)
        if not res:
            return
        self.get_tasks_extensions(profile, schedule_task)
        directory = profile.get('directory')
        # if self.profile_id != '0e0ced5774fe508072b34df1f972cae3':
        #    return
        self.logger.info(f"start  profile: {self.profile_id}")
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # self.chrome_options.add_argument('--no-sandbox')
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-first-run')
        self.chrome_options.add_argument('--no-default-browser-check')
        self.chrome_options.add_argument('--disable-gpu')
        # self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--hide-crash-restore-bubble')
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--ignore-ssl-errors')
        self.chrome_options.add_argument('--window-size=1200,1400')
        self.chrome_options.add_argument(f"--user-data-dir={os.path.join(self.user_data_dir, directory)}")
        # self.chrome_options.add_experimental_option("debuggerAddress", res['data']['http'])
        # self.driver = webdriver.Chrome(service=Service(executable_path=self.driver_path), options=self.chrome_options)
        # self.driver_path.replace("%s", "")
        self.driver = self.get_driver()
        res = self.open_browser()
        if not res:
            self.logger.error(f"open profile: {self.profile_id} failed...")
            return

        res = self.exe_profile()
        self.known_handles = []
        if not res:
            self.logger.error(f"running profile: {self.profile_id} failed...")

    def run_profiles(self):
        profiles = self.get_profiles()
        for profile in self.get_random_items(profiles):
            self.run_profile(profile)
            self.close_browser()


class BitBrowser(PostGressDB):
    def __init__(self) -> None:
        super().__init__()
        self.headers = {'Content-Type': 'application/json'}
        self.BIT_URL = "http://127.0.0.1:54345"
        self.driver_path = None

    def open_browser(self):    # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
        return requests.post(f"{self.BIT_URL}/browser/open", data=self.JSON_ID % self.profile_id, headers=self.headers).json()

    def close_browser(self):   # 关闭窗口
        requests.post(f"{self.BIT_URL}/browser/close", data=self.JSON_ID % self.profile_id, headers=self.headers).json()

    def get_bit_profiles(self):
        return requests.post(f"{self.BIT_URL}/browser/list", data=json.dumps({"page":0,"pageSize":10}), headers=self.headers).json()

    def get_bit_url(self):
        url = "http://127.0.0.1:"
        for proc in psutil.process_iter():
            if proc.name() == '比特浏览器.exe':
                for x in proc.connections():
                    if x.status == psutil.CONN_LISTEN:
                        url = url + str(x.laddr.port)
                        return url
        return None

    def check_browser(self):
        BIT_URL = self.get_bit_url()
        return BIT_URL or False

    def run_profile(self, profile, normal_check=False):
        self.profile_id = profile.get('id')
        res = self.profile_records_check(profile, normal_check)
        if not res:
            return
        # if self.profile_id != '580cd51c8ff835db4ccba5514a461d14':
        #     continue
        self.logger.info(f"start  profile: {self.profile_id}")
        # profile_path = profile.get('path')
        # profile_extensions = ",".join([os.path.join(profile_path,"Extensions", extension) for extension in extensions])
        # proxy = get_proxy_by_profile(profile_id)

        res = self.open_browser()
        if not res['success']:
            self.logger.error(f"open profile: {self.profile_id} failed...")
            ### need to update the DB status which profile is failed
            return

        self.chrome_options = Options()
        # position = self.get_position()
        # chrome_options.add_argument("--window-position=%s" % position)
        self.chrome_options.add_experimental_option("debuggerAddress", res['data']['http'])
        self.driver_path = res['data']['driver']

        # chrome_options.add_argument("--window-size=1280,720")
        # chrome_options.add_argument("--disable-component-update")
        # chrome_options.add_argument("--no-first-run")
        # chrome_options.add_argument("--no-default-browser-check")
        # chrome_options.add_argument("--password-store=basic")
        # chrome_options.add_argument("--user-data-dir=%s" % profile_path)
        # chrome_options.add_argument("--fingerprint-config=%s" % profile_path)
        # chrome_options.add_argument("--load-extension=%s" % profile_extensions)
        # chrome_options.add_argument("--proxy-server=%s" % proxy)
        # profile_driver = webdriver.Chrome(service=Service(executable_path=executable_path), options=chrome_options)
        self.driver = self.get_driver()
        res = self.exe_profile()
        if not res:
            return

    def run_profiles(self):
        profile_resp = self.get_bit_profiles()
        profiles = profile_resp.get('data').get('list')
        ### random select profile to execute
        for profile in self.get_random_items(profiles):
            self.run_profile(profile)


class Wallets(MouseTask, PostGressDB):
    ### https://stackoverflow.com/questions/76252205/runtime-callfunctionon-threw-exception-error-lavamoat-property-proxy-of-gl
    ### https://github.com/MetaMask/metamask-extension
    ### https://github.com/LavaMoat/LavaMoat/pull/360#issuecomment-1547726986
    ### https://pypi.org/project/auto-metamask/
    ### https://dev.to/ltmenezes/automated-dapps-scrapping-with-selenium-and-metamask-2ae9
    ### https://github.com/MetaMask/metamask-extension/issues/19018

    def __init__(self) -> None:
        super().__init__()

    def login_wallet_task(self, extension):
        ext_id = extension.get("id")
        self.logger.info(f"login to wallet: {ext_id}...")
        login_steps = self.sql_info(wallet_steps_select_sql, (ext_id, 'login'))
        return self.exe_steps(login_steps)

    def login_wallets(self):
        # if self.pf == "Linux":
        #     wall_handle = self.get_handle_res("MetaMask")
        # else:
        wall_handle = self.get_new_handle()
        self.logger.info(f"new wallet handle is: {wall_handle}")
        if not wall_handle:
            self.logger.error("get wallet handle failed...")
            return
        for extension in self.extensions:
            # if extension.get("id") != "dmkamcknogkgcdfhhbddcghachkejeap":
            #     continue
            res = self.login_wallet_task(extension)
            if not res:
                return
        ### close login tab then switch back to origin tab...
        self.driver.close()
        self.driver.switch_to.window(self.orig_handle)
        return True

    def reset_last_net(self, cur_net):
        if self.last_net == cur_net:
            return True
        self.last_net = cur_net
        return


class SeleniumTask(MouseTask):
    def __init__(self) -> None:
        super().__init__()
        self.driver      = None
        self.wait        = None
        self.action      = None
        self.ignored_exceptions=(NoSuchElementException, StaleElementReferenceException,)

    def get_driver(self):
        return webdriver.Chrome(service=Service(executable_path=self.driver_path), options=self.chrome_options)

    def get_wait(self, driver, wait_time):
        return WebDriverWait(driver, wait_time)

    def get_action(self, driver):
        return ActionChains(driver)

    def get_xpath_ele(self, ele):
        if ele:
            val = str(ele[0])
            if "(" in val:
                val = val.split("(")[0]
            for c in self.RLIST:
                val = val.replace(c, "")
            return unicodedata.normalize('NFKD', val).strip()
        return ""

    def wait_for_element(self, findby, findvalue, val, retry, eles=False, operation=None):
        self.logger.debug(f"wait_for_element findby: {findby}, findvalue: {findvalue}, retry: {retry}, operation: {operation}")
        for _ in range(retry):
            try:
                # if operation == "click":
                #     return self.wait.until(EC.element_to_be_clickable((findby, findvalue)))
                # return self.driver.find_elements(findby, findvalue) if eles else self.wait.until(EC.presence_of_element_located((findby, findvalue)))
                if not operation:
                    if eles:
                        res = self.driver.find_elements(findby, findvalue)
                    else:
                        res = self.wait.until(EC.element_to_be_clickable((findby, findvalue)))
                    return  res
                else:
                    WebDriverWait(self.driver, self.wait_time, ignored_exceptions=self.ignored_exceptions).until(EC.presence_of_element_located((findby, findvalue))).click()
                    return True
            except Exception as e:
                self.logger.debug(f"retry get value again: {findvalue}")
                self.logger.debug(f"error message: {e}")
                self.wait_input()
        if val != "skip":
            self.logger.error(f"cannot find the element with value: {findvalue}")
        return

    def element_click(self, ele):
        try:
            # self.logger.info(step.get('operation'))
            # self.exe_step(step)
            ele.click()
            self.wait_input()
        except Exception as e:
            ### to do check fall back task, if exist perform fall back task
            self.logger.error(e)
            self.wait_page_load()

    def save_page_to_local(self, file_name):
        with codecs.open(self.get_cur_path(file_name), "w", "utf-8") as hf:
            hf.write(self.driver.page_source)

    def get_handle(self, handle_title):
        self.logger.debug(f"try to get handle with title: {handle_title}")
        self.logger.debug(f"current known  handles: {self.known_handles}")
        self.logger.debug(f"current window handles: {self.driver.window_handles}")

        for handle in self.driver.window_handles:
            if handle in self.known_handles:
                continue
            self.wait_input()
            self.driver.switch_to.window(handle)
            try:
                cur_title = self.driver.title
            except:
                ### some handle get title failed, append this handle to known handle then continue to next handle to get the target handle
                self.logger.debug(f"failed switch handle: {handle_title}")
                self.known_handles.append(handle)
                continue

            self.logger.info(f"current handle: {handle}, title: {cur_title}")

            con = False
            for known_tile in self.known_titles:
                if known_tile in cur_title:
                    self.known_handles.append(handle)
                    con = True
                    break
            if con:
                continue

            if not handle_title and (cur_title not in self.known_titles):
                self.driver.close()
                self.driver.switch_to.window(self.task_handle)
            elif handle_title in cur_title:
                return handle

        return False if handle_title else True

    def get_handle_res(self, switch_handle):
        for _ in range(self.wait_handle):
            handle_res = self.get_handle(switch_handle)
            if handle_res:
                self.logger.info(f"succeed switch handle: {switch_handle}")
                return handle_res
            self.wait_input()
        return

    def get_new_handle(self):
        ### running task in new tab
        if self.task_handle:
            self.driver.switch_to.window(self.task_handle)
        self.driver.execute_script(f'''window.open("{self.new_url}", "_blank");''')
        self.wait_wallet()
        return self.get_handle_res(self.new_title)

    def handle_url(self, findvalue, **kwargs):
        for _ in range(self.r):
            try:
                self.driver.get(findvalue)
                # if not self.wait_for_element("xpath", "//head"):
                #     continue
                break
            except Exception as e:
                self.logger.error(f"failed to open url: {findvalue}...")
        self.logger.info(f"wait for a moment to let url: {findvalue} load...")
        self.wait_page_load()
        return True

    def handle_mouse(self, findby, findvalue, val, subtask, **kwargs):
        if findby == "replace":
            if not val and subtask == "login":
                val = self.wallet_pass
                findvalue = findvalue % val
        self.logger.debug(f"execute mouse task step: {findvalue}")
        return self.execute_task_step(json.loads(findvalue))

    def handle_sleep(self, findvalue, **kwargs):
        wait_time = self.get_random_from_range(self.split_str, findvalue)
        self.sleep(wait_time)
        return True

    def handle_close(self, **kwargs):
        return self.get_handle_res(None)

    def handle_scroll(self, findvalue, **kwargs):
        self.driver.execute_script(f'window.scrollBy(0, {findvalue})')
        return True


class WebTask(Wallets, SeleniumTask, ChromeBrowser):
    def __init__(self) -> None:
        self._log_name = __file__
        super().__init__()
        self.cur_dir = self.get_cur_dir(__file__)

    def get_user_by_profile(self, profile_id):
        # twitter & telegram & discord & metamask etc.
        pass

    def login_social(self):
        ### login to twitter & discord...
        return True

    def handle_task_elements(self, task_eles, fallback):
        # self.save_page_to_local("eles.html")
        self.logger.info(f"start  eles  task, eles count: {len(task_eles)}...")
        for task_ele in task_eles:
            self.element_click(task_ele)
            if fallback:
                res = self.handle_tasks(fallback, "fallback")
                if not res:
                    return
            self.wait_wallet()
        return True

    def handle_eles(self, findby, findvalue, val, retry, fallback, **kwargs):
        task_eles = self.wait_for_element(findby, findvalue, val, retry, eles=True)
        if not task_eles:
            self.logger.info("elements not found...")
            return True if val == "skip" else False
        return self.handle_task_elements(task_eles, fallback)

    def handle_presence(self, findby, findvalue, val, retry, operation, **kwargs):
        self.wait_input()
        # self.save_page_to_local("presence.html")
        return self.wait_for_element(findby, findvalue, val, retry, operation=operation)

    def handle_wallet(self, findby, findvalue, val, **kwargs):
        wallet_operation = findby
        wallet_id = findvalue
        wallet_val = val
        wallet_task_steps = self.sql_info(wallet_steps_select_sql, (wallet_id, wallet_operation))

        self.logger.info(f"wait for a moment to switch handle: {wallet_operation}...")
        handle_res = None
        if wallet_operation in self.wallet_operation_list:
            self.logger.debug(f"wallet_task_steps: {wallet_task_steps}...")
            switch_handle = wallet_task_steps[-1].get('val')
            self.wait_wallet()
            handle_res = self.get_handle_res(switch_handle)
            wallet_val = switch_handle

        elif wallet_operation == "switch":
            res = self.reset_last_net(wallet_val)
            if res:
                self.logger.info("wallet network already switched, no need to switch...")
                return True
            handle_res = self.get_new_handle()
            ### replace the val for switch
            switch_search  = wallet_task_steps[-1]['findvalue'] % (f"switch/{wallet_val}")
            wallet_task_steps[-1]['findvalue'] = switch_search
            ### input the switch chain value
            switch_task    = wallet_task_steps[-2]['findvalue'] % wallet_val
            wallet_task_steps[-2]['findvalue'] = switch_task

        if not handle_res:
            self.logger.error(f"failed switch to wallet: {wallet_val} handle...")
            return

        res = self.exe_steps(wallet_task_steps)

        if wallet_operation == "switch":
            self.driver.close()

        if not res:
            return

        if wallet_operation == "switchnet":
            self.reset_last_net(wallet_val)

        self.logger.info("wait for a moment let transaction finished then switch back to task tab...")
        self.wait_wallet()
        self.driver.switch_to.window(self.task_handle)
        return True

    def handle_tasks(self, findby, findvalue, **kwargs):
        task_sub_steps = self.sql_info(tasks_select_sql, (findvalue, findby))
        return self.handle_sub_tasks(findvalue, task_sub_steps)

    def handle_operation(self, operation, task_ele, subtask, val):
        match operation:
            case "click":
                self.element_click(task_ele)
            case "find":
                self.logger.info(f"ele finded with unsupported operation: {operation}")
            case "clear":
                task_ele.clear()
            case "input":
                if subtask == "login":
                    val = self.wallet_pass
                elif ';;' in val:
                    val = self.get_random_from_range(self.split_str, val)
                for v in str(val):
                    task_ele.send_keys(v)
                    self.sleep(self.INPUT_TIME)
                self.wait_input()
            case "select":
                for op in task_ele.find_elements(By.TAG_NAME, 'option'):
                    if val.lower() in op.text.lower():
                        op.click()
            case "action":
                self.action.move_to_element(task_ele).click().perform()
            case "iframe":
                self.driver.switch_to.frame(task_ele)
            case _:
                self.logger.error(f"running step:{self.profile_id} failed with unsupported operation: {operation}")
                return
        return True

    def exe_step(self, step):
        findby    = step.get('findby')
        findvalue = step.get('findvalue')
        val       = step.get('val')
        retry     = step.get('retry') or self.r
        operation = step.get('operation')
        subtask   = step.get('subtask')
        fallback  = step.get('fallback')

        self.logger.info(f"start  step: {findvalue}")

        if operation in ["url", "wallet", "mouse", "presence", "eles", "sleep", "close", "scroll", "tasks"]:
            res = self.handle_function(parameter=operation, findby=findby, findvalue=findvalue, val=val, retry=retry, operation=operation, subtask=subtask, fallback=fallback)
            if val == "skip":
                return True
            return res

        task_ele = self.wait_for_element(findby, findvalue, val, retry)

        if not task_ele:
            return True if val == "skip" else False

        try:
            res = self.handle_operation(operation, task_ele, subtask, val)
        except Exception as e:
            self.logger.error(e)
            return
        if fallback == "fall_close":
            res = self.handle_tasks(fallback, "fallback")
            if not res:
                return
        self.wait_input()
        self.logger.debug(f"finish step: {findvalue}")
        return res

    def exe_steps(self, steps):
        ### need to switch to tasks tab, already change it in wallet
        for step in steps:
            res = self.exe_step(step)
            if not res:
                ### handle fallback
                fallback = step.get('fallback')
                operation = step.get('operation')
                if operation != "eles" and fallback:
                    if str(step.get('name')) != "metamask":
                        self.driver.switch_to.window(self.task_handle)
                    res = self.handle_tasks(fallback, "fallback")
                    if not res:
                        self.logger.error(f"fallback task: {fallback} failed...")
                        return
                    continue

                self.logger.error(f"execute step: {step} failed...")
                return
        self.logger.info("all steps finished...")
        return True

    def handle_sub_oth_tasks(self, other_sub_exe_task, sub_task):
        ### get times list
        times_list = list({oset["times"] for oset in other_sub_exe_task})
        self.logger.info(f"get times list for sub task: {sub_task}, times list: {times_list}")

        for times in times_list:
            self.logger.info(f"get specific steps for specific sub task: {sub_task}, times: {times}")
            exe_times_list = [oset for oset in other_sub_exe_task if oset["times"] == times]
            for _ in range(times):
                res = self.exe_steps(exe_times_list)
                if not res:
                    return
        return True

    def handle_sub_tasks(self, task_name, task_list):
        self.logger.info(f"execute task: {task_name}, task: {task_list}")
        res = self.exe_steps(task_list)
        if not res:
            self.logger.error(f"failed execute task: {task_name}, task: {task_list}")
        return res

    def exe_sub_tasks(self, task_name):
        task_sub_steps = self.sql_info(task_sub_select_sql, (self.profile_id, task_name))
        self.logger.debug(f"exe_sub_tasks: {task_sub_steps}")

        pre_sub_task = []
        oth_sub_task = []
        end_sub_task = []
        for st in task_sub_steps:
            if st.get('times') == 0:
                pre_sub_task.append(st)
            elif st.get('times') == -1:
                end_sub_task.append(st)
            else:
                oth_sub_task.append(st)

        ### execute pre sub task
        res = self.handle_sub_tasks(task_name, pre_sub_task)
        if not res:
            return

        ### execute oth sub task, shuffle the sub task, random select one of it
        other_list = list({ost["subtask"] for ost in oth_sub_task})
        self.logger.info(f"task: {task_name} other taks list: {other_list}")
        sub_failed_count = 0
        for ost in self.get_random_items(other_list):
            res = self.check_task(task_name, ost)
            if not res:
                self.logger.info(f"profile: {self.profile_id}, task: {task_name}, subtask: {ost} failed, try next one")
                continue
            self.driver.switch_to.window(self.task_handle)
            self.logger.info(f"start  execute task: {task_name}, other task: {ost}")
            other_sub_exe_task = []

            for tss in task_sub_steps:
                if tss.get('subtask') == ost:
                    other_sub_exe_task.append(tss)

            self.logger.debug(f"other  task list: {other_sub_exe_task}")
            res = self.handle_sub_oth_tasks(other_sub_exe_task, ost)

            update_params = (self.profile_id, task_name, ost)
            if not res:
                sub_failed_count += 1
                self.update_records(records_failed_by_subtask, update_params)
                self.logger.error(f"failed execute task: {task_name}, other task: {ost}")
                continue

            self.update_records(records_finish_by_subtask, update_params)
            self.logger.info(f"finish execute task: {task_name}, other task: {ost}")

        total_task_count = len(other_list)
        ### execute end sub task
        if end_sub_task:
            total_task_count += 1
            ost = end_sub_task[0].get("subtask")
            res = self.check_task(task_name, ost)
            if not res:
                self.logger.info(f"profile: {self.profile_id}, task: {task_name}, subtask: {ost} failed, try next one")
            else:
                res = self.handle_sub_tasks(task_name, end_sub_task)
                update_params = (self.profile_id, task_name, ost)
                if not res:
                    sub_failed_count += 1
                    self.update_records(records_failed_by_subtask, update_params)
                    self.logger.error(f"failed execute task: {task_name}, other task: {ost}")
                else:
                    self.update_records(records_finish_by_subtask, update_params)

        return sub_failed_count < total_task_count

    def run_tasks_by_profile(self):
        ### shuffle the task
        for task in self.get_random_items(self.tasks):
            task_name = task.get('name')
            # if task_name not in ["nftfeed"]:
            #     continue

            # check if task is failed or already running
            res = self.check_task(task_name)
            if not res:
                self.logger.info(f"profile: {self.profile_id}, task: {task_name} check failed, try next task")
                continue

            self.logger.info(f"start  profile: {self.profile_id}, task: {task_name}")
            res = self.exe_sub_tasks(task_name)
            update_params = (self.profile_id, task_name)
            if not res:
                ### update DB
                self.update_records(records_failed_by_task, update_params)
                self.logger.error(f"profile: {self.profile_id}, task: {task_name} execute failed, try next task")
                continue

            ### update DB task finished.
            # if not self.schedule_task:
            self.update_records(records_finish_by_task, update_params)
            self.logger.info(f"finish profile: {self.profile_id}, task: {task_name}")

        self.logger.info(f"all tasks finished for profile: {self.profile_id}")
        self.driver.switch_to.window(self.task_handle)
        self.driver.close()

    def exe_profile(self):
        self.wait = self.get_wait(self.driver, self.wait_time)
        self.action = self.get_action(self.driver)

        self.orig_handle = self.driver.current_window_handle
        self.logger.debug(f"original window is: {self.orig_handle}")
        self.known_handles.append(self.orig_handle)

        profile_item = self.get_profile(self.profile_id)
        self.wallet_pass = profile_item.get('pass')

        # self.last_net = "zircuit"
        # self.last_net = "morph holesky"
        ### login to wallets first...
        log_wallet = self.login_wallets()
        if not log_wallet:
            self.logger.error("login wallet failed, try next profile...")
            return
        self.logger.info("login to wallets successfully...")

        ### login to social account(twitter & discord...)
        # log_social = login_social()
        # if not log_social:
        #     print("login social failed")
        #     continue

        ### create new tab for login & running tasks
        self.task_handle = self.get_new_handle()
        if not self.task_handle:
            self.logger.error("get  tasks handle failed, try next profile")
            return
        self.known_handles.append(self.task_handle)
        self.logger.info(f"new  tasks handle is: {self.task_handle}")

        ### normal task or schedule task
        self.run_tasks_by_profile()

        ### all task finished for current profile, close the browser
        self.logger.info(f"finish profile: {self.profile_id}")
        self.last_net = ""
        self.task_handle = ""
        # self.position.append(position)
        return True

    def start_web(self):
        self.run_profiles()

    def pre_check(self):
        return self.check_browser()

    def run_web_task(self):
        if not self.pre_check():
            raise Exception(f"web3 pre check failed")
        self.start_web()


def main():
    st = WebTask()
    st.run_web_task()
    # st.close_xvfb()


if __name__ == '__main__':
    main()
