#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File: pause_continue_cancel_move.py
# @Author: shiyixuan
# @Date: 2021/1/28
# @Describe: 展示移动控制的暂停移动，继续移动，结束移动，例子说明：移动过程先暂停移动持续10s，然后后继续移动、继续移动持续5s、结束移动

from src.sr_modbus_sdk import *

mb_server = SRModbusSdk()
mb_server.connect_tcp('192.168.71.212')

print('Start task')
mb_server.move_to_station_no(1, 1)  # 移动到站点1，移动任务编号为1
print('Move to station 1')
mb_server.start_action_task_no(129, 5, 0, 1)  # 在这里等待5秒动作的作用是AGV向站点1移动5秒后暂停，动作任务编号为1
print('Waiting 5 s')
mb_server.wait_action_task_finish(1)  # 结束编号为1的动作任务
mb_server.pause_task()  # 暂停移动
print('Pause move')
mb_server.start_action_task_no(129, 10, 0, 2)  # 暂停等待10
print('Waiting 10 s')
mb_server.wait_action_task_finish(2)  # 等待编号为2的动作任务完成
mb_server.continue_task()  # 继续移动
print('Continue move')
mb_server.start_action_task_no(129, 5, 0, 3)  # 在这里等待5秒动作的作用是AGV继续移动5秒
print('Waiting 5 s')
mb_server.wait_action_task_finish(3)
mb_server.cancel_movement_task()  # 取消移动任务
print('Cancel move')
print('End')
