"""
翻译功能模块：使用Gemini API进行批量翻译
"""
import time
import re
from config import TRANSLATION_AVAILABLE, GEMINI_API_KEY

def translate_titles_batch(titles, max_retries=3):
    """
    使用 Gemini API 批量翻译论文标题为中文
    @param titles: list of str - 英文标题列表
    @param max_retries: int - 最大重试次数
    @return: dict - {title: translated_title} 映射字典
    """
    if not TRANSLATION_AVAILABLE or not GEMINI_API_KEY:
        return {title: "" for title in titles}
    
    if not titles or len(titles) == 0:
        return {}
    
    # 过滤空标题
    valid_titles = [t for t in titles if t and t.strip()]
    if not valid_titles:
        return {}
    
    # 构建批量翻译提示词（更专业的学术翻译）
    titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(valid_titles)])
    prompt = f"""你是一位专业的学术翻译专家，擅长将英文学术论文标题翻译成简体中文。

请将以下英文论文标题翻译成简体中文。要求：
1. 保持学术术语的准确性和专业性
2. 对于专业术语（如Cell-Free、Massive MIMO、RIS、ISAC等），使用学术界通用的中文翻译
3. 保持标题的简洁性和可读性
4. 只返回翻译结果，每行一个，格式为：序号. 中文翻译
5. 不要添加任何解释、说明或其他内容

英文标题列表：
{titles_text}

请直接输出翻译结果："""
    
    for attempt in range(max_retries):
        try:
            from google import genai
            
            # 根据官方文档使用新的 API 方式：https://ai.google.dev/gemini-api/docs/text-generation
            # 使用 Client 而不是 GenerativeModel
            try:
                # 尝试传递 api_key 参数
                client = genai.Client(api_key=GEMINI_API_KEY)
            except (TypeError, AttributeError):
                # 如果 Client 不接受 api_key 参数，使用默认方式（从环境变量读取）
                client = genai.Client()
            
            # 尝试不同的模型名称
            model_names = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
            model_name = model_names[0]  # 默认使用最新的模型
            
            # 尝试导入 types 用于配置
            try:
                from google.genai import types
                # 使用配置参数
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2
                    )
                )
            except (ImportError, AttributeError):
                # 如果没有 types 模块或配置不工作，尝试直接传递配置字典
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={'temperature': 0.2}
                    )
                except (TypeError, AttributeError):
                    # 最简单的调用方式（不使用配置）
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
            
            if response and response.text:
                translated_text = response.text.strip()
                print(f"Translation response received, length: {len(translated_text)}")
                
                # 解析翻译结果
                translations = {}
                lines = [line.strip() for line in translated_text.split('\n') if line.strip()]
                
                # 方法1: 尝试匹配格式：序号. 翻译内容
                for line in lines:
                    # 匹配格式：数字. 翻译内容 或 数字、翻译内容
                    # 尝试匹配开头的数字（可能带括号、点号等）
                    match = re.match(r'^[(\[]?\s*(\d+)\s*[).\]、:：.]\s*(.+)$', line)
                    if match:
                        try:
                            idx = int(match.group(1)) - 1  # 转换为0-based索引
                            translated = match.group(2).strip()
                            # 清理可能的标点符号
                            translated = re.sub(r'^["\'「」『』]|["\'「」『』]$', '', translated).strip()
                            if 0 <= idx < len(valid_titles) and translated:
                                translations[valid_titles[idx]] = translated
                        except (ValueError, IndexError):
                            continue
                
                # 方法2: 如果解析成功数量不足，尝试按行顺序匹配
                if len(translations) < len(valid_titles):
                    # 过滤掉已经解析成功的行
                    remaining_lines = []
                    for line in lines:
                        # 检查是否已经匹配过
                        matched = False
                        for idx, title in enumerate(valid_titles):
                            if title in translations and translations[title]:
                                continue
                            match = re.match(r'^[(\[]?\s*(\d+)\s*[).\]、:：.]\s*(.+)$', line)
                            if match and int(match.group(1)) - 1 == idx:
                                matched = True
                                break
                        if not matched:
                            remaining_lines.append(line)
                    
                    # 按顺序匹配剩余的标题
                    line_idx = 0
                    for idx, title in enumerate(valid_titles):
                        if title not in translations or not translations[title]:
                            if line_idx < len(remaining_lines):
                                translated = remaining_lines[line_idx].strip()
                                # 移除可能的序号前缀
                                translated = re.sub(r'^[(\[]?\s*\d+\s*[).\]、:：.]\s*', '', translated)
                                translated = re.sub(r'^["\'「」『』]|["\'「」『』]$', '', translated).strip()
                                if translated:
                                    translations[title] = translated
                                line_idx += 1
                
                # 为所有标题创建映射（包括未翻译的）
                result = {}
                for title in valid_titles:
                    result[title] = translations.get(title, "")
                
                print(f"Successfully translated {sum(1 for v in result.values() if v)}/{len(valid_titles)} titles")
                return result
                    
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))  # 指数退避
            else:
                print(f"Batch translation failed: {str(e)}")
                # 返回空翻译
                return {title: "" for title in valid_titles}
    
    return {title: "" for title in valid_titles}

