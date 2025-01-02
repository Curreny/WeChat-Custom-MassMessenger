import sys
import os
import logging  # 添加日志模块
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_dir, '../'))
# sys.path.insert(0, project_root)

from typing import Dict
from collections import defaultdict
from PySide6.QtCore import (QObject, QRunnable, QThreadPool, Slot, Signal)
from PySide6.QtCore import QCoreApplication, QTimer, QEventLoop
from utils import (WxOperation)
import pythoncom
import json
import time

# 配置日志
log_file_path = 'application.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_file_path, encoding='utf-8'),
    logging.StreamHandler(sys.stdout)
])

def write_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class TaskRunnable(QRunnable):
    def __init__(self, func, task_id, *args, **kwargs):
        super().__init__()
        self.func = func
        self.task_id = task_id
        self.args = args
        self.kwargs = kwargs
        self.toggleTaskStatusSignal = kwargs.get('toggleTaskStatusSignal')

    def run(self):
        pythoncom.CoInitialize()  # 初始化 COM 库
        try:
            self.execute_task()
        except Exception as e:
            self.handle_error(e)
        finally:
            self.toggleTaskStatusSignal.emit(self.task_id)
            pythoncom.CoUninitialize()  # 释放 COM 库


    def execute_task(self):
        # 将由子类实现具体任务
        pass
        

    def handle_error(self, error):
        print(f"Error in {self.task_id}: {error}")


class SendMessageTask(TaskRunnable):
    def execute_task(self):
        # 实现发送消息的逻辑
        message_info = self.kwargs.get('message_info')
        check_pause = self.kwargs.get('check_pause')
        updatedProgressSignal = self.kwargs.get('updatedProgressSignal')
        recordExecInfoSignal = self.kwargs.get('recordExecInfoSignal')
        showInfoBarSignal = self.kwargs.get('showInfoBarSignal')
        cacheProgressSignal = self.kwargs.get('cacheProgressSignal')
        deleteCacheProgressSignal = self.kwargs.get('deleteCacheProgressSignal')
        #
        name_list = message_info.pop('name_list')
        cache_index = int(message_info.pop('cache_index', int(0)))
        text_name_list_count = int(message_info.pop('text_name_list_count', int(0)))
        #
        texts = '\n'.join(message_info.get('msgs', str()))
        files = '\n'.join(message_info.get('file_paths', str()))
        #
        exec_info_map = dict()
        infobar_info = [0, 0]
        # 首先更新 progress 进度条
        updatedProgressSignal.emit(0, len(name_list))
        #
        for idx, name in enumerate(name_list):
            # 不满足 (不存在缓存进度索引 和 当前索引小于进度索引) 就往下执行, 用于跳过以发送的用户
            if not (cache_index and idx <= cache_index):
                check_pause()  # 检查程序是否暂停
                try:
                    exec_info_map.update({'昵称': name, '文本': texts, '文件': files, '状态': '成功'})
                    self.func(name, **message_info)
                    infobar_info = [True, f'{name[:8]} 发送成功']
                except (ValueError, TypeError, AssertionError, NameError) as e:
                    exec_info_map.update({'状态': '失败', '备注': str(e)})
                    infobar_info = [False, f'{name[:8]} {str(e)}']
                finally:
                    recordExecInfoSignal.emit(exec_info_map)
                    showInfoBarSignal.emit(*infobar_info)
                    # 触发缓存文件保存文件操作
                    if text_name_list_count > (idx + 1):
                        cacheProgressSignal.emit(str(idx))
                    # 触发删除缓存进度索引文件
                    if text_name_list_count == (idx + 1):
                        deleteCacheProgressSignal.emit(True)
            # 通知更新进度条
            updatedProgressSignal.emit(idx + 1, len(name_list))  # 通知控制器任务完成
        self.toggleTaskStatusSignal.emit(self.task_id)  # 任务完成后发出信号


class GetNameListTask(TaskRunnable):
    def execute_task(self):
        tag = self.kwargs.get('tag')
        file_path = self.kwargs.get('file_path')
        exportNameListSignal = self.kwargs.get('exportNameListSignal')
        try:
            result = self.func(tag)
            write_file(file_path, data=result)
            exportNameListSignal.emit(True, '文件导出成功')
        except LookupError:
            exportNameListSignal.emit(False, f'找不到 {tag} 标签')


class GetChatGroupNameListTask(TaskRunnable):
    def execute_task(self):
        file_path = self.kwargs.get('file_path')
        exportChatGroupNameListSignal = self.kwargs.get('exportChatGroupNameListSignal')
        result = self.func()
        write_file(file_path, data=result)
        exportChatGroupNameListSignal.emit(True, '文件导出成功')


class ModelMain(QObject):
    toggleTaskStatusSignal = Signal(str)
    recordExecInfoSignal = Signal(dict)
    exportNameListSignal = Signal(bool, str)
    exportChatGroupNameListSignal = Signal(bool, str)
    showInfoBarSignal = Signal(bool, str)
    cacheProgressSignal = Signal(str)
    deleteCacheProgressSignal = Signal(bool)
    updatedProgressSignal = Signal(int, int)  # 添加这些信号
    
    
    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(10)
        #
        self.wx = WxOperation()
        #
        self.task_status_map: Dict[str, bool] = defaultdict()  # 用于存放不同任务的状态
        self.toggleTaskStatusSignal.connect(self.change_task_status)
        self.exportNameListSignal.connect(self.handle_export_name_list_result)
        self.toggleTaskStatusSignal.connect(self.quit_application)  # 连接信号到槽函数

    def export_name_list(self, tag, file_path):
        """导出标签好友名单"""
        task_id = 'name_list'
        if self.task_status_map.get(task_id):
            return
        self.toggleTaskStatusSignal.emit(task_id)

        runnable = GetNameListTask(
            self.wx.get_friend_list,
            task_id=task_id,
            tag=None if tag == '全部' else tag,
            file_path=file_path,
            toggleTaskStatusSignal=self.toggleTaskStatusSignal,
            exportNameListSignal=self.exportNameListSignal
        )
        self.thread_pool.start(runnable)

    def export_chat_group_name_list(self, file_path):
        """导出群聊名单"""
        task_id = 'chat_group_name_list'
        if self.task_status_map.get(task_id):
            return
        self.toggleTaskStatusSignal.emit(task_id)

        runnable = GetChatGroupNameListTask(
            self.wx.get_chat_group_name_list,
            task_id=task_id,
            file_path=file_path,
            toggleTaskStatusSignal=self.toggleTaskStatusSignal,
            exportChatGroupNameListSignal=self.exportChatGroupNameListSignal
        )
        self.thread_pool.start(runnable)

    def send_wechat_message(self, message_info: dict, check_pause, updatedProgressSignal):
        """发送微信消息"""
        task_id = 'send_msg'
        if self.task_status_map.get(task_id):
            return
        self.toggleTaskStatusSignal.emit(task_id)

        runnable = SendMessageTask(
            self.wx.send_msg,
            task_id=task_id,
            check_pause=check_pause,
            message_info=self.process_message_info(message_info=message_info),
            updatedProgressSignal=updatedProgressSignal,
            toggleTaskStatusSignal=self.toggleTaskStatusSignal,
            recordExecInfoSignal=self.recordExecInfoSignal,
            showInfoBarSignal=self.showInfoBarSignal,
            cacheProgressSignal=self.cacheProgressSignal,
            deleteCacheProgressSignal=self.deleteCacheProgressSignal
        )
        self.thread_pool.start(runnable)

    @staticmethod
    def process_message_info(message_info):
        # 处理昵称，以换行符为分割
        if names := message_info.pop('names', list()):
            message_info['name_list'].extend(names.split('\n'))

        # 简单去重（导入名单和手动输入重复), 保持获取时候的顺序
        message_info['name_list'] = list(dict.fromkeys(message_info['name_list']))

        # 处理消息
        msg_list = list()
        if signal_text := message_info.pop('single_text', None):
            msg_list.extend(signal_text.split('\n'))
        if multi_text := message_info.pop('multi_text', None):
            msg_list.append(multi_text)

        message_info['msgs'] = msg_list
        return message_info

    @Slot(bool)
    def change_task_status(self, task_id):
        self.task_status_map[task_id] = not self.task_status_map.get(task_id)
        
    @Slot(bool, str)
    def handle_export_name_list_result(self, success, message):
        if success:
            print("好友列表导出成功:", message)
        else:
            print("好友列表导出失败:", message)
            
        QCoreApplication.quit()  # 任务完成后退出应用程序

    @Slot(str)
    def quit_application(self, task_id):
        if task_id == 'send_msg':
            QCoreApplication.quit()


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def friend_list_export(tag):  # 导出好友列表
    pythoncom.CoInitialize()  # 初始化 COM 库
    try:
        app = QCoreApplication(sys.argv)
        model = ModelMain()
        file_path = f"{tag}.json"
        
        # 检查文件是否存在，如果不存在则创建一个空的 JSON 文件
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)
        
        model.export_name_list(tag, file_path)
        print(f"正在导出标签为 '{tag}' 的好友列表到 '{file_path}'")
        sys.exit(app.exec())
    finally:
        pythoncom.CoUninitialize()  # 释放 COM 库

def send_message_to_sb(json_file_path, template_name):
    pythoncom.CoInitialize()  # 初始化 COM 库
    try:
        app = QCoreApplication(sys.argv)
        model = ModelMain()
        
        # 读取 JSON 文件中的好友名单
        with open(json_file_path, 'r', encoding='utf-8') as f:
            name_list = json.load(f)
        
        # 处理消息内容
        def process_message(name):
            return(MESSAGE_TEMPLATES.get(template_name).format(name=name))
        
        for name in name_list:
            logging.info(f"开始发送消息给: {name}")  # 添加日志
            model = ModelMain()
            message_info = {
                'names': name,
                'single_text': '',
                'multi_text': None,
                'name_list': [name],
                'msgs': [],
                'file_paths': []
            }
            
            # 更新文本内容
            message_info['single_text'] = process_message(name)
            model.send_wechat_message(
                message_info=message_info,
                check_pause=lambda: None,
                updatedProgressSignal=model.updatedProgressSignal
            )

            # 创建一个事件循环，等待任务完成信号
            loop = QEventLoop()
            def on_task_finished(task_id):
                if task_id == 'send_msg':
                    loop.quit()
                    model.toggleTaskStatusSignal.disconnect(on_task_finished)
            
            model.toggleTaskStatusSignal.connect(on_task_finished)
            loop.exec()

            logging.info(f"消息发送成功，时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")  # 添加日志

        # # 启动事件循环
        # sys.exit(app.exec())

    finally:
        pythoncom.CoUninitialize()  # 释放 COM 库

# 定义消息模板
MESSAGE_TEMPLATES = {
    'new_year': "{name}，新年快乐！愿您在新的一年里，事业蒸蒸日上，家庭幸福美满，身体健康，万事如意！",
    'birthday': "{name}，生日快乐！愿您在这特别的日子里，心想事成，幸福美满！",
    'christmas': "{name}，圣诞快乐！愿您的节日充满温馨与欢乐！",
    'thanksgiving': "{name}，感恩节快乐！感谢您一直以来的支持与陪伴！",
    'valentines': "{name}，情人节快乐！愿您与爱人共度美好时光！",
    'mid_autumn': "{name}，中秋节快乐！愿您与家人团圆美满，幸福安康！"
}

if __name__ == '__main__':
    # friend_list_export('可发')# 导出标签为"tag_name"的好友列表为json文件，若为全部好友则传入"全部"
    send_message_to_sb('test.json','new_year')
