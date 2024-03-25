#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   offer.py
@Time    :   2023/06/12
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
from lxml import html
from logging import handlers
from datetime import datetime
from multiprocessing.pool import ThreadPool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from flask import Flask, jsonify, make_response, request
# from flask_cors import CORS
# app = Flask(__name__)
# CORS(app, supports_credentials=True)


creds_table  =  """
                    CREATE TABLE IF NOT EXISTS creds(
                    cred_uuid CHAR(50) NOT NULL,
                    cred_num int NOT NULL,
                    year int(4) NOT NULL,
                    month int(2) NOT NULL,
                    cvv int(4) NOT NULL,
                    dt datetime DEFAULT current_timestamp);
                """

urls_table   =  """
                    CREATE TABLE IF NOT EXISTS urls(
                    url_uuid CHAR(50) NOT NULL,
                    url CHAR(50) NOT NULL,
                    type CHAR(10) DEFAULT 'offer',
                    dt datetime DEFAULT current_timestamp);
                """

tasks_table  =  """
                    CREATE TABLE IF NOT EXISTS tasks(
                    find_uuid CHAR(50) NOT NULL,
                    task_uuid CHAR(50) NOT NULL,
                    step int NOT NULL,
                    findby CHAR(10) DEFAULT 'xpath',
                    findvalue TEXT NOT NULL,
                    operation CHAR(10) DEFAULT NULL,
                    mapto CHAR(20) DEFAULT NULL);
                """

bits_table   =  """
                    CREATE TABLE IF NOT EXISTS bits(
                    bit_uuid CHAR(50) NOT NULL,
                    bit_user CHAR(50) NOT NULL,
                    bit_pass CHAR(50) NOT NULL,
                    dt datetime DEFAULT current_timestamp);
                """


### cred related sql
cred_sql         = "SELECT * FROM creds;"
cred_check_sql   = "SELECT * FROM creds  limit 1;"
cred_select_sql  = "SELECT * FROM creds  WHERE cred_num=?;"
cred_insert_sql  = "INSERT   INTO creds(cred_uuid,year,month,cvv,cred_num) VALUES(?,?,?,?,?);"
cred_update_sql  = "UPDATE  creds SET cred_uuid=?,year=?,month=?,cvv=?,dt=current_timestamp WHERE cred_num=?;"
cred_delete_sql  = "DELETE   FROM creds  WHERE cred_uuid=?;"
cred_delete_all  = "DELETE * FROM creds;"

### offer related sql
offer_sql        = "SELECT * FROM urls WHERE type='offer';"
offer_check_sql  = "SELECT * FROM urls type='offer' limit 1;"
offer_select_sql = "SELECT * FROM urls WHERE url_uuid=? and type='offer';"
offer_insert_sql = "INSERT   INTO urls(url,url_uuid) VALUES(?,?);"
offer_update_sql = "UPDATE   urls SET url=?,dt=current_timestamp WHERE url_uuid=?;"
offer_delete_sql = "DELETE   FROM urls WHERE url_uuid=?;"
offer_delete_all = "DELETE * FROM urls WHERE type='offer';"

users_sql        = "SELECT * FROM urls WHERE type='user';"
users_check_sql  = "SELECT * FROM urls type='user' limit 1;"
users_select_sql = "SELECT * FROM urls WHERE url_uuid=? and type='user';"
users_insert_sql = "INSERT   INTO urls(url,url_uuid,type) VALUES(?,?,'user');"
users_update_sql = "UPDATE   urls SET url=?,dt=current_timestamp WHERE url_uuid=?;"
users_delete_sql = "DELETE   FROM urls WHERE url_uuid=?;"
users_delete_all = "DELETE * FROM urls type='user';"

### task related sql
task_count_sql   = "SELECT   count(distinct step) c from tasks WHERE task_uuid=?;"
task_select_sql  = "SELECT * FROM tasks WHERE task_uuid=? and step=?;"
task_insert_sql  = "INSERT   INTO tasks(task_uuid,step,findby,findvalue,operation) VALUES(?,?,?,?,?);"
task_delete_sql  = "DELETE   FROM tasks WHERE find_uuid=?;"
task_delete_all  = "DELETE   FROM tasks WHERE task_uuid=?;"

### bit user related sql
bit_sql          = "SELECT * FROM bits;"
bit_insert_sql   = "INSERT   INTO users(user_uuid,user_name,user_pass) VALUES(?,?,?);"
bit_update_sql   = "UPDATE  users SET user_uuid=?,user_name=?,user_pass=?,dt=current_timestamp WHERE user_uuid=?;"
bit_delete_sql   = "DELETE   FROM users  WHERE user_uuid=?;"
bit_delete_all   = "DELETE * FROM users;"

### create related index
create_index     = "create index cred_uuid on creds (cred_uuid);"


headers          = {'Content-Type': 'application/json'}

BIT_URL          = "http://127.0.0.1:54345"
RLIST            = [",", "-"]
OFFER_URL        = ""
DRIVER_URL       = "https://chromedriver.storage.googleapis.com/"
DRIVER_VERSION   = "112.0.5615.49"
JSON_ID          = '{"id": "%s"}'
YEAR_PRE         = '20'
USER_PASS        = "]z6x!GGx!+nUvC]f"
WEB_PAGE_TIMEOUT = 60
INIT_FLAG        = False
OFFER_TEST       = False
INPUT_TIME       = 0.1
MINS             = 0.5
MAXS             = 2.0
WINDOWW          = 3
WINDOWH          = 1

CUR_DIR          = os.path.dirname(os.path.abspath(__file__))
CONFIG_DB_PATH   = os.path.join(CUR_DIR, "config.db")
DIRECTORY        = os.path.join(CUR_DIR, "./logs/")
LOG_NAME         = os.path.splitext(os.path.basename(__file__))[0]

def check_path(c_path):
    if not os.path.isdir(c_path):
        os.makedirs(c_path)

def check_not_exist(c_path):
    return not os.path.isfile(c_path)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

if check_not_exist(CONFIG_DB_PATH):
    check_path(os.path.dirname(CONFIG_DB_PATH))
    INIT_FLAG = True

conn = sqlite3.connect(CONFIG_DB_PATH, check_same_thread=False, isolation_level=None)
conn.row_factory = dict_factory
cur = conn.cursor()

if INIT_FLAG:
    cur.execute(urls_table)
    cur.execute(creds_table)
    cur.execute(tasks_table)
    cur.execute(bits_table)
    # cur.execute(create_index)

check_path(DIRECTORY)
log_handler = handlers.TimedRotatingFileHandler(filename=DIRECTORY + LOG_NAME + ".log", backupCount=5)
log_handler.suffix = "%Y%m%d"
formatter = logging.Formatter(
    '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    '%a, %d %b %Y %H:%M:%S'
)
log_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

def sql_info(sql, param=None, query=True):
    cur.execute(sql, param) if param else cur.execute(sql)
    return cur.fetchall() if query else cur.lastrowid

def read_from_local(read_path):
    """
    from a needed path read a file return it's content
    :param read_path:
    :return: yield line
    """
    if check_not_exist(read_path) or (not str(read_path).endswith("txt")):
        logger.error("file does not exists or unsupported file type.")
        return ""
    with codecs.open(read_path, "r", "utf-8") as r:
        for line in r:
            if line.strip():
                yield line.strip()

def load_cred(load_path):
    for line in read_from_local(load_path):
        cred_num,month,year,cvv,*_ = line.split("|")
        save_cred(cred_num,month,year,cvv)

def load_offer(load_path):
    for line in read_from_local(load_path):
        save_offer(line.strip())

def get_uuid(hstr):
    return hashlib.md5(hstr.strip().encode('utf-8')).hexdigest()

def save_cred(cred_num,month,year,cvv):
    load_uuid = get_uuid(cred_num+year+month)
    param = (load_uuid,year,month,cvv,cred_num)
    load_sql = cred_insert_sql
    if sql_info(cred_select_sql, (cred_num,)):
        load_sql = cred_update_sql
    logger.info("save/update %s: %s.", " cred", load_uuid)
    sql_info(load_sql, param, False)

def save_offer(offer_url):
    offer_url = offer_url.strip()
    load_uuid = get_uuid(offer_url)
    param = (offer_url, load_uuid)
    load_sql = offer_insert_sql
    if sql_info(offer_select_sql, (load_uuid,)):
        load_sql = offer_update_sql
    logger.info("save/update %s: %s.", "offer", load_uuid)
    sql_info(load_sql, param, False)

def save_task():
    task_id = '822f353a7d3048503d2a2bb333723d48'
    step = 4
    findby = 'xpath'
    findvalue = '//form[@id="cardDataForm"]//input[@id="cardexpiration"]'
    operation = 'input' # click/input/select
    mapto = None        # task value default None
    pass

def delete_task():
    find_uuid = ""
    sql_info(task_delete_sql, (find_uuid,))

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

def get_sleep(mi, mx):
    return random.uniform(mi, mx)

def proxy_exist():
    proxy = {
        "socks5": "192.168.1.9:7890"
    }
    return False

def get_xpath_ele(ele):
    if ele:
        val = ele[0]
        if "(" in val:
            val = val.split("(")[0]
        for c in RLIST:
            val = val.replace(c, "")
        return unicodedata.normalize('NFKD', val).strip()
    return ""

def get_user():
    user = {}
    user_urls = sql_info(users_sql)
    url = random.choice(user_urls)
    user_url = url.get("url")
    url_uuid = url.get("url_uuid")
    user_url = "https://www.fakepersongenerator.com/"
    url_uuid = "5122167f66a858e9872434bafaadd7f5"
    # user_url = "https://www.shenfendaquan.com/"
    # url_uuid = "96da9428960dfa2613826167c913a530"
    proxy = proxy_exist()

    if proxy:
        res=requests.get(user_url, proxies=proxy)
    else:
        res=requests.get(user_url)

    user_xpath = html.etree.HTML(res.text)
    task_count = sql_info(task_count_sql, (url_uuid,))[0].get('c')

    for i in range(1, task_count + 1):
        task_step_list = sql_info(task_select_sql, (url_uuid, i))
        for task in task_step_list:
            findvalue = task.get('findvalue')
            mapto = task.get('mapto')
            k = mapto.split(".")[-1]
            if findvalue:
                v = get_xpath_ele(user_xpath.xpath(findvalue))
            else:
                if "mail" in mapto:
                    mlist = ["@gmail.com", "@outlook.com", "@hotmail.com", "@foxmail.com"]
                    v = user.get("name").replace(" ", ".").lower() + random.choice(mlist)
                else:
                    continue
            user[k] = v
    user['pass'] = USER_PASS
    return user

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

def get_bit_url():
    url = "http://127.0.0.1:"
    for proc in psutil.process_iter():
        if proc.name() == '比特浏览器.exe':
            for x in proc.connections():
                if x.status == psutil.CONN_LISTEN:
                    url = url + str(x.laddr.port)
                    return url
    return None

def create_bit_browser(user, proxy):
    browser_uuid = str(uuid.uuid4())
    mw, mh = getMWH(platform.system())
    json_data = {
        'platform': '',  # 账号平台
        'platformIcon': '',  # 取账号平台的 hostname 或者设置为other
        'url': '',  # 打开的url，多个用,分开
        'name': browser_uuid,  # 窗口名称
        'remark': '',  # 备注
        'userName': '',  # 用户账号
        'password': '',  # 用户密码
        'cookie': '',  # Cookie，符合标准的序列化字符串，具体可参考文档
        # IP库，默认ip-api，选项 ip-api | ip123in | luminati，luminati为Luminati专用
        'ipCheckService': 'ip-api',
        'proxyMethod': 2,  # 代理方式 2自定义 3 提取IP
        # 代理类型  ['noproxy', 'http', 'https', 'socks5', '911s5']
        'proxyType': proxy.get("type"),
        'host': proxy.get("host"),  # 代理主机
        'port': proxy.get("port"),  # 代理端口
        'proxyUserName': '',  # 代理账号
        'proxyPassword': '',  # 代理密码
        'city': user.get("city"),  # 城市
        'province': user.get("state"),  # 州/省
        'country': proxy.get("country"),  # 国家地区
        'ip': proxy.get("ip"),  # ip
        'dynamicIpUrl': '',  # 提取IP url，参考文档
        'dynamicIpChannel': '',  # 提取IP服务商，参考文档
        'isDynamicIpChangeIp': True,  # 提取IP方式，参考文档
        'isGlobalProxyInfo': False,  # 提取IP设置，参考文档
        'isIpv6': False,  # 是否是IP6
        'syncTabs': False,  # 同步标签页
        'syncCookies': False,  # 同步Cookie
        'syncIndexedDb': False,  # 同步IndexedDB
        'syncLocalStorage': False,  # 同步 Local Storage
        'syncBookmarks': False,  # 同步书签
        'credentialsEnableService': True,  # 禁止保存密码弹窗
        'syncHistory': False,  # 保存历史记录
        'clearCacheFilesBeforeLaunch': True,  # 启动前清理缓存文件
        'clearCookiesBeforeLaunch': True,  # 启动前清理cookie
        'clearHistoriesBeforeLaunch': True,  # 启动前清理历史记录
        'randomFingerprint': True,  # 每次启动均随机指纹
        # 'workbench': 'chuhai2345',
        'disableGpu': False,  # 关闭GPU硬件加速 False取反 默认 开启
        'enableBackgroundMode': False,  # 关闭浏览器后继续运行应用
        'disableTranslatePopup': False,  # 翻译弹窗
        'syncExtensions': False,  # 同步扩展应用数据
        'syncUserExtensions': False,  # 跨窗口同步扩展应用
        'allowedSignin': False,  # 允许google账号登录浏览器
        'abortImage': False,  # 禁止加载图片
        'abortMedia': True,  # 禁止视频自动播放
        'muteAudio': True,  # 禁止播放声音
        'stopWhileNetError': True,  # 网络不通停止打开
        "browserFingerPrint": {  # 指纹对象
            'isIpCreateTimeZone': True,
            'isIpCreateLanguage': True,
            'isIpCreateDisplayLanguage': True, 
            'openWidth': mw//WINDOWW,     # 窗口宽度
            'openHeight': mh//WINDOWH,    # 窗口高度
            'windowSizeLimit': True,
            'coreVersion': DRIVER_VERSION.split('.')[0] # 内核版本 112 | 104，建议使用112，注意，win7/win8/winserver 2012 已经不支持112内核了，无法打开
        }
    }
    res = requests.post(f"{BIT_URL}/browser/update", data=json.dumps(json_data), headers=headers).json()
    browserId = res['data']['id']
    return browserId if browserId else None

def open_browser(id):    # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
    return requests.post(f"{BIT_URL}/browser/open", data=JSON_ID % id, headers=headers).json()

def close_browser(id):   # 关闭窗口
    requests.post(f"{BIT_URL}/browser/close", data=JSON_ID % id, headers=headers).json()

def delete_browser(id):  # 删除窗口
    requests.post(f"{BIT_URL}/browser/delete", data=JSON_ID % id, headers=headers).json()

def wait_for_element(driver, findby, findvalue, max_attempts=3):
    for _ in range(max_attempts):
        try:
            return driver.find_element(findby, findvalue)
        except Exception:
            logger.info("retry get value again: %s" % findvalue)
            time.sleep(get_sleep(MINS, MAXS))
    raise Exception(f"cannot find the element with value: %s" % findvalue)

def check_offer_cred():
    if sql_info(offer_check_sql) and sql_info(cred_check_sql):
        return True
    else:
        logger.error("offer/cred not exist need upload first")
        return False

def check_bit_browser():
    BIT_URL = get_bit_url()
    return True if BIT_URL else False

def check_get_user():
    return True

def check_get_proxy():
    return True

def start_offers(offers, cred, user, proxy):
    # browser_id = create_bit_browser(user, proxy)
    browser_id = "c75833941404406abd2d276c32d38b0f"
    if not browser_id:
        logger.error("failed start offer due to create bit browser failed")
        return

    logger.info("successfully created bit browser with id: %s" % browser_id)
    res = open_browser(browser_id)

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", res['data']['http'])
    # offer_driver = webdriver.Chrome(service=Service(ChromeDriverManager(version=DRIVER_VERSION,path=CUR_DIR,cache_valid_range=0).install()), options=chrome_options)
    offer_driver = webdriver.Chrome(service=Service(executable_path=f"{CUR_DIR}/chromedriver.exe"), options=chrome_options)
    offer_driver.set_page_load_timeout(WEB_PAGE_TIMEOUT)
    tasks = {}
    hc = 0
    # open offer in tabs
    for offer in offers:
        offer_uuid = offer.get('url_uuid')
        task_count = sql_info(task_count_sql, (offer_uuid,))[0].get('c')
        if task_count == 0:
            logger.info("no task for offer: %s" % offer_uuid)
            continue
        logger.info("open offer: %s" % offer_uuid)
        hc += 1
        offer_driver.execute_script('''window.open("%s", "%s");''' % (offer.get('url'), offer_uuid))
        offer_driver.switch_to.window(offer_driver.window_handles[hc])
        tasks[offer_uuid] = {"handle": offer_driver.current_window_handle, "tc": task_count}
        time.sleep(MAXS)

    # run offer tasks
    for offer_uuid in tasks.keys():
        task_count = tasks.get(offer_uuid).get('tc')
        offer_driver.switch_to.window(tasks.get(offer_uuid).get('handle'))
        logger.info("started offer: %s" % offer_uuid)
        for i in range(1, task_count + 1):
            task_step_list = sql_info(task_select_sql, (offer_uuid, i))
            for task in task_step_list:
                findby = task.get('findby')
                findvalue = task.get('findvalue')
                task_ele = wait_for_element(offer_driver, findby, findvalue)
                if not task_ele:
                    logger.error("running offer:%s failed with get element failed, %s" % (offer_uuid, findvalue))
                    return
                operation = task.get('operation')
                mapto = task.get('mapto')
                val = ""
                if mapto:
                    if "cred" in mapto:
                        val = str(cred.get(mapto.split('.')[-1])).strip()
                        val = YEAR_PRE + val if "YYYY" in mapto else val
                    elif "user" in mapto:
                        val = str(user.get(mapto.split('.')[-1])).strip()
                        if "first" in mapto:
                            val = val.split(' ')[0]
                        elif "last" in mapto:
                            val = val.split(' ')[-1]
                    else:
                        logger.error("running offer:%s failed, unsupported mapto value for input operation." % offer_uuid)
                        return
                if operation == 'click':
                    task_ele.click()
                elif operation == 'input':
                    for v in val:
                        task_ele.send_keys(v)
                        time.sleep(INPUT_TIME)
                elif operation == 'select':
                    for op in task_ele.find_elements(By.TAG_NAME, 'option'):
                        if val.lower() in op.text.lower():
                            op.click()
                else:
                    logger.error("running offer:%s failed with unsupported operation: %s" % (offer_uuid, operation))
                    return
                logger.info("finish task: %s" % findvalue)
                time.sleep(MINS)
            logger.info("finish task count: %s" % i)
            time.sleep(get_sleep(MINS, MAXS))
        offer_driver.close()
        logger.info("finish offer: %s" % offer_uuid)
        time.sleep(MAXS)
    close_browser(browser_id)
    # delete_browser(browser_id)

def check_offer(offer):
    offer_uuid = offer.get('url_uuid')
    res = sql_info(task_count_sql, (offer_uuid,))[0].get('c')
    if res > 0:
        return True
    else:
        logger.info("remove unsupported offer: %s, please add related task then try again" % offer_uuid)
        sql_info(offer_delete_sql, (offer_uuid,))
        return False

def get_offers():
    return sql_info(offer_sql)

def get_creds():
    return sql_info(cred_sql)


def start_task():
    TASK_NUM = 1
    creds = get_creds()
    # OFFER_URL = 'https://hotspotadds.g2afse.com/click?pid=1059&offer_id=939'
    # OFFER_TEST = True
    if OFFER_URL and OFFER_TEST:
        start_offers([{"url": OFFER_URL, "url_uuid": get_uuid(OFFER_URL)}], random.choice(creds), get_user(), get_proxy_by_user(user))
    else:
        offers = get_offers()
        while True:
            cred = random.choice(creds)
            user = get_user()
            print(user)
            if not user:
                logger.error("failed start offer due to failed get user")
                return

            proxy = get_proxy_by_user(user)
            if not proxy:
                logger.error("failed start offer due to failed get proxy")
                return

            if  TASK_NUM == 0:
                logger.info("change to another user start again")
                break

            if  TASK_NUM > 0:
                TASK_NUM -= 1
                start_offers(offers, cred, user, proxy)
            logger.info("this bit user left %s times" % TASK_NUM)

def pre_check():
    return check_offer_cred() and check_bit_browser() and check_get_user() and check_get_proxy()

def run_offer_task():
    if pre_check():
        logger.info("start running tasks")
        start_task()
    else:
        logger.error("pre check failed")

def main():
    # load_cred("./cred.txt")
    # load_offer("./offer.txt")
    # get_random_user()
    start_task()
    pass


if __name__ == '__main__':
    main()
    # app.run(host='0.0.0.0')