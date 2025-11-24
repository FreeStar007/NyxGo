#!/bin/bash
if [ "$EUID" -ne 0 ]; then
    echo "要以root用户的身份运行啊!"
    exit
fi
apt install python3-venv
TEMP_PYTHON=/usr/bin/python3
TARGET=/usr/lib/nyxbot_venv
TEMP_HOME=$TARGET/bin
if [ ! -d "$TARGET" ]; then
    echo "初始化虚拟环境……"
    $TEMP_PYTHON -m venv $TARGET
    chmod +x -R $TARGET
    $TEMP_HOME/pip install -r requirements.txt
fi
$TEMP_HOME/python ./core.py
