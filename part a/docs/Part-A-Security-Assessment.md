# Project 3 — Part A 初步安全评估

评估日期：2026 年 10 月 18 日。对象：[StudentHub / student-management-system-django](https://github.com/tasmiul/student-management-system-django)，MIT 许可，上游提交 `ecbffaa293753af50d93eb052ac94d87d28d0845`。本交付只覆盖 Part A：安装运行、了解功能/数据/用户/登录机制、识别潜在安全弱点及 CIA 影响；未实施 B–E 的安全功能。

已在隔离环境复现 3 个问题：匿名下载标记为私有的文件、GET 请求改变学生状态、选课窗口过期后仍可提交申请。另进行了 6 次错误登录的有限观察，并记录 2 项源码层面的条件性风险。**“复现成功”表示弱点确实存在，不表示安全检查通过。**

## 1. 评估方法与隔离边界

使用交付包的 Python 3.12.10、Django 6.0.9 和 `tools/assess_part_a.py`。脚本先读取网站配置，在 `django.setup()` 之前把数据库替换为系统临时目录中的 SQLite 文件，再执行迁移。媒体文件也放入临时目录；测试完成后关闭数据库连接并删除临时目录。

全部请求使用进程内的 `Client(enforce_csrf_checks=True)`，没有连接正在运行的网站，也没有向 GitHub 或其他网站发起攻击请求。账号、学生、文件、课程和密码均为临时合成数据。脚本不打开、不修改演示数据库，也不修改网站源码。为复现上游默认开发媒体路由，隔离配置明确使用 `DEBUG=True`；签名密钥为仅在该测试进程中存在的随机值，测试主机允许列表限于本地测试名称。

机器可读证据位于 `evidence/security-assessment.json`，其中包含运行时间、实际响应、判断依据、源码链接、测试限制及临时目录清理结果。该次运行 `status=completed`，`top_three_insecure_behaviors_reproduced=true`。

在项目根目录重新执行：

```powershell
.\runtime\python.exe .\tools\assess_part_a.py
```

终端中的两条 `Forbidden` 是用于验证 CSRF 和权限控制的预期结果。脚本成功退出表示预期观察得到复现；如果后续另行实施安全修复，复现脚本可能返回非零，需要重新解释证据。

## 2. 用户、认证与权限现状

`website/accounts/models.py:5-13` 定义 `admin`、`faculty`、`student` 三个角色。主要业务视图实际按 `is_staff=True` 或 `role=="admin"` 判断管理权限；其余用户通常进入学生流程。证据例如 `website/students/views.py:27-28`、`website/dashboard/views.py:24-26`、`website/core/context_processors.py:35-36`。

交付包的 Faculty 演示账号设置了 `is_staff=True`，因此能使用原项目已有的工作人员管理界面。**这不是教师与管理员之间的细粒度 RBAC**，也不表示教师只能管理本人授课课程。原 `dashboard/views.py:61` 对非管理员直接读取 `student_profile`，仅把角色设为 faculty、又没有学生档案的账号不构成完整教师工作流。本次未改写认证或权限源码。

登录继承 Django `LoginView` / `AuthenticationForm`（`accounts/views.py:9-20`、`accounts/forms.py:19-46`）。数据库存储密码哈希，本次实测算法为 `pbkdf2_sha256`；错误密码没有产生登录会话。新建学生支持首次改密标记，入口见 `students/views.py:113-123`，强制跳转见 `accounts/middleware.py:9-18`。这些已有控制不能替代下列下载鉴权、操作方法和业务条件检查。

## 3. 已复现问题

### A1 — 私有文档的实际下载缺少身份和权限检查

**优先级：高；CIA：机密性（C）。** 条件是用户能够知道文件 URL，且部署沿用开发媒体路由或示例 Nginx 的公开媒体目录。

文档页面在 `documents/views.py:14-20` 对普通用户使用 `is_public=True` 过滤，而下载链接直接使用 `d.file.url`（`templates/documents/index.html:3`）。`sims/urls.py:41-42` 在开发模式下公开提供整个媒体目录；示例 `deploy/nginx.conf.example:9-11` 也直接映射 `/media/`，没有按 Document 对象权限鉴权。[列表源码](https://github.com/tasmiul/student-management-system-django/blob/ecbffaa293753af50d93eb052ac94d87d28d0845/documents/views.py#L14-L20)；[媒体路由源码](https://github.com/tasmiul/student-management-system-django/blob/ecbffaa293753af50d93eb052ac94d87d28d0845/sims/urls.py#L41-L42)。

隔离测试创建 `is_public=False` 的无敏感内容文本文件，得到：

| 请求或检查 | 观察结果 |
|---|---|
| 匿名访问文档列表 | HTTP 302，要求登录 |
| 学生访问文档列表 | HTTP 200，私有条目被隐藏 |
| 匿名直接访问该文件 URL | HTTP 200 |
| 下载内容 | 与合成测试文件逐字节一致 |

因此，列表隐藏不能保护文件内容。如果媒体目录中保存成绩单、证件或内部材料，其内容可能被未授权人员获取。本次没有枚举目录、猜测真实文件名或读取真实个人信息；也不声称存在路径遍历。仅关闭 DEBUG 不能证明生产私有文件已受保护，还需要核对实际文件服务配置。

后续修复方向仅供记录：下载请求应经过对象权限检查，私有存储不得被公开目录路由绕过。本次未实施。

### A2 — 改变学生状态的 GET 请求不需要 CSRF token

**优先级：高；CIA：完整性（I）。** 需要已登录且具有相应权限的浏览器会话。潜在跨站利用还受浏览器 Cookie 策略、访问方式和部署位置影响。

`students/views.py:197-208` 仅检查登录、管理员权限和状态值，没有限制 HTTP 方法，直接保存 `student.status`。`students/urls.py:14` 提供该入口，`templates/students/student_list.html:67-71` 使用普通链接触发。`gradebook/views.py:78-86` 发布成绩也有同类 GET 写操作。[状态修改源码](https://github.com/tasmiul/student-management-system-django/blob/ecbffaa293753af50d93eb052ac94d87d28d0845/students/views.py#L197-L208)。

使用同一临时管理员会话并启用 CSRF 检查：

| 操作 | HTTP 状态 | 数据库中的学生状态 |
|---|---:|---|
| 初始状态 | — | active |
| 不带 token 的 POST | 403 | active |
| 不带 token 的 GET | 302 | suspended |

这证明 CSRF 中间件已启用，但 GET 写操作避开了安全方法不应产生副作用的设计前提。外部链接导航可能使已登录用户触发非预期操作；不能据此声称所有跨站图片请求都能携带会话，也没有在真实浏览器中诱导用户点击。[Django CSRF 文档](https://docs.djangoproject.com/en/6.0/ref/csrf/)明确要求安全方法不产生危险副作用。

额外实测：改变 Student 学籍状态后，关联 `User.is_active` 仍为 true。“Suspend”在当前实现中是学籍状态变更，不等于禁用登录。不能把其完整性影响写成已经造成账号锁定或服务中断。

后续修复方向仅供记录：状态改变使用受 CSRF 保护的非 GET 方法，服务端显式限制方法。本次未实施。

### A3 — 过期选课窗口可以通过操作 URL 绕过

**优先级：中；CIA：完整性（I）。** 需要拥有学生档案的登录账号以及目标 offering 的 ID。

`registration/views.py:27-29` 在学生列表中按窗口启用状态和起止时间筛选课程。然而 `registration/views.py:58-71` 的 `register_course()` 只按主键取课程，随后 `get_or_create()` 注册记录，没有再次验证窗口。操作权限必须在服务端执行操作时检查，页面不显示入口并不等于拒绝请求。[列表筛选](https://github.com/tasmiul/student-management-system-django/blob/ecbffaa293753af50d93eb052ac94d87d28d0845/registration/views.py#L27-L29)；[操作入口](https://github.com/tasmiul/student-management-system-django/blob/ecbffaa293753af50d93eb052ac94d87d28d0845/registration/views.py#L58-L71)。

测试创建已于请求前一天结束的选课窗口。学生课程列表返回 HTTP 200，且不含该课程；直接请求它的注册 URL 后返回 HTTP 302，数据库创建了 `status="pending"` 的记录。

该结果证明可绕过截止时间提交申请，影响注册流程与数据可信度。**申请仍待审批，没有证明学生自动获得已批准名额。** 另从源码可见，`registration/models.py:15` 虽定义 capacity，但注册及批准处理（`registration/views.py:84-93`）没有容量检查；容量超限并未在本次测试中单独复现。

后续修复方向仅供记录：在操作端检查窗口和适用的业务条件，并在审批时核对容量。本次未实施。

## 4. 有限观察与条件性风险

### A4 — 六次失败登录后未观察到账户锁定

**优先级：中；CIA：潜在机密性（C）、完整性（I）及可用性（A）。** `accounts/views.py:9-20` 只增加会话期限行为；`accounts/forms.py:19-46` 继承标准认证表单；`sims/settings.py:58-68` 未包含可见的限速中间件。[登录视图](https://github.com/tasmiul/student-management-system-django/blob/ecbffaa293753af50d93eb052ac94d87d28d0845/accounts/views.py#L9-L20)。

同一个临时用户使用有效 CSRF token 连续提交 6 次错误密码，6 次均返回 HTTP 200 登录表单，且始终未认证。随后使用正确密码返回 HTTP 302 并建立会话。HTTP 200 在这里不代表登录成功。

此观察只说明这 6 次失败未触发已观察到的锁定；不能证明任何次数都没有限流，也没有测试代理/WAF 等外部保护。若实际部署缺少防自动化控制，密码猜测成功可能影响 C/I，大量密码哈希计算也可能影响 A。未进行密码破解、负载或拒绝服务测试，未证明服务可用性已受损。后续方向是评估适当限速及失败监测，而非直接推定必须永久锁定账号。

### A5 — 上游配置依赖部署者覆盖开发默认值（仅源码审阅）

**优先级：对外部署时高；CIA：潜在 C/I。** `sims/settings.py:24` 的签名密钥有公开、固定的回退值，`:27` 默认启用 DEBUG。若未通过环境配置覆盖，调试错误页可能披露源码、局部变量和内部信息，已知签名材料也不满足生产要求。[配置源码](https://github.com/tasmiul/student-management-system-django/blob/ecbffaa293753af50d93eb052ac94d87d28d0845/sims/settings.py#L23-L29)；[Django 部署检查表](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)。

这不是“当前网站已经泄露数据”的结论；实际启动环境可能覆盖默认值。隔离脚本使用临时随机密钥，没有尝试伪造 token。不能声称仅凭回退密钥便可直接登录默认的数据库会话。本地开发使用调试设置也不能直接等同于已遭远程攻击。

### A6 — 学生姓名进入 CSV 时存在公式注入条件（仅源码审阅）

**优先级：中；CIA：导出数据的潜在 I，以及依赖表格软件行为的潜在 C。** 学生可编辑本人姓名，见 `students/views.py:139-163` 的锁定字段列表；`reports/views.py:26-29` 将姓名直接写入 CSV，没有处理公式前缀。[导出源码](https://github.com/tasmiul/student-management-system-django/blob/ecbffaa293753af50d93eb052ac94d87d28d0845/reports/views.py#L20-L30)。

如果管理员用会把 `=` 开头单元格解释为公式的表格软件打开该文件，用户输入可能被当作公式处理。无害说明示例是 first_name 为 `=1+1`、last_name 为 `+1`，拼接后为 `=1+1 +1`。本次没有修改演示姓名、没有在 Excel 中运行公式，也没有证明外部请求、信息外传或代码执行。[OWASP CSV Injection](https://community.owasp.org/attacks/CSV_Injection)说明了这一风险类别。后续方向是导出格式和目标表格软件适配的公式中和；本次未实施。

## 5. 已有防护与结论限制

本次验证确认：错误密码不能登录；密码以哈希存储；学生访问管理员学生目录返回 403；无 CSRF token 的 POST 返回 403；私有文档在学生列表中被隐藏。源码还启用了 `CsrfViewMiddleware`、`SecurityMiddleware`、`XFrameOptionsMiddleware`，并设置了 HttpOnly 会话 Cookie（`sims/settings.py:58-68,148-154`）。不能把本报告概括为“完全没有认证或 CSRF 保护”。

报告将 C（机密性）、I（完整性）、A（可用性）的已证明影响与潜在影响分开。前 3 项是隔离功能级复现，A4 是有次数边界的观察，A5–A6 是明确标注条件的源码发现。未进行全站渗透、外部部署检查、真实数据访问、负载测试或完整安全认证；其他模块未被据此宣称安全。文件与数据库安装修复、界面资源本地化及演示账号准备不等于实现 B–E 安全功能。

参考技术依据：[Django 安全机制与限制](https://docs.djangoproject.com/en/6.0/topics/security/)。
