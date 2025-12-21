"""
配置文件：包含API密钥和全局配置
所有敏感信息都从环境变量读取
"""
import os

# Gemini API 配置（必须从环境变量读取）
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY environment variable not set. Translation feature will be disabled.")
    print("Set it with: export GEMINI_API_KEY='your-api-key' (Linux/Mac)")
    print("           or: set GEMINI_API_KEY=your-api-key (Windows)")

# PushDeer 配置（必须从环境变量读取）
PUSHDEER_KEY = os.getenv('PUSHDEER_KEY', '')#
if not PUSHDEER_KEY:
    print("Warning: PUSHDEER_KEY environment variable not set. Push notification feature will be disabled.")
    print("Set it with: export PUSHDEER_KEY='your-push-key' (Linux/Mac)")
    print("           or: set PUSHDEER_KEY=your-push-key (Windows)")

# 功能开关
TRANSLATION_AVAILABLE = False
PUSH_AVAILABLE = True

# 初始化翻译功能
if GEMINI_API_KEY:
    try:
        from google import genai
        TRANSLATION_AVAILABLE = True
        # 确保环境变量已设置
        os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
    except ImportError:
        TRANSLATION_AVAILABLE = False
        print("Warning: google-genai not installed. Translation feature will be disabled.")
        print("Install it with: pip install google-genai")
else:
    TRANSLATION_AVAILABLE = False

