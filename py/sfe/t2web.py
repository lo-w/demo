#!/usr/bin/python
# -*- coding: utf-8 -*-
# ============================
# @Author  : stone wu
# @Time    : 18-7-19 下午1:22
# @File    : t2web
# @Software: PyCharm
# ============================

import json
import time
import codecs
import sqlite3
import win32ui
import win32gui
import win32con
import win32com.client
import requests
from datetime import datetime
from trans_files import TransFiles, os
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
from multiprocessing.pool import ThreadPool
# import sys
# reload(sys)
# sys.setdefaultencoding('utf8')


app = Flask(__name__)
CORS(app, supports_credentials=True)

# save user project recent file
config_db_path = "./config/config.db"
config_dir = os.path.dirname(config_db_path)

# create a trans object
tf = TransFiles()

# file dialog related
f_title = "Find"
file_type = (("Json Files", "*.json"), ("All Files", "*.*"))
must_exists = win32con.OFN_FILEMUSTEXIST

# user info related
user_name_param = "userName"
d_dir_param = "sfeDefaultSavePath"
d_dir_c = "C:"
user_config_path = "./config/%s"
init_flag = False
# if os.path.isdir("//temp/"):
#     pass

config_db_table = """
                    CREATE TABLE config_db(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name CHAR(50) NOT NULL,
                    config_value CHAR(50) DEFAULT NULL);
                  """
user_db_table = """
                    CREATE TABLE user_db(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name CHAR(50) DEFAULT '',
                    recent_path CHAR(50) DEFAULT '',
                    sfe_path CHAR(50) DEFAULT '');
                """
insert_sql = """
                INSERT INTO config_db(config_name, config_value)
                VALUES
                    ('origin_type', 'igs;iges'),
                    ('target_type', 'obj'),
                    ('copy_type', 'info'),
                    ('partition', '0.1'),
                    ('default_end', '.json'),
                    ('cad_exchanger_path', '');
             """

config_sql = "SELECT config_value FROM config_db WHERE config_name=?;"
user_config_sql = "SELECT recent_path,sfe_path FROM user_db WHERE user_name=?;"
user_insert_sql = "INSERT INTO user_db(user_name) VALUES(?);"
sfe_update_sql = "UPDATE user_db SET sfe_path=? WHERE user_name=?;"
recent_update_sql = "UPDATE user_db SET recent_path=? WHERE user_name=?;"


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def check_path(c_path):
    if not os.path.isdir(c_path):
        os.makedirs(c_path)


if not os.path.isfile(config_db_path):
    check_path(config_dir)
    init_flag = True

conn = sqlite3.connect(config_db_path, check_same_thread=False)
conn.row_factory = dict_factory
cur = conn.cursor()

if init_flag:
    cur.execute(config_db_table)
    cur.execute(user_db_table)
    cur.execute(insert_sql)
    conn.commit()


def sql_info(sql, param=None, query=True):
    if param:
        cur.execute(sql, param)
    else:
        cur.execute(sql)

    if query:
        return cur.fetchall()
    else:
        conn.commit()
        return cur.lastrowid


def get_config_val(sql, param, c_key="config_value"):
    if isinstance(param, str):
        param = (param,)

    result = sql_info(sql, param)
    if result:
        return result[0].get(c_key)
    else:
        return None


def read_from_local(read_path):
    """
    from a needed path read a file return it's content
    :param read_path:
    :return: this file content
    """

    if not os.path.isfile(read_path):
        return ""

    with codecs.open(read_path, "r", "utf-8") as r:
        return r.read()


def write2local(save_path, content):
    """
    save content to target path
    :param save_path:
    :param content:
    :return: none
    """
    save_dir = os.path.dirname(save_path)
    check_path(save_dir)

    with codecs.open(save_path, "w", "utf-8") as w:
        w.write(content)


def get_save_code(file_fullname, item):
    """
        save user project to local
    """
    file_name = os.path.basename(file_fullname)
    short_name, _ = os.path.splitext(file_name)
    item['name'] = short_name
    content = json.dumps(item)
    write2local(file_fullname, content)
    return 0


def win_enum_handler(hwnd, top_windows):
    """
        get all window append it to a list
    """
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))


def create_window(dlg):
    """
        create a system file related dialog
    """
    flag = dlg.DoModal()
    return flag, dlg


def pop_up(w_name):
    """
        move file dialog on the top
    """
    time.sleep(0.1)
    top_windows = []
    win32gui.EnumWindows(win_enum_handler, top_windows)
    for i in top_windows:
        if w_name in i[1]:
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')
            win32gui.ShowWindow(i[0], 5)
            win32gui.SetForegroundWindow(i[0])
            break


def get_flag(open_num, open_name, open_dir, d_title,
             open_flags=win32con.OFN_OVERWRITEPROMPT,
             filter_file="Json File(*.json)|*.json|All Files (*.*)|*.*|"):
    dlg = win32ui.CreateFileDialog(open_num, "", open_name, open_flags, filter_file)
    dlg.SetOFNInitialDir(open_dir)
    dlg.SetOFNTitle(d_title)
    pool = ThreadPool(processes=1)
    async_result = pool.apply_async(create_window, (dlg, ))
    pop_up(d_title)
    flag, dlg = async_result.get()
    return flag, dlg


def get_user_name():
    """
    return user name from request
    :return:
    """
    user_name = None
    r_method = request.method.upper()

    if r_method == "POST":
        try:
            user_name = request.json.get(user_name_param)
        except Exception as te:
            tf.logger.error(te)

    elif r_method == "GET":
        user_name = request.args.get(user_name_param)
    else:
        tf.logger.error("get user name method not support")

    return user_name


def get_user_config(user_name, user_key):
    u_val = ""
    if user_name:
        u_result = sql_info(user_config_sql, (user_name,))
        if u_result:
            u_val = u_result[0].get(user_key)
        else:
            sql_info(user_insert_sql, (user_name,), False)
    return u_val


def get_default_dir(request_dir, base_dir):
    if request_dir and os.path.isdir(request_dir):
        return request_dir
    return base_dir


@app.route('/trans', methods=['POST'])
def trans():
    """
    read dir trans all Industry file to web load 3d file
    :return: 0 if success else 1
    """
    trans_status = 1

    # get need trans file type
    origin_type_str_temp = get_config_val(config_sql, 'origin_type')
    origin_type_str = origin_type_str_temp.strip(';') if origin_type_str_temp else 'igs'
    # get copy file type
    copy_type_str_temp = get_config_val(config_sql, 'copy_type')
    copy_type_str = copy_type_str_temp.strip(';') if copy_type_str_temp else None
    # web target 3d file type
    new_type_temp = get_config_val(config_sql, 'target_type')
    new_type = new_type_temp.strip() if new_type_temp else "obj"
    # model precision, the more big the more fuzzy
    partition_temp = get_config_val(config_sql, 'partition')
    partition = partition_temp if partition_temp else 1
    # get cad exchanger abs path
    cad_exchange_path_temp = get_config_val(config_sql, 'cad_exchanger_path')
    cad_exchange_path = cad_exchange_path_temp.strip() if cad_exchange_path_temp else None

    try:
        item = request.json
        start_path = item.get('start')
        end_path = item.get('end')
        if start_path and end_path and os.path.isdir(start_path):
            check_path(end_path)
            # trans file
            if cad_exchange_path:
                trans_status = tf.trans_files(start_path, end_path, origin_type_str,
                                              copy_type_str, partition, new_type, cad_exchange_path)
            else:
                tf.logger.info("no cad_exchange_path to trans files")
        else:
            tf.logger.error("trans path error")
    except Exception as te:
        tf.logger.error(te)
        tf.logger.error("trans params error")

    v = {"code": trans_status}
    return make_response(jsonify(v))


@app.route('/execute', methods=['POST'])
def execute():
    """
    execute a bat file and download needed config file
    :return: 0 if success else 1
    """
    try:
        item = request.json
        execute_path = item.get('executePath')
        download_url = item.get('downloadUrl')
        download_name = item.get('downloadName')
        # user_path = get_user_path()

        if os.path.isfile(execute_path):
            download_path = os.path.join(config_dir, "conf")
            save_path = os.path.join(download_path, download_name)
            if download_url:
                resp = requests.get(download_url)
                if resp.status_code == 200:
                    # write to download file
                    write2local(save_path, resp.content)
                    # tf.logger.info("e path: %s  ; c path: %s..." % (execute_path, save_path))
                    # execute bat file
                    os.system("%s -b %s" % (execute_path, save_path))
                    execute_status = 0
                else:
                    execute_status = 1
                    tf.logger.error("can not get download file")
            else:
                execute_status = 1
                tf.logger.error("download url error")
        else:
            execute_status = 1
            tf.logger.error("execute file error")
    except Exception as te:
        tf.logger.error(te)
        execute_status = 1

    v = {"code": execute_status}
    return make_response(jsonify(v))


@app.route('/scheme', methods=['GET', 'POST'])
def save_load():
    """
    save or load project depend on directory
    :return: 0 if success else 1
    """
    save_code = 1
    file_fullname = ""
    data = []
    user_name = get_user_name()
    if user_name:
        default_end_temp = get_config_val(config_sql, 'default_end')
        default_end = default_end_temp.strip() if default_end_temp else None
        default_name = "default%s" % default_end
        recent_file = get_user_config(user_name, "recent_path")

        r_method = request.method.upper()
        try:
            base_dir = os.path.dirname(recent_file)
            if not os.path.isdir(base_dir):
                base_dir = d_dir_c
            # open_num  0: save as; 1: open a file
            open_num = 1
            dialog_title = "Save"

            if r_method == "POST":
                item = request.json

                project_name_list = []
                data_time = str(datetime.now().strftime('%Y%m%d'))
                project_code = item.get('projectCode')
                # d_dir = item.get(d_dir_param)

                # m_time = datetime.now()
                # base_dir = get_default_dir(d_dir, base_dir)
                # e_time = datetime.now()
                # print("mid: %s" % (e_time - m_time))
                project_name_list.append(project_code)
                project_name_list.append(user_name)
                project_name_list.append(data_time)
                project_name_list.append("01")
                save_as = item.get('saveAs')

                if save_as:
                    project_name = default_name
                    open_num = 0
                    dialog_title = "Save As"
                else:
                    project_name = "%s%s" % ("_".join(project_name_list), default_end)

                file_fullname = recent_file if recent_file else os.path.join(base_dir, project_name)

                if os.path.isfile(file_fullname) and project_name != default_name \
                        and project_code in file_fullname \
                        and user_name in file_fullname:
                    save_code = get_save_code(file_fullname, item)
                else:
                    check_path(base_dir)
                    flag, dlg = get_flag(open_num, project_name, base_dir, d_title=dialog_title)

                    if flag == 1:
                        file_fullname = dlg.GetPathName()
                        save_code = get_save_code(file_fullname, item)
                        sql_info(recent_update_sql, (file_fullname, user_name), False)
                    else:
                        tf.logger.info("canceling...")

            elif r_method == "GET":
                # d_dir = request.args.get(d_dir_param)
                # base_dir = get_default_dir(d_dir, base_dir)

                flag, dlg = get_flag(open_num, default_name, base_dir, d_title=f_title, open_flags=must_exists)
                if flag == 1:
                    file_fullname = dlg.GetPathName()
                    item_str = read_from_local(file_fullname)
                    data.append(json.loads(item_str))
                    sql_info(recent_update_sql, (file_fullname, user_name), False)
                    save_code = 0
                else:
                    tf.logger.info("canceling...")
            else:
                tf.logger.error("not supported method")
        except Exception as te:
            tf.logger.error(te)

    v = {"code": save_code, "data": data, "file_name": file_fullname}
    return make_response(jsonify(v))


@app.route('/memberSfePath', methods=['POST'])
def get_sfe_path():
    save_code = 1
    path = ""

    user_name = get_user_name()
    if user_name:
        sfe_file = get_user_config(user_name, "sfe_path")

        if not os.path.isfile(sfe_file):
            base_dir = d_dir_c
        else:
            base_dir = os.path.dirname(sfe_file)

        flag, dlg = get_flag(1, "", base_dir,
                             d_title=f_title,
                             open_flags=must_exists,
                             filter_file="All Files (*.*)|*.*|")
        if flag == 1:
            path = dlg.GetPathName()
            sql_info(sfe_update_sql, (path, user_name), False)
            save_code = 0
        else:
            tf.logger.info("canceling...")

    v = {"code": save_code, "path": path}
    return make_response(jsonify(v))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
