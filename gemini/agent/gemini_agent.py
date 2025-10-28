import os
import sys
import json
import logging
from pathlib import Path
from google import genai
from google.genai import types
from typing import Any

# 添加项目根目录到 Python 路径，以便导入 log_config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入统一的日志配置
import log_config

# 导入本地模块
from .modbus_ai_cmd import ModbusAICmd
from .config import PROMPT, GEMINI_API_KEY, GEMINI_MODEL

# 获取日志记录器（使用统一的日志系统）
logger = logging.getLogger(__name__)

class GeminiAgent:
    def __init__(self):
        """初始化 Gemini Agent
        
        从 config.py 读取配置：
        - GEMINI_API_KEY: Gemini API 密钥
        - GEMINI_MODEL: 使用的模型名称
        - PROMPT: AI 系统提示词
        """
        self.prompt = PROMPT
        self.modbus_ai_cmd = ModbusAICmd()
        
        # 验证 API Key
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY 未设置！请在 config.py 或环境变量中配置")
        
        # 使用配置文件中的 API Key 和模型
        logger.info(f"初始化 Gemini Agent，使用模型: {GEMINI_MODEL}")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMINI_MODEL
        
        # 基础功能函数声明
        mv_to_station = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.mv_to_station, client=self.client)
        execute_action = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.execute_action, client=self.client)
        terminate_chat = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.terminate_chat, client=self.client)
        get_battery_info = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_battery_info, client=self.client)

        # AGV基本信息相关函数声明
        get_agv_access_time = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_agv_access_time, client=self.client)
        get_agv_device_info = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_agv_device_info, client=self.client)
        get_agv_statistics = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_agv_statistics, client=self.client)
        get_agv_current_location = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_agv_current_location, client=self.client)
        get_agv_area_statistics = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_agv_area_statistics, client=self.client)

        # AGV任务和性能相关函数声明
        get_agv_task_status = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_agv_task_status, client=self.client)
        get_agv_weekly_trends = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_agv_weekly_trends, client=self.client)
        get_agv_performance = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_agv_performance, client=self.client)
        get_today_task_statistics = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_today_task_statistics, client=self.client)
        get_yesterday_performance = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_yesterday_performance, client=self.client)

        # 区域性能相关函数声明
        get_weekly_area_performance = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_weekly_area_performance, client=self.client)
        get_weekly_factory_trends = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_weekly_factory_trends, client=self.client)
        get_weekly_warehouse_trends = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_weekly_warehouse_trends, client=self.client)
        get_weekly_efficiency_trends = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_weekly_efficiency_trends, client=self.client)

        # 电池相关函数声明
        get_battery_temperature_warnings = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_battery_temperature_warnings, client=self.client)
        get_battery_usage_info = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_battery_usage_info, client=self.client)
        get_today_charging_statistics = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_today_charging_statistics, client=self.client)

        # 故障相关函数声明
        get_today_failure_statistics = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_today_failure_statistics, client=self.client)

        # 工单相关函数声明
        get_today_work_orders = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_today_work_orders, client=self.client)
        get_monthly_work_order_types = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_monthly_work_order_types, client=self.client)
        get_monthly_work_order_trends = types.FunctionDeclaration.from_callable(
            callable=self.modbus_ai_cmd.get_monthly_work_order_trends, client=self.client)

        # 配置所有函数声明
        self.config = types.GenerateContentConfig(
            tools=[
                # 基础功能
                types.Tool(function_declarations=[mv_to_station]),
                types.Tool(function_declarations=[execute_action]),
                types.Tool(function_declarations=[get_battery_info]),
                types.Tool(function_declarations=[terminate_chat]),
                
                # AGV基本信息
                types.Tool(function_declarations=[get_agv_access_time]),
                types.Tool(function_declarations=[get_agv_device_info]),
                types.Tool(function_declarations=[get_agv_statistics]),
                types.Tool(function_declarations=[get_agv_current_location]),
                types.Tool(function_declarations=[get_agv_area_statistics]),
                
                # AGV任务和性能
                types.Tool(function_declarations=[get_agv_task_status]),
                types.Tool(function_declarations=[get_agv_weekly_trends]),
                types.Tool(function_declarations=[get_agv_performance]),
                types.Tool(function_declarations=[get_today_task_statistics]),
                types.Tool(function_declarations=[get_yesterday_performance]),
                
                # 区域性能
                types.Tool(function_declarations=[get_weekly_area_performance]),
                types.Tool(function_declarations=[get_weekly_factory_trends]),
                types.Tool(function_declarations=[get_weekly_warehouse_trends]),
                types.Tool(function_declarations=[get_weekly_efficiency_trends]),
                
                # 电池相关
                types.Tool(function_declarations=[get_battery_temperature_warnings]),
                types.Tool(function_declarations=[get_battery_usage_info]),
                types.Tool(function_declarations=[get_today_charging_statistics]),
                
                # 故障相关
                types.Tool(function_declarations=[get_today_failure_statistics]),
                
                # 工单相关
                types.Tool(function_declarations=[get_today_work_orders]),
                types.Tool(function_declarations=[get_monthly_work_order_types]),
                types.Tool(function_declarations=[get_monthly_work_order_trends])
            ],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True)
        )
        
        # 创建聊天会话（使用配置的模型）
        self.chat = self.client.chats.create(model=self.model, config=self.config)
        response = self.chat.send_message(self.prompt)
        logger.info(f"✅ Gemini Agent 初始化完成")
        logger.info(f"📝 初始化响应: {response.text}")

    def is_working(self):
        return self.modbus_ai_cmd.is_working
    
    def send_message(self, message, callback=None):
        """发送消息给AI并处理响应
        
        Args:
            message (str): 用户输入的消息
            
        Returns:
            str: AI的响应文本
            
        Raises:
            Exception: 当AI处理或函数调用出现错误时抛出
        """
        try:
            logger.info(f"发送消息给AI: {message}")
            response = self.chat.send_message(message)
            
            if response.function_calls:
                for fn in response.function_calls:
                    try:
                        # 构建函数参数
                        arg_dict = {}
                        for key, val in fn.args.items():
                            arg_dict[key] = val
                        args = ", ".join(f"{key}={val}" for key, val in arg_dict.items())
                        logger.info(f"执行函数: {fn.name}({args})")
                        if callback:
                            callback(f"执行函数: {fn.name}({args})")
                        logger.debug(f"函数参数: {arg_dict}")
                        
                        # 执行函数调用
                        method = self.modbus_ai_cmd.execute_method(fn.name)
                        if not method:
                            raise ValueError(f"未找到方法: {fn.name}")
                        
                        result = method(**arg_dict)
                        logger.info(f"函数执行结果: {result}")
                        
                        # 将执行结果发送回AI
                        response = self.chat.send_message(result)
                        
                    except Exception as e:
                        error_msg = f"执行函数 {fn.name} 时出错: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        return f"执行出错: {error_msg},请重新执行"
            
            return response.text
            
        except Exception as e:
            # 重新创建聊天会话（使用配置的模型）
            try:
                self.chat = self.client.chats.create(model=self.model, config=self.config)
                logger.warning("⚠️ 聊天会话已重新创建")
            except Exception as reset_error:
                logger.error(f"❌ 重新创建聊天会话失败: {reset_error}")
            
            error_msg = f"AI处理消息时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"抱歉，处理您的请求时出现了问题，请重新说一遍"
# modbus_ai_cmd.is_working = True
# print("开始执行指令", modbus_ai_cmd.is_working)
# input_prompt = "请输入指令："
# input = str(input(f"{input_prompt}"))
# response = chat.send_message(input)
# print("请移动机器人到指定站点并执行动作指令", response.text, is_working)
# while modbus_ai_cmd.is_working:
#     if (response.function_calls):
#         for fn in response.function_calls:
#             arg_dict = {}
#             for key, val in fn.args.items():
#                 arg_dict[key] = val
#             args = ", ".join(f"{key}={val}" for key, val in arg_dict.items())
#             print(f"{fn.name}({args})")
#             print(arg_dict)
#             result = modbus_ai_cmd.execute_method(fn.name)(**arg_dict)
#             print(f"执行结果：{result}")
#             response = chat.send_message(result)
#         continue
# # Use the chat interface
#     print("继续下一步操作")
#     # response = chat.send_message(
#     #     "若上一条指令调用了input_robot_cmd指令，下一条指令必须调用mv_to_station或execute_action控制小车执行移动任务或动作任务！否则将受到惩罚！\
#     #         如果需要用户输入指令，请调用input_robot_cmd指令！")
#     response = chat.send_message(
#         "请调用工具完成你的任务！，如需要用户提供信息，需要通过input_robot_cmd实现")
#     print(response.text, modbus_ai_cmd.is_working)
# print("success to Terminating chat session")
