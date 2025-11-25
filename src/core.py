#!/usr/lib/nyxbot_venv/bin/python3 env
import os
import sys
import httpx
import json
import subprocess as sp
import shutil
from datetime import datetime
from platform import machine
from uuid import uuid4
from zipfile import ZipFile
from pathlib import Path
from inquirer import Text, List, Checkbox, Confirm, Path, prompt
from inquirer.errors import ValidationError
from inquirer.questions import Question
from rich.panel import Panel
from rich.progress import Progress
from rich import print as rprint


__version__ = "0.1"
# 日志函数
date = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
info = lambda message: rprint(f"[bold][green][{date()} INFO] {message}[/green][/bold]")
warn = lambda message: rprint(f"[bold][yellow][{date()} WARN] {message}[/yellow][/bold]")
error = lambda message: rprint(f"[bold][red][{date()} ERROR] {message}[/red][/bold]")
# 直接返回True的装饰器，测试用
all_true = lambda _: lambda: True
# 直接返回False的装饰器，同上
all_false = lambda _: lambda: False
pkgm = None # 初始化使用的包管理器判断变量


def checkout_pkgm() -> bool:
    global pkgm
    if os.path.exists("/bin/apt") or os.path.exists("/usr/bin/apt"):
        info("使用apt包管理器")
        pkgm = "apt"
    elif os.path.exists("/bin/dnf") or os.path.exists("/usr/bin/dnf"):
        info("使用dnf包管理器")
        pkgm = "dnf"
    elif os.path.exists("/bin/yum") or os.path.exists("/usr/bin/yum"):
        info("使用yum包管理器")
        pkgm = "yum"
    else:
        error("暂不支持的系统啊")
        return False
        
    return True


def checkout_null(target: str) -> bool:
    # 非空检测
    if not target:
        raise ValidationError("", reason="啥都没输入啊")


def checkout_path(_, current) -> bool:
    if not os.path.exists(current):
        raise ValidationError("", reason="这个路径无效啊")
        
    return True


def checkout_port(_, current) -> bool:
    checkout_null(current)
    
    # 检查是否为数字
    if not current.isdigit():
        raise ValidationError("", reason="端口号必须是数字啊")
    
    # 检查端口范围
    if not (0 <= int(current) < 65536):
        raise ValidationError("", reason="端口必须在0-65535范围内啊")
    
    return True


def ask(questions):
    return tuple(prompt((questions,)).values())[0]


def downloader(url: str, save_path: str) -> bool:
    # 利用rich的进度条来进行文件下载的显示，用httpx库来进行下载
    try:
        with httpx.stream("GET", url, follow_redirects=True) as response:
            with Progress() as progress:
                task = progress.add_task("下载必要文件中", total=int(response.headers.get("Content-Length", 0)))
                with open(save_path, "wb") as wb:
                    for chunk in response.iter_bytes():
                        wb.write(chunk)
                        progress.update(task, advance=len(chunk))
    except httpx.HTTPError:
        error(f"下载失败了，要确保网络稳定啊！")
        return False

    return True


# @all_true
def install_jdk() -> bool:
    try:
        target_pkg = {
            "apt": ("openjdk-21-jdk",),
            "dnf": ("java-21-openjdk",)
        }
        target_pkg["yum"] = target_pkg["dnf"]
        sp.run((pkgm, "install", "-y", *target_pkg[pkgm]), check=True)
    except sp.CalledProcessError:
        error("openjdk21安装失败了，只能你自己先装上再重启脚本了")
        return False
        
    info("openjdk21装完了")
    return True


def checkout_structure() -> str:
    match machine().lower():
        case "x86_64" | "amd64" | "x64":
            return "x64"
        case "arm64" | "aarch64" | "armv7l" | "armv8l":
            return "arm"

    return "unknown"


# @all_true
def install_qq() -> bool:
    # 下载Linux版QQ
    info("开始帮你搞Linux版的QQ……")
    target_pkg = {
        "apt": {
            "x64": "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.21_251114_amd64_01.deb",
            "arm":  "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.21_251114_arm64_01.deb",
            "suffix": ".deb"
        },
        "dnf": {
            "x64": "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.21_251114_x86_64_01.rpm",
            "arm": "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.21_251114_aarch64_01.rpm",
            "suffix": ".rpm"
        }
    }
    target_pkg["yum"] = target_pkg["dnf"]
    save_path = f"linuxqq-{uuid4()}{target_pkg[pkgm]['suffix']}"
    if not downloader(target_pkg[pkgm][checkout_structure], save_path):
        return False

    info("我装一下它……")
    try:
        sp.run((pkgm, "install", "-y", save_path), check=True)
    except sp.CalledProcessError:
        error("我靠，装失败了，你自己装试试看")
        return False

    info(f"Linux版QQ装完了")
    os.remove(save_path)
    return True


# @all_true
def install_napcat() -> bool:
    save_path = f"/tmp/napcat-{uuid4()}.zip"
    info("开始帮你搞Xvfb和xauth……")
    target_pkg = {
        "apt": ("xvfb", "xauth"),
        "dnf": ("xorg-x11-server-Xvfb", "xorg-x11-xauth")
    }
    target_pkg["yum"] = target_pkg["dnf"]
    try:
        sp.run((pkgm, "install", "-y", *target_pkg[pkgm]), check=True)
    except sp.CalledProcessError:
        error("安装xvfb和xauth时失败了，只能靠你自己了或者求助吧")
        return False

    info("开始帮你搞NapCat……")
    shutil.copy("./loadNapCat.cjs", "/opt/QQ/resources/app")

    if not downloader("https://github.com/NapNeko/NapCatQQ/releases/download/v4.9.74/NapCat.Shell.zip", save_path):
            return False

    info("开始解压NapCat压缩包……")
    if not os.path.exists("/opt/QQ/resources/app/napcat"):
        shutil.unpack_archive(save_path, "/opt/QQ/resources/app/napcat")
    else:
        warn("目标目录已经有安排好的NapCat文件了，那我就不再解压了")

    info("开始处理package.json文件……")
    with open("/opt/QQ/resources/app/package.json", "r+") as ra:
        data = json.loads(ra.read())
        data["main"] = "./loadNapCat.cjs"
        ra.seek(0)
        ra.write(json.dumps(data))
        ra.truncate()

    info("NapCat搞定，输入“xvfb-run -a qq --no-sandbox -q <你的QQ号>”来启动，会让你扫码登录，随后在它给的WebUI地址中配置一个WS服务器，消息格式选Array，然后自己输入一个端口，记住这个地址，例如6666端口地址就是ws://127.0.0.1:6666，然后在NyxBot的WebUI里面选择客户端模式去连接它就行了")
    os.remove(save_path)
    return True


def install_llonebot() -> bool:
    # TODO: LLOneBot实现
    ...


# @all_true
def env_check() -> bool:
    # 检查系统环境
    info("让我看看你环境正不正常啊……")
    if os.name == "posix":
        if not checkout_pkgm():
            return
            
        if checkout_structure() == "unknown":
            error("暂不支持你这架构啊")
            return False
            
        if not (os.path.exists("/usr/bin/java") or os.path.exists("/bin/java")):
            warn("没有java啊，我给你装个openjdk21吧")
            if not install_jdk():
                return False
            
        if not (os.path.exists("/bin/qq") or os.path.exists("/usr/bin/qq")):
            warn("你没装QQ啊，我帮你装一个吧，这是QQ机器人框架运行的必须条件啊")
            if not install_qq():
                return False
            
        info("环境没问题，继续")
        return True
    else:
        error("目前仅支持Debian系统啊也就是用apt包管理器的，等我再开发其它的吧")
        return False


def main():
    # 主函数，用于引导NyxBot的安装
    rprint(Panel(
        "Warframe状态查询机器人，由著名架构师王小美开发，部署简易，更新勤奋，让我们追随她！\n请在安装过程中确保网络通畅啊！\n王小美个人博客地址：https://kingprimes.top",
        title="NyxBot引导脚本",
        subtitle=f"版本：{__version__}",
        border_style=" bold cyan"
    ))
    if not ask(Confirm("choice", message="要开始吗？", default=True)):
        return

    if not env_check():
        return
    
    if not ask(Confirm("qqframe", message="有没有装QQ机器人框架？这是NyxBot和QQ对话的基础啊", default=True)):
        info("那你就选一下，我帮你装一个")
        match ask(List("frame", message="选择一个QQ机器人框架（推荐NapCat）", choices=["NapCat", "LLOneBot"])):
            case "NapCat":
                if not install_napcat():
                    return

            case "LLOneBot":
                if not install_llonebot():
                    return

            case _:
                error("出现了点让你我始料不及的情况啊，报告一下开发者吧")
                return

    ask(Text("_", message="这里我会等你多开终端启动好QQ机器人框架，好了就随便输入点什么，然后继续配置NyxBot吧"))
    nyxbot_path = ask(Path("nyxbot_path", message="请输入NyxBot.jar的路径", validate=checkout_path))
    info("配置NyxBot……")
    choices = ask(Checkbox("functions", message="请选择你要配置的选项", choices=(
        "NyxBot启动时的端口号",
    )))
    command = ["java", "-jar", nyxbot_path]
    for choice in choices:
        match choice:
            case "NyxBot启动时的端口号":
                command.append(f"--server.port={ask(Text('nyxbot_port', message='请输入NyxBot启动时端口号（默认8080）', default=8080, validate=checkout_port))}")
            case _:
                pass

    info("配置完成，启动NyxBot……")
    info("在启动完成后可以根据其终端的输出查看WebUI（也就是配置NyxBot的界面）地址和端口号以及账号密码，记得牢记哦！")
    try:
        sp.run(command, check=True)
    except sp.CalledProcessError:
        error(f"启动失败，你只能自己来了")
        return


if __name__ == "__main__":
    main()
