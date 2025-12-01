#!/usr/lib/nyxgo_venv/bin/python3 env
import os
import httpx
import json
import yaml
import subprocess as sp
import shutil
from typing import Any
from enum import Enum
from datetime import datetime
from platform import machine
from uuid import uuid4
from pathlib import Path
from inquirer import Text, List, Checkbox, Confirm, Path, prompt
from inquirer.errors import ValidationError
from inquirer.questions import Question
from rich import print as rprint
from rich.panel import Panel
from rich.progress import Progress


# 选项枚举类
class Choices(Enum):
    NAPCAT = "NapCat"
    STARTING_PORT = "启动时的端口号"
    STARTING_MODE = "启动时的连接模式"
    CONNECTION_URL = "启动时连接的URL"
    END_POINT = "启动时被连接的URL端点"
    TOKEN = "启动时连接/被连接的token"
    SERVER_MODE = "Server模式"
    CLIENT_MODE = "Client模式"


# 日志函数
date = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
info = lambda message: rprint(f"[bold][green][{date()} INFO] {message}[/green][/bold]")
warn = lambda message: rprint(f"[bold][yellow][{date()} WARN] {message}[/yellow][/bold]")
error = lambda message: rprint(f"[bold][red][{date()} ERROR] {message}[/red][/bold]")
pkgm = None # 初始化使用的包管理器判断变量
structure = None # 初始化架构
locate_file = "locate.yaml" # 定位文件
locate_dir = "./data" # 定位文件夹
locate_target = f"{locate_dir}/{locate_file}"
# 全局下载资源URL文件
with open("./source.json", "r") as r:
    source = json.load(r)


# 命令输入
def shell(command: str, error_info: str, complex_mode=False) -> bool:
    try:
        sp.run(command.strip().split(" ") if not complex_mode else command, check=True, shell=complex_mode)
    except sp.CalledProcessError:
        error(error_info)
        return False
        
    return True
    

# 文件删除
def remove(target: str, error_info: str, append="") -> bool:
    return shell(f"sudo rm -f {target}{append}", error_info)


# 文件移动
def move(source: str, target: str, error_info: str) -> bool:
    return shell(f"sudo mv {source} {target}", error_info)
    

# 文件复制
def copy(source: str, target: str, error_info: str, append="") -> bool:
    return shell(f"sudo cp -f {source} {target}{append}", error_info)


# 检测包管理器
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
    
    
# 检测架构
def checkout_structure() -> bool:
    global structure
    match machine().lower():
        case "x86_64" | "amd64" | "x64":
            info("x64架构")
            structure = "x64"
        case "arm64" | "aarch64" | "armv7l" | "armv8l":
            info("arm架构")
            structure = "arm"
        case _:
            error("不支持你这架构啊")
            return False
            
    return True


# 编辑定位文件
def edit_locate(key, value) -> bool:
    global locate_dir, locate_file, locate_target
    if not (os.path.exists(locate_dir) and os.path.isdir(locate_dir)):
        error("没找到data文件夹或者已经有叫data的文件了，把它弄走然后启动一次NyxBot来初始化data文件夹吧")
        return False
        
    if os.path.exists(locate_target):
        locate_file = locate_target

    try:
        with open(locate_file, "r") as r:
            locate_data = yaml.safe_load(r)
            locate_data[key] = value
            
        with open(locate_target, "w") as w:
            yaml.safe_dump(locate_data, w)
    except (OSError, FileNotFoundError) as e:
        error(f"配置文件编辑失败了啊，报告开发者吧：{e}")
        return False

    return True


# 检测输入内容
def checkout_null(target: str) -> bool:
    if not target:
        raise ValidationError("", reason="啥都没输入啊")


# 输入路径检测
def checkout_path(_, current) -> bool:
    if not os.path.exists(current):
        raise ValidationError("", reason="这个路径无效啊")
        
    return True


# 检测输入端口
def checkout_port(_, current) -> bool:
    checkout_null(current)
    
    # 检查是否为数字
    if not current.isdigit():
        raise ValidationError("", reason="端口号必须是数字啊")
    
    # 检查端口范围
    if not (0 <= int(current) < 65536):
        raise ValidationError("", reason="端口必须在0-65535范围内啊")
    
    return True


# 检测URL
def checkout_url(_, current) -> bool:
    checkout_null(current)
    
    # 检查是否为以http/https/ws/wss开头
    if not current.startswith(("http://", "https://", "ws://", "wss://")):
        raise ValidationError("", reason="URL必须以http/https/ws/wss开头啊")

    return True
    

# 单次提问简化
def ask(question) -> Any:
    return tuple(prompt((question,)).values())[0]


# 下载器
def downloader(url: str, saved_path: str, downloading_info: str) -> bool:
    # 利用rich的进度条来进行文件下载的显示，用httpx库来进行下载
    try:
        with httpx.stream("GET", url, follow_redirects=True) as response:
            with Progress() as progress:
                task = progress.add_task(downloading_info, total=int(response.headers.get("Content-Length", 0)))
                with open(saved_path, "wb") as wb:
                    for chunk in response.iter_bytes():
                        wb.write(chunk)
                        progress.update(task, advance=len(chunk))
    except httpx.HTTPError:
        error(f"{saved_path}下载失败了，要确保网络稳定啊！")
        return False

    return True


def install_jdk() -> bool:
    target_pkg = {
        "apt": "openjdk-21-jdk",
        "dnf": "java-21-openjdk"
    }
    target_pkg["yum"] = target_pkg["dnf"]
    if not shell(f"sudo {pkgm} install -y {target_pkg[pkgm]}", "openjdk21安装失败了，只能你自己先装上再重启脚本了"):
        return False
        
    info("openjdk21装完了")
    return True


# 安装Linux版QQ
def install_qq() -> bool:
    info("开始帮你搞Linux版QQ……")
    target_pkg = source["qq"]
    target_pkg["yum"] = target_pkg["dnf"]
    saved_path = f"/tmp/linuxqq-{uuid4()}{target_pkg[pkgm]['suffix']}"
    if not downloader(target_pkg[pkgm][structure], saved_path, "Linux版QQ文件下载中……"):
        return False

    info("我装一下它……")
    if not shell(f"sudo {pkgm} install -y {saved_path}", "我靠，装失败了，你自己装试试看"):
        return False
        
    info(f"Linux版QQ装完了")
    remove(saved_path, "临时文件移除失败了啊")
    return True


# 安装NapCat
def install_napcat() -> bool:
    saved_path = f"/tmp/napcat-{uuid4()}.zip"
    info("开始帮你搞Xvfb和xauth……")
    target_pkg = {
        "apt": "xvfb xauth",
        "dnf": "xorg-x11-server-Xvfb xorg-x11-xauth"
    }
    target_pkg["yum"] = target_pkg["dnf"]
    if not shell(f"sudo {pkgm} install -y {target_pkg[pkgm]}", "安装xvfb和xauth时失败了，只能靠你自己了或者求助吧"):
        return False
        
    info("开始帮你搞NapCat……")
    if not copy("./loadNapCat.cjs", "/opt/QQ/resources/app", "配置文件复制失败了啊，报告开发者吧"):
        return False

    if not downloader(source["napcat"], saved_path, "NapCat文件下载中……"):
        if not remove(saved_path, "缓存文件删除失败，我重新命名下"):
            saved_path = f"/tmp/napcat-{uuid4()}.zip"

        warn("我试试git国内源……")
        target_git = f"/tmp/napcat-git-{uuid4()}"
        if shell(f"git clone {source['napcat_git']} {target_git}", "git国内源失败，联系开发者吧"):
            if not move(f"{target_git}/NapCat.Shell.zip", saved_path, "文件移动失败了，得找开发者啊"):
                return False

            remove(target_git, "文件夹删除失败了，不过无伤大雅", append=" -r")
        else:
            return False

    info("开始解压NapCat压缩包……")
    target_dir = "/opt/QQ/resources/app/napcat"
    if not os.path.exists(target_dir):
        shutil.unpack_archive(saved_path, f"{saved_path}-temp")
        if not move(f"{saved_path}-temp", target_dir, "我靠，文件移动失败了，找开发者去"):
            return False
    else:
        warn("目标目录已经有安排好的NapCat文件了，那我就不再解压了")

    info("开始处理package.json文件……")
    package_file = "/opt/QQ/resources/app/package.json"
    if not shell(r"""sudo sed -i 's/"main": ".*\/index.js"/"main": ".\/loadNapCat.cjs"/' /opt/QQ/resources/app/package.json""", "package.json处理失败了啊", complex_mode=True):
        return False

    info("NapCat搞定，输入“xvfb-run -a qq --no-sandbox -q <你的QQ号>”来启动，会让你扫码登录，随后在它给的WebUI地址中配置一个WS服务器，消息格式选Array，然后自己输入一个端口，记住这个地址，例如6666端口地址就是ws://127.0.0.1:6666，然后在NyxBot的WebUI里面选择客户端模式去连接它就行了")
    remove(saved_path, "删除临时文件失败了啊")
    return True


# 检测环境
def checkout_env() -> bool:
    # 检查系统环境
    info("让我看看你环境正不正常啊……")
    if os.name == "posix":
        if not checkout_pkgm():
            return False
            
        if not checkout_structure():
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


# 主函数
def main() -> None:
    rprint(Panel(
        "Warframe状态查询机器人，由著名架构师王小美开发，部署简易，更新勤奋，让我们追随她！\n请在安装过程中确保网络通畅啊！\n王小美个人博客地址：https://kingprimes.top",
        title="NyxBot引导脚本",
        subtitle="快速部署NyxBot",
        border_style="bold cyan"
    ))
    if not ask(Confirm("choice", message="要开始吗？", default=True)):
        return

    if not checkout_env():
        return
    
    if not ask(Confirm("qqframe", message="有没有装QQ机器人框架？这是NyxBot和QQ对话的基础啊", default=True)):
        info("那你就选一下，我帮你装一个")
        match ask(List("frame", message=f"选择一个QQ机器人框架（推荐{Choices.NAPCAT.value}）", choices=(
            Choices.NAPCAT.value,
            ))):
            case Choices.NAPCAT.value:
                if not install_napcat():
                    return
            case _:
                return

    ask(Text("_", message="这里我会等你多开终端启动好QQ机器人框架，好了就随便输入点什么，然后继续配置NyxBot吧"))
    nyxbot_path = ask(Path("nyxbot_path", message="请输入NyxBot.jar的路径", validate=checkout_path))
    info("配置NyxBot……")
    choices = ask(Checkbox("functions", message="请选择你要配置的选项（默认不需要勾选，到WebUI里面配置就行）", choices=(
        Choices.STARTING_PORT.value,
        Choices.STARTING_MODE.value,
        Choices.CONNECTION_URL.value,
        Choices.END_POINT.value,
        Choices.TOKEN.value
        )))
    command = ["java", "-jar", nyxbot_path]
    for choice in choices:
        match choice:
            case Choices.STARTING_PORT.value:
                command.append(f"--server.port={ask(Text('nyxbot_port', message=f'请输入{Choices.STARTING_PORT.value}（默认8080）', default=8080, validate=checkout_port))}")
            case Choices.STARTING_MODE.value:
                match ask(List("nyxbot_mode", message=f"请选择{Choices.STARTING_MODE.value}（推荐Client模式）", choices=(
                    Choices.SERVER_MODE.value,
                    Choices.CLIENT_MODE.value
                    ))):
                    case Choices.SERVER_MODE.value:
                        if not edit_locate("isServerOrClient", True):
                            return
                    case Choices.CLIENT_MODE.value:
                        if not edit_locate("isServerOrClient", False):
                            return
                    case _:
                        return
            case Choices.CONNECTION_URL.value:
                    if not edit_locate("wsClientUrl", ask(Text("wsClientUrl", message=f"请输入{Choices.CONNECTION_URL.value}（默认ws://127.0.0.1:8081）", default="ws://127.0.0.1:8081", validate=checkout_url))):
                        return
            case Choices.END_POINT.value:
                if not edit_locate("wsServerUrl", ask(Text("wsServerUrl", message=f"请输入{Choices.END_POINT.value}（默认/ws/shiro，那么连接NyxBot时URL就是ws://127.0.0.1:<你启动时配置的端口>/ws/shiro）", default="/ws/shiro"))):
                    return
            case Choices.TOKEN.value:
                if not edit_locate("token", ask(Text("token", message=f"请输入{Choices.TOKEN.value}（默认为空）"))):
                    return
            case _:
                return

    info("配置完成，启动NyxBot……")
    info("在启动完成后可以根据其终端的输出查看WebUI（也就是配置NyxBot的界面）地址和端口号以及账号密码，记得牢记哦！")
    shell(" ".join(command), "启动失败，只能你自己来了")


if __name__ == "__main__":
    main()
