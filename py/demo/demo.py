#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@Time    :   2023/10/17
@Author  :   renjun
'''

import os
import sqlite3
import threading
from flask import Flask, request, jsonify, make_response, render_template
from flask_cors import CORS

license_table       = """
                        CREATE TABLE IF  NOT EXISTS license(
                        product       CHAR(50) NOT NULL,
                        value_package CHAR(50) NOT NULL,
                        use_case      TEXT     DEFAULT NULL,
                        description   TEXT     DEFAULT NULL,
                        dt            datetime DEFAULT current_timestamp);
                    """

license_insert_sql      = "INSERT   INTO license(product,value_package,use_case,description) VALUES(?,?,?,?);"
product_select_sql      = "SELECT distinct product  FROM license;"
use_case_select_sql     = "SELECT distinct use_case FROM license where product=?;"
all_select_sql          = "SELECT * FROM license;"
license_select_sql      = "SELECT * FROM license    WHERE product=?;"
detail_by_prod_uc       = "SELECT * FROM license    WHERE product=? and use_case=?;"
detail_by_prod_uc_vp    = "SELECT * FROM license    WHERE product=? and use_case=? and value_package=?;"

init_sql = """
INSERT INTO license(product,value_package,use_case,description) VALUES
('EDA','2G 3G','HLR - FE, AUC - FE with CAI/CAI3G interface, Number Portability - FE,Administration of Multi-region,Administration of BSS Capacity,M2M support','The 2G 3G value package provides support for CUDB in the UDC solution, which includes not only MML/CAI/CAI3G interfaces of HLR-FE, AUC-FE, and MNP-FE provisioning, but also sharing of UDC HLR network infrastructure among different regions/countries/service  providers.'),\
('EDA','LTE EPC','LTE/SAE (4G) - HSS-FE','This value package provides provisioning support for layered deployments of the EPC in UDC.'),\
('EDA','5G EPC','IoT / 5G - HSS-FE','This Value Package includes support for Non-Standalone deployment of 5G, requires the LTE EPC Value Package.'),\
('EDA','Exposure','IoT / 5G - HSS-FE','This Value Package includes provisioning support for SCEF related features in HSS.'),\
('EDA','Shared Networks','IoT / 5G - HSS-FE','The Shared Networks Value Packages includes support for Dedicated Core Networks, the 3GPP feature DECOR, in Layered HSS. This Value Package requires the LTE EPC Value Package.'),\
('EDA','Subscriber Services','AAA - FE,EIR - FE , ILF/DSC','Subscriber Services value package provides off-the-shelf provisioning support towards CUDB for the front-ends IPWorks Authentication Authorization Accounting (AAA-FE) and Equipment Identity Register (EIR-FE) applications in Data Layered Architecture.Included in this Value Package is also off-the-shelf support for ILF/DSC.'),\
('EDA','Charging','Charging Solutions','This value package provides pre-verified provisioning solution for charging related solutions.'),\
('EDA','Billing & CBiO','BSCS and CBiO','The Billing & CBiO value package provides Off-the-shelf support of Billing & CBiO. CBiO Provisioning also requires Software Advanced and other Value Packages used in the CBiO solution, e.g. if there is an HLR included then 2G 3G Value Package is required.'),\
('EDA','IMS Core','IPWorks ENUM/ENUM-FE, HSS-FE','The IMS Core value package provides provisioning support for layered deployments of the IMS core and IMS applications. All included network elements are hidden behind the service, simplifying the provisioning of user data.'),\
('EO','Multimedia Telephony','MTAS, vMTAS, BCE, PGM','The Multimedia Telephony value package provides Off-the-shelf support of Ericsson MMTel.'),\
('EO','WiFi Calling','ECAS,IPWorks AAA (NDS),Classic HSS (Non-Sim Part)','The WiFi Calling value package provides Off-the-shelf support for Voice over WiFi. For non-SIM based devices.'),\
('EO','eSIM Calling','HLR,HSS,ENUM,MTAS (eSIM related data)','The Ericsson embedded SIM (eSIM) solution enables Voice over LTE (VoLTE) service on a secondary device using eSIM.The use of HLR, HSS, ENUM, and MTAS is limited to the use within LCM of eSIM subscriptions.'),\
('SAPC','Policy Control','SAPC','Policy Control value package provides off-the-shelf provisioning support towards the Service Aware Policy Controller.'),\
('SAPC','Multi Vendor Subscriber Services','Multi Vendor Subscriber Services','MVNE of network including wireline,wireless network, and applications, such as non-Ericsson 2G/3G, LTE, IMS, WiFi, FTTx, xDSL, non-Ericsson Policy Control,non-Ericsson messaging application, etc');
"""

app = Flask(__name__)
CORS(app, supports_credentials=True)

INIT_FLAG        = False
CUR_DIR          = os.path.dirname(os.path.abspath(__file__))
CONFIG_DB_PATH   = os.path.join(CUR_DIR, "config.db")
lock             = threading.Lock()

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
    cur.execute(license_table)
    cur.execute(init_sql)

def sql_info(sql, param=None, query=True):
    try:
        lock.acquire(True)
        cur.execute(sql, param) if param else cur.execute(sql)
    finally:
        lock.release()
    return cur.fetchall() if query else cur.lastrowid

def get_result(get_sql, param=None):
    res = sql_info(get_sql, param) if param else sql_info(get_sql)
    return make_response(jsonify(res))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/product', methods=['GET'])
def get_licenses_by_prod():
    prod_name = request.args["prod_name"]
    select_sql = license_select_sql
    param = (prod_name,)

    if prod_name == "":
        select_sql = product_select_sql
        param = None
    elif prod_name.lower() == "all":
        select_sql = all_select_sql
        param = None
    return get_result(select_sql, param)

@app.route('/usecase', methods=['GET'])
def get_use_case_by_prod():
    param = (request.args["prod_name"],)
    return get_result(use_case_select_sql, param)

@app.route('/vp', methods=['GET'])
def get_prod_detail():
    value_package = request.args["value_package"]
    if value_package:
        select_sql = detail_by_prod_uc_vp
        param = (request.args["prod_name"], request.args["use_case_name"], value_package)
    else:
        select_sql = detail_by_prod_uc
        param = (request.args["prod_name"], request.args["use_case_name"])
    return get_result(select_sql, param)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
