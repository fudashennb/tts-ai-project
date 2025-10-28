#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File: mb_unit_test.py
# @Author: shiyixuan
# @Date: 2021/1/20
# @Describe:


import unittest

from src.sr_modbus_sdk import *
from src.sr_modbus_model import *
import logging
import sys
import time

FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=FORMAT)

mb_server = SRModbusSdk()

mb_server.connect_tcp('10.10.69.35')  # modbus-TCP连接方式


# mb_server.connect_rtu('COM3')  # modbus-RTU连接方式


class UnitTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_trigger_emergency(self):
        """急停"""
        mb_server.trigger_emergency()

    def test_cancel_emergency(self):
        """取消急停"""
        mb_server.cancel_emergency()

    def test_start_manual_control(self):
        mb_server.start_manual_control()

    def test_stop_manual_control(self):
        mb_server.stop_manual_control()

    def test_set_volume(self):
        mb_server.set_volume(50)

    def test_locate(self):
        """
        移动到站点1重新定位
        :return:
        """
        mb_server.cancel_locate_task()  # 取消定位
        mb_server.station_locate(1)  # 在站点1开始定位
        mb_server.wait_locate_task_finish()

    def test_station_locate(self):
        """根据站点定位"""
        mb_server.station_locate(2)

    def test_get_cur_station_no(self):
        """获取当前站点"""
        print(mb_server.get_cur_station_no())
        self.assertEqual(mb_server.get_cur_station_no(), 3)

    def test_is_wait_release_action_id_131(self):
        """是否处于等待放行状态"""
        print(mb_server.is_wait_release_action_id_131())

    def test_release_action_id_131(self):
        """放行"""
        mb_server.release_action_id_131()

    def test_get_battery_info(self):
        """获取电池信息"""
        battery_info = mb_server.get_battery_info()
        print('电压：', battery_info.voltage, 'mV')
        print('电流：', battery_info.current, 'mA')
        print('温度：', battery_info.temperature, '°C')
        print('电池预计使用时间：', battery_info.remain_time, '分钟')
        print('电量百分比：', battery_info.percentage_electricity, '%')
        print('电池状态：', battery_info.state)
        print('电池循环次数：', battery_info.use_cycles, '次')
        print('电量：', battery_info.nominal_capacity, 'mAh')

    def test_is_emergency(self):
        """是否处于急停"""
        print('是否处于急停：', mb_server.is_trigger_emergency())

    def test_get_movement_task_info(self):
        """当前移动任务信息"""
        movement_task_info = mb_server.get_movement_task_info()
        print('移动状态：', movement_task_info.state)
        print('移动任务编号：', movement_task_info.no)
        print('目标站点：', movement_task_info.target_station)
        print('路径编号：', movement_task_info.path_no)
        print('结果：', movement_task_info.result)
        print('结果值：', movement_task_info.result_value)

    def test_get_action_task_info(self):
        """获取动作任务信息"""
        action_task_info = mb_server.get_action_task_info()
        print('动作状态：', action_task_info.state)
        print('动作任务编号：', action_task_info.no)
        print('任务id：', action_task_info.id)
        print('动作参数：', action_task_info.param0)
        print('动作参数：', action_task_info.param1)
        print('结果：', action_task_info.result)
        print('结果值：', action_task_info.result_value)

    def test_backward_movement(self):
        """手动控制移动,谨慎使用"""
        mb_server.start_manual_control()
        mb_server.manual_control(500, 0, 0)  # 向x轴方向移动100毫秒
        mb_server.start_action_task_no(129, 1, 0, 1)
        mb_server.wait_action_task_finish(1)
        mb_server.stop_manual_control()

    def test_get_mission_task_info(self):
        """获取mission任务信息"""
        mission_task_info = mb_server.get_mission_task_info()
        print(mission_task_info.mission_id)
        print(mission_task_info.mission_state)
        print(mission_task_info.mission_result)
        print(mission_task_info.mission_error_code)

    def test_pause_mission_task(self):
        """暂停mission任务"""
        mb_server.pause_mission_task()

    def test_continue_mission_task(self):
        """继续mission任务"""
        mb_server.continue_mission_task()

    def test_cancel_mission_task(self):
        """取消mission任务"""
        mb_server.cancel_mission_task()

    def test_set_DO0(self):
        """设置高、低电频"""
        mb_server.set_DO0(0)

    def test_set_DO1(self):
        mb_server.set_DO1(0)

    def test_set_DO2(self):
        mb_server.set_DO2(0)

    def test_set_DO3(self):
        mb_server.set_DO3(0)

    def test_set_DO4(self):
        mb_server.set_DO4(0)

    def test_set_DO5(self):
        mb_server.set_DO5(0)

    def test_set_DO6(self):
        mb_server.set_DO6(0)

    def test_set_DO7(self):
        mb_server.set_DO7(0)

    def test_get_DO_state(self):
        print(mb_server.get_DO_state())

    def test_move_to_station_no(self):
        """移动到站点2"""
        mb_server.move_to_station_no(2, 1)
        mb_server.wait_movement_task_finish(1)
        print('End')

    def test_move_with_goods(self):
        mb_server.move_to_station_no(19, 1)
        mb_server.wait_movement_task_finish(1)
        mb_server.start_action_task_no(4, 1, 0, 1)
        mb_server.wait_action_task_finish(1)
        mb_server.start_action_task_no(4, 13, 0, 2)  # 关闭同步旋转
        mb_server.wait_action_task_finish(2)
        mb_server.move_to_station_no(2, 2)
        mb_server.wait_movement_task_finish(2)
        mb_server.start_action_task_no(4, 12, 900, 3)
        mb_server.wait_action_task_finish(3)
        mb_server.start_action_task_no(4, 2, 0, 4)
        mb_server.wait_action_task_finish(4)
        mb_server.start_action_task_no(4, 12, 0, 5)
        mb_server.wait_action_task_finish(5)

    def test_switch_map(self):
        mb_server.switch_map('ldm')

    def test_get_cur_map_byte_code(self):
        print(mb_server.get_cur_map_byte_code())

    def test_move_to_pose_no(self):
        mb_server.move_to_pose_no(137, 281, 1570, 2)
        mb_server.wait_movement_task_finish(2)

    def test_get_cur_pose(self):
        pose = mb_server.get_cur_pose()
        print(pose.x, pose.y, pose.yaw)


if __name__ == '__main__':
    unittest.main()
