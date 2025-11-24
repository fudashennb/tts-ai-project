"""
文本处理器 - 数字和百分比处理

功能：
1. 符号标准化（全角转半角）
2. 编号识别（关键词距离判断）
3. 数字转中文（支持万、亿）
4. 小数处理（四舍五入、逐位朗读）
5. 百分比处理

设计理念：
- 配置驱动：所有规则从CSV读取
- 易于扩展：添加新规则只需修改CSV
- 职责单一：每个方法只做一件事
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from config.config_loader import get_config_loader

_logger = logging.getLogger(__name__)


class TextProcessor:
    """文本处理器"""
    
    def __init__(self):
        """初始化"""
        self.config_loader = get_config_loader()
        
        # 配置缓存
        self.symbol_rules = []
        self.identifier_keywords = []
        self.number_config = {}
        
        # 加载配置
        self._load_configs()
    
    def _load_configs(self):
        """加载所有配置"""
        try:
            # 符号标准化规则
            self.symbol_rules = self.config_loader.get_enabled_items('symbol_normalization')
            
            # 编号关键词
            self.identifier_keywords = self.config_loader.get_enabled_items('number_identifier_keywords')
            
            # 口语数字标准化规则
            self.spoken_digit_rules = self.config_loader.get_enabled_items('spoken_normalization')
            
            # 缩写词规则（新增）
            self.abbreviation_rules = self.config_loader.get_enabled_items('abbreviations')
            
            # 特殊字符移除规则（新增）
            self.special_chars_rules = self.config_loader.get_enabled_items('special_chars_removal')
            
            # 关键词替换规则（新增）
            self.replacement_rules = self.config_loader.get_enabled_items('keyword_replacements')
            
            # 数字处理配置
            self.number_config = {
                'decimal_places': self.config_loader.get_config_value('number_processing_config', 'decimal_places', 2),
                'enable_wan_yi': self.config_loader.get_config_value('number_processing_config', 'enable_wan_yi', True),
                'percentage_allow_space': self.config_loader.get_config_value('number_processing_config', 'percentage_allow_space', True),
                'keyword_max_search_chars': self.config_loader.get_config_value('number_processing_config', 'keyword_max_search_chars', 10),
            }
            
            _logger.info(f"✅ 文本处理器配置加载完成: {len(self.symbol_rules)}条符号规则, {len(self.identifier_keywords)}个关键词, {len(self.spoken_digit_rules)}条口语规则, {len(self.abbreviation_rules)}个缩写词, {len(self.special_chars_rules)}个特殊字符, {len(self.replacement_rules)}个关键词替换规则")
        
        except Exception as e:
            _logger.error(f"❌ 加载配置失败: {e}")
    
    def reload_configs(self):
        """重新加载配置"""
        self.config_loader.reload_all()
        self._load_configs()
    
    def normalize_symbols(self, text: str) -> str:
        """
        符号标准化：全角转半角
        
        处理：％ → %, ０ → 0, １ → 1, 等
        """
        result = text
        
        for rule in self.symbol_rules:
            original = rule.get('original', '')
            replacement = rule.get('replacement', '')
            if original and replacement:
                result = result.replace(original, replacement)
        
        return result
    
    def process_keyword_replacements(self, text: str) -> str:
        """
        处理关键词替换（基于配置）
        
        从 config/rules/keyword_replacements.csv 读取替换规则
        将发音不清晰的词替换为发音清晰的词
        
        示例:
        - "堆垛" → "堆堕"
        - "AGV" → "埃及威"
        
        参数:
            text: 原始文本
        
        返回:
            处理后的文本
        """
        if not text:
            return text
        
        # 从配置加载替换规则
        replacements = {}
        for rule in self.replacement_rules:
            original = rule.get('original_word', '')
            replacement = rule.get('replacement_word', '')
            if original and replacement:
                replacements[original] = replacement
        
        if not replacements:
            return text
        
        # 按长度排序（长的优先匹配，避免部分匹配）
        sorted_words = sorted(replacements.keys(), key=len, reverse=True)
        
        result = text
        
        # 先处理单位替换（需要特殊处理：只替换数字后的单位）
        # 定义单位字符列表
        unit_chars = {'V': '福特', '℃': '摄氏度', 'I': '安培'}
        
        for original in sorted_words:
            replacement = replacements[original]
            
            # 如果是单位字符，使用特殊的正则匹配（只匹配数字后的单位）
            if original in unit_chars:
                # 匹配模式：数字（整数或小数）+ 单位
                # 支持：26.5V, 32.0℃, 26.5I, 26V, 32℃等
                # 正则：(\d+\.?\d*)(V|℃|I) - 匹配数字（可选小数点）+ 单位
                pattern = r'(\d+\.?\d*)' + re.escape(original)
                replacement_with_number = r'\1' + replacement
                new_result = re.sub(pattern, replacement_with_number, result)
                if new_result != result:
                    _logger.debug(f"🔄 单位替换: 数字+'{original}' → 数字+'{replacement}'")
                    result = new_result
                continue
            
            # 判断是英文单词还是中文词
            is_english_word = bool(re.match(r'^[a-zA-Z]+$', original))
            
            if is_english_word:
                # 英文单词：先处理带空格的变体（如 "A G V"、"a g v"、"A    G       V"）
                # 对于多字母单词，生成带空格的变体模式
                if len(original) > 1:
                    # 构建字母间带空格的模式：每个字母之间可以有1个或多个空格
                    # 例如：AGV -> [Aa]\s+[Gg]\s+[Vv]
                    letters = list(original)
                    spaced_pattern_parts = []
                    for i, letter in enumerate(letters):
                        if i > 0:
                            spaced_pattern_parts.append(r'\s+')  # 字母之间有一个或多个空格
                        # 匹配大小写不敏感
                        spaced_pattern_parts.append(f'[{letter.upper()}{letter.lower()}]')
                    
                    spaced_pattern = ''.join(spaced_pattern_parts)
                    # 添加词边界：前后不能是字母
                    spaced_pattern = r'(?<![a-zA-Z])' + spaced_pattern + r'(?![a-zA-Z])'
                    
                    # 先替换带空格的变体
                    new_result = re.sub(spaced_pattern, replacement, result)
                    if new_result != result:
                        _logger.debug(f"🔄 关键词替换（带空格）: '{original}' → '{replacement}'")
                        result = new_result
                
                # 再处理连续字母的变体（如 "AGV"、"agv"）
                # 匹配模式：前面不能是字母（但可以是数字、中文、标点、开头）
                #           后面不能是字母（但可以是数字、中文、标点、结尾）
                # 这样可以匹配：句子开头、末尾、中间、与中文/数字/标点相邻的情况
                # 注意：允许与数字相邻（如AGV123、123AGV），但不允许与字母相邻（如AGVabc）
                pattern = r'(?<![a-zA-Z])' + re.escape(original) + r'(?![a-zA-Z])'
            else:
                # 中文词：使用特殊处理，避免部分匹配
                pattern = re.escape(original)
                
                # 特殊处理：如果原始词的最后一个字符可能重复（如"堆垛"后面可能跟"垛"）
                # 检查后面不是该字符，避免部分匹配
                # 例如："堆垛" → "堆堕"，检查后面不是"垛"，避免匹配"堆垛垛"中的"堆垛"
                if len(original) > 0:
                    last_char = original[-1]
                    # 如果最后一个字符可能重复，添加负向前瞻
                    pattern = pattern + f'(?!{re.escape(last_char)})'
            
            # 执行替换（对于英文单词，这里处理连续字母的变体）
            if original in result or (is_english_word and len(original) > 1):
                new_result = re.sub(pattern, replacement, result)
                if new_result != result:
                    _logger.debug(f"🔄 关键词替换: '{original}' → '{replacement}'")
                    result = new_result
        
        return result
    
    def remove_special_chars(self, text: str) -> str:
        """
        移除特殊字符（基于配置）
        
        从 config/rules/special_chars_removal.csv 读取要移除的字符
        
        参数:
            text: 原始文本
        
        返回:
            移除特殊字符后的文本
        """
        if not text:
            return text
        
        result = text
        
        # 遍历所有要移除的字符
        for rule in self.special_chars_rules:
            char = rule.get('character', '')
            if char:
                result = result.replace(char, '')
                if char in text:
                    _logger.debug(f"🗑️ 移除特殊字符: '{char}'")
        
        return result
    
    def process_abbreviations(self, text: str) -> str:
        """
        处理英文缩写（基于配置）
        
        从 config/rules/abbreviations.csv 读取缩写词规则
        将缩写词转换为TTS友好格式（字母间加空格）
        
        示例：
        - "AGV" → "A G V"
        - "AMR系统" → "A M R 系统"
        
        参数:
            text: 原始文本
        
        返回:
            处理后的文本
        """
        if not text:
            return text
        
        import re
        
        result = text
        
        # 构建缩写词列表
        abbreviations = {}
        for rule in self.abbreviation_rules:
            abbr = rule.get('abbreviation', '')
            tts_format = rule.get('tts_format', '')
            if abbr and tts_format:
                abbreviations[abbr] = tts_format
        
        if not abbreviations:
            return result
        
        # 按长度排序（长的优先匹配，避免部分匹配）
        sorted_abbrs = sorted(abbreviations.keys(), key=len, reverse=True)
        
        # 构建正则模式（词边界匹配，避免误匹配）
        pattern = r'(?<![a-zA-Z])(' + '|'.join(re.escape(abbr) for abbr in sorted_abbrs) + r')(?![a-zA-Z])'
        
        def replace_func(match):
            abbr = match.group(1).upper()
            tts_format = abbreviations.get(abbr, abbreviations.get(match.group(1), ''))
            if tts_format:
                _logger.debug(f"🔤 缩写词转换: '{match.group(1)}' → '{tts_format}'")
                return f' {tts_format} '
            return match.group(0)
        
        result = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
        
        # 清理多余空格
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    def normalize_spoken_digits(self, text: str) -> str:
        """
        口语数字标准化：将口语数字转换为标准数字（基于上下文判断）
        
        处理：
        - "编号幺三零七" → "编号一三零七"
        - "洞拐勾" → "零七九"（在数字上下文）
        - "幺蛾子" → "幺蛾子"（保持不变，非数字上下文）
        
        参数:
            text: 原始文本
        
        返回:
            处理后的文本
        """
        if not text:
            return text
        
        result = text
        
        # 获取所有口语数字词
        spoken_words = {rule['spoken_word']: rule['standard_word'] 
                       for rule in self.spoken_digit_rules}
        
        if not spoken_words:
            return result
        
        # 构建所有数字字符集合（用于上下文判断）
        digit_chars = set('0123456789零一二三四五六七八九十')
        digit_chars.update(spoken_words.keys())  # 添加口语数字本身
        
        # 编号关键词（用于上下文判断）
        number_keywords = {kw['keyword'] for kw in self.identifier_keywords}
        
        # 量词关键词（用于排除非数字上下文）
        quantifier_words = {'个', '只', '件', '条', '位', '名', '人', '次', '遍', '回', '趟'}
        
        def is_digit_context(text: str, pos: int) -> bool:
            """
            判断位置pos的字符是否在数字上下文中
            
            判断规则：
            1. 前方有编号关键词
            2. 前后有数字字符（0-9或中文数字）
            3. 前后有其他口语数字
            4. 前方有"第"等序数词
            
            排除规则：
            1. 后面紧跟量词（如"两个"）
            """
            # 获取前后文本（各取5个字符）
            search_range = 5
            start = max(0, pos - search_range)
            end = min(len(text), pos + search_range + 1)
            before = text[start:pos]
            after = text[pos + 1:end]
            
            # 获取当前字符
            current_char = text[pos]
            
            # 排除规则：检查是否是量词用法
            # 如"两个"、"俩人"等
            if current_char in ['两', '俩']:
                # 检查后面1-2个字符
                next_chars = text[pos + 1:pos + 3]
                for qw in quantifier_words:
                    if next_chars.startswith(qw):
                        _logger.debug(f"🚫 排除量词用法: '{text[pos:pos+3]}'")
                        return False
            
            # 检查前方是否有编号关键词
            for keyword in number_keywords:
                if keyword in before:
                    _logger.debug(f"✅ 检测到编号关键词: '{keyword}'")
                    return True
            
            # 检查前方是否有"第"（序数词）
            if '第' in before:
                _logger.debug(f"✅ 检测到序数词: '第'")
                return True
            
            # 检查前后是否有数字字符
            for char in before[-3:]:  # 检查前3个字符
                if char in digit_chars:
                    _logger.debug(f"✅ 前方有数字字符: '{char}'")
                    return True
            
            for char in after[:3]:  # 检查后3个字符
                if char in digit_chars:
                    _logger.debug(f"✅ 后方有数字字符: '{char}'")
                    return True
            
            return False
        
        # 遍历文本，查找并替换口语数字
        i = 0
        while i < len(result):
            # 检查当前位置是否匹配口语数字
            matched = False
            for spoken_word, standard_word in sorted(spoken_words.items(), key=lambda x: -len(x[0])):
                # 检查是否匹配
                if result[i:i+len(spoken_word)] == spoken_word:
                    # 判断是否在数字上下文中
                    if is_digit_context(result, i):
                        _logger.debug(f"🔄 口语数字转换: '{spoken_word}' → '{standard_word}' (位置{i})")
                        result = result[:i] + standard_word + result[i+len(spoken_word):]
                        i += len(standard_word)
                        matched = True
                        break
                    else:
                        _logger.debug(f"⏭️ 跳过非数字上下文: '{spoken_word}' (位置{i})")
            
            if not matched:
                i += 1
        
        return result
    
    def is_identifier_number(self, text: str, number_pos: int) -> bool:
        """
        判断数字是否为编号类（需要逐位朗读）
        
        参数:
            text: 完整文本
            number_pos: 数字在文本中的起始位置
        
        返回:
            True: 编号类（逐位朗读）
            False: 数值类（按数值朗读）
        
        逻辑:
            向前搜索指定字符数，检查是否存在编号关键词
        """
        # 确定搜索范围
        max_search = self.number_config.get('keyword_max_search_chars', 10)
        search_start = max(0, number_pos - max_search)
        prefix_text = text[search_start:number_pos]
        
        # 检查关键词
        for keyword_item in self.identifier_keywords:
            keyword = keyword_item.get('keyword', '')
            max_distance = int(keyword_item.get('max_distance', 3))
            
            if keyword in prefix_text:
                # 计算关键词到数字的距离
                keyword_pos = prefix_text.rfind(keyword)
                distance = len(prefix_text) - keyword_pos - len(keyword)
                
                if distance <= max_distance:
                    _logger.debug(f"🔍 检测到编号关键词: '{keyword}', 距离={distance}")
                    return True
        
        return False
    
    def number_to_chinese(self, num: int) -> str:
        """
        整数转中文（支持万、亿）
        
        示例:
            10 → "十"
            1007 → "一千零七"
            7864 → "七千八百六十四"
            12345 → "一万二千三百四十五"
        """
        if num == 0:
            return "零"
        
        # 数字映射
        digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
        units = ["", "十", "百", "千"]
        big_units = ["", "万", "亿"]
        
        # 是否启用万、亿
        enable_wan_yi = self.number_config.get('enable_wan_yi', True)
        
        if not enable_wan_yi:
            # 不启用万、亿，直接逐位朗读
            return " ".join([digits[int(d)] for d in str(num)])
        
        # 处理负数
        negative = num < 0
        num = abs(num)
        
        # 分段处理（亿、万、个）
        def convert_section(n):
            """转换0-9999的数字"""
            if n == 0:
                return ""
            
            result = ""
            str_n = str(n)
            length = len(str_n)
            
            for i, digit in enumerate(str_n):
                digit_val = int(digit)
                pos = length - i - 1  # 位置（0=个位，1=十位，2=百位，3=千位）
                
                if digit_val == 0:
                    # 零的处理：避免连续零，末尾零不读
                    if result and not result.endswith("零"):
                        result += "零"
                else:
                    # 特殊处理：10-19 读作"十x"而不是"一十x"
                    if pos == 1 and digit_val == 1 and length == 2:
                        result += units[pos]
                    else:
                        result += digits[digit_val] + units[pos]
            
            # 去除末尾的零
            return result.rstrip("零")
        
        # 分段
        yi = num // 100000000
        wan = (num % 100000000) // 10000
        ge = num % 10000
        
        result = ""
        
        # 亿
        if yi > 0:
            result += convert_section(yi) + "亿"
        
        # 万
        if wan > 0:
            result += convert_section(wan) + "万"
        elif yi > 0 and ge > 0:
            # 亿和个之间需要补零
            result += "零"
        
        # 个
        if ge > 0:
            result += convert_section(ge)
        
        # 处理负数
        if negative:
            result = "负" + result
        
        return result
    
    def process_decimal(self, decimal_str: str) -> str:
        """
        处理小数部分
        
        逻辑:
            1. 四舍五入到指定位数
            2. 逐位朗读
        
        示例:
            "1234" → "一二"  (保留2位)
            "5" → "五"
            "50" → "五"  (去除末尾零)
        """
        decimal_places = self.number_config.get('decimal_places', 2)
        
        # 四舍五入
        if len(decimal_str) > decimal_places:
            # 转换为浮点数进行四舍五入
            decimal_value = float("0." + decimal_str)
            rounded_value = round(decimal_value, decimal_places)
            decimal_str = str(rounded_value).split('.')[1] if '.' in str(rounded_value) else "0"
        
        # 去除末尾零
        decimal_str = decimal_str.rstrip('0')
        
        if not decimal_str:
            return ""
        
        # 逐位朗读（不加空格，更自然）
        digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
        return "".join([digits[int(d)] for d in decimal_str])
    
    def process_number(self, text: str, match_obj, is_percentage: bool = False) -> str:
        """
        处理单个数字
        
        参数:
            text: 完整文本
            match_obj: 正则匹配对象
            is_percentage: 是否为百分比
        
        返回:
            处理后的数字字符串
        """
        number_str = match_obj.group(0)
        number_pos = match_obj.start()
        
        # 去除百分号（如果有）
        if is_percentage:
            number_str = number_str.rstrip('%').rstrip()
        
        # 判断是否为编号类（只对纯整数判断）
        if not is_percentage and '.' not in number_str and self.is_identifier_number(text, number_pos):
            # 编号类：逐位朗读
            digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
            result = " ".join([digits[int(d)] if d.isdigit() else d for d in number_str if d.isdigit()])
            _logger.debug(f"📝 编号类: {number_str} → {result}")
            return result
        
        # 数值类：整数部分按数值读，小数部分逐位读
        if '.' in number_str:
            integer_part, decimal_part = number_str.split('.')
            
            # 整数部分
            if integer_part:
                integer_chinese = self.number_to_chinese(int(integer_part))
            else:
                integer_chinese = "零"
            
            # 小数部分
            decimal_chinese = self.process_decimal(decimal_part)
            
            if decimal_chinese:
                result = f"{integer_chinese}点{decimal_chinese}"
            else:
                result = integer_chinese
        else:
            # 纯整数
            result = self.number_to_chinese(int(number_str))
        
        # 百分比特殊处理
        if is_percentage:
            result = f"百分之{result}"
        
        _logger.debug(f"📝 数值类: {number_str} → {result}")
        return result
    
    def date_to_chinese(self, year: str, month: str, day: str) -> str:
        """
        将日期转换为中文格式
        
        参数:
            year: 年份字符串（4位数字）
            month: 月份字符串（1-2位数字）
            day: 日期字符串（1-2位数字）
        
        返回:
            中文日期字符串，如"二零二五年七月二十九日"
        
        示例:
            date_to_chinese("2025", "07", "29") → "二零二五年七月二十九日"
            date_to_chinese("2025", "7", "9") → "二零二五年七月九日"
        """
        # 数字映射
        digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
        month_names = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
        
        # 年份：逐位转换
        year_chinese = "".join([digits[int(d)] for d in year])
        
        # 月份：转换为整数后按数值读
        month_int = int(month)
        if 1 <= month_int <= 12:
            month_chinese = month_names[month_int] + "月"
        else:
            # 无效月份，保持原样
            month_chinese = month + "月"
        
        # 日期：转换为整数后按数值读
        day_int = int(day)
        if 1 <= day_int <= 31:
            # 使用number_to_chinese转换日期
            day_chinese = self.number_to_chinese(day_int) + "日"
        else:
            # 无效日期，保持原样
            day_chinese = day + "日"
        
        return f"{year_chinese}年{month_chinese}{day_chinese}"
    
    def process_dates(self, text: str) -> str:
        """
        处理日期格式：YYYY-MM-DD, YYYY.MM.DD, YYYY年MM月DD日
        
        转换为中文日期：二零二五年七月二十九日
        
        不处理斜杠分隔的日期（如：2025/07/29）
        
        参数:
            text: 原始文本
        
        返回:
            处理后的文本
        
        示例:
            "2025-07-29" → "二零二五年七月二十九日"
            "2025.07.29" → "二零二五年七月二十九日"
            "2025-7-9" → "二零二五年七月九日"
            "2025年7月29日" → "二零二五年七月二十九日"
            "2025年07月29日" → "二零二五年七月二十九日"
            "2025/07/29" → "2025/07/29"（保持不变，不处理）
        """
        if not text:
            return text
        
        # 1. 先处理中文日期格式：YYYY年MM月DD日
        pattern_chinese = r'\d{4}年\d{1,2}月\d{1,2}日'
        
        def replace_chinese_date(match):
            date_str = match.group(0)
            
            # 提取年、月、日
            # 使用正则提取：2025年7月29日
            match_parts = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
            if match_parts:
                year, month, day = match_parts.groups()
                
                # 基本验证：确保年份是4位，月份和日期在合理范围内
                if len(year) == 4 and year.isdigit():
                    try:
                        month_int = int(month)
                        day_int = int(day)
                        
                        # 验证月份和日期范围
                        if 1 <= month_int <= 12 and 1 <= day_int <= 31:
                            # 转换为中文日期
                            chinese_date = self.date_to_chinese(year, month, day)
                            _logger.debug(f"📅 中文日期转换: '{date_str}' → '{chinese_date}'")
                            return chinese_date
                    except ValueError:
                        # 转换失败，保持原样
                        pass
            
            # 验证失败或格式错误，保持原样
            return date_str
        
        # 先处理中文日期格式
        text = re.sub(pattern_chinese, replace_chinese_date, text)
        
        # 2. 再处理横杠和点分隔的日期格式：YYYY-MM-DD, YYYY.MM.DD
        # 使用负向前瞻和负向后顾，确保前后不是数字或中文字符
        # \d{4} 匹配4位年份
        # [-.] 匹配 -、. 两种分隔符（不包含斜杠）
        # \d{1,2} 匹配1-2位月份和日期
        # 使用 (?<![0-9年月日]) 和 (?![0-9年月日]) 确保前后不是数字或中文字符
        pattern = r'(?<![0-9年月日])\d{4}[-.]\d{1,2}[-.]\d{1,2}(?![0-9年月日])'
        
        def replace_date(match):
            date_str = match.group(0)
            
            # 提取分隔符和数字部分
            # 使用正则提取年、月、日（只匹配横杠和点）
            parts = re.split(r'[-.]', date_str)
            
            if len(parts) == 3:
                year, month, day = parts
                
                # 基本验证：确保年份是4位，月份和日期在合理范围内
                if len(year) == 4 and year.isdigit():
                    try:
                        month_int = int(month)
                        day_int = int(day)
                        
                        # 验证月份和日期范围
                        if 1 <= month_int <= 12 and 1 <= day_int <= 31:
                            # 转换为中文日期
                            chinese_date = self.date_to_chinese(year, month, day)
                            _logger.debug(f"📅 日期转换: '{date_str}' → '{chinese_date}'")
                            return chinese_date
                    except ValueError:
                        # 转换失败，保持原样
                        pass
            
            # 验证失败或格式错误，保持原样
            return date_str
        
        result = re.sub(pattern, replace_date, text)
        return result
    
    def process_percentages(self, text: str) -> str:
        """
        处理百分比
        
        支持:
            - % 和 ％ 两种符号
            - 空格：85.5 % 或 85.5%
        
        示例:
            "85.5%" → "百分之八十五点五"
            "100 %" → "百分之一百"
        """
        # 正则：匹配数字+可选空格+百分号
        allow_space = self.number_config.get('percentage_allow_space', True)
        
        if allow_space:
            pattern = r'\d+\.?\d*\s*%'
        else:
            pattern = r'\d+\.?\d*%'
        
        def replace_func(match):
            return self.process_number(text, match, is_percentage=True)
        
        result = re.sub(pattern, replace_func, text)
        return result
    
    def process_decimals(self, text: str) -> str:
        """
        处理所有剩余数字和小数
        
        逻辑:
            1. 检查是否为编号类（前方有关键词）
            2. 编号类：逐位朗读
            3. 数值类：整数按数值读，小数逐位读
        
        示例:
            "车辆编号1307" → "车辆编号 一 三 零 七"
            "移动了7864米" → "移动了 七千八百六十四 米"
            "距离12345米" → "距离 一万二千三百四十五 米"
            "高度10.5米" → "高度 十点五 米"
        """
        # 正则：匹配所有数字（整数和小数）
        pattern = r'\d+\.?\d*'
        
        def replace_func(match):
            return self.process_number(text, match, is_percentage=False)
        
        result = re.sub(pattern, replace_func, text)
        return result
    
    def process_text(self, text: str) -> str:
        """
        完整文本处理流程
        
        顺序:
            1. 移除特殊字符
            2. 处理缩写词
            3. 符号标准化（全角转半角）
            4. 处理关键词替换（TTS发音优化）
            5. 处理日期（YYYY-MM-DD、YYYY.MM.DD、YYYY年MM月DD日格式转中文）
            6. 百分比处理
            7. 数字和小数处理
        
        参数:
            text: 原始文本
        
        返回:
            处理后的文本
        """
        if not text:
            return text
        
        _logger.debug(f"📥 原始文本: {text}")
        
        # 1. 移除特殊字符（新增）
        text = self.remove_special_chars(text)
        _logger.debug(f"🗑️ 特殊字符移除: {text}")
        
        # 2. 符号标准化（全角转半角）- 必须在关键词替换之前，确保全角符号先转换
        text = self.normalize_symbols(text)
        _logger.debug(f"🔄 符号标准化: {text}")
        
        # 3. 处理关键词替换（新增）- 在缩写词处理之前，确保AGV等词先被替换
        text = self.process_keyword_replacements(text)
        _logger.debug(f"🔄 关键词替换: {text}")
        
        # 4. 处理缩写词（新增）
        text = self.process_abbreviations(text)
        _logger.debug(f"🔤 缩写词处理: {text}")
        
        # 5. 处理日期（新增）
        text = self.process_dates(text)
        _logger.debug(f"📅 日期处理: {text}")
        
        # 6. 百分比处理
        text = self.process_percentages(text)
        _logger.debug(f"📊 百分比处理: {text}")
        
        # 7. 数字和小数处理
        text = self.process_decimals(text)
        _logger.debug(f"🔢 数字处理: {text}")
        
        _logger.debug(f"📤 最终文本: {text}")
        
        return text


# 全局实例
_text_processor = None


def get_text_processor() -> TextProcessor:
    """获取全局文本处理器实例"""
    global _text_processor
    if _text_processor is None:
        _text_processor = TextProcessor()
    return _text_processor

