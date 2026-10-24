@echo off
chcp 65001 >nul
title 托摆 OPC 全链路开张助手
cd /d "%~dp0"
if not exist .venv (
    echo [初始化] 首次运行：创建虚拟环境并安装依赖...
    "C:\Users\44162\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
    ".venv\Scripts\pip.exe" install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)
echo [启动] 托摆面板：http://localhost:8501
".venv\Scripts\streamlit.exe" run app.py --server.port 8501
pause
