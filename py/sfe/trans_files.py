#!/usr/bin/python
# -*- coding: utf-8 -*-
# ============================
# @Author  : stone wu
# @Time    : 2018/7/19 16:32
# @File    : t2stl
# @Software: PyCharm
# ============================
import os
import shutil
import logging
import threading
from datetime import datetime

# import sys
# FREE_CAD_PATH = '/usr/lib/freecad/lib'
# sys.path.append(FREE_CAD_PATH)
# import FreeCAD
# import Part
# import Mesh
# from Tkinter import Tk


class TransFiles(object):
    _instance_lock = threading.Lock()
    DIRECTORY = "./logs/"
    LOG_NAME = str(datetime.now().strftime('%Y%m%d'))
    if not os.path.isdir(DIRECTORY):
        os.makedirs(DIRECTORY)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
        filename=DIRECTORY + LOG_NAME + ".log",
        filemode='a'
    )
    logger = logging.getLogger(__name__)
    cad_exchange_path = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(TransFiles, "_instance"):
            with TransFiles._instance_lock:
                if not hasattr(TransFiles, "_instance"):
                    TransFiles._instance = object.__new__(cls)
        return TransFiles._instance

    @classmethod
    def trans_file(cls, origin_file, new_file, partition):
        if cls.cad_exchange_path and new_file.endswith(".obj"):
            if cls.cad_exchange_path:
                os.system("%s -i %s -e %s" % (cls.cad_exchange_path, origin_file, new_file))
        # else:
        #     shape = Part.read(origin_file)
        #     mesh = Mesh.Mesh()
        #     mesh.addFacets(shape.tessellate(partition))
        #     # mesh.smooth()
        #     mesh.write(new_file)

    @classmethod
    def trans_files(cls, directory_path, trans_2_dir_path, file_type_str,
                    copy_type_str, partition, new_type, cad_exchange_path):
        cls.cad_exchange_path = cad_exchange_path
        # get all files base on directory
        file_list = os.walk(directory_path)
        dir_end_name = '2%s' % new_type.strip()
        file_type_list = file_type_str.split(";")
        copy_type_list = copy_type_str.split(";")

        for (dir_path, dir_list, file_names) in file_list:
            if file_names:
                for file_name in file_names:
                    file_path = os.path.join(dir_path, file_name)
                    if trans_2_dir_path:
                        t_path = dir_path.replace(directory_path, trans_2_dir_path)
                    else:
                        t_path = dir_path.replace(directory_path, directory_path + dir_end_name)

                    if not os.path.isdir(t_path):
                        os.makedirs(t_path)

                    short_name, extend_temp = os.path.splitext(file_name)
                    extend = extend_temp.lower()
                    # check if is trans file
                    for file_type in file_type_list:
                        if extend.endswith(file_type):
                            new_file = os.path.join(t_path, file_name.replace(extend_temp.strip("."), new_type))

                            if os.path.isfile(new_file):
                                continue

                            try:
                                cls.trans_file(file_path, new_file, partition)
                            except Exception as e:
                                cls.logger.error(e)
                                cls.logger.error("%s FILE ERROR: %s" % (extend_temp.upper(), file_path))

                    # check if is copy file
                    for copy_type in copy_type_list:
                        if extend.endswith(copy_type):
                            new_file = os.path.join(t_path, file_name)
                            shutil.copyfile(file_path, new_file)

        cls.logger.info("TRANSFER FINISH")
        return 0


if __name__ == '__main__':
    pass
