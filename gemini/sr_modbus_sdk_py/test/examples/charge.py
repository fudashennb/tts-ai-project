#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File: charge.py
# @Author: shiyixuan
# @Date: 2021/1/28
# @Describe: 移动到充电站点开始充电，达到指定电量后停止充电

from src.sr_modbus_sdk import *

mb_server = SRModbusSdk()
mb_server.connect_tcp('192.168.71.212')

print('Start task')
mb_server.move_to_station_no(3, 1)  # 移动到站点3,即充电准备站点，移动任务编号为1
print('Move to station 3')
mb_server.wait_movement_task_finish(1)  # 等待编号为1的移动任务执行结束
mb_server.move_to_station_no(4, 2)  # 移动到站点4,即充电站点，充电准备站点到充电站点的路径设置为后退路径
print('Move to charge station 4')
mb_server.wait_movement_task_finish(2)  # 等待编号为2的移动任务完成
mb_server.start_action_task_no(78, 11, 90)  # 开始充电，电量到达90%自动停止充电
print('Start charge')
