# Copyright 2025 Standard Robots Co. All rights reserved.

from dialog.dialog_recognize import AudioStreamReader
from tts.audio_player import (
    AudioPlayer,
    SystemStateManager,
    PlayRequest,
    StatusCommand,
    PlayMode,
    PlayTask,
)
import log_config
import asyncio
import time
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import uvicorn
import logging
import os
import sys
from pathlib import Path
import subprocess
import random
from typing import Dict, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入统一的日志配置

# 导入 Gemini Agent
try:
    from gemini.agent.gemini_agent import GeminiAgent
    GEMINI_AVAILABLE = True
    _logger = logging.getLogger(__name__)
    _logger.info("✅ Gemini Agent 模块导入成功")
except ImportError as e:
    GEMINI_AVAILABLE = False
    _logger = logging.getLogger(__name__)
    _logger.warning(f"⚠️ 无法导入 Gemini Agent: {e}")
    _logger.warning("将使用本地测试回复")

_logger = logging.getLogger(__name__)

audio_player = None
state_manager = None
gemini_agent = None  # 添加全局 Gemini Agent
# tts_app = None
play_worker_task = None  # 添加全局播放工作器任务

conversation_worker_task = None
conversation_reader = AudioStreamReader()

# # 本地回复系统
# def get_local_response(user_input: str) -> str:
#     return "resultCode=200,resultMsg=不好意思，你是个好人"   


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    global audio_player, state_manager, tts_app, play_worker_task, gemini_agent

    _logger.info('语音播放服务正在启动...')

    # 清理播放队列中的播放任务
    _logger.info('清理播放队列中的播放任务')

    # 初始化全局实例（先初始化以便清理）
    audio_player = AudioPlayer()
    state_manager = SystemStateManager()
    
    # 初始化 Gemini Agent
    if GEMINI_AVAILABLE:
        try:
            _logger.info('🤖 正在初始化 Gemini Agent...')
            gemini_agent = GeminiAgent()
            _logger.info('✅ Gemini Agent 初始化成功')
        except Exception as e:
            _logger.error(f'❌ Gemini Agent 初始化失败: {e}', exc_info=True)
            _logger.warning('将使用本地测试回复')
            gemini_agent = None
    else:
        _logger.warning('⚠️ Gemini Agent 不可用，将使用本地测试回复')
        gemini_agent = None
    
    # tts_app = audio_player.tts_app

    # 清理播放队列
    audio_player.clear_queue_sync()
    audio_player.stop_current()
    audio_player.is_playing = False

    # 清理程序相关缓存
    _logger.info('清理程序相关缓存，确保启动时状态干净')

    # 清理临时音频文件
    try:
        import os
        import glob
        temp_patterns = ['/tmp/tmp*.wav',
                         '/tmp/tts_*.wav', '/tmp/output_*.wav']
        for pattern in temp_patterns:
            files = glob.glob(pattern)
            for file in files:
                try:
                    if os.path.exists(file):
                        os.unlink(file)
                        _logger.debug(f'清理临时文件: {file}')
                except:
                    pass
    except:
        pass

    # 清理可能的程序残留进程（只清理程序相关的）
    try:
        import subprocess
        # 只清理可能由程序创建的音频进程，不清理系统默认音频
        result = subprocess.run(
            ['pgrep', '-f', 'aplay.*tmp'], capture_output=True, text=True)
        if result.returncode == 0:
            subprocess.run(['pkill', '-f', 'aplay.*tmp'],
                           capture_output=True, check=False)
            _logger.info('清理程序相关的临时音频进程')
    except:
        pass

    _logger.info('播放队列和程序缓存清理完成')

    # 启动播放工作器
    play_worker_task = threading.Thread(target=play_queue_worker, daemon=True)
    play_worker_task.start()

    conversation_worker_task = threading.Thread(
        target=conversation_reader.conversation_stream_loop, daemon=True
    )
    conversation_worker_task.start()

    _logger.info('语音播放服务已启动')
    _logger.info('系统默认进入音乐模式')
    _logger.info('可用的API端点:')
    _logger.info('  POST /play - 播放音频/切换模式')
    _logger.info('  GET /status - 获取播放状态和系统状态')
    _logger.info('\n模式切换说明:')
    _logger.info('  - 默认音乐模式: 支持 PLAY_MUSIC, PLAY_TEXT, START_CONVERSATION')
    _logger.info('  - 对话模式: 支持 PLAY_CONVERSATION, STOP_CONVERSATION')
    _logger.info('  - 对话模式下音乐相关命令将被忽略')
    _logger.info('\n使用示例:')
    _logger.info('  - 切换模式: /play?status_command=start_conversation')
    _logger.info(
        '  - 播放音乐: /play?file_path=/path/to/music.wav&status_command=play_music')
    _logger.info('  - 播放文本: /play?music_text=你好世界&status_command=play_text')
    _logger.info('  - 查看状态: /status')

    yield

    # 关闭时的清理
    _logger.info('语音播放服务正在关闭...')
    # 取消播放工作器任务
    if play_worker_task and play_worker_task.is_alive():
        _logger.info('等待播放工作器线程结束...')
        # 由于线程是守护线程，主程序退出时会自动结束
    # 停止音频播放
    if conversation_worker_task and conversation_worker_task.is_alive():
        conversation_reader.stop_audio_stream()

    if audio_player:
        audio_player.stop()

    # 清理TTS应用资源
    # if tts_app:
    #     try:
    #         # 这里可以添加TTS应用的清理逻辑
    #         _logger.info('正在清理TTS资源...')
    #         tts_app = None
    #         _logger.info('TTS资源清理完成')
    #     except Exception as e:
    #         _logger.error(f'清理TTS资源时出错: {e}')

    # _logger.info('语音播放服务已关闭')


app = FastAPI(title='语音播放服务', description='通过API控制语音文件播放', lifespan=lifespan)


@app.post('/start_button_conversation')
async def start_button_conversation():
    conversation_reader.start_button_conversation()
    return {'status': 'success', 'message': '已启动按钮对话'}


@app.post('/stop_button_conversation')
async def stop_button_conversation():
    conversation_reader.stop_button_conversation()
    return {'status': 'success', 'message': '已停止按钮对话'}


@app.get('/get_conversation_playing_status')
async def get_conversation_playing_status():
    
    return {'status': 'success', 'message': '对话播放状态', 'is_playing_now': state_manager.is_playing_now, 'last_play_end_time': state_manager.last_play_end_time}


@app.post('/play')
async def play_audio(request: PlayRequest):
    _logger.info(request.status_command)
    """播放音频文件或切换系统状态"""
    try:
        if state_manager.is_conversation_mode() and request.status_command in [StatusCommand.PLAY_MUSIC, StatusCommand.PLAY_TEXT]:
            _logger.info('忽略音乐请求: 当前对话模式')
            return {'status': 'ignored', 'message': 'Music paused in conversation mode'}

        if request.status_command == StatusCommand.START_CONVERSATION:
            _logger.info('start conversation')
            if state_manager.switch_to_conversation_mode():
                # 立即清理播放队列中累积的"急停已触发"等系统录音
                _logger.info('清理播放队列中累积的系统录音')
                audio_player.clear_queue_sync()
                _logger.info('强制清理累积的系统录音进程')
                if audio_player.executor:
                    audio_player.executor.shutdown(wait=True)
                _logger.info('executor shutdown')
                audio_player.executor = None

                audio_player.stop_current()
                # 强制终止所有 aplay 进程，清理累积的系统录音

                return {
                    'status': 'success',
                    'message': '已切换到对话模式',
                    'current_mode': 'conversation',
                }
            else:
                raise HTTPException(
                    status_code=400, detail='当前已在对话模式或无法切换到对话模式')

        elif request.status_command == StatusCommand.STOP_CONVERSATION:
            if state_manager.switch_to_music_mode():
                return {'status': 'success', 'message': '已切换到音乐模式', 'current_mode': 'music'}
            else:
                raise HTTPException(
                    status_code=400, detail='当前已在音乐模式或无法切换到音乐模式')

        elif request.status_command in [
            StatusCommand.PLAY_MUSIC,
            StatusCommand.PLAY_TEXT,
            StatusCommand.PLAY_CONVERSATION,
        ]:
            _logger.info(request.status_command)
            # 检查当前模式是否可以处理该命令
            if not state_manager.can_process_command(request.status_command):
                current_mode = state_manager.current_mode
                # 将模式名称转换为中文
                mode_name_map = {'music': '音乐', 'conversation': '对话'}
                current_mode_cn = mode_name_map.get(current_mode, current_mode)
                _logger.info(
                    f'当前处于{current_mode_cn}模式，{request.status_command.value}命令不生效'
                )
                if request.status_command in [StatusCommand.PLAY_MUSIC, StatusCommand.PLAY_TEXT]:
                    raise HTTPException(
                        status_code=400,
                        detail=f'当前处于{current_mode_cn}模式，{request.status_command.value}命令不生效',
                    )
                else:  # PLAY_CONVERSATION
                    raise HTTPException(
                        status_code=400, detail=f'当前处于{current_mode_cn}模式，无法播放对话内容'
                    )
            # 创建播放任务
            task = PlayTask(
                file_path=request.file_path,
                play_interval=request.play_interval,
                play_count=request.play_count,
                priority=request.priority,
                volume=request.volume,
                music_text=request.music_text,
                created_time=time.time(),
            )

            task.status_command = request.status_command  # Added: Set status_command

            # 计算并设置预估播放时长
            if task.file_path:
                _logger.info(f'get audio file duration: {task.file_path}')
                task.duration = audio_player.get_audio_file_duration(
                    task.file_path)
            elif task.music_text:
                task.duration = audio_player.estimate_text_duration(
                    task.music_text)

            # 修复：当 PLAY_MUSIC 使用 replace 模式时，强制改为 add 模式，避免打断提示语
            # 同步处理队列操作
            if request.mode == PlayMode.REPLACE:
                audio_player.replace_queue_sync(task)
            else:
                audio_player.add_to_queue_sync(task)
            if state_manager.is_conversation_mode():
                state_manager.is_playing_now = True
            else:
                state_manager.is_playing_now = False
                state_manager.last_play_end_time = 0
            # 立即返回响应，不等待播放完成
            return {
                'status': 'success',
                'message': f'已{"替换" if request.mode == PlayMode.REPLACE else "添加"}播放任务',
                'current_mode': state_manager.current_mode,
                'task': {
                    'file_path': task.file_path,
                    'play_count': task.play_count,
                    'priority': task.priority,
                    'volume': task.volume,
                    'command': request.status_command.value,
                    'duration': task.duration,  # 添加duration字段
                },
            }

        else:
            raise HTTPException(
                status_code=400, detail=f'不支持的命令: {request.status_command}')

    except Exception as e:
        _logger.error(f'播放音频时发生错误: {e}')
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get('/status')
async def get_status():
    """获取播放状态和系统状态"""
    try:
        # 获取播放状态
        play_status = audio_player.get_queue_status_sync()

        # 计算队列中所有任务的预估时间
        queue_duration_info = []
        total_queue_duration = 0.0

        with audio_player.sync_lock:
            for i, task in enumerate(audio_player.play_queue):
                single_duration = task.duration  # 使用task中存储的duration
                total_duration = audio_player.calculate_total_duration(task)
                total_queue_duration += total_duration

                queue_duration_info.append(
                    {
                        'queue_position': i + 1,
                        'single_duration': single_duration,
                        'total_duration': total_duration,
                        'play_count': task.play_count,
                        'play_interval': task.play_interval,
                        'type': 'audio_file' if task.file_path else 'text',
                    }
                )

        # 获取系统状态
        system_status = {
            'current_mode': state_manager.current_mode,
            'is_music_mode': state_manager.is_music_mode(),
            'is_conversation_mode': state_manager.is_conversation_mode(),
            'available_commands': {
                'music_mode': [
                    StatusCommand.PLAY_MUSIC.value,
                    StatusCommand.PLAY_TEXT.value,
                    StatusCommand.START_CONVERSATION.value,
                ],
                'conversation_mode': [
                    StatusCommand.PLAY_CONVERSATION.value,
                    StatusCommand.STOP_CONVERSATION.value,
                ],
            },
        }

        return {
            'status': 'success',
            'data': {
                'play_status': play_status,
                'system_status': system_status,
                'queue_duration': {
                    'total_queue_duration': total_queue_duration,
                    'queue_items': queue_duration_info,
                    'unit': 'seconds',
                },
            },
        }
    except Exception as e:
        _logger.error(f'获取状态时发生错误: {e}')
        raise HTTPException(status_code=500, detail=str(e)) from e


def play_queue_worker():
    """后台播放队列工作器"""
    while True:
        try:
            task = None
            with audio_player.sync_lock:
                if not audio_player.play_queue:
                    audio_player.is_playing = False
                    if state_manager.is_playing_now:
                        state_manager.is_playing_now = False
                        state_manager.last_play_end_time = time.time()

                    # 释放锁后再等待
                    pass
                else:
                    task = audio_player.play_queue.pop(0)
                    audio_player.is_playing = True
            # 如果队列为空，等待一段时间再检查
            if task is None:
                time.sleep(0.1)
                continue

            try:
                cmd = task.status_command
                if state_manager.is_conversation_mode() and cmd in [StatusCommand.PLAY_MUSIC, StatusCommand.PLAY_TEXT]:
                    _logger.warning(
                        f'Skipping music task: Currently in conversation mode')
                    continue
            except AttributeError:
                _logger.warning(
                    'Skipping invalid task: Missing status_command attribute')
                continue

            # 播放指定次数
            # 如果play_count为0或1，都播放一次
            actual_play_count = max(
                1, task.play_count) if task.play_count == 0 else task.play_count
            for i in range(actual_play_count):
                try:
                    # 等待文本播放完成（通过检查进程状态）
                    if task.file_path:
                        _logger.info(f'播放文件: {task.file_path}')
                        audio_player.play_file(task.file_path, task.volume)
                    else:
                        _logger.info(f'！！！！！！！！！！！播放文本: {task.music_text}')
                        # 使用新的play_text方法播放文本
                        audio_player.play_text(task.music_text, task.volume)
                    # 如果播放数大于1，播放间隔大于0，则等待play_interval秒后再播放一次
                    if i < actual_play_count - 1 and task.play_interval > 0:
                        time.sleep(task.play_interval)
                except Exception as e:  # noqa: PERF203
                    if task.music_text:
                        _logger.error(f'播放文本失败: {e}')
                    else:
                        _logger.error(f'播放文件 {task.file_path} 失败: {e}')
                    break

        except Exception as e:
            _logger.error(f'播放队列工作器错误: {e}')
            _logger.error(f'播放队列工作器错误: {e}')
            time.sleep(1)  # 出错时等待1秒再继续


def wait_for_playback_completion():
    """等待播放完成"""
    while True:
        # 检查当前播放进程是否还在运行
        if audio_player.current_process is None:
            break

        # 检查进程是否还在运行
        if audio_player.current_process.poll() is not None:
            # 进程已结束
            break

        # 等待一段时间再检查
        time.sleep(0.1)


@app.post('/pause_music')
async def pause_music():
    _logger.info('收到暂停音乐请求')
    # 这里可以添加逻辑通知外部停止发送
    return {'status': 'success'}


@app.post('/resume_music')
async def resume_music():
    state_manager.switch_to_music_mode()  # Ensure mode and reset paused
    _logger.info('音乐请求已恢复')
    return {'status': 'success'}


@app.post('/local_chat')
async def local_chat(request_data: dict):
    """本地对话处理 - 使用 Gemini Agent 或测试回复"""
    try:
        user_input = request_data.get("query", "")
        _logger.info(f'📥 收到本地对话请求: {user_input}')
        
        # 如果 Gemini Agent 可用，优先使用它处理请求
        if gemini_agent is not None:
            try:
                _logger.info(f'🤖 调用 Gemini Agent 处理: {user_input}')
                
                # 创建回调函数，用于记录函数调用过程
                def log_callback(message: str):
                    _logger.info(f'🔧 Function Call: {message}')
                
                # 调用 Gemini Agent
                ai_response = gemini_agent.send_message(user_input, callback=log_callback)
                _logger.info(f'✅ Gemini 回复: {ai_response}')
                
                # 返回原API期望的字符串格式
                return f"resultCode=200,resultMsg={ai_response}"
                
            except Exception as e:
                _logger.error(f'❌ Gemini Agent 处理失败: {e}', exc_info=True)
                # 降级到测试回复
                reply_msg = "AI服务暂时不可用，请稍后再试"
        else:
            # Gemini Agent 不可用，使用测试回复
            _logger.warning('⚠️ Gemini Agent 不可用，使用测试回复')
            
            # 自定义回复规则 - 可以根据关键词匹配返回不同回复
            custom_replies = {
                "你好": "AGV的移动速度是95.678%，距离为3.14159米. 电池85.5%. 任务完成.我们了解到，95.678已经不少了，所以95  .  6是想要的结果。a d v . d a d。有时候我认为 . 1 是对的。车辆编号为1307的AGV在前天的**利用率**为 **96.52％**。",
                "天气": "抱歉，我无法查询天气信息。",
                "时间": f"现在是{time.strftime('%H点%M分')}。",
                "名字": "我叫小德，是一个智能助手。",
                # 在这里添加更多自定义回复规则
            }
            
            # 检查是否匹配自定义回复
            reply_msg = None
            for keyword, reply in custom_replies.items():
                if keyword in user_input:
                    reply_msg = reply
                    break
            
            # 如果没有匹配到，使用默认回复
            if reply_msg is None:
                reply_msg = "不好意思，这个问题，我还在学习"
            
            _logger.info(f'💬 测试回复: {reply_msg}')
            return f"resultCode=200,resultMsg={reply_msg}"
        
    except Exception as e:
        _logger.error(f'本地对话处理错误: {e}')
        return "resultCode=500,resultMsg=处理错误"





if __name__ == '__main__':
    uvicorn.run('tts.speak_server:app', host='0.0.0.0',
                port=8800, reload=False)
