# Part A 应用审查（第 1-3 项）

## 范围

本文只完成作业 Part A 的第 1-3 项：选择现有系统、下载并运行，以及检查现有功能、数据库交互和账号登录流程。按照当前任务要求，第 4 项“识别至少三个安全弱点或缺失的安全控制”暂缓处理；本文不列出安全问题，也不分析其对学生信息机密性、完整性或可用性的影响。

## 1. 选定的现有系统

- 项目：**School Management System**
- 上游作者：`zaydkassimi`
- 上游仓库：<https://github.com/zaydkassimi/school-management>
- 检查和打包所依据的固定提交：[`cb6035cebfd40da5a244e2671d3a9631018e25a2`](https://github.com/zaydkassimi/school-management/commit/cb6035cebfd40da5a244e2671d3a9631018e25a2)
- 技术栈：Python、Flask、Jinja 模板、原生 HTML/CSS/JavaScript 和 SQLite。
- 固定提交的原始 ZIP 快照保存在 `upstream/school-management-cb6035c-original.zip`，便于将本地可运行版本与上游代码对照。

该项目符合“基于 Web 的学生信息系统”范围：它管理学生账号、课程成绩、缺勤、学年与学期数据，并提供管理员和学生两类页面。

## 2. 下载、配置和运行结果

上游固定提交已下载，本地可运行副本位于 `website/`。运行环境使用 Flask 2.3.3、openpyxl 3.1.2 和 fpdf2 2.8.9；具体依赖调整及代码改动见 `Source-and-Changes.md`。

本项目已在 Windows 上完成本地配置和启动验证。应用启动后监听 `http://127.0.0.1:5000`，首次在工作目录中运行时会创建 SQLite 文件 `school.db` 以及所需数据表。成品另附便携 Python 运行环境和启动脚本，因此不依赖系统中预装的 Python；完整操作以成品根目录的安装与启动说明为准。

## 3. 现有功能检查

### 3.1 用户账号和登录流程

以下内容是对现有行为的描述，不是安全评价。

- **管理员登录**：登录页接受固定凭据 `admin` / `admin`。匹配后，程序直接在 Flask session 中写入管理员身份，并转到管理员面板；该管理员不是从 `users` 表读取的记录。
- **学生注册**：`/register` 接收姓名、电子邮件和密码；电子邮件不能与现有 `users.email` 重复。新账号以 `student` 角色写入 `users` 表。
- **学生登录**：`/login` 根据电子邮件查询 `users`，对提交的密码作 SHA-256 运算，然后与表内值比较。成功后，session 保存 `user_id`、`role` 和 `name`，并转到学生面板。
- **页面访问**：`login_required` 检查 session 中是否存在 `user_id`；`admin_required` 还检查 `role == "admin"`。`/logout` 清空 session 并返回登录页。

### 3.2 管理员功能

- 查看所有学生及其课程成绩、教师、学年、学期和缺勤次数。
- 按学年、课程、教师、风险等级和学期筛选数据。
- 按“学生 + 课程 + 学年 + 学期”组合新增或更新成绩及缺勤次数。
- 以成绩 `>= 10` 显示 `Admis`（通过），否则显示 `Non Admis`（未通过）。
- 查看总体学生人数、总体平均分、未通过课程数、课程表现、风险学生和分学期趋势。
- 将汇总数据导出为 CSV、Excel (`.xlsx`) 或 PDF。

### 3.3 学生功能

- 查看本人各课程的成绩、教师、学年、学期、通过状态和缺勤次数。
- 查看平均成绩、班级排名、风险等级以及跨学期表现变化。
- 学生页面使用 session 中的 `user_id` 查询本人的数据库记录。

### 3.4 SQLite 数据表和交互

数据库文件名为 `school.db`，包含以下六张业务表：

| 表 | 主要字段 | 当前用途 |
| --- | --- | --- |
| `users` | `id`, `name`, `email`, `password`, `role` | 保存学生账号；注册时插入，登录和各类报表读取。 |
| `grades` | `student_id`, `module_name`, `grade`, `teacher_name`, `academic_year`, `semester`, `created_at` | 保存每名学生的课程成绩；管理员写入，学生面板、分析页和导出读取。 |
| `absences` | `student_id`, `module_name`, `count`, `total_hours`, `academic_year`, `semester` | 保存按课程、学年和学期记录的缺勤次数；管理员写入，面板、风险计算和导出读取。 |
| `classes` | `name`, `academic_year`, `teacher_name` | 创建于初始化过程，供班级资料使用；当前页面没有直接管理该表的功能。 |
| `student_class` | `student_id`, `class_id` | 连接学生与班级；当前页面没有直接管理该表的功能。 |
| `risk_thresholds` | `min_grade`, `max_absences`, `risk_level` | 首次初始化写入默认阈值 `10.0`、`10`、`medium`，供风险等级计算读取。 |

主要数据流程如下：

1. 学生注册向 `users` 插入一条 `student` 记录。
2. 管理员提交成绩时，应用在 `grades` 和 `absences` 中查找相同学生、课程、学年和学期的记录，然后执行更新或插入。
3. 学生面板将 `grades` 与 `absences` 连接，只读取当前 session 对应学生的数据。
4. 管理员面板、分析页和导出功能连接或聚合 `users`、`grades` 与 `absences`。
5. 风险、排名和趋势函数分别读取阈值、全体学生平均分，以及按学年和学期聚合的成绩。

### 3.5 路由和输出

| 路由 | 方法 | 访问角色 | 作用 |
| --- | --- | --- | --- |
| `/` | GET | 所有人 | 转到登录页。 |
| `/login` | GET, POST | 所有人 | 显示登录页并处理管理员或学生登录。 |
| `/register` | GET, POST | 所有人 | 显示并处理学生注册。 |
| `/admin_dashboard` | GET, POST | 管理员 | 浏览、筛选以及新增或更新学生成绩和缺勤。 |
| `/student_dashboard` | GET | 已登录学生 | 显示当前学生的成绩、缺勤、排名、风险和趋势。 |
| `/analytics` | GET | 管理员 | 显示全局统计、课程表现和学期趋势。 |
| `/export_data?format=csv` | GET | 管理员 | 下载 CSV 数据和摘要。 |
| `/export_data?format=excel` | GET | 管理员 | 下载包含 Student Data 与 Summary 工作表的 Excel 文件。 |
| `/export_data?format=pdf` | GET | 管理员 | 下载学生表现 PDF 报告。 |
| `/api/student_risk/<student_id>` | GET | 管理员 | 返回指定学生的风险、排名、平均分和趋势 JSON。 |
| `/api/performance_evolution` | GET | 管理员 | 返回全体成绩按学期聚合的 JSON。 |
| `/logout` | GET | 所有人 | 清空当前 session 并返回登录页。 |

## 暂缓项目

Part A 第 4 项安全弱点与安全控制评估按当前要求暂不完成，后续可单独补充。
