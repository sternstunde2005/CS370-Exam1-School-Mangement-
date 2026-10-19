# 来源与本地改动记录

## 上游来源

- 项目：**School Management System**
- 仓库：<https://github.com/zaydkassimi/school-management>
- 固定提交：[`cb6035cebfd40da5a244e2671d3a9631018e25a2`](https://github.com/zaydkassimi/school-management/commit/cb6035cebfd40da5a244e2671d3a9631018e25a2)
- 原始快照：`upstream/school-management-cb6035c-original.zip`

所有功能说明与本地改动比较都以该固定提交为基准，而不是以未来可能变化的 `main` 分支为基准。

## 许可证状态和使用范围

该固定提交的仓库根目录没有 `LICENSE`、`COPYING` 或 `NOTICE` 文件，GitHub 仓库也没有声明可识别的许可证。因此，本项目不能据此声称上游代码采用某个开源许可证，也不把“GitHub 上公开可见”等同于获得开放源代码许可。

本地副本仅用于本次课程作业、离线运行和教学演示。保留上游链接、固定提交和原始快照是为了注明来源并便于复核，不代表取得额外授权。如需公开发布、重新分发或用于课程之外的用途，应先向上游权利人确认许可。

## 网站源码的最小改动

与上游固定提交相比，`website/` 中只修改了以下两处：

1. **依赖清单 `website/requirements.txt`**
   - 移除 `pandas==2.0.3`。当前 Excel 导出直接使用 openpyxl，应用没有运行时 pandas 调用。
   - 移除 `pdfkit==1.0.0`。当前 PDF 导出使用 `FPDF`，应用没有运行时 pdfkit 调用。
   - 加入实际需要的 `fpdf2==2.8.9`，与 `from fpdf import FPDF` 对应。
   - 保留 `Flask==2.3.3` 和 `openpyxl==3.1.2`。
2. **PDF 字节输出 `website/app.py`**
   - 上游代码假定 `pdf.output(dest="S")` 一定返回字符串，并直接调用 `.encode("latin1")`。
   - 本地代码调用 `pdf.output()`，若返回字符串则编码；若返回 bytes 或 bytearray，则转换为 `bytes`。这样可兼容当前 fpdf2 的返回类型并正常交给 Flask `send_file`。

除上述内容外，`website/README.md`、`website/run.py`、`website/test_app.py` 和 `website/templates/` 中的页面模板保持与固定提交一致。

## 本地演示与打包内容

这些内容用于让课程成品能够直接检查，不属于上游仓库：

- **虚构演示数据**：成品数据库中的演示姓名、邮箱、课程、成绩、教师和缺勤记录均为虚构数据，只用于展示注册、登录、成绩、缺勤、筛选、统计和导出流程，不包含真实学生信息。
- **便携运行环境**：`runtime/` 包含 Windows 便携 Python 及已安装依赖，供成品离线运行。
- **启动和停止脚本**：成品根目录的脚本负责从正确工作目录启动或停止 Flask 应用，避免用户手动配置 Python 路径。
- **数据库准备脚本**：打包流程创建或重建演示数据库，并写入虚构记录，使管理员和学生页面有可检查的数据。
- **验证脚本与记录**：打包流程检查数据库结构、主要页面和 CSV/Excel/PDF 导出，供提交前复核。

安装、启动、停止、演示账号和文件结构以成品根目录的说明文件为准。

## 改动边界

本地适配的目标是让上游应用在指定 Windows 成品环境中可重复运行并便于课堂演示。没有把这些兼容性、演示数据或打包改动描述为上游作者的原始内容；原始快照与本地运行副本分开保存，以便逐项比较。
