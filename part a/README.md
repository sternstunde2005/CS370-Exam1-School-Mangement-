# Project 3 - Part A School Management System

本交付包使用课程 PDF 推荐列表中的第 3 个项目：

- 原仓库：<https://github.com/zaydkassimi/school-management>
- 固定版本：`cb6035cebfd40da5a244e2671d3a9631018e25a2`
- 技术栈：Python、Flask、Jinja、SQLite、原生 HTML/CSS/JavaScript

当前范围只完成 Part A 第 1-3 项：选定现有系统、配置并成功运行、检查现有功能与数据库/账户/登录。用户要求暂缓的 Part A 第 4 项（至少三个安全弱点或缺失控制）未包含；Part B-E 也未实施。

## Windows 一键启动

1. 如果拿到 ZIP，先完整解压整个文件夹，不能只在压缩包预览中运行。
2. 双击 `01-Start-Website.cmd`。
3. 浏览器打开 <http://127.0.0.1:5000/> 后登录。
4. 使用结束后双击 `02-Stop-Website.cmd`。

此包自带 Windows x64 Python 3.12.10 和全部依赖，不需要另外安装 Python、Node.js、MySQL、Docker 或 XAMPP，也不需要联网。服务器只监听本机 `127.0.0.1`。

## 演示账户

所有学生资料均为虚构。

| 身份 | 登录名 / Email | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `admin` |
| 学生 Alex Demo | `alex.demo@example.test` | `Student123!` |
| 学生 Morgan Example | `morgan.example@example.test` | `Student123!` |
| 学生 Jamie Sample | `jamie.sample@example.test` | `Student123!` |

管理员账号由原项目代码直接识别，不存放在 `users` 表。三个学生账号存放于 SQLite `users` 表。

## 已检查的原有功能

- 管理员和学生登录、学生自行注册、退出登录。
- 管理员查看学生列表，录入或更新模块成绩与缺勤次数。
- 学年、学期、模块、教师与风险级别筛选。
- 学生查看自己的成绩、平均分、排名、缺勤和学习状态。
- Analytics 仪表盘与 performance/risk JSON API。
- CSV、Excel 和 PDF 导出。
- SQLite 交互与 6 张业务表：`users`、`grades`、`absences`、`classes`、`student_class`、`risk_thresholds`。

更完整的 Part A 第 3 项说明见 `docs/Part-A-Application-Review.md`。

## 数据库文件

| 路径 | 用途 |
| --- | --- |
| `website/school.db` | 网站实际读写的 SQLite 数据库 |
| `database/school-demo.sqlite3` | 未经修改的虚构演示数据快照 |
| `database/school-demo.sql` | 可阅读和重建数据库的 SQLite SQL 转储 |

要恢复初始演示数据：先停止网站，将 `database/school-demo.sqlite3` 复制并覆盖为 `website/school.db`，再重新启动。

重新生成演示数据和数据库快照：

```powershell
.\runtime\python.exe .\tools\seed_demo.py
.\runtime\python.exe .\tools\export_database.py
```

`seed_demo.py` 可重复执行；它只补充缺少的虚构演示记录。

## 验证

在项目根目录运行：

```powershell
.\runtime\python.exe .\tools\verify_app.py
```

该检查覆盖数据库结构与演示数据、登录页/注册页、管理员和学生登录、两个仪表盘、API，以及 CSV/Excel/PDF 导出。最近一次结果保存在 `evidence/functional-checks.json`；桌面路径、一键启停和便携运行环境的检查记录保存在 `evidence/package-checks.json`。

`SHA256SUMS.txt` 记录稳定交付文件的 SHA-256 校验值。正常使用时会变化的 `logs/`、`website/school.db` 与 `evidence/functional-checks.json` 不列入清单。

## 使用系统 Python 手动安装

一键启动不需要此步骤。若要自行创建环境，建议使用 Python 3.12：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\website\requirements.txt
Set-Location .\website
..\.venv\Scripts\python.exe app.py
```

然后访问 <http://127.0.0.1:5000/>。`website/requirements.txt` 已按当前源代码修正；完整测试版本见 `requirements-lock.txt`。

若 5000 端口被占用，可在项目根目录手动运行其他端口：

```powershell
.\runtime\python.exe -c "import os,sys; os.chdir('website'); sys.path.insert(0,'.'); from app import app,init_db; init_db(); app.run(host='127.0.0.1',port=5001,debug=False,use_reloader=False)"
```

此时访问 <http://127.0.0.1:5001/>。

## 文件结构

```text
01-Start-Website.cmd        一键启动
02-Stop-Website.cmd         停止本包服务器
03-Open-Guide.cmd           打开图形说明页
START-HERE.html             快速使用说明
website/                    原项目源码、本地兼容修正和实际数据库
database/                   数据库快照与 SQL 转储
docs/                       Part A 功能检查、来源和改动说明
evidence/                   自动功能检查结果
runtime/                    Windows x64 便携 Python 与依赖
tools/                      启停、演示数据、导出和验证脚本
upstream/                   固定提交的原始源码归档与来源记录
```
