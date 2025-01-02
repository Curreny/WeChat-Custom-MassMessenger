class WeChatConfig:
    WeChat_PROCESS_NAME = 'WeChat.exe'
    APP_NAME = 'WeChatMassTool'
    APP_PROCESS_NAME = 'WeChatMassTool.exe'
    APP_LOCK_NAME = 'WeChatMassTool.lock'
    WINDOW_NAME = '微信'
    WINDOW_CLASSNAME = 'WeChatMainWndForPC'

class IntervalConfig:
    BASE_INTERVAL = 0.1  # 基础间隔（秒）
    SEND_TEXT_INTERVAL = 0.05  # 发送文本间隔（秒）
    SEND_FILE_INTERVAL = 0.25  # 发送文件间隔（秒）
    MAX_SEARCH_SECOND = 0.1
    MAX_SEARCH_INTERVAL = 0.05
