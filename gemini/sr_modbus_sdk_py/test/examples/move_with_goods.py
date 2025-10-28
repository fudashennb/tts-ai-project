#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File: move_with_goods.py
# @Author: shiyixuan
# @Date: 2021/1/28
# @Describe: 空车移动到装货站点，扫码举升货架，载着货架移动到卸货点，放下货架


from src.sr_modbus_sdk import *

mb_server = SRModbusSdk()
mb_server.connect_tcp('192.168.71.193')

print('Start')
mb_server.move_to_station_no(2, 1)  # 移动到站点2，移动任务编号为1
print('Move to station 2')
mb_server.wait_movement_task_finish(1)  # 等待编号为1的移动任务结束，即移动到站点2
mb_server.start_action_task_no(4, 1, 0, 1)  # 扫码举升货架，动作任务编号为1
print('Excute raise')
mb_server.wait_action_task_finish(1)  # 等待编号为1的动作任务完成，即举升货架
mb_server.move_to_station_no(19, 2)  # 移动到站点19，任务编号为2
mb_server.wait_movement_task_finish(2)  # 等待编号为2的移动任务完成，即移动到站点19
mb_server.start_action_task_no(4, 12, 900, 2)  # 旋转货架至相对AGV方向90度，任务编号为3
mb_server.wait_action_task_finish(2)  # 等待任务编号为3的动作任务完成
mb_server.start_action_task_no(4, 2, 0, 3)  # 放下货架，任务编号为4
mb_server.wait_action_task_finish(3)  # 等待编号为4的动作任务完成，即放下货架
mb_server.start_action_task_no(4, 12, 0, 5)  # 旋转货架顶板至相对AGV方向0度
mb_server.wait_action_task_finish(5)  # 等待编号为5的动作任务完成
mb_server.move_to_station_no(2, 3)  # 移动到站点2，移动任务编号为3
mb_server.wait_movement_task_finish(3)  # 等待编号为3的移动任务完成
print('End')
