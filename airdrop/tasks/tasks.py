#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   tasks.py
@Author  :   renjun
'''

import json
import codecs
import psutil
import requests
import unicodedata

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

from airdrop.utils.utils import InitConf, MouseTask, PostGressDB


profiles_select_sql     =  "SELECT * FROM profiles;"
task_sub_select_sql     =  '''
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
# task_sub_select_sql     = 'SELECT * FROM tasks t left join inputs i on t.id=i.task and (i.profile=%s or i.profile is null) where t."name"=%s order by t.id;'
tasks_select_sql        = 'SELECT * FROM tasks t where name=%s and subtask=%s order by t.id;'
wallet_steps_select_sql = 'SELECT * FROM tasks t left join inputs i on t.id=i.task left join extensions e on t."name"=e."name" where e.id=%s and t.subtask=%s order by t.id;'


class ChromeBrowser(InitConf):
    def __init__(self) -> None:
        super().__init__()

    def get_profiles(self):
        return [
            {
                "id": "8daa7a1341634a1db8bb2e3fd3aa8289",
                "path": "C:/Users/lo/AppData/Local/Google/Chrome/User Data/Profile 1"
            }
        ]


class BitBrowser(InitConf):
    def __init__(self) -> None:
        super().__init__()
        self.headers = {'Content-Type': 'application/json'}
        self.BIT_URL = "http://127.0.0.1:54345"

    def open_browser(self, id):    # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
        return requests.post(f"{self.BIT_URL}/browser/open", data=self.JSON_ID % id, headers=self.headers).json()

    def close_browser(self, id):   # 关闭窗口
        requests.post(f"{self.BIT_URL}/browser/close", data=self.JSON_ID % id, headers=self.headers).json()

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

    def check_bit_browser(self):
        BIT_URL = self.get_bit_url()
        return BIT_URL or False

    def pre_check(self):
        return self.check_bit_browser()


class Wallets( MouseTask, PostGressDB):
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
        self.logger.info("login to wallet: %s..." % ext_id)
        login_steps = self.sql_info(wallet_steps_select_sql, (ext_id, 'login'))
        return self.exe_steps(login_steps)

    def login_wallets(self, extensions):
        wall_handle = self.get_new_handle()
        self.logger.info("new wallet handle is: %s" % wall_handle)
        if not wall_handle:
            self.logger.error("get wallet handle failed...")
            return
        for extension in extensions:
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
        self.profile_id  = ""
        self.wallet_pass = ""
        self.orig_handle = ""
        self.task_handle = ""
        self.wall_handle = ""
        self.last_net    = ""
        self.know_handle = []
        self.know_titles = ["MetaMask","https://testnet.zulunetwork.io"]
        self.wallet_operation_list = ["confirm", "cancel", "switchnet", "signpay", "sign"]
        self.ignored_exceptions=(NoSuchElementException, StaleElementReferenceException,)

    def get_driver(self, executable_path, chrome_options):
        return webdriver.Chrome(service=Service(executable_path=executable_path), options=chrome_options)

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
        self.logger.debug("wait_for_element findby: %s, findvalue: %s, retry:%s, operation: %s" % (findby, findvalue, retry, operation))
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
                self.logger.debug("retry get value again: %s" % findvalue)
                self.logger.debug("error message: %s" % e)
                self.wait_input()
        if val != "skip":
            self.logger.error("cannot find the element with value: %s" % findvalue)
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

    def get_proxy_by_profile(self, profile_id):
        return "socks://192.168.1.13:10808"
    
    def save_page_to_local(self, file_name):
        with codecs.open(self.get_cur_path(file_name), "w", "utf-8") as hf:
            hf.write(self.driver.page_source)

    def get_handle(self, handle_title):
        self.logger.debug("try to get handle with title: %s" % handle_title)
        self.logger.debug("current known  handles: %s" % self.know_handle)
        self.logger.debug("current window handles: %s" % self.driver.window_handles)

        for handle in self.driver.window_handles:
            if handle in self.know_handle:
                continue
            self.wait_input()
            try:
                self.driver.switch_to.window(handle)
                cur_title = self.driver.title
                self.logger.debug("current handle: %s, title %s" % (handle, cur_title))
                if cur_title == handle_title or (not handle_title and cur_title not in self.know_titles):
                    return handle
            except:
                ### some handle get title failed, append this handle to known handle then continue to next handle to get the target handle
                self.logger.info("failed switch handle: %s" % handle_title)
                self.know_handle.append(handle)
                continue
        return False

    def get_handle_res(self, switch_handle):
        for _ in range(self.wait_handle):
            handle_res = self.get_handle(switch_handle)
            if handle_res:
                self.logger.info("succeed switch handle: %s" % switch_handle)
                return handle_res
            self.wait_input()
        return

    def get_new_handle(self):
        ### running task in new tab
        if self.task_handle:
            self.driver.switch_to.window(self.task_handle)
        self.driver.execute_script('''window.open("%s", "%s");''' % (self.new_url, '_blank'))
        self.wait_wallet()
        return self.get_handle_res(self.new_title)

    def handle_url(self, findvalue, **kwargs):
        for _ in range(self.r):
            try:
                self.driver.get(findvalue)
                break
            except Exception as e:
                self.logger.error("failed to open url: %s..." % findvalue)
        self.logger.info("wait for a moment to let url: %s load..." % findvalue)
        self.wait_page_load()
        return True

    def handle_mouse(self, findby, findvalue, val, subtask, **kwargs):
        if findby == "replace":
            if not val and subtask == "login":
                val = self.wallet_pass
                findvalue = findvalue % val
        self.logger.debug("execute mouse task step: %s" % findvalue)
        return self.execute_task_step(json.loads(findvalue))

    def handle_sleep(self, findvalue, **kwargs):
        wait_time = self.get_random_from_range(self.split_str, findvalue)
        self.sleep(wait_time)
        return True

    def handle_close(self, **kwargs):
        new_handle = self.get_handle_res(None)
        if not new_handle:
            return
        self.driver.close()
        self.driver.switch_to.window(self.task_handle)
        return True

    def handle_scroll(self, findvalue, **kwargs):
        self.driver.execute_script('window.scrollBy(0, %s)' % findvalue)
        return True


class WebTask(Wallets, SeleniumTask, BitBrowser):
    def __init__(self) -> None:
        super().__init__()
        self.cur_dir = self.get_cur_dir(__file__)

    def get_proxy_by_user(self, user):
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

    def check_get_proxy(self):
        return True

    def get_user_by_profile(self, profile_id):
        # twitter & telegram & discord & metamask etc.
        pass

    def get_proxy(self):
        proxy = {
            "socks5": "192.168.1.12:10808"
        }
        return proxy

    def login_social(self):
        ### login to twitter & discord...
        return True

    def handle_task_elements(self, task_eles, fallback):
        # self.save_page_to_local("eles.html")
        self.logger.info("start  eles  task, eles count: %s..." % len(task_eles))
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

        self.logger.info("wait for a moment to switch handle: %s..." % wallet_operation)
        handle_res = None
        if wallet_operation in self.wallet_operation_list:
            switch_handle = wallet_task_steps[-1].get('val')
            self.wait_wallet()
            handle_res = self.get_handle_res(switch_handle)

        elif wallet_operation == "switch":
            res = self.reset_last_net(wallet_val)
            if res:
                self.logger.info("wallet network already switched, no need to switch...")
                return True
            handle_res = self.get_new_handle()
            ### replace the val for switch
            switch_search  = wallet_task_steps[-1]['findvalue'] % ("switch/%s" % wallet_val)
            wallet_task_steps[-1]['findvalue'] = switch_search
            switch_task    = wallet_task_steps[-2]['findvalue'] % wallet_val
            wallet_task_steps[-2]['findvalue'] = switch_task

        if not handle_res:
            self.logger.error("failed switch to wallet: %s handle..." % wallet_val)
            return

        res = self.exe_steps(wallet_task_steps)
        if not res:
            return

        if wallet_operation == "switch":
            self.driver.close()
        elif wallet_operation == "switchnet":
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
                self.logger.error("running step:%s failed with unsupported operation: %s" % (self.profile_id, operation))
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

        self.logger.info("start  step: %s" % findvalue)

        if operation in ["url", "wallet", "mouse", "presence", "eles", "sleep", "close", "scroll", "tasks"]:
            res = self.handle_function(parameter=operation, findby=findby, findvalue=findvalue, val=val, retry=retry, operation=operation, subtask=subtask, fallback=fallback)
            ### handle fallback
            if not res and fallback:
                res = self.handle_tasks(fallback, "fallback")
                if res:
                    step.update({"fallback": None})
                    return self.exe_step(step)
            return res

        task_ele = self.wait_for_element(findby, findvalue, val, retry)

        if not task_ele:
            return True if val == "skip" else False

        res = self.handle_operation(operation, task_ele, subtask, val)
        if not res:
            return

        self.wait_input()
        self.logger.debug("finish step: %s" % findvalue)
        return True

    def exe_steps(self, steps):
        ### need to switch to tasks tab, already change it in wallet
        for step in steps:
            res = self.exe_step(step)
            if not res:
                self.logger.error("execute step: %s failed..." % step)
                return
        self.logger.info("all steps finished...")
        return True

    def handle_sub_oth_tasks(self, other_sub_exe_task, sub_task):
        ### get times list
        times_list = list({oset["times"] for oset in other_sub_exe_task})
        self.logger.info("get times list for sub task: %s, times list: %s" % (sub_task, times_list))

        for times in times_list:
            self.logger.info("get specific steps for specific sub task: %s, times: %s" % (sub_task, times))
            exe_times_list = [oset for oset in other_sub_exe_task if oset["times"] == times]
            for _ in range(times):
                res = self.exe_steps(exe_times_list)
                if not res:
                    return
        return True

    def handle_sub_tasks(self, task_name, task_list):
        self.logger.info("execute task: %s, task: %s" % (task_name, task_list))
        res = self.exe_steps(task_list)
        if not res:
            self.logger.error("failed execute task: %s, task: %s" % (task_name, task_list))
        return res

    def exe_sub_tasks(self, task_name):
        task_sub_steps = self.sql_info(task_sub_select_sql, (self.profile_id, task_name))
        self.logger.debug("exe_sub_tasks: %s" % task_sub_steps)

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
        self.handle_sub_tasks(task_name, pre_sub_task)

        ### execute oth sub task, shuffle the sub task, random select one of it
        other_list = list({ost["subtask"] for ost in oth_sub_task})
        self.logger.info("task: %s other taks list: %s" % (task_name, other_list))
        sub_failed_count = 0
        for ost in self.get_random_items(other_list):

            # if ost not in ["bridge"]:
            #     continue

            self.driver.switch_to.window(self.task_handle)
            self.logger.info("start  execute task: %s, other task: %s" % (task_name, ost))
            other_sub_exe_task = []

            for tss in task_sub_steps:
                if tss.get('subtask') == ost:
                    other_sub_exe_task.append(tss)

            self.logger.debug("other  task list: %s" % other_sub_exe_task)
            res = self.handle_sub_oth_tasks(other_sub_exe_task, ost)

            if not res:
                sub_failed_count += 1
                self.logger.error("failed execute task: %s, other task: %s" % (task_name, ost))
                continue

            self.logger.info("finish execute task: %s, other task: %s" % (task_name, ost))

        ### execute end sub task
        if end_sub_task:
            self.handle_sub_tasks(task_name, end_sub_task)

        return sub_failed_count != len(other_list)
        # return True

    def run_tasks_by_profile(self, tasks):
        ### shuffle the task
        for task in self.get_random_items(tasks):
            task_name = task.get('name')
            # if task_name not in ["morphl2"]:
            #     continue
            self.logger.info("start  profile: %s, task: %s" % (self.profile_id, task_name))
            res = self.exe_sub_tasks(task_name)
            if not res:
                self.logger.info("failed task: %s, try next one..." % task_name)
                ### update DB let other profile skip this failed task
                continue
            self.logger.info("finish profile: %s, task: %s" % (self.profile_id, task_name))

        self.logger.info("all tasks finished for profile: %s" % self.profile_id)
        self.driver.switch_to.window(self.task_handle)
        self.driver.close()

    def start_web(self):
        profile_resp = self.get_bit_profiles()
        profiles = profile_resp.get('data').get('list')
        # profiles = get_profiles()
        extensions = self.get_extensions()
        # executable_path = "C:/others/dev/py/chromedriver-win64/chromedriver.exe"

        ### get tasks
        tasks = self.get_tasks()
        self.logger.debug("successfully get tasks: %s" % tasks)

        ### random select profile to execute
        for profile in self.get_random_items(profiles):
            ### TODO using multi thread to running profile
            self.profile_id = profile.get('id')
            # if self.profile_id == '156665546fe14caf894d1f01565c862a':
            #     continue
            self.logger.info("start  profile: %s" % self.profile_id)
            # profile_path = profile.get('path')
            # profile_extensions = ",".join([os.path.join(profile_path,"Extensions",extension) for extension in extensions])
            # proxy = get_proxy_by_profile(profile_id)

            res = self.open_browser(self.profile_id)
            if not res['success']:
                self.logger.error("open profile: %s failed..." % self.profile_id)
                ### need to update the DB status which profile is failed
                continue
            chrome_options = Options()
            # position = self.get_position()
            # chrome_options.add_argument("--window-position=%s" % position)
            chrome_options.add_experimental_option("debuggerAddress", res['data']['http'])
            self.driver = self.get_driver(res['data']['driver'], chrome_options)

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

            self.wait = self.get_wait(self.driver, self.wait_time)
            self.action = self.get_action(self.driver)

            self.orig_handle = self.driver.current_window_handle
            self.logger.debug("original window is: %s" % self.orig_handle)
            self.know_handle.append(self.orig_handle)

            profile_item = self.get_profile()
            self.wallet_pass = profile_item.get('pass')

            # self.last_net = "zircuit"
            # self.last_net = "morph holesky"
            ### login to wallets first...
            log_wallet = self.login_wallets(extensions)
            if not log_wallet:
                self.logger.error("login wallet failed, try next profile...")
                continue
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
                continue
            self.know_handle.append(self.task_handle)
            self.logger.info("new  tasks handle is: %s" % self.task_handle)

            self.run_tasks_by_profile(tasks)

            ### all task finished for current profile, close the browser
            self.logger.info("finish profile: %s" % self.profile_id)
            self.last_net = ""
            self.task_handle = ""
            # self.position.append(position)
            self.close_browser(self.profile_id)

    def run_web_task(self):
        if not self.pre_check():
            raise Exception(f"web3 pre check failed")
        self.start_web()

def main():
    st = WebTask()
    st.run_web_task()
    # st.profile_id = "156665546fe14caf894d1f01565c862a"
    # print(st.get_profile())
    # print(st.get_extensions())
    # res = st.sql_info(input_select_sql,('8daa7a1341634a1db8bb2e3fd3aa8289', 6))
    # print(res)

if __name__ == '__main__':
    main()
