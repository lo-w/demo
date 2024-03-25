#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   ticket.py
@Time    :   2023/07/13
@Author  :   renjun
'''
import os
import time
import pytz
import json
import logging
import requests
import configparser
from logging import handlers
from datetime import datetime
from http.cookies import SimpleCookie

CUR_DIR             = os.path.dirname(os.path.abspath(__file__))
LOG_DIR             = os.path.join(CUR_DIR, "./logs/")
LOG_NAME            = os.path.splitext(os.path.basename(__file__))[0]

def check_path(c_path):
    if not os.path.isdir(c_path):
        os.makedirs(c_path)

check_path(LOG_DIR)
log_handler = handlers.TimedRotatingFileHandler(filename=LOG_DIR + LOG_NAME, backupCount=5)
log_handler.suffix = "%Y%m%d"
formatter = logging.Formatter(
    '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    '%a, %d %b %Y %H:%M:%S'
)
log_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

def get_cookies(cookies_data):
    cookie = SimpleCookie()
    cookie.load(cookies_data)
    cookies = {}
    for key, morsel in cookie.items():
        cookies[key] = morsel.value
    return cookies

def get_tickets(cookies, headers, data, conf_defaults):
    tickets_url = "https://ericsson.lightning.force.com/aura?r=%s&ui-force-components-controllers-lists-listViewDataManager.ListViewDataManager.getItems=1&ui-force-components-controllers-lists-listViewManagerGrid.ListViewManagerGrid.getRecordLayoutComponent=1"
    data['message'] = conf_defaults.get('message')
    resp = requests.post(tickets_url % conf_defaults.get('rseed'), headers=headers, cookies=cookies, data=data)
    try:
        if resp.status_code != 200:
            return None
        res = resp.json()
    except: 
        logger.error("get tickets failed!")
        return None
    return res

def get_cases(resp):
    gvp = resp.get('context').get('globalValueProviders')
    cases = {}
    for gv in gvp:
        if gv.get('type') == "$Record":
            cases = gv.get('values').get('records')
    return cases

def get_case_own_count(cases, case_own):
    case_own_count = 0
    for r in cases.values():
        co = r.get('Case').get('record').get('fields').get('OC_TH_LIOwner__c').get('value')
        if co == case_own:
            case_own_count += 1
    return case_own_count

def assign_ticket(c, cookies, headers, data, conf_defaults):
    case_own = conf_defaults.get('case_owner')
    owner_id = conf_defaults.get('owner_id')
    update_url = "https://ericsson.lightning.force.com/aura?r=%s&ui-force-components-controllers-ownerChangeContent.OwnerChangeContent.performOwnerChange=1"
    field = c.get('Case').get('record').get('fields')
    cnumber = field.get('CaseNumber').get('value')
    case_id = field.get('Id').get('value')
    logger.info("assign ticket: %s to owner: %s" % (cnumber, case_own))
    message = {
      "actions": [
        {
          "id": "14150;a",
          "descriptor": "serviceComponent://ui.force.components.controllers.ownerChangeContent.OwnerChangeContentController/ACTION$performOwnerChange",
          "callingDescriptor": "UNKNOWN",
          "params": {
            "recordIds": [case_id],
            "newOwnerId": owner_id,
            "changeOwnerOptions": {
              "editableOptions": [{"label":"Send notification email","optionName":"SendEmail","isChecked":False,"isEditable":True,"isDisabled":False}],
              "nonEditableOptions": [
                {"label": "Notes and attachments","optionName": "TransferNotesAndAttachments","isChecked": True,"isEditable": False,"isDisabled": False},
                {"label": "Open activities","optionName": "TransferOpenActivities","isChecked": True,"isEditable": False,"isDisabled": False}
              ],
              "qualifiedApiName": "Case",
              "ownerFieldLabel": "Case Owner"
            },
            "doAccessCheck": False
          }
        }
      ]
    }
    data["message"] = json.dumps(message)
    resp = requests.post(update_url % conf_defaults.get('rseed'), headers=headers, cookies=cookies, data=data)
    logger.debug(resp.content)
    if resp.status_code == 200:
        logger.info("successfully assign ticket: %s" % cnumber)

def get_skip(flag, skip_list, skip_str):
    for s in skip_list:
        if s.strip().lower() in skip_str.lower():
            return not flag
    return flag

def try_assign_ticket(cases, cookies, headers, data, conf_defaults):
    assign_queue = conf_defaults.get('assign_queue')
    country_list = conf_defaults.get('country_list').split(',')
    exclude_vend = conf_defaults.get('exclude_vend').split(',')
    for c in cases.values():
        field = c.get('Case').get('record').get('fields')
        co = field.get('OC_TH_LIOwner__c').get('value')
        if co == assign_queue:
            ### skip vender
            caccount_name = field.get('Account').get('displayValue')
            if get_skip(False, exclude_vend, caccount_name):
                continue

            ### if have country list check if this case in the list else assign all
            ccountry = field.get('IL_Country__c').get('value')
            if get_skip(True, country_list, ccountry):
                continue

            assign_ticket(c, cookies, headers, data, conf_defaults)

def get_sleep(min_refresh, max_refresh):
    cur_time = datetime.now(pytz.timezone('Asia/Shanghai'))
    sleep_time = max_refresh
    skip = True
    if cur_time.weekday() != 5 and cur_time.weekday() != 6:
        if cur_time.hour > 6 and cur_time.hour < 18:
            sleep_time = min_refresh
            skip = False
    return sleep_time, skip

def get_configs(config):
    config.read(os.path.join(CUR_DIR, "ticket.ini"))
    conf_defaults = config.defaults()
    aura_context = conf_defaults.get('aura_context')
    aura_token = conf_defaults.get('aura_token')
    filter_name = json.loads(conf_defaults.get('message')).get('actions')[-1].get('params').get('filterName')

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept":"*/*",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept-Language":"en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Cache-Control":"no-cache",
        "Connection":"keep-alive",
        "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
        "Host":"ericsson.lightning.force.com",
        "Origin":'https://ericsson.lightning.force.com',
        "Pragma":"no-cache",
        "Referer":"https://ericsson.lightning.force.com/lightning/o/Case/list?filterName=%s" % filter_name,
        "Sec-Ch-Ua":'"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        "Sec-Ch-Ua-Mobile":"?0",
        "Sec-Ch-Ua-Platform":"Windows",
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-origin",
    }

    data = {
        "message": "",
        "aura.pageURI": "/lightning/o/Case/list?filterName=%s" % filter_name,
        "aura.context": aura_context,
        "aura.token": aura_token
    }
    return headers, data, conf_defaults

def main():
    config = configparser.ConfigParser()
    while True:
        logger.debug("reading configs from local")
        headers, data, conf_defaults = get_configs(config)
        max_refresh = float(conf_defaults.get('max_refresh')) * 60 * 60
        min_refresh = int(conf_defaults.get('min_refresh'))
        count_limit = int(conf_defaults.get('count_limit')) - 1
        case_own = conf_defaults.get('case_owner')
        cookies_data = conf_defaults.get('cookies_data')

        ### refresh cookies
        logger.debug("try to get tickets")
        cookies = get_cookies(cookies_data)
        # print(cookies)
        resp = get_tickets(cookies, headers, data, conf_defaults)
        if not resp:
            logger.error("session expired/get tickets failed you need to change all tokens")
            break

        ### get sleep time base on week days
        sleep_time, skip = get_sleep(min_refresh, max_refresh)
        time.sleep(sleep_time)
        if skip:
            continue

        logger.debug("get cases from response")
        cases = get_cases(resp)
        case_own_count = get_case_own_count(cases, case_own)
        if case_own_count > count_limit:
            logger.info("user cases %s exceed count limit %s" % (case_own_count, case_own_count))
            time.sleep(max_refresh)
            continue
        total_count = len(cases.values())
        logger.info("total cases: %s, owner count: %s" % (total_count, case_own_count))

        ### owner should take cases
        if total_count > case_own_count:
            ### we have ticket can be assigned
            logger.debug("try to assign tickets")
            try_assign_ticket(cases, cookies, headers, data, conf_defaults)

if __name__ == '__main__':
    main()
