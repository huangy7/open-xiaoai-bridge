import asyncio
import os


async def before_wakeup(speaker, text, source, app):
    """
    处理收到的用户消息，并决定是否唤醒对应的大模型。
    """
    text_lower = text.lower()

    if source == "kws":
        # 小艺 (DeepSeek)
        if any(w in text_lower for w in ["小艺", "小易", "小意", "小翼", "肥鲸", "肥金", "肥京", "深度", "深搜", "deepseek"]):
            await speaker.play(text="小艺在的，请讲")
            return "openai:deepseek"

        # 美国豆包 (Gemini)
        if any(w in text_lower for w in ["美国豆包", "双子", "gemini"]):
            await speaker.play(text="美国豆包在的，请讲")
            return "openai:gemini"

        return None

    if source == "xiaoai":
        # 小艺 (DeepSeek)
        if any(w in text_lower for w in ["小艺", "小易", "小意", "小翼", "肥鲸", "肥金", "肥京", "深度", "深搜", "deepseek"]):
            await speaker.abort_xiaoai()
            await speaker.play(text="小艺在的，请讲")
            return "openai:deepseek"

        # 美国豆包 (Gemini)
        if any(w in text_lower for w in ["美国豆包", "双子", "gemini", "双子星"]):
            await speaker.abort_xiaoai()
            await speaker.play(text="美国豆包在的，请讲")
            return "openai:gemini"

        # 单次直达指令（免唤醒连续模式）
        if "让小艺" in text:
            await speaker.abort_xiaoai()
            await app.send_to_openai_and_play_reply(text.replace("让小艺", ""), profile="deepseek")
            return None

        if "让肥鲸" in text:
            await speaker.abort_xiaoai()
            await app.send_to_openai_and_play_reply(text.replace("让肥鲸", ""), profile="deepseek")
            return None

        if "让美国豆包" in text:
            await speaker.abort_xiaoai()
            await app.send_to_openai_and_play_reply(text.replace("让美国豆包", ""), profile="gemini")
            return None

        if "让双子" in text:
            await speaker.abort_xiaoai()
            await app.send_to_openai_and_play_reply(text.replace("让双子", ""), profile="gemini")
            return None

    return None


async def after_wakeup(speaker, source=None, session_key=None):
    """
    退出唤醒连续对话状态时的提示语。
    """
    if source == "openai":
        if session_key and "deepseek" in session_key:
            await speaker.play(text="小艺告退，再见")
        elif session_key and "gemini" in session_key:
            await speaker.play(text="美国豆包告退，再见")
        else:
            await speaker.play(text="再见")


APP_CONFIG = {
    # 唤醒词与连续对话设置
    "wakeup": {
        "keywords": [
            "小艺",
            "小艺小艺",
            "你好小艺",
            "美国豆包",
            "你好美国豆包",
            "双子双子",
            "你好双子",
            "gemini",
            "你好gemini",
        ],
        "timeout": 20,
        "before_wakeup": before_wakeup,
        "after_wakeup": after_wakeup,
    },

    # 关键词检测（KWS）
    "kws": {
        "keywords_score": 2.2,
        "keywords_threshold": 0.15,
        "min_silence_duration": 800,
    },

    # 语音活动检测（VAD）
    "vad": {
        "threshold": 0.10,
        "min_speech_duration": 250,
        "min_silence_duration": 500,
    },

    # 音频输入增益
    "audio_input": {
        "gain": 1.0,
    },

    # 本地离线语音识别（ASR）
    "asr": {
        "model": "sense_voice",
        "int8": True,
    },

    # 小爱音箱连续对话打断设置
    "xiaoai": {
        "continuous_conversation_mode": True,
        "exit_command_keywords": ["停止", "退下", "退出", "下去吧"],
        "max_listening_retries": 2,
        "exit_prompt": "再见，主人",
        "continuous_conversation_keywords": ["开启连续对话", "启动连续对话", "我想跟你聊天"],
    },

    # 火山引擎豆包语音合成（TTS）
    "tts": {
        "doubao": {
            "app_id": os.getenv("VOLCANO_TTS_APP_ID", "5596585664"),
            "access_key": os.getenv("VOLCANO_TTS_ACCESS_KEY", ""),
            "default_speaker": "zh_female_vv_uranus_bigtts",
            "audio_format": "pcm",
            "stream": True,
        }
    },

    # 大模型与多角色配置
    "openai": {
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "model": "deepseek-flash",
        "input_mode": "local_asr",
        "session_key": "agent:deepseek:open-xiaoai-bridge",
        "session_header": "",
        "system_prompt": "你是智能语音助手小艺（由 DeepSeek 驱动），具备卓越的思考推理能力，性格机智幽默、回答精练。请使用亲切自然的口语回答，控制在200字以内，不要输出任何 Markdown 格式或代码块，适合音箱语音播报。",
        "temperature": 0.7,
        "max_tokens": 512,
        "history_max_messages": 20,
        "response_timeout": 120,
        "tts_speaker": "zh_female_shuangkuaisisi_uranus_bigtts",
        "tts_speed": 1.0,
        "exit_keywords": ["退出", "停止", "再见"],
        "rule_prompt": "注意：将结果处理成纯文字版，不要返回任何 markdown 格式，也不要包含任何代码块，并将字数控制在200字以内",
        "rule_prompt_for_skill": "注意：这条消息是主人通过小爱音箱发送的，他看不到你回复的文字。字数控制在200字以内",
        "extra_body": {},

        # 多角色路由配置
        "profiles": {
            # 小艺：DeepSeek-Flash + 爽朗清脆甜美女声（爽快思思 2.0）
            "deepseek": {
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "model": "deepseek-flash",
                "session_header": "",
                "system_prompt": "你是智能语音助手小艺（由 DeepSeek 驱动），具备卓越的思考推理能力，性格机智幽默、回答精练。请使用亲切自然的口语回答，控制在200字以内，不要输出任何 Markdown 格式或代码块，适合音箱语音播报。",
                "tts_speaker": "zh_female_shuangkuaisisi_uranus_bigtts",
                "tts_speed": 1.0,
            },

            # 美国豆包：Gemini + 活泼开朗甜美女声（Vivi 2.0）
            "gemini": {
                "base_url": os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"),
                "api_key": os.getenv("GEMINI_API_KEY", ""),
                "model": "gemini-2.5-flash",
                "session_header": "",
                "system_prompt": "你是智能语音助手美国豆包（由 Google Gemini 驱动），性格热情开朗、风趣幽默。请使用亲切自然的口语回答，控制在200字以内，不要输出任何 Markdown 格式或代码块，适合音箱语音播报。",
                "tts_speaker": "zh_female_vv_uranus_bigtts",
                "tts_speed": 1.0,
            },
        },
    },
}
