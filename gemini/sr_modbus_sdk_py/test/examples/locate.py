#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File: locate.py
# @Author: shiyixuan
# @Date: 2021/2/22
# @Describe: 在站点1重新定位，定位前提：AGV处于未定位状态

from src.sr_modbus_sdk import *

mb_server = SRModbusSdk()
mb_server.connect_tcp('192.168.71.212')

mb_server.cancel_locate_task()  # 取消定位
mb_server.station_locate(1)  # 在站点1开始定位
mb_server.wait_locate_task_finish()  # 等待定位完成
