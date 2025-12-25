# NyxGo项目简介

NyxGo**项目本身是为**NyxBot**定制的引导脚本，与**NyxBot**环境配置及其启动关联，该项目会在**/usr/lib**文件夹里面创建一个名为**nyxgo_venv**的文件夹作为虚拟环境防止污染系统，脚本提供**基础运行环境**的配置、**QQ机器人框架**的安装以及**NyxBot**的启动配置

# 运行准备

  - 目前仅支持**Debian系**以及**RedHat系**的**标准Linux系统**
 
    - **Debian系**：以**apt**作为包管理器的，如**Debian本体/Ubuntu/Kali/Deepin/Mint**等

    - **RedHat系**：以**dnf/yum**作为包管理器的，如**RedHat本体（即RHEL）/Fedora/CentOS/Rocky/ClearOS**等

      - **epel-release源**：部分发行版例如**Rocky**需要安装该源，输入`sudo dnf install -y epel-release`以安装

  - **Python**环境配置

    - 命令行输入`python3 --version`即可查看当前环境下的Python版本，要求为**Python3.10.x**及其以上版本，若高于，则继续跳过此条；若低于，一般可通过系统包管理器来安装，推荐**Python3.11.x**，常见包名为`python3.11`，安装例子：`sudo apt install -y python3.11`/`sudo dnf install python3.11`，安装后需要重新链接，命令行输入`sudo ln -sf /usr/bin/python3.11 /usr/bin/python && ln -sf /usr/bin/python3.11 /usr/bin/python3`，这样就完成Python配置了

  - **确保网络通畅**：安装过程中确保网络**稳定**，**波动小**，防止**下载**/**请求**等网络操作意外中断
    
# 项目用法

  - **start.sh**：启动脚本，输入`chmod +x ./start.sh`赋予权限后再输入`bash ./start.sh`即可执行脚本

  - **kill.sh**：终止服务脚本，输入`chmod +x ./kill.sh`赋予权限后再输入`bash ./kill`即可终止服务进程

  - **教学视频**：新手可以点击这里观看[**使用教学视频**](https://b23.tv/Yf52q6a)

# NyxBot项目

  - Warframe状态查询机器人，部署简易，功能丰富，更新及时，这里是[**项目地址**](https://github.com/KingPrimes/NyxBot)

# OneBot协议端项目（即QQ机器人框架）

  - **NapCat**：这里是[**项目地址**](https://github.com/NapNeko/NapCatQQ)
