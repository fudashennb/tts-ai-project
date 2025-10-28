#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File: two_stations_move.py
# @Author: shiyixuan
# @Date: 2021/1/28
# @Describe: 在两个站点间来回移动10次，并在到达每个站点后等待5s

from src.sr_modbus_sdk import SRModbusSdk

mb_server = SRModbusSdk()
mb_server.connect_tcp('10.10.71.58')

print('Start task')
for i in range(10):
    print('{} times'.format(i))
    mb_server.move_to_station_no(1, 1)  # 向站点1移动，移动任务编号为1
    print('Move to station 1')
    mb_server.wait_movement_task_finish(1)  # 等待编号为1的移动任务完成
    mb_server.start_action_task_no(4, 11, 50, 1)  # 等待5秒，动作任务编号为1
    print('Waiting 5 s')
    mb_server.wait_action_task_finish(1)  # 等待编号为1的动作任务完成
    mb_server.move_to_station_no(2, 2)  # 向站点2移动，移动任务编号为2
    print('Move to station 2')
    mb_server.wait_movement_task_finish(2)  # 等待编号为2的移动任务完成
    mb_server.start_action_task_no(4, 11, 0, 2)  # 等待5秒，动作任务编号为2
    print('Waiting 5 s')
    mb_server.wait_action_task_finish(2)  # 等待编号为2的动作任务完成
print('End')
