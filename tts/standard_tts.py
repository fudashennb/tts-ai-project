# Copyright 2025 Standard Robots Co. All rights reserved.
import numpy as np
import onnxruntime as ort
from piper_phonemize import phonemize_espeak  # 注释掉原来的导入
import json
import time
import wave
import re


# 配置
class TTSConfig:
    def __init__(self, model_path, config_path):
        self.model_path = model_path
        self.config_path = config_path
        # 初始化性能监控器
        # 加载配置文件
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        # 初始化ONNX会话
        self.session = ort.InferenceSession(model_path)
        # 采样率
        self.sample_rate = self.config.get(
            'audio', {}).get('sample_rate', 22050)
        print('✅ 自定义TTS配置加载成功')


class AudioProcessor:
    """音频处理类"""

    @staticmethod
    def save_audio(audio, text_hint='', sample_rate=22050):
        """保存音频为WAV文件"""
        print(f'音频数据形状: {audio.shape}')
        print(f'音频数据类型: {audio.dtype}')
        print(f'音频数值范围: [{np.min(audio):.4f}, {np.max(audio):.4f}]')
        print(f'采样率: {sample_rate}')
        try:
            # 转换为16位整数

            # 生成文件名
            if text_hint:
                # 保留下划线、数字等字符，只过滤特殊符号
                clean_text = re.sub(r'[^\u4e00-\u9fff\w\d_\s]', '', text_hint)
                # 限制长度，但保留完整信息
                if len(clean_text) > 30:
                    clean_text = clean_text[:30]
                timestamp = int(time.time())
                wav_filename = f'tts_{clean_text}_{timestamp}.wav'
            else:
                timestamp = int(time.time())
                wav_filename = f'output_{timestamp}.wav'

            # 保存WAV文件
            sample_rate = 22050
            audio_int16 = (audio * 32767).astype(np.int16)
            with wave.open(wav_filename, 'w') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())

            print(f'✅ 音频文件已保存: {wav_filename}')
            print(f'📁 文件路径: {wav_filename}')
            print(f'💾 文件大小: {len(audio_int16) * 2} 字节')
            print('🔊 提示：由于您在远程环境中，请下载WAV文件到本地播放')

            return wav_filename

        except Exception as e:
            print(f'❌ 保存WAV文件失败: {e}')
            return None


class TTSSynthesizer:
    """TTS合成器基类"""

    def __init__(self, config):
        self.config = config

    def synthesize(self, text):
        """合成语音（子类必须实现）"""
        raise NotImplementedError


class OfficialPiperSynthesizer(TTSSynthesizer):
    """官方Piper合成器"""

    def synthesize(self, text):
        """使用官方Piper合成语音"""
        if not self.config.piper_voice:
            print('❌ 官方Piper库不可用')
            return np.array([], dtype=np.float32)

        try:
            print(f'🔄 使用官方Piper合成: {text}')

            # 获取官方Piper输出
            audio_bytes = bytes()
            for audio_chunk in self.config.piper_voice.synthesize_stream_raw(text):
                audio_bytes += audio_chunk

            # 转换为numpy数组
            audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(
                np.float32) / 32767.0

            print(
                f'✅ 官方Piper合成完成: {len(audio)} 样本, {len(audio) / self.config.sample_rate:.3f} 秒'
            )
            return audio

        except Exception as e:
            print(f'❌ 官方Piper合成失败: {e}')
            return np.array([], dtype=np.float32)


class CustomSynthesizer(TTSSynthesizer):
    """自定义中文合成器 - 完全按照Piper源码实现"""

    def synthesize(self, text):
        """使用自定义中文处理进行合成"""
        try:
            # 1. 音素化（按照Piper的方式）
            sentence_phonemes = self._phonemize_chinese(text)

            # 2. 对每个句子进行合成
            all_audio = []
            for i, phonemes in enumerate(sentence_phonemes):
                # 3. 转换为音素ID（按照Piper的方式）
                phoneme_ids = self._phonemes_to_ids(phonemes)
                # 4. ONNX推理（按照Piper的方式）
                audio = self._synthesize_ids_to_audio(phoneme_ids)
                if len(audio) > 0:
                    all_audio.append(audio)
                else:
                    print(f'❌ 第 {i + 1} 个句子合成失败')

            # 5. 合并所有音频
            if all_audio:
                final_audio = np.concatenate(all_audio)
                return final_audio
            else:
                print('❌ 自定义中文合成失败')
                return np.array([], dtype=np.float32)

        except Exception as e:
            print(f'❌ 自定义中文合成失败: {e}')
            import traceback

            traceback.print_exc()
            return np.array([], dtype=np.float32)

    def synthesize_stream(self, text, audio_processor):
        """流式合成 - 每句话单独输出音频文件"""
        try:
            # 开始整体监控
            sentence_phonemes = self._phonemize_chinese(text)
            # 2. 对每个句子进行合成并立即保存
            saved_files = []
            sentence_timings = []

            for i, phonemes in enumerate(sentence_phonemes):
                sentence_start_time = time.time()
                # 开始句子处理监控
                phoneme_ids = self._phonemes_to_ids(phonemes)
                # 4. ONNX推理（按照Piper的方式）
                audio = self._synthesize_ids_to_audio(phoneme_ids)

                if len(audio) > 0:
                    # 5. 立即保存当前句子的音频
                    import re

                    clean_text = re.sub(
                        r'[^\u4e00-\u9fff\w\s]', '', text).strip()
                    if len(clean_text) > 20:
                        clean_text = clean_text[:20] + '...'
                    friendly_name = f'{clean_text}_第{i + 1}句'
                    filename = audio_processor.save_audio(
                        audio, friendly_name, self.config.sample_rate
                    )
                    if filename:
                        saved_files.append(filename)

                        # 记录句子处理时长
                        sentence_end_time = time.time()
                        sentence_duration = sentence_end_time - sentence_start_time
                        sentence_timings.append(
                            {
                                'sentence_index': i + 1,
                                'duration': sentence_duration,
                                'audio_length': len(audio),
                                'audio_duration': len(audio) / self.config.sample_rate,
                                'filename': filename,
                            }
                        )
                    else:
                        print(f'❌ 第 {i + 1} 个句子保存失败')
                else:
                    print(f'❌ 第 {i + 1} 个句子合成失败')

            # 打印详细的性能统计
            return saved_files

        except Exception as e:
            print(f'❌ 流式自定义中文合成失败: {e}')
            import traceback

            traceback.print_exc()
            return []

    def _print_stream_performance_summary(self, sentence_timings, saved_files):
        """打印流式合成性能摘要"""
        if not sentence_timings:
            return

        print('\n' + '=' * 60)
        print('📊 流式合成性能统计摘要')
        print('=' * 60)

        # 总体统计
        total_processing_time = sum(timing['duration']
                                    for timing in sentence_timings)
        total_audio_duration = sum(
            timing['audio_duration'] for timing in sentence_timings)
        total_audio_samples = sum(timing['audio_length']
                                  for timing in sentence_timings)

        print(f'📈 总体统计:')
        print(f'   🎯 处理句子数: {len(sentence_timings)}')
        print(f'   ⏱️  总处理时长: {total_processing_time:.3f} 秒')
        print(f'   🔊 总音频时长: {total_audio_duration:.3f} 秒')
        print(f'   📊 总音频样本数: {total_audio_samples}')
        print(
            f'   🚀 处理速度: {total_audio_duration / total_processing_time:.2f}x 实时速度')

        # 每句话详细统计
        print(f'\n📋 每句话详细统计:')
        for timing in sentence_timings:
            print(f'   第{timing["sentence_index"]}句:')
            print(f'     ⏱️  处理时长: {timing["duration"]:.3f} 秒')
            print(f'     🔊 音频时长: {timing["audio_duration"]:.3f} 秒')
            print(f'     📊 音频样本数: {timing["audio_length"]}')
            print(
                f'     🚀 处理速度: {timing["audio_duration"] / timing["duration"]:.2f}x 实时速度'
            )
            print(f'     💾 文件名: {timing["filename"]}')

        # 性能分析
        processing_times = [timing['duration'] for timing in sentence_timings]
        audio_durations = [timing['audio_duration']
                           for timing in sentence_timings]

        print(f'\n📊 性能分析:')
        print(f'   ⏱️  平均处理时长: {np.mean(processing_times):.3f} 秒')
        print(f'   ⏱️  最短处理时长: {np.min(processing_times):.3f} 秒')
        print(f'   ⏱️  最长处理时长: {np.max(processing_times):.3f} 秒')
        print(f'   🔊 平均音频时长: {np.mean(audio_durations):.3f} 秒')
        print(
            f'   🚀 平均处理速度: {np.mean([a / p for a, p in zip(audio_durations, processing_times)]):.2f}x 实时速度'
        )

        print('=' * 60)

    def _phonemize_chinese(self, text):
        """中文音素化处理 - 按照Piper的方式"""
        try:
            # 使用piper_phonemize进行中文音素化，返回句子列表
            phonemes = phonemize_espeak(text, 'cmn')

            # 确保返回的是列表的列表格式
            if isinstance(phonemes, list):
                # 如果phonemes是字符串列表，转换为列表的列表
                if phonemes and isinstance(phonemes[0], str):
                    return [phonemes]
                # 如果已经是列表的列表，直接返回
                elif phonemes and isinstance(phonemes[0], list):
                    return phonemes
                else:
                    print(f'⚠️  意外的音素化结果格式: {type(phonemes)}')
                    return [[text]]
            else:
                print(f'⚠️  音素化结果不是列表: {type(phonemes)}')
                return [[text]]

        except Exception as e:
            print(f'❌ 音素化失败: {e}')
            return [[text]]

    def _phonemes_to_ids(self, phonemes):
        """将音素转换为ID - 按照Piper的方式"""
        try:
            phoneme_id_map = self.config.config.get('phoneme_id_map', {})

            if not phoneme_id_map:
                print('❌ 音素ID映射表为空')
                return []

            # 按照Piper的方式：BOS + phonemes + PAD + EOS
            ids = list(phoneme_id_map.get('^', [1]))  # BOS

            unknown_phonemes = []

            for phoneme in phonemes:
                if phoneme in phoneme_id_map:
                    ids.extend(phoneme_id_map[phoneme])
                    ids.extend(phoneme_id_map.get('_', [0]))  # PAD
                else:
                    print(f'⚠️  未知音素: {phoneme}')
                    unknown_phonemes.append(phoneme)

            ids.extend(phoneme_id_map.get('$', [2]))  # EOS

            if unknown_phonemes:
                print(
                    f'⚠️  发现 {len(unknown_phonemes)} 个未知音素: {unknown_phonemes}')

            return ids

        except Exception as e:
            print(f'❌ 音素ID转换失败: {e}')
            import traceback

            traceback.print_exc()
            return []

    def _synthesize_ids_to_audio(self, phoneme_ids):
        """从音素ID合成音频 - 按照Piper的方式"""
        try:
            if len(phoneme_ids) == 0:
                print('❌ 音素ID为空')
                return np.array([], dtype=np.float32)

            # 按照Piper的方式准备输入数据
            phoneme_ids_array = np.expand_dims(
                np.array(phoneme_ids, dtype=np.int64), 0)
            phoneme_ids_lengths = np.array(
                [phoneme_ids_array.shape[1]], dtype=np.int64)

            # 获取推理参数（按照Piper的方式）
            length_scale = self.config.config.get(
                'inference', {}).get('length_scale', 1.0)
            noise_scale = self.config.config.get(
                'inference', {}).get('noise_scale', 0.667)
            noise_w = self.config.config.get(
                'inference', {}).get('noise_w', 0.8)

            scales = np.array([noise_scale, length_scale,
                              noise_w], dtype=np.float32)

            # 检查ONNX模型的输入要求
            input_names = [
                input.name for input in self.config.session.get_inputs()]
            # 按照Piper的方式执行推理
            inputs = {
                'input': phoneme_ids_array,
                'input_lengths': phoneme_ids_lengths,
                'scales': scales,
            }

            # 如果有speaker_id输入，添加它
            if 'sid' in input_names:
                inputs['sid'] = np.array([0], dtype=np.int64)  # 默认speaker_id

            outputs = self.config.session.run(None, inputs)

            # 按照Piper的方式处理输出 - 确保返回一维数组
            audio = outputs[0]
            print(f'   - 原始输出形状: {audio.shape}')

            # 移除所有可能的维度，确保是一维数组
            while len(audio.shape) > 1:
                audio = audio.squeeze(0)

            print(f'   - 处理后音频形状: {audio.shape}')
            print(f'   - 音频长度: {len(audio)} 样本')
            print(f'   - 音频时长: {len(audio) / self.config.sample_rate:.3f} 秒')
            # Amplify by 3 times
            audio = audio * 6.0
            # Clip to [-1, 1] to prevent distortion
            audio = np.clip(audio, -1.0, 1.0)
            return audio

        except Exception as e:
            print(f'❌ ONNX推理失败: {e}')
            import traceback

            traceback.print_exc()
            return np.array([], dtype=np.float32)

    def _generate_friendly_filename(self, original_text, sentence_index, total_sentences):
        """生成友好的文件名"""
        try:
            import time
            import re

            # 清理原始文本，只保留中文、英文、数字
            clean_text = re.sub(r'[^\u4e00-\u9fff\w\s]',
                                '', original_text).strip()

            # 如果清理后为空，使用默认名称
            trunc_count = 15
            if not clean_text:
                clean_text = f'句子{sentence_index}'
            elif len(clean_text) > trunc_count:
                clean_text = clean_text[:trunc_count] + '...'
            # 添加时间戳确保唯一性
            timestamp = int(time.time())

            # 生成文件名格式：原文本_第X句_时间戳
            if total_sentences > 1:
                filename = f'{clean_text}_第{sentence_index}句_{timestamp}'
            else:
                filename = f'{clean_text}_完整_{timestamp}'

            return filename

        except Exception as e:
            print(f'⚠️  生成文件名失败: {e}')
            import time

            timestamp = int(time.time())
            return f'句子{sentence_index}_{timestamp}'


class TTSApp:
    """TTS应用程序主类"""

    def __init__(self):
        # 初始化配置
        self.config = TTSConfig(
            'model/piper/standard_tts.onnx', 'model/piper/standard_tts.onnx.json')
        # 初始化合成器
        self.custom_synthesizer = CustomSynthesizer(self.config)
        # 初始化音频处理器
        self.audio_processor = AudioProcessor()
        # 显示初始内存使用情况
        print('📊 程序启动内存使用情况:')

    def stream_synthesize(self, text):
        """
        流式合成接口 - 供外部调用
        输入：带有段落的文本信息
        输出：生成器，每次yield一个句子的音频数据和相关信息

        Args:
            text (str): 输入文本

        Yields:
            dict: {
                'audio': numpy.ndarray,  # 音频数据
                'sentence_index': int,   # 句子索引（从1开始）
                'total_sentences': int,  # 总句子数
                'sentence_text': str,    # 句子文本
                'sample_rate': int,      # 采样率
                'duration': float,       # 音频时长（秒）
                'processing_time': float, # 处理时长（秒）
                'success': bool          # 是否成功
            }
        """
        try:
            # 开始整体监控
            sentence_phonemes = self.custom_synthesizer._phonemize_chinese(
                text)
            total_sentences = len(sentence_phonemes)

            # 2. 逐句处理并yield结果
            for i, phonemes in enumerate(sentence_phonemes):
                sentence_start_time = time.time()
                sentence_index = i + 1

                try:
                    # 转换为音素ID
                    phoneme_ids = self.custom_synthesizer._phonemes_to_ids(
                        phonemes)
                    # ONNX推理
                    audio = self.custom_synthesizer._synthesize_ids_to_audio(
                        phoneme_ids)
                    if len(audio) > 0:
                        audio_duration = len(audio) / self.config.sample_rate

                        result = {
                            'audio': audio,
                            'sentence_index': sentence_index,
                            'total_sentences': total_sentences,
                            'sentence_text': ' '.join(phonemes)
                            if isinstance(phonemes, list)
                            else str(phonemes),
                            'sample_rate': self.config.sample_rate,
                            'duration': audio_duration,
                            'success': True,
                        }
                        yield result

                    else:
                        print(f'❌ 第 {sentence_index} 个句子合成失败')
                        yield {
                            'audio': np.array([], dtype=np.float32),
                            'sentence_index': sentence_index,
                            'total_sentences': total_sentences,
                            'sentence_text': ' '.join(phonemes)
                            if isinstance(phonemes, list)
                            else str(phonemes),
                            'sample_rate': self.config.sample_rate,
                            'duration': 0.0,
                            'success': False,
                        }
                except Exception as e:
                    sentence_end_time = time.time()
                    processing_time = sentence_end_time - sentence_start_time

                    print(f'❌ 第 {sentence_index} 个句子处理失败: {e}')
                    yield {
                        'audio': np.array([], dtype=np.float32),
                        'sentence_index': sentence_index,
                        'total_sentences': total_sentences,
                        'sentence_text': ' '.join(phonemes)
                        if isinstance(phonemes, list)
                        else str(phonemes),
                        'sample_rate': self.config.sample_rate,
                        'duration': 0.0,
                        'processing_time': processing_time,
                        'success': False,
                        'error': str(e),
                    }
            # 结束整体监控
            print(f'✅ 流式合成完成，共处理 {total_sentences} 个句子')

        except Exception as e:
            print(f'❌ 流式合成接口失败: {e}')
            import traceback

            traceback.print_exc()

            # 如果出错，至少返回一个错误结果
            yield {
                'audio': np.array([], dtype=np.float32),
                'sentence_index': 1,
                'total_sentences': 1,
                'sentence_text': text,
                'sample_rate': self.config.sample_rate,
                'duration': 0.0,
                'processing_time': 0.0,
                'success': False,
                'error': str(e),
            }


def run_official_mode(tts_app: TTSApp):
    """运行官方模式"""
    print('🎤 官方Piper模式')
    print('使用官方Piper库进行语音合成')
    print("输入 '返回' 回到主菜单")
    print()

    while True:
        text = input('官方> ')

        if text.strip() == '返回':
            break
        elif not text.strip():
            print('请输入有效文本！')
            continue

        try:
            audio = tts_app.official_synthesizer.synthesize(text)
            if len(audio) > 0:
                filename = tts_app.audio_processor.save_audio(
                    audio, f'{text}_官方', tts_app.config.sample_rate
                )
                if filename:
                    print(f'🎉 官方语音合成完成: {filename}')
            else:
                print('😞 官方语音合成失败')
        except Exception as e:
            print(f'❌ 官方模式错误: {e}')

        print()


def run_custom_mode(tts_app: TTSApp):
    """运行自定义模式"""
    print('🇨🇳 自定义中文模式')
    print('使用自定义中文音素化和ONNX推理进行语音合成')
    print("输入 '返回' 回到主菜单")
    print()

    while True:
        text = input('自定义> ')

        if text.strip() == '返回':
            break
        elif not text.strip():
            print('请输入有效文本！')
            continue

        try:
            audio = tts_app.custom_synthesizer.synthesize(text)
            if len(audio) > 0:
                filename = tts_app.audio_processor.save_audio(
                    audio, text, tts_app.config.sample_rate
                )
                if filename:
                    print(f'🎉 自定义中文处理完成！文件已保存为: {filename}')
                    print('💡 您可以使用以下方式获取文件：')
                    print(f'   - scp 命令: scp user@host:{filename} ./')
                    print(f'   - 或在本地终端运行: rsync -av user@host:{filename} ./')
            else:
                print('😞 自定义中文合成失败')
        except Exception as e:
            print(f'❌ 自定义模式错误: {e}')

        print()


def run_stream_mode(tts_app: TTSApp):
    """运行流式输出模式"""
    print('🌊 流式输出模式')
    print('每句话单独生成音频文件，实时输出')
    print("输入 '返回' 回到主菜单")
    print()

    while True:
        text = input('流式> ')

        if text.strip() == '返回':
            break
        elif not text.strip():
            print('请输入有效文本！')
            continue

        try:
            # 使用流式合成
            saved_files = tts_app.custom_synthesizer.synthesize_stream(
                text, tts_app.audio_processor
            )
            if saved_files:
                print(f'🎉 流式处理完成！共生成 {len(saved_files)} 个音频文件：')
                for i, filename in enumerate(saved_files, 1):
                    print(f'   {i}. {filename}')
                print('💡 您可以使用以下方式获取文件：')
                for filename in saved_files:
                    print(f'   - scp 命令: scp user@host:{filename} ./')
                    print(f'   - 或在本地终端运行: rsync -av user@host:{filename} ./')
            else:
                print('😞 流式中文合成失败')
        except Exception as e:
            print(f'❌ 流式模式错误: {e}')

        print()


def run(tts_app: TTSApp):
    """运行主程序"""
    print('=== 文本转语音程序（远程版本）===')
    print('🎯 专为远程SSH环境设计，生成WAV文件供下载播放')
    print()
    print('🌊 流式输出模式：每句话单独生成音频文件')
    print("输入 '退出' 结束程序")
    print('或者直接输入中文文本进行语音合成')
    print()

    while True:
        text = input('> ')

        if text.strip().lower() == '退出':
            break
        elif text.strip().lower() == '官方':
            run_official_mode(tts_app)
            print('=== 文本转语音程序（远程版本）===')
            print('🎯 专为远程SSH环境设计，生成WAV文件供下载播放')
            print()
            print('🌊 流式输出模式：每句话单独生成音频文件')
            print("输入 '退出' 结束程序")
            print('或者直接输入中文文本进行语音合成')
            print()
        elif text.strip().lower() == '自定义':
            run_custom_mode(tts_app)
            print('=== 文本转语音程序（远程版本）===')
            print('🎯 专为远程SSH环境设计，生成WAV文件供下载播放')
            print()
            print('🌊 流式输出模式：每句话单独生成音频文件')
            print("输入 '退出' 结束程序")
            print('或者直接输入中文文本进行语音合成')
            print()
        elif text.strip().lower() == '流式':
            run_stream_mode(tts_app)
            print('=== 文本转语音程序（远程版本）===')
            print('🎯 专为远程SSH环境设计，生成WAV文件供下载播放')
            print()
            print('🌊 流式输出模式：每句话单独生成音频文件')
            print("输入 '退出' 结束程序")
            print('或者直接输入中文文本进行语音合成')
            print()
        elif not text.strip():
            print('请输入有效文本！')
            continue
        else:
            try:
                # 默认使用流式输出模式
                print('🌊 使用流式输出模式处理文本...')
                saved_files = tts_app.custom_synthesizer.synthesize_stream(
                    text, tts_app.audio_processor
                )
                if saved_files:
                    print(f'🎉 流式处理完成！共生成 {len(saved_files)} 个音频文件：')
                    for i, filename in enumerate(saved_files, 1):
                        print(f'   {i}. {filename}')
                    print('💡 您可以使用以下方式获取文件：')
                    for filename in saved_files:
                        print(f'   - scp 命令: scp user@host:{filename} ./')
                        print(
                            f'   - 或在本地终端运行: rsync -av user@host:{filename} ./')

                    # 显示最终性能统计
                else:
                    print('😞 流式中文合成失败')
            except Exception as e:
                print(f'❌ 错误：{e}')


def main():
    """主函数"""
    app = TTSApp()
    run(app)


if __name__ == '__main__':
    main()
