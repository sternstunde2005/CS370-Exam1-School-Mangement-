# StudentHub · Project 3 Part A

本文件夹包含可直接运行的网站、SQLite 数据库、源代码、中文安装说明和 Part A 安全评估。只完成 A 部分的应用部署与评估；未开发 B–E 的安全改造。所有演示资料均为虚构。

## 在这台电脑上启动

1. 如果拿到的是 ZIP，先完整解压。不要在压缩包内运行。
2. 双击 `01-Start-Website.cmd`，等待浏览器打开。
3. 网址：<http://127.0.0.1:8000/>，点击 **LOGIN**。
4. 完成演示后双击 `02-Stop-Website.cmd`。只关闭浏览器不会停止后台网站。
5. 双击 `03-Open-Guide.cmd` 可打开图文快速说明 `START-HERE.html`。

此包自带 Windows x64 的 Python 3.12.10、Django 6.0.9、Pillow 12.3.0 及依赖。无需另外安装 Python、MySQL、XAMPP、Docker 或 Node.js，无需管理员权限。页面资源已本地化，运行演示无需联网。启动程序只监听本机 `127.0.0.1`，不会向局域网公开。

| 演示身份 | 用户名 | 密码 |
|---|---|---|
| 管理员 | `admin` | `Admin@12345` |
| 教师 / 工作人员 | `faculty1` | `Faculty@12345` |
| 学生 Alex Demo | `student1` | `Student@12345` |
| 学生 Morgan Example | `student2` | `Student@12345` |
| 学生 Jamie Sample | `student3` | `Student@12345` |

**教师账号说明：** 上游主要按 `is_staff` 判断管理功能。演示教师的 `role=faculty`、`is_staff=True`、`is_superuser=False`，因此使用已有工作人员页面。它具有较广泛的业务管理权限，不是限制到任课课程的独立 RBAC。本次没有实现 Part C。

## 可以展示什么

- 管理员 / 教师：学生目录、查询、创建/编辑/删除学生；院系、专业与课程；成绩录入、费用记录和 CSV 导出。
- 学生：自己的档案、联系方式和地址；成绩、GPA、课程学分；考勤；学费、已缴金额和未缴余额。
- 数据库：3 名学生、2 个院系、2 个专业、3 门课程、5 条已批准选课、3 场考试、5 条成绩，以及费用和考勤记录。
- A 部分评估：至少 3 个已复现弱点，见 `docs/Part-A-Security-Assessment.md`。现有登录、哈希、权限和日志来自上游，不是本次实现的 B–E 工作。

建议演示顺序：管理员登录 → Students → Alex Demo → Grades & Results → Fees & Payments → 退出；学生登录 → My Profile → Grades & Results → Fees & Payments。

## 文件位置

| 路径 | 用途 |
|---|---|
| `website/` | 可修改的网站源码；入口 `manage.py` |
| `website/db.sqlite3` | 网站实际读写的 SQLite 数据库 |
| `database/studenthub-demo.sqlite3` | 干净演示数据库快照 |
| `database/studenthub-demo.sql` | 可重建数据库的 SQLite SQL 转储；不是 MySQL 语法 |
| `runtime/` | 随包附带的 Windows x64 Python 和依赖 |
| `requirements-lock.txt` | 已验证的 Python 依赖版本 |
| `docs/Database-Guide.md` | 表结构、关联、查询及备份恢复说明 |
| `docs/Part-A-Security-Assessment.md` | 中文详细评估及 CIA 影响 |
| `docs/Part-A-Report-English.md` | 简短英文 A 部分报告，供整理作业使用 |
| `docs/Changes-and-Sources.md` | 上游来源、许可证和本次修改清单 |
| `evidence/` | 实际运行截图与 JSON 验证结果 |
| `logs/` | 后台网站日志与进程记录 |
| `upstream/StudentHub-ecbffaa-original.zip` | 原始提交的源代码归档 |

## 手动运行与重新安装

在本文件夹打开 PowerShell，执行：

```powershell
.\runtime\python.exe .\website\manage.py check
.\runtime\python.exe .\website\manage.py runserver 127.0.0.1:8000 --noreload
```

手动运行前应先停止一键启动的实例。手动进程用 Ctrl+C 停止。指定其他端口时，例如 `8001`，浏览器地址也要改为 `http://127.0.0.1:8001/`。

若数据库丢失，首次一键启动会自动执行 `migrate` 和 `seed_part_a`。手动创建方式：

```powershell
.\runtime\python.exe .\website\manage.py migrate --noinput
.\runtime\python.exe .\website\manage.py seed_part_a
```

`seed_part_a` 可重复执行，不重置已有密码或覆盖已有学生修改。**不要使用上游 `seed_demo` 命令**：其院系/专业字段仍按旧结构写入，而且会重置演示密码。

如需在另一台电脑使用自己的 Python，要求 Python 3.12+；完整复制源码和 `requirements-lock.txt`。Windows 示例：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe website\manage.py migrate --noinput
.\.venv\Scripts\python.exe website\manage.py seed_part_a
.\.venv\Scripts\python.exe website\manage.py runserver 127.0.0.1:8000 --noreload
```

macOS/Linux 使用 `python3 -m venv .venv` 和 `.venv/bin/python` 替代上面的 Python 路径。依赖安装需要网络；这两种其他系统的安装方式未在本机实测。随包的 `runtime/` 仅供 Windows x64 使用。

## 验证

```powershell
.\runtime\python.exe .\tools\verify_app.py
.\runtime\python.exe .\tools\assess_part_a.py
```

功能检查在临时数据库副本上进行；安全评估在全新临时数据库与媒体目录中进行，都不会修改正在演示的数据。`functional-checks.json` 记录功能检查，`security-assessment.json` 记录弱点复现。安全脚本报告 `reproduced` 表示发现了弱点，不表示已经修复。

## 使用边界和排错

- 这是保留已知弱点的本地教学评估版本，不应对外部署或录入真实学生资料。
- 原项目并没有完整的教师独立工作流；新增普通 faculty 账号不自动具备演示教师的工作人员配置。
- 联系方式和地址已存在数据库并在档案页显示；原个人编辑表单主要修改基础资料，不包含完整联系方式/地址编辑流程。本次不扩展 Part C 功能。
- GPA 沿用上游算法：按成绩记录关联课程学分加权，不等同于完整大学成绩核算规则。多场考试可能重复计入同一门课学分，累计已完成学分管理尚非完整实现。
- 原密码找回默认使用控制台邮件后端，不会向外发送邮件。相关输出见 `logs/server.stdout.log`。
- 原学籍 `Suspend` 不等于停用登录账号。学籍状态和登录状态是两个不同字段。
- 若端口 8000 被别的程序占用，启动脚本不会终止该程序；请改用手动运行的其他端口。
- 启动错误见 `logs/startup-error.log`、`logs/server.stderr.log`。移动文件夹前先停止网站，移动后再启动。
- 学生需要查看个人成绩时请使用 **Grades & Results**；Audit Logs 是上游工作人员功能。

## 来源与许可

原项目：[tasmiul/student-management-system-django](https://github.com/tasmiul/student-management-system-django)。固定提交：`ecbffaa293753af50d93eb052ac94d87d28d0845`。MIT 许可证完整保存在 `website/LICENSE`，原 README 保存在 `website/README.md`。第三方资源许可证见 `docs/licenses/` 与 Python 各依赖的 `.dist-info` 目录。
