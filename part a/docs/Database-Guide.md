# 数据库使用说明

## 三份数据库文件的区别

- `website/db.sqlite3`：网站实际连接的数据库，浏览器修改会持久保存到这里。
- `database/studenthub-demo.sqlite3`：初始化完成后的干净快照，不随网站操作更新。
- `database/studenthub-demo.sql`：同一干净快照的 SQLite 建表和数据脚本，可在空 SQLite 数据库中执行。不是 MySQL 导入文件。

无需安装或启动数据库服务。Python 自带 `sqlite3`；Django 的 `sims/settings.py` 将数据库位置设为网站源码目录下的 `db.sqlite3`。采用 Django ORM 读写；登录账号与学生资料分表。

## 主要数据表及关联

| 表 | 内容和关联 |
|---|---|
| `accounts_user` | 用户名、密码哈希、role、is_staff、is_active、首次改密标记 |
| `students_student` | 学号、姓名、注册号、学年、学期、状态；user_id 一对一关联账号；department_id、program_id 关联院系/专业 |
| `students_contactinformation` | 邮箱、电话；student_id 一对一关联学生 |
| `students_address` | 现住/永久地址；student_id 关联学生 |
| `students_emergencycontact` | 虚构紧急联系人；student_id 一对一关联学生 |
| `academics_department` / `academics_program` | 院系和专业；专业关联院系 |
| `academics_faculty` | 员工号和教师资料；user_id 关联账号 |
| `academics_course` | 课程、credit_hours、学期、教师与院系 |
| `registration_registrationwindow` / `registration_courseoffering` / `registration_courseregistration` | 选课窗口、开课、学生选课及审批状态 |
| `gradebook_exam` / `gradebook_graderecord` | 考试、分数、字母成绩和绩点；成绩的 student_id 是学号文本，exam_id 是外键 |
| `fees_feestructure` / `fees_payment` | 学费/实验费及支付记录；付款关联学生和费用项目 |
| `attendance_enrollment` / `attendance_attendancesession` / `attendance_attendancerecord` | 修课关系、考勤场次和考勤记录 |
| `audits_auditlog` | 上游现成审计记录；不属于本次新增 Part E 实现 |
| `django_session` / `django_migrations` | 登录会话及数据库迁移状态 |

注意：部分表中的 `student_id` 是学号字符串，例如 `STU-0001`；另外一些表的 `student_id` 是关联 `students_student.id` 的数字外键，不能混用。具体以模型和 SQL schema 为准。

## 查看数据

可以使用已有的 SQLite 图形工具，或在项目根目录的 PowerShell 运行以下只读示例：

```powershell
@'
import sqlite3
db = sqlite3.connect('file:website/db.sqlite3?mode=ro', uri=True)
for row in db.execute('SELECT username, role, is_staff, is_active FROM accounts_user ORDER BY id'):
    print(row)
db.close()
'@ | .\runtime\python.exe -
```

常用 SQL：

```sql
-- 学生、账号和联系方式
SELECT s.student_id, s.first_name, s.last_name, u.username,
       c.primary_email, c.mobile_number
FROM students_student AS s
JOIN accounts_user AS u ON u.id = s.user_id
LEFT JOIN students_contactinformation AS c ON c.student_id = s.id;

-- 学生的已发布成绩和课程学分
SELECT g.student_id, e.course_code, g.marks_obtained,
       g.letter_grade, g.grade_points, c.credit_hours
FROM gradebook_graderecord AS g
JOIN gradebook_exam AS e ON e.id = g.exam_id
LEFT JOIN academics_course AS c ON c.code = e.course_code
WHERE e.is_published = 1;

-- 各学生已缴费金额
SELECT s.student_id, COALESCE(SUM(p.amount_paid), 0) AS paid
FROM students_student AS s
LEFT JOIN fees_payment AS p ON p.student_id = s.id
GROUP BY s.id;

PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

密码以 Django 哈希存储，不应把数据库哈希列当作可直接输入的登录密码。演示密码在根目录 README 中列出。

初始数据中学费 2400、实验费 200，每人应缴 2600。student1/student2/student3 的初始未缴余额依次为 900、400、1200；金额未声明真实货币或真实账单。

## 备份

在项目根目录运行，每次使用新的备份名称：

```powershell
.\runtime\python.exe .\tools\export_database.py --name my-backup-20261018
```

该脚本使用 SQLite 备份 API，生成 `database/my-backup-20261018.sqlite3` 和同名 `.sql`。若任一目标已存在会拒绝覆盖；不改变正在运行的数据。

## 恢复演示快照

先双击 `02-Stop-Website.cmd`；若你手动启动了服务器，应在对应终端按 Ctrl+C。确认停止后：

```powershell
.\runtime\python.exe .\tools\export_database.py --name before-restore-20261018
Copy-Item -LiteralPath .\database\studenthub-demo.sqlite3 -Destination .\website\db.sqlite3 -Force
```

再双击启动脚本。恢复会把当前网站数据替换为快照内容，所以必须先完成上面的备份；备份名称已用过时请更换名称。快照仅包含数据库，新增上传文件还应另外备份 `website/media/`。

## 从 SQL 创建一个新的数据库

以下命令使用一个尚不存在的目标，不会改动网站数据库：

```powershell
@'
from pathlib import Path
import sqlite3
target = Path('database/restored-example.sqlite3')
if target.exists():
    raise SystemExit('Target exists; choose another name')
db = sqlite3.connect(target)
db.executescript(Path('database/studenthub-demo.sql').read_text(encoding='utf-8'))
print(db.execute('PRAGMA integrity_check').fetchone())
db.close()
'@ | .\runtime\python.exe -
```

本包已在临时目录验证 SQL 导入后完整性为 `ok`、无外键错误，并有 3 名学生。详细结果见 `evidence/functional-checks.json`。
