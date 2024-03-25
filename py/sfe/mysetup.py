#!/usr/bin/python
# -*- coding: utf-8 -*-
# ============================
# @Author  : stone wu
# @Time    : 2018/7/20 01:57
# @File    : mysetup
# @Software: PyCharm
# ============================

# import sys
# FREECADPATH = 'D:\\development\\python\\freecad\\FreeCAD 0.17\\lib'
# sys.path.append(FREECADPATH)
from py2exe.build_exe import py2exe
import sqlite3
import win32ui
import win32gui
import win32con
import win32com.client
import py2exe
# import FreeCAD
# import Part
# import Mesh
from distutils.core import setup

# console=["E:\\mat_web\\t2web.py"] 非静默运行  windows
setup(
    console=[
        {
            "script": "C:\\Users\\win7_mat\\Desktop\\sfe\\t2web.py",
            "icon_resources": [(1, u"icon.ico")]
        }
    ],
    options={
        'py2exe': {
            "dll_excludes": [
                "OLEAUT32.dll",
                "USER32.dll",
                "mfc90.dll",
                "SHELL32.dll",
                "ole32.dll",
                "COMDLG32.dll",
                "COMCTL32.dll",
                "ADVAPI32.dll",
                "GDI32.dll",
                "WS2_32.dll",
                "WINSPOOL.DRV",
                "CRYPT32.dll",
                "IMM32.dll",
                "VERSION.dll",
                "KERNEL32.dll",
                "NETAPI32.dll",
                "ntdll.dll",
                # "api-ms-win-core-rtlsupport-l1-2-0.dll", "api-ms-win-core-heap-l1-2-0.dll",
                # "api-ms-win-core-registry-l1-1-0.dll", "api-ms-win-core-errorhandling-l1-1-1.dll",
                # "api-ms-win-core-string-l2-1-0.dll", "api-ms-win-core-profile-l1-1-0.dll",
                # "api-ms-win-core-processthreads-l1-1-2.dll", "api-ms-win-core-libraryloader-l1-2-1.dll",
                # "api-ms-win-core-file-l1-2-1.dll", "api-ms-win-security-base-l1-2-0.dll",
                # "api-ms-win-eventing-provider-l1-1-0.dll", "api-ms-win-core-heap-l2-1-0.dll",
                # "api-ms-win-core-libraryloader-l1-2-0.dll", "api-ms-win-core-localization-l1-2-1.dll",
                # "api-ms-win-core-sysinfo-l1-2-1.dll", "api-ms-win-core-synch-l1-2-0.dll",
                # "api-ms-win-core-com-l1-1-1.dll", "api-ms-win-core-memory-l1-1-2.dll",
                # "api-ms-win-core-version-l1-1-1.dll", "api-ms-win-core-version-l1-1-0.dll",
                # "api-ms-win-core-handle-l1-1-0.dll", "api-ms-win-core-io-l1-1-1.dll", "api-ms-win*.dll",
                # "msvcp90.dll", "msvcm90.dll", "OLEAUT32.dll", "USER32.dll", "IMM32.dll", "SHELL32.dll",
                # "ole32.dll", "COMDLG32.dll", "WSOCK32.dll", "COMCTL32.dll",
                # "ADVAPI32.dll", "NETAPI32.dll", "msvcrt.dll", "WS2_32.dll",
                # "GDI32.dll", "VERSION.dll", "KERNEL32.dll", "ntdll.dll","WINSPOOL.DRV"
            ],
            "bundle_files": 3,
            "skip_archive": True
        }
    }
)
