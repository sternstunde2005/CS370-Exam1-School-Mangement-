# 来源、版本与修改范围

## 上游

- 项目：[StudentHub](https://github.com/tasmiul/student-management-system-django)
- 提交：[ecbffaa293753af50d93eb052ac94d87d28d0845](https://github.com/tasmiul/student-management-system-django/tree/ecbffaa293753af50d93eb052ac94d87d28d0845)
- 作者许可证：MIT；完整副本 `website/LICENSE`。
- 原始代码归档：`upstream/StudentHub-ecbffaa-original.zip`。
- 查阅与打包日期：2026-10-18。

PDF 的建议列表允许选择其他开源学生信息系统。本项目选用的是具有明确 MIT 许可、现成浏览器界面、SQLite 数据库和学生/工作人员功能的 GitHub 项目。

## 本次 Part A 交付所作调整

1. 依照现有模型生成缺失的 Python 迁移源文件，使干净数据库能够正常 `migrate`，未改动模型结构。
2. 新增 `accounts/management/commands/seed_part_a.py`，使用真实外键对象建立虚构演示数据，重复执行保留已有修改和密码。原 `seed_demo.py` 保留供追溯。
3. 把 `base.html`、`home.html` 和 `attendance/index.html` 的 Tailwind、Alpine、Chart.js 引用改为本地固定版本。使用系统字体替代联网字体；首页外链图片替换为本地原创 SVG 校园插图。
4. 在原学生详情模板中显示已有数据库的学年、学期、电话、邮箱和地址，未增加联系人编辑、对象授权或新数据模型。
5. 去除学生导航中指向工作人员专用 `/audits/` 的错误菜单项；服务器已有访问控制保持原样。
6. 配置教师演示账号为现有 `is_staff=True` 工作人员模式。没有补写独立 faculty 权限控制。
7. 附带可移动的 Windows Python、依赖锁定、启动/停止脚本、数据库备份工具、安装说明和隔离验证脚本。

不应将本次工作描述为原创开发整套系统，或已完成 B、C、D、E。认证、密码哈希、权限判断和日志功能来自上游。A 部分弱点仍保留，供评估记录；后续修复不在此次范围内。

## 第三方资源

| 资源 | 固定版本 / 来源 | 许可位置 |
|---|---|---|
| CPython Windows embeddable | [3.12.10 官方目录](https://www.python.org/ftp/python/3.12.10/) | `runtime/LICENSE.txt` |
| Django、Pillow、asgiref、sqlparse、tzdata | PyPI；版本在 `requirements-lock.txt` | `runtime/Lib/site-packages/*.dist-info/` |
| Tailwind CSS Play CDN | [3.4.17](https://cdn.tailwindcss.com/3.4.17)，本地开发运行器 | `docs/licenses/Tailwind-MIT.txt` |
| Alpine.js | [3.14.9](https://cdn.jsdelivr.net/npm/alpinejs@3.14.9/dist/cdn.min.js) | `docs/licenses/Alpine-MIT.txt` |
| Chart.js | [4.4.8](https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.js) | `docs/licenses/ChartJS-MIT.txt` |

本包使用本地开发服务器和本地 Tailwind 浏览器编译器，不宣称适合生产部署。网络下载仅用于准备交付包；正常演示不需要外部服务。
