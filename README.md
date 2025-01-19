# Easy Agents

## 项目介绍
这个项目旨在提供简易的agent应用程序，利用本项目，你可以学习到
* `Agent State`, `workflow`, `node`的含义；
* agent之间的消息传递方式；
* 一个简易的agent程序结构。

本项目包含了两个agent实例：
* exercise management Agents: 结合历史行为信息，可以提供次日的锻炼计划；
* project management Agents: 通过定义的项目定义和成员信息，进行项目管理。



## QuickStart
### 环境准备
1. 克隆或下载项目代码到本地。
    ```
    ```

2. 确保已安装所需的依赖库，可以使用以下命令安装：
    ```bash
    pip install -r requirements.txt
    ```

### 环境变量
准备glm 的api_key 并保存到`.env`文件中

### 其他必要文件
为了运行project management Agents 需要准备以下文件：
* `project_description.txt`: 描述你的项目目标
* `team.csv`: 定义项目组员以及各自的背景描述

为了运行exercise management Agents 需要准备以下文件：
* `behavior_history.csv`: 包含了 `date`, `tasks`, `duration`, `intensity`, `calories`, `mood`, `sleep` 表头

### 运行结果
