#!/bin/python3 env
import os
import sys
import httpx
import json
import subprocess as sp
from platform import machine
from uuid import uuid4
from zipfile import ZipFile
from pathlib import Path
# 尝试导入inquirer，如果失败则提供替代方案
try:
    from inquirer import Text, List, Checkbox, Confirm, Path, prompt
    from inquirer.errors import ValidationError
    from inquirer.questions import Question
    INQUIRER_AVAILABLE = True
except ImportError as e:
    print(f"警告: inquirer库导入失败: {e}")
    print("将使用简化的命令行交互")
    INQUIRER_AVAILABLE = False
    
    # 简化的替代函数
    class ValidationError(Exception):
        pass
    
    def simple_prompt(message, default=None, validator=None):
        """简化的提示输入函数"""
        while True:
            if default is not None:
                user_input = input(f"{message} (默认: {default}): ").strip()
                if not user_input:
                    user_input = default
            else:
                user_input = input(f"{message}: ").strip()
            
            if validator:
                try:
                    if validator(user_input):
                        return user_input
                except ValidationError as e:
                    print(f"错误: {e}")
                    continue
            else:
                return user_input
    
    def simple_confirm(message, default=True):
        """简化的确认函数"""
        default_str = "Y/n" if default else "y/N"
        while True:
            response = input(f"{message} ({default_str}): ").strip().lower()
            if not response:
                return default
            return response in ['y', 'yes', '是', 'true', '1']
from rich.panel import Panel
from rich.console import Console
from rich.progress import Progress


__version__ = "0.1"
# rich的全局控制台对象实例
console = Console()
# 字体基础颜色，这里为加粗
BASE = "bold"
# 日志函数
info = lambda message: console.print(message, style=f"{BASE} green")
warn = lambda message: console.print(message, style=f"{BASE} yellow")
error = lambda message: console.print(message, style=f"{BASE} red")
# 直接返回True的装饰器，测试用
all_true = lambda _: lambda: True
# 直接返回False的装饰器，同上
all_false = lambda _: lambda: False


def check_null(target: str) -> bool:
    # 非空检测
    if not target:
        raise ValidationError("", reason="啥都没输入啊")


def check_path(_, current) -> bool:
    if not os.path.exists(current):
        raise ValidationError("", reason="这个路径无效啊")
        
    return True


def check_port(_, current) -> bool:
    check_null(current)
    
    # 检查是否为数字
    if not current.isdigit():
        raise ValidationError("", reason="端口号必须是数字啊")
    
    # 检查端口范围
    if not (0 <= int(current) < 65536):
        raise ValidationError("", reason="端口必须在0-65535范围内啊")
    
    return True


def ask(questions):
    """统一的提问函数，支持inquirer和简化模式"""
    if INQUIRER_AVAILABLE:
        return tuple(prompt((questions,)).values())[0]
    else:
        # 简化模式处理
        if hasattr(questions, 'message'):
            return simple_prompt(questions.message, 
                               getattr(questions, 'default', None),
                               getattr(questions, 'validate', None))
        elif isinstance(questions, (list, tuple)) and len(questions) > 0:
            question = questions[0]
            return simple_prompt(question.message,
                               getattr(question, 'default', None),
                               getattr(question, 'validate', None))
        else:
            return input("请输入: ")


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
        error(f"下载失败，你手动下载这个文件{url}然后存到{save_path}")
        return False

    return True


# @all_true
def install_jdk() -> bool:
    try:
        sp.run(("apt", "install", "-y", "openjdk-21-jdk"), check=True)
    except sp.CalledProcessError:
        error("openjdk21安装失败了，只能你自己先装上再重启脚本了")
        return False
        
    info("openjdk21装完了")
    return True


def check_structure() -> str:
    structure = machine().lower()
    if structure in ("x86_64", "amd64", "x64"):
        return "x64"

    if structure in ("arm64", "aarch64", "armv7l", "armv8l"):
        return "arm"

    if structure in ("mips", "mips64"):
        return "mips"

    return "unknown"


# @all_true
def install_qq() -> bool:
    # 下载Linux版QQ
    save_path = f"/tmp/linuxqq-{uuid4()}.deb"
    info("开始帮你搞Linux版的QQ……")
    target_url = ""
    match check_structure():
        case "x64":
            target_url = "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.21_251114_amd64_01.deb"
        case "arm":
            target_url = "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.21_251114_arm64_01.deb"
        case "mips":
            target_url = "https://dldir1v6.qq.com/qqfile/qq/QQNT/Linux/QQ_3.2.21_251114_mips64el_01.deb"
        case "unknown":
            error("我靠，我不知道你这机器是啥架构的，你自己去下载吧")
            return False
        case _:
            error("神人啊，你这机器我还真不知道")
            return False

    if not downloader(target_url, save_path):
        return False

    info("我装一下它……")
    try:
        sp.run(("apt", "install", "-y", save_path), check=True)
    except sp.CalledProcessError:
        error("我靠，装失败了，你自己装试试看")
        return False

    info(f"Linux版QQ装完了")
    os.remove(save_path)
    return True


# @all_true
def install_napcat() -> bool:
    save_path = f"/tmp/napcat-{uuid4()}.zip"
    info("开始帮你搞xvfb和xauth……")
    try:
        sp.run(("apt", "install", "xvfb", "xauth"), check=True)
    except sp.CalledProcessError:
        error("安装xvfb和xauth时失败了，只能靠你自己了或者求助吧")
        return False

    info("开始帮你搞NapCat……")
    with open("/opt/QQ/resources/app/loadNapCat.cjs", "w") as w:
        w.write("""const fs = require("fs");
const path = require("path");
const CurrentPath = path.dirname(__filename);
const hasNapcatParam = process.argv.includes("--no-sandbox");
if (hasNapcatParam) {
    (async () => {
        await import("file://" + path.join(CurrentPath, "./napcat/napcat.mjs"));
        // await import("file://" + "/path/to/napcat/napcat.mjs");
        // 需要修改napcat的用户，在"/path/to/napcat"段写自己的napcat文件夹位置，并注释path.join所在行
    })();
} else {
    require("./application/app_launcher/index.js");
    setTimeout(() => {
        global.launcher.installPathPkgJson.main = "./application.asar/app_launcher/index.js";
    }, 0);
}""")

    if not downloader("https://github.com/NapNeko/NapCatQQ/releases/download/v4.9.74/NapCat.Shell.zip", save_path):
            return False

    info("开始解压NapCat压缩包……")
    if not os.path.exists("/opt/QQ/resources/app/napcat"):
        with ZipFile(save_path, "r") as zip_ref:
            zip_ref.extractall("/opt/QQ/resources/app/napcat")
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
        if not (os.path.exists("/usr/bin/apt") or os.path.exists("/bin/apt")):
            error("没有apt包管理器啊，你这是不是非标准Debian系的系统啊")
            return False
            
        if not (os.path.exists("/usr/bin/java") or os.path.exists("/bin/java")):
            warn("没有java啊，我给你装个openjdk21吧")
            if not install_jdk():
                return False
            
        if not (os.path.exists("/bin/qq") or os.path.exists("/usr/bin/qq")):
            warn("你没装QQ啊，我帮你装一个吧，这是QQ机器人框架运行的必须条件啊")
            if not install_qq():
                return False
            
        return True
    else:
        error("目前仅支持Debian系统啊也就是用apt包管理器的，等我再开发其它的吧")
        return False


def main():
    # 主函数，用于引导NyxBot的安装
    if INQUIRER_AVAILABLE:
        console.print(Panel(
            "Warframe状态查询机器人，由著名架构师王小美开发，部署简易，更新勤奋，让我们追随她！\n请在安装过程中确保网络通畅啊！\n王小美个人博客地址：https://kingprimes.top",
            title="NyxBot引导脚本",
            subtitle=f"版本：{__version__}",
            border_style=" bold cyan"
        ))
        if not ask(Confirm("choice", message="要开始吗？", default=True)):
            return
    else:
        print("=" * 60)
        print("NyxBot引导脚本 v{}".format(__version__))
        print("=" * 60)
        print("Warframe状态查询机器人，由著名架构师王小美开发")
        print("请在安装过程中确保网络通畅！")
        print("王小美个人博客地址：https://kingprimes.top")
        print("=" * 60)
        
        if not simple_confirm("要开始吗？", default=True):
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
    nyxbot_path = ask(Path("nyxbot_path", message="请输入NyxBot.jar的路径", validate=check_path))
    info("配置NyxBot……")
    choices = ask(Checkbox("functions", message="请选择你要配置的选项", choices=(
        "NyxBot启动时的端口号",
    )))
    command = ["java", "-jar", nyxbot_path]
    for choice in choices:
        match choice:
            case "NyxBot启动时的端口号":
                command.append(f"--server.port={ask(Text('nyxbot_port', message='请输入NyxBot启动时端口号（默认8080）', default=8080, validate=check_port))}")
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