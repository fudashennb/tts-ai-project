#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File: move_without_turning.py
# @Author: shiyixuan
# @Date: 2021/2/07
# @Describe: 在不允许调头的场景中移动，条件：1、在不允许调头的的区域两边设置两个站点，如站点1、站点2
#                                     2、把站点1到站点2的路径e1设置为后退路径（或者把站点2到站点1的路径e2设置为后退路径）
#                                     3、向站点1和站点2路径上的某个位置移动

from src.sr_modbus_sdk import *

mb_server = SRModbusSdk()
mb_server.connect_tcp('192.168.71.212')

print('Start task')
mb_server.move_to_pose_no(0, 0, 0, 1)  # 向某个指定位置移动，这个位置坐标（x,y）需要在站点1和站点2之间路径上
print('End')
