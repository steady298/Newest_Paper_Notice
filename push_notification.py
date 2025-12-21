"""
推送通知模块：PushDeer推送功能
"""
import datetime
import time
import traceback
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
import urllib3
from config import PUSH_AVAILABLE, PUSHDEER_KEY

# 禁用SSL警告（如果使用verify=False）
urllib3.disable_warnings(InsecureRequestWarning)

def push_deer(text, desp='', type_='text', verify_ssl=True):
    """
    PushDeer推送函数
    @param text: str - 推送消息文本
    @param desp: str - 推送消息描述（可选）
    @param type_: str - 消息类型，默认为'text'
    @param verify_ssl: bool - 是否验证SSL证书，默认True
    @return: bool - 是否成功发送
    """
    try:
        url = "https://api2.pushdeer.com/message/push"
        data = {
            'text': text,
            'desp': desp,
            'type': type_,
            'pushkey': PUSHDEER_KEY
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # 创建session并配置重试策略
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        # 如果SSL验证失败，尝试禁用SSL验证
        try:
            response = session.post(url, data=data, headers=headers, timeout=10, verify=verify_ssl)
        except requests.exceptions.SSLError:
            if verify_ssl:
                # 如果SSL验证失败，尝试禁用SSL验证
                print("SSL verification failed, retrying without SSL verification...")
                response = session.post(url, data=data, headers=headers, timeout=10, verify=False)
            else:
                raise
        
        # 检查响应状态
        if response.ok:
            # 尝试解析JSON响应
            try:
                result = response.json()
                # 检查API返回的错误码
                if result.get('code') == 0:
                    print("PushDeer 推送成功:", response.text)
                    return True
                else:
                    error_msg = result.get('error', 'Unknown error')
                    error_code = result.get('code', 'Unknown')
                    print(f"PushDeer 推送失败 [错误码 {error_code}]: {error_msg}")
                    if error_code == 80501:
                        print("提示: PushDeer Key 可能无效，请检查 PUSHDEER_KEY 配置")
                    return False
            except (ValueError, KeyError):
                # 如果不是JSON格式，直接显示文本
                print("PushDeer 推送成功:", response.text)
                return True
        else:
            print("PushDeer 推送失败:", response.status_code, response.text)
            return False
    except Exception as e:
        traceback.print_exc()
        print("PushDeer 推送异常:", e)
        return False

def send_push_notification(message, max_retries=3):
    """
    发送推送通知（带重试机制）
    @param message: str - 推送消息内容
    @param max_retries: int - 最大重试次数
    @return: bool - 是否成功发送
    """
    if not PUSH_AVAILABLE:
        return False
    
    if not PUSHDEER_KEY:
        print("Warning: PUSHDEER_KEY not set. Push notification skipped.")
        return False
    
    # 获取当前日期
    date_now = datetime.date.today().strftime('%Y年%m月%d日')
    
    # 构建推送消息描述
    desp = f"""**更新时间**: {date_now}

{message}
"""
    
    # 重试机制
    verify_ssl = True  # 首先尝试使用SSL验证
    for attempt in range(max_retries):
        try:
            # 调用push_deer函数发送消息
            result = push_deer(text=message, desp=desp, type_='text', verify_ssl=verify_ssl)
            
            if result:
                return True
            else:
                raise Exception("API returned failure")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Attempt {attempt + 1}/{max_retries} failed: {error_msg}")
            
            # 如果是SSL错误，尝试禁用SSL验证
            if 'ssl' in error_msg.lower() or 'eof' in error_msg.lower():
                if verify_ssl:
                    print("SSL error detected, retrying without SSL verification...")
                    verify_ssl = False
                    continue
                elif attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 指数退避：2秒、4秒、6秒
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Failed to send push notification after {max_retries} attempts due to SSL error.")
                    # 尝试使用更简单的方式发送（不包含额外内容）
                    try:
                        result = push_deer(text=message, desp='', type_='text', verify_ssl=False)
                        if result:
                            print("Push notification sent with simplified message.")
                            return True
                    except Exception as e2:
                        print(f"Simplified push also failed: {str(e2)}")
                        return False
            # 如果是其他网络错误，等待后重试
            elif any(keyword in error_msg.lower() for keyword in ['connection', 'timeout', 'http']):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 指数退避：2秒、4秒、6秒
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Failed to send push notification after {max_retries} attempts due to network error.")
                    return False
            else:
                # 其他类型的错误，不重试
                print(f"Failed to send push notification: {error_msg}")
                return False
    
    return False

