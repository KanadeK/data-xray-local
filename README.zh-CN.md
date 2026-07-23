# Data XRay Local

> 完全本地扫描文件夹或导出包，解释其中可能暴露的个人数据类别、位置、重复路径和处理顺序，
> 不上传源文件。

[![CI](https://github.com/KanadeK/data-xray-local/actions/workflows/ci.yml/badge.svg)](https://github.com/KanadeK/data-xray-local/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/KanadeK/data-xray-local)](https://github.com/KanadeK/data-xray-local/releases/tag/v0.1.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-8fffc1.svg)](LICENSE)

[English](README.md) · 当前状态：**v0.1.0**

![由仓库内合成导出包真实生成的 Data XRay Local 报告](media/demo-report.png)

适合记者、律师、开发者和隐私敏感用户在披露、归档或交接文件夹前进行检查。

- **一张暴露地图：**统一检查文本、CSV、JSON、Office Open XML 内容/元数据和常见图片 EXIF。
- **报告本身不制造新泄漏：**只保留相对路径、类别、计数和掩码片段，不保存完整匹配值或绝对源路径。
- **告诉你先清什么：**提供文件风险热力图、跨文件重复暴露组和按优先级排列的建议。

## 快速开始

需要 Python 3.12。

```bash
python -m pip install -e ".[dev]"
data-xray scan ./examples/synthetic_export --output ./reports/first-scan --no-network
```

打开 `reports/first-scan/data-xray-report.html`。本地可视化界面：

```bash
data-xray serve
# 打开 http://127.0.0.1:8765
```

## 真实输入 → 掩码输出

仓库内 CC0 样例在 CSV、JSON、DOCX、XLSX 和 JPEG EXIF 中重复放置了虚构邮箱
`avery.north@example.com`。报告只写入：

```json
{
  "category": "email",
  "path": "contacts.csv",
  "location": "table · row 2, column 2 · line 1, column 1",
  "masked_fragment": "a•••@e•••.com",
  "duplicate_group": "dup-001"
}
```

完整值只在当前进程的匹配阶段短暂存在，不写入 JSON 或 HTML。

## 功能

| 输入 | 检查内容 |
|---|---|
| TXT、Markdown、日志、配置 | UTF-8/UTF-16 文本规则 |
| CSV、TSV | 精确到单元格 |
| JSON | 确定性的 JSON 路径 |
| DOCX、PPTX | OOXML 文本、创建者与修改者 |
| XLSX | 单元格值与工作簿属性 |
| JPEG、PNG、TIFF、WebP | Pillow 可读 EXIF，包括 GPS 与作者信息 |

透明规则覆盖邮箱、电话、中英文街道地址样式、美式 SSN 与中国居民身份证样式、
AWS/GitHub/JWT/通用赋值凭据，以及通过 Luhn 校验的银行卡号。检测是启发式的，但每条规则都可解释。

输出包括脱敏 JSON、无远程资源的独立 HTML、风险热力图、严重度筛选、编号重复暴露组和类别化处理建议。

## 非目标

- 不是法律意见、合规认证、恶意软件检测、OCR，也不能证明文件夹一定可以公开。
- v0.1.0 不修改、删除、自动打码或上传源文件。
- 暂不处理旧版二进制 Office、PDF、压缩包、视频或音频。
- 优先使用确定、透明的规则，不在首次运行下载语言模型。

## 架构

```text
本地文件源
  → 格式适配器（文本 / 表格 / OOXML / EXIF）
  → 纯规则检测 + 仅驻留内存的等值摘要
  → 风险、重复与建议聚合
  → 不含原值的报告模型
  → CLI / 回环 FastAPI / JSON + 独立 HTML
```

领域层不依赖 FastAPI、Typer、文件系统或网络；CLI 与 Web UI 调用同一个
`ScannerService`。详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## CLI、API 与界面

```text
data-xray scan TARGET [--output PATH] [--no-network] [--fail-on SEVERITY]
data-xray demo [--output PATH] [--sample PATH]
data-xray serve [--host 127.0.0.1] [--port 8765]
data-xray version
```

`--fail-on high` 在发现 high/critical 时返回退出码 `10`；输入或读取失败返回 `2`。
默认扫描期间会阻断 DNS 和常见出站 socket 帮助函数。浏览器只与本机回环 FastAPI 通信。

`POST /api/scan` 的请求示例：

```json
{
  "target": "examples/synthetic_export",
  "output": "reports/web",
  "no_network": true
}
```

响应只返回脱敏报告和制品文件名，不回显绝对目标路径。Web 首页面向键盘操作、窄屏和读屏状态提示，
并遵循“减少动态效果”系统偏好。

## 样例、隐私与安全

`examples/synthetic_export/` 是确定性虚构数据，按 CC0-1.0 发布，包含 CSV、JSON、文本、
DOCX、XLSX 和带合成 EXIF 的 JPEG。`MANIFEST.json` 记录文件哈希并明确声明没有真实个人数据。

- 扫描只读且不跟随符号链接目录。
- 报告不保存源根目录与绝对路径。
- 可序列化模型没有“原始匹配值”字段。
- 重复比较摘要只存在于内存，输出时变成不透明 `dup-NNN`。
- 报告转义动态内容并设置严格 Content Security Policy。
- 超出大小或不支持的文件会明确列为 skipped，不会被静默当作安全。

完整边界见 [docs/PRIVACY_AND_SECURITY.md](docs/PRIVACY_AND_SECURITY.md)，漏洞报告方式见
[SECURITY.md](SECURITY.md)。

## 测试、演示与打包

```bash
python -m pip install -e ".[dev]"
python scripts/verify.py
python scripts/demo.py
python -m build
python scripts/package_release.py
python scripts/release_check.py
```

也提供 `make verify`、`make demo`、`make package`、`make release-check`，以及 Windows
`scripts/*.ps1` / POSIX `scripts/*.sh` 等价入口。测试覆盖规则、状态聚合、解析错误、真实合成格式、
报告泄漏、无网络门、CLI 和 FastAPI。性能证据见 [docs/BENCHMARK.md](docs/BENCHMARK.md)。

`package_release.py` 会生成 wheel、sdist、样例/启动包、真实脱敏报告和
`SHA256SUMS.txt`，并在干净临时目标中安装 wheel 做冒烟验证。

## 竞品差异

公开 GitHub 仓库抽样检索未发现同名且高度同构的活跃项目。相邻项目包括 PII 引擎、秘密扫描器、
上传前净化器、数据库目录扫描器与 EXIF 读取器。Data XRay Local 不做自动净化，重点是把跨格式、
跨文件的隐私暴露解释清楚，同时保持源文件不变。带日期、Star、更新时间和功能对比的证据见
[docs/COMPETITOR_SCAN.md](docs/COMPETITOR_SCAN.md)；这只是公开仓库抽样，不是“全球唯一”声明。

## 路线图

- v0.2：在相同无网络与脱敏报告保证下加入可选 PDF 文本/OCR 适配器。
- v0.3：本地自定义规则包与置信度调节。
- 后续：通过平台专项安全审查后提供签名桌面包。

## 贡献、FAQ 与许可

贡献前阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，样例只能使用合成数据。新增规则必须包含阳性、
阴性、报告泄漏与序列化测试。

**扫描为零是否代表安全？** 不代表。未知格式、新型标识符、依赖语境的信息与隐写内容仍需人工检查。

**Web UI 是否上传文件？** 不上传。页面把本地路径发给本机回环进程，由该进程读取并在本地写报告。

**为什么不自动删除？** 记者与法律工作流需要保持来源证据，破坏性清理可能损坏溯源。因此 v0.1.0
只读并给出建议。

代码使用 [MIT](LICENSE)；合成样例使用 CC0-1.0。

