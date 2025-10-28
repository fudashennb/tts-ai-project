#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File: switch_map.py
# @Author: shiyixuan
# @Date: 2021/2/22
# @Describe: 切换地图
#            切换地图说明：1、当地图名字符串长度大于或等于2时，自动取需要设置地图名字符串的前两个字节，当地图名只有一个字符，可以直接设置地图。
#                       2、若存在多张地图字符串的前两个字节相同，则按照字符排序，取第一张地图。
#                       3、建议用此功能时将地图名都命名为纯ASCII字符形式。

from src.sr_modbus_sdk import *

mb_server = SRModbusSdk()
mb_server.connect_tcp('192.168.71.212')

mb_server.switch_map('12楼地图')  # 例1：需要将当前地图设置为:“12楼地图”，此处设置的值为:0x3132，即只根据“12”来切换地图

# mb_server.switch_map('55aa') # 例2：若存在两张地图名分别为:“55a”和“55aa”，当设置0x3535时，即只根据“55”来切换地图，按照字符排序，设置的当前地图为:“55a”。
