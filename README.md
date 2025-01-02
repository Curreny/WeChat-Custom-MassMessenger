# WeChat Custom MassMessenger

WeChat Custom MassMessenger 是一个微信自定义群发祝福脚本。主要支持自定义消息模板和提取微信好友列表并设置称呼的功能，能够发送带称呼的节日祝福语。

## 项目结构
```
WeChat-Custom-MassMessenger              
├─ config                                      
│  ├─ config.py                          
│  └─ __init__.py                        
├─ utils                                     
│  ├─ clipboard_utils.py                 
│  ├─ window_utils.py                    
│  ├─ wx_operation.py                    
│  └─ __init__.py                                             
├─ main.py                               
├─ README.md                             
└─ requirements.txt                                                       
```

## 功能
- 自定义消息模板：用户可以创建和编辑消息模板
- 提取微信好友列表：提取指定标签的微信好友列表导出成`json`格式
- 发送带称呼的节日祝福语：根据好友列表和消息模板，发送个性化的节日祝福语

## 启动
1. 克隆项目到本地：
    ```bash
    git clone https://github.com/yourusername/WeChat-Custom-MassMessenger.git
    ```
2. 进入项目目录：
    ```bash
    cd WeChat-Custom-MassMessenger
    ```
3. 安装依赖：
    ```bash
    pip install -r requirements.txt
    ```
4. 运行主程序：
    ```bash
    python main.py
    ```

## 项目来源
本项目基于[Frica01](https://github.com/Frica01)的GitHub开源项目[WeChatMassTool](https://github.com/Frica01/WeChatMassTool)进行修改，感谢原作者的开源项目提供的基础功能。
