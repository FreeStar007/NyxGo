#!/bin/bash
if [ "$EUID" -eq 0 ]; then
    echo "不能以root用户的身份运行啊！"
    exit
fi
readonly NUSER=$USER
readonly TEMP_PYTHON="$(command -v python3)"
readonly TARGET="/usr/lib/nyxgo_venv"
readonly TEMP_HOME="$TARGET/bin"
pkgm=""
if command -v apt &> /dev/null; then
    pkgm="apt"
elif command -v dnf &> /dev/null; then
    pkgm="dnf"
elif command -v yum &> /dev/null; then
    pkgm="yum"
else
    echo "暂不支持的系统"
    exit
fi
if [ ! -d "$TARGET" ]; then
    echo "初始化运行环境……"
    if ! command -v git &> /dev/null; then
        echo "安装git……"
        sudo "$pkgm" install -y git
    fi
    if ! "$TEMP_PYTHON" -m pip --help &> /dev/null; then
        echo "安装pip3……"
        sudo "$pkgm" install -y python3-pip
    fi
    if ! "$TEMP_PYTHON" -m venv --help &> /dev/null; then
        echo "安装venv……"
        sudo "$pkgm" install -y python3-venv
    fi
    sudo "$TEMP_PYTHON" -m venv "$TARGET"
    sudo chown -R "$NUSER:$NUSER" "$TARGET"
    sudo chmod -R +x "$TARGET"
    "$TEMP_HOME/pip3" install -r ./requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
fi
echo "启动脚本……"
"$TEMP_HOME/python3" ./core.py
