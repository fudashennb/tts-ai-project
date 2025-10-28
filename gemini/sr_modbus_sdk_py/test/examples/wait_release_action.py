#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File: wait_release_action.py
# @Author: shiyixuan
# @Date: 2021/1/27
# @Describe: 移动到站点2，在站点2执行等待放行，在AGV屏幕上确认放行，在这个例子中使用等待10秒放行


from src.sr_modbus_sdk import *

mb_server = SRModbusSdk()
mb_server.connect_tcp('192.168.71.212')

print('Start task')
mb_server.move_to_station_no(2, 2)  # 移动到站点2,移动任务编号为2
print('Move to station 2')
mb_server.wait_movement_task_finish(2)  # 等待编号为2的移动任务完成
mb_server.start_action_task_no(131, 0, 0, 1)  # 在站点2执行等待放行
print('Excute waiting command, Waiting for loading')
time.sleep(10)  # 等待10s
mb_server.release_action_id_131()  # 等待10s后执行放行命令，在生产场景中应该在AGV屏幕上点击确认货物放行
print('Excute release command')
mb_server.move_to_station_no(3, 3)  # 移动到站点3,移动任务编号为3
print('Move to station 3')
mb_server.wait_movement_task_finish(3)  # 等待编号为3的移动任务完成
print('End')
