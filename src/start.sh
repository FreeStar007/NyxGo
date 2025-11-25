#!/bin/bash
if [ "$EUID" -ne 0 ]; then
    echo "要以root用户的身份运行啊!"
    exit
fi
BASE="/bin"
USER_BASE="/usr/bin"
PKGM=""
if [ -f "$BASE/apt" -o -f "$USER_BASE/apt" ]; then
    PKGM="apt"
elif [ -f "$BASE/dnf" -o -f "$USER_BASE/dnf" ]; then
    PKGM="dnf"
elif [ -f "$BASE/yum" -o -f "$USER_BASE/yum" ]; then
    PKGM="yum"
else
    echo "暂不支持的系统"
    exit
fi
$PKGM install python3-venv
TEMP_PYTHON=/usr/bin/python3
TARGET=/usr/lib/nyxbot_venv
TEMP_HOME=$TARGET/bin
if [ ! -d "$TARGET" ]; then
    echo "初始化虚拟环境……"
    $TEMP_PYTHON -m venv $TARGET
    chmod +x -R $TARGET
    $TEMP_HOME/pip3 install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
fi
$TEMP_HOME/python3 ./core.py
