# 邱舒扬 — Part B 使用说明

## 你拿到的是什么

这是可独立运行的 PartB 文件夹，里面已整合你负责的身份认证和密码安全代码。基础是你上传的组内 PartC/website，保留了该版本已有的 C、D、E 代码，不把组员的实现算作你的贡献。

你新增/修改的重点：Argon2id 密码哈希、错误登录拒绝、连续失败次数限制、服务器会话校验、安全退出、测试与说明。

## 上传 GitHub

1. 解压本压缩包，得到 `PartB` 文件夹。
2. 打开你们的 GitHub 仓库，建议新建你自己的 `part-b-authentication` 分支。
3. 在仓库根目录点击 **Add file → Upload files**，把整个 `PartB` 文件夹拖进去（保留文件夹层级）。
4. 提交信息可填：`Add Part B authentication and password security`。
5. 点击提交；如果使用自己的分支，再创建 Pull Request 供组员合并。

不要只把 ZIP 上传为仓库里的一个压缩包；解压后的代码更方便阅读和运行。也不要把 `website` 里面的文件散放到仓库根目录。

注意：上传 PartB 文件夹不会自动改变你们之前启动的 `part a/website` 或 `PartC/website`。演示 B 时必须运行 `PartB/website/run.py`。统一整合时，README.md 提供了仅包含 B 改动的 changes.patch，先检查再应用；不要直接覆盖其他组员的新代码。

## 在你的 Mac 上运行

1. 在终端输入 `cd `（后面有空格），把解压出的 **PartB 文件夹**拖进终端，再回车。
2. 依次执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r website/requirements.txt
python website/setup_demo.py
python website/run.py
```

3. 浏览器打开 http://127.0.0.1:5001 。终端保持开启，停止时按 Control+C。
4. 学生：`student3@example.test`；教师：`faculty2@example.test`。密码都是 `DemoPass123!`。
5. 后续再次启动只需激活环境并执行 `python website/run.py`。不要重复创建演示数据库；脚本遇到已有数据库会拒绝覆盖。

在 PartB 文件夹运行 `python verify.py` 可重跑全部测试。测试使用临时数据库，不影响你的演示数据。程序需要联网安装依赖；仓库不需要上传 .venv、数据库、缓存或个人密码。

## 课堂演示顺序

1. 无痕窗口直接访问 `/student_dashboard`：显示 401，未登录不能访问。
2. 用学生账号正确登录：进入学生页面。退出后用教师账号登录：进入教师页面。
3. 退出后故意输入错误密码：提示 Invalid username or password。
4. 对同一账号累计输错 5 次：出现 15 分钟限制提示，此时即使输入正确密码也暂时不能登录。时间窗口从第一次失败起算。
5. 等待窗口结束后重试。不要为了演示去删除有用的数据库。自动测试中已验证限制到期后的恢复，无需现场等 15 分钟。
6. 展示 Argon2id 密码格式：在第二个终端进入 PartB，运行 `python3 website/inspect_auth.py`。只打印算法前缀和日志摘要，不打印完整哈希或会话令牌。
7. 点击 Logout 后再次访问受保护页面：401。自动测试还会复制退出前的 Cookie，验证退出后即使重放旧 Cookie 也失败。

## 你要能解释的几个问题

- 为什么不用 SHA-256 存密码？它太快，且原代码没有随机盐，泄露后更容易批量猜密码。Argon2id 专门为密码设计，并有内存/计算成本。
- 盐是什么？每次哈希自动生成的随机值。同样的密码会得到不同哈希；验证时使用哈希记录里的参数和盐。
- 为什么失败次数存在数据库？避免刷新、换浏览器或重启服务器就绕过限制。
- 为什么退出还要删除服务器记录？只删除浏览器 Cookie，先前复制出去的 Cookie 可能继续有效；服务器撤销能拒绝旧 Cookie。
- B 和 C 的区别？B 判断“你有没有成功证明身份”；C 判断“你的角色有没有权力执行这个操作”。
- 旧账号怎么处理？成功登录后把旧 SHA-256 升级为 Argon2id；没登录过的旧账号不会自动完成升级。新建演示数据库已经全是 Argon2id。

`PRESENTATION_NOTES.md` 提供简单英文讲解和报告素材。它不是小组完整的两页报告，也不是整组的最终 PPT。你的组员仍需要统一整合、准备报告、展示和 check-off。
