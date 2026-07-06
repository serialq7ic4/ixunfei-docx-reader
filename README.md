# ixunfei-docx-reader

**简体中文** | [English](README.en.md)

让 Codex、Claude Code 等本地 coding agent 读取已授权访问的 i讯飞/LarkShell 私有文档，并转换为本地 Markdown/TSV 供分析使用。

> 面向 Codex / Claude Code 使用，`ixfdoc` 作为本地执行引擎；复用本机登录态，无服务端，无遥测，不需要飞书开放平台应用。

<p>
  <img alt="python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB">
  <img alt="platform" src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20experimental-lightgrey">
  <img alt="license" src="https://img.shields.io/badge/license-Apache%202.0-green">
</p>

`ixunfei-docx-reader` 默认作为 Codex / Claude Code skill 安装和使用；`ixfdoc` 是 skill 依赖的本地执行引擎，也可直接用于调试和自动化。

- 在 Codex / Claude Code 里直接粘贴私有 i讯飞/LarkShell `docx`、`wiki` 链接并读取为 Markdown。
- 将支持的嵌入 sheet 展开为 TSV sidecar 文件。
- 复用本机 i讯飞/LarkShell 桌面端登录态进行认证。
- 提供 Codex / Claude Code skill，底层统一调用 `ixfdoc`。
- 文档内容、cookie 和生成产物默认都留在本机。

项目刻意保持小而清晰。它不是浏览器扩展、常驻 daemon、同步服务，也不是通用飞书备份产品。

## 为什么做这个

私有 i讯飞/LarkShell 文档通常不能被 coding agent 直接通过普通 HTTP fetch 读取。这个项目的目标是补上这段本地工作流：让 Codex / Claude Code 通过本机 skill 调用 `ixfdoc`，复用你已经登录的桌面端会话，把你有权限访问的文档转换成 agent 更容易处理的本地 Markdown/TSV 文件。

和通用浏览器扩展类导出工具相比，本项目的边界更窄：

| 项目形态 | 更适合 |
|---|---|
| Codex / Claude Code skill + `ixfdoc` | 在本地开发时让 agent 读取已授权的私有文档 |
| 浏览器扩展 | 浏览器里一键导出、可视化 UI、PDF/HTML、附件下载等工作流 |

设计原则也很简单：Codex / Claude Code skill 是用户入口；解析、cookie 导出、诊断和格式转换都收敛到 `ixfdoc` 本地执行引擎里，避免每个 agent 集成都重复实现 reader。

## 安装到 Codex / Claude Code

推荐让当前正在使用的 agent 直接完成安装。安装过程会先安装 `ixunfei-docx-reader` Python 包，再把 `ixunfei-docx-reader` skill 注册到 Codex 或 Claude Code。

### 安装到 Codex

如果你正在使用 Codex，可以直接对 Codex 说：

> 请帮我把 https://github.com/serialq7ic4/ixunfei-docx-reader 安装为 Codex skill。使用 GitHub Release wheel 安装本地执行引擎（macOS 用 `[crypto]`，Windows 用 `[windows]`），然后运行 `ixfdoc setup skills --runtimes codex --json` 注册 skill，最后用 `ixfdoc --version` 验证。

手动命令：

```bash
python -m pip install "ixunfei-docx-reader[crypto] @ https://github.com/serialq7ic4/ixunfei-docx-reader/releases/download/v0.1.1/ixunfei_docx_reader-0.1.1-py3-none-any.whl"
ixfdoc setup skills --runtimes codex --json
ixfdoc --version
```

### 安装到 Claude Code

如果你正在使用 Claude Code，可以直接对 Claude Code 说：

> 请帮我把 https://github.com/serialq7ic4/ixunfei-docx-reader 安装为 Claude Code skill。使用 GitHub Release wheel 安装本地执行引擎（macOS 用 `[crypto]`，Windows 用 `[windows]`），然后运行 `ixfdoc setup skills --runtimes claude-code --json` 注册 skill，最后用 `ixfdoc --version` 验证。

手动命令：

```bash
python -m pip install "ixunfei-docx-reader[crypto] @ https://github.com/serialq7ic4/ixunfei-docx-reader/releases/download/v0.1.1/ixunfei_docx_reader-0.1.1-py3-none-any.whl"
ixfdoc setup skills --runtimes claude-code --json
ixfdoc --version
```

### 同时安装到两个 agent

```bash
python -m pip install "ixunfei-docx-reader[crypto] @ https://github.com/serialq7ic4/ixunfei-docx-reader/releases/download/v0.1.1/ixunfei_docx_reader-0.1.1-py3-none-any.whl"
ixfdoc setup skills --runtimes auto --json
ixfdoc --version
```

Windows cookie 导出目前仍是实验支持。Windows 安装时把 `[crypto]` 换成 `[windows]`：

```bash
python -m pip install "ixunfei-docx-reader[windows] @ https://github.com/serialq7ic4/ixunfei-docx-reader/releases/download/v0.1.1/ixunfei_docx_reader-0.1.1-py3-none-any.whl"
```

`crypto` 用于 macOS cookie 解密。Windows 已有 CI 和单元测试覆盖，但还需要在真实 Windows i讯飞/LarkShell 桌面端登录环境验证后，才会提升为 Tier 1 支持。

## 在 Agent 里使用

安装 skill 后，在 Codex / Claude Code 里直接贴 i讯飞/LarkShell 私有文档链接即可，例如：

> 请用 ixunfei-docx-reader 读取并总结这个文档：https://your-domain.xfchat.iflytek.com/wiki/xxxx

也可以让 agent 读取多个链接并综合分析：

> 请用 ixunfei-docx-reader 读取下面 3 个 i讯飞文档，提取关键结论、数据支撑和待办事项：<link-1> <link-2> <link-3>

第一次读取私有文档前，需要先确保本机 i讯飞/LarkShell 桌面端已登录。skill 会通过 `ixfdoc` 复用本机登录态，并把文档转换为本地 Markdown/TSV 供 agent 分析。

## 底层命令

通常不需要手动调用这些命令；它们主要用于调试、自动化或排查登录态问题。

| 命令 | 用途 |
|---|---|
| `ixfdoc setup skills` | 安装 Codex / Claude Code skill |
| `ixfdoc read <source>...` | 将私有链接或本地 Markdown 文件读取为 Markdown/TSV 产物 |
| `ixfdoc cookies export` | 从本机 i讯飞/LarkShell 桌面端会话导出 cookie |
| `ixfdoc doctor` | 检查运行环境和 cookie 元数据，不打印 cookie 值 |
| `ixfdoc --version` | 输出当前本地执行引擎版本 |

## 手动读取流程

如果需要绕过 agent skill 做底层调试，可以手动执行：

1. 打开 i讯飞/LarkShell 桌面端，并确认已经登录。
2. 导出本地会话 cookie。
3. 用 `doctor` 检查 cookie 文件形态，不会打印 cookie 值。
4. 读取一个或多个私有文档链接。

```bash
ixfdoc cookies export \
  --provider auto \
  --output /tmp/ixunfei_profile_explorer_cookies.json

ixfdoc doctor \
  --json \
  --cookies /tmp/ixunfei_profile_explorer_cookies.json

ixfdoc read \
  "https://your-domain.xfchat.iflytek.com/wiki/xxxx" \
  --cookies /tmp/ixunfei_profile_explorer_cookies.json \
  --out-dir ./out \
  --expand-sheets \
  --print-manifest
```

生成的 Markdown 和 TSV 都是本地文件。如果源文档敏感，这些产物也应按敏感数据处理。

常用读取参数：

| 参数 | 用途 |
|---|---|
| `--out-dir <dir>` | 生成产物目录 |
| `--cookies <file>` | `ixfdoc cookies export` 导出的 cookie JSON 文件 |
| `--expand-sheets` | 将支持的嵌入 sheet 展开为 TSV sidecar 文件 |
| `--print-manifest` | 输出 JSON manifest，包含产物路径和元数据 |
| `--cleanup` | 命令退出前删除本次命令生成的文件 |

如果生成文件只在当前 agent run 中临时使用，可以加 `--cleanup`：

```bash
out="$(mktemp -d /tmp/ixfdoc.XXXXXX)"
ixfdoc read "<private-link>" \
  --cookies /tmp/ixunfei_profile_explorer_cookies.json \
  --out-dir "$out" \
  --expand-sheets \
  --print-manifest \
  --cleanup
```

`--cleanup` 只会删除本次命令生成的文件，不会递归删除输出目录里的其他内容。

这些 skill 不重复实现文档解析逻辑。它们调用 `ixfdoc read`，读取 CLI 的 manifest / JSON error contract，并按 CLI 返回的 hint 处理错误。

打包的 skill 源文件在：

- `skills/codex/ixunfei-docx-reader/SKILL.md`
- `skills/claude-code/ixunfei-docx-reader/SKILL.md`

## 支持的来源

当前 reader 覆盖：

- i讯飞/LarkShell `docx` 文档。
- 可解析到受支持文档类型的 i讯飞/LarkShell `wiki` 链接。
- 通过受支持文档 payload 暴露出来的 mindnote / 嵌入 sheet 标记。
- 本地 Markdown 文件，主要用于 skill 和工作流测试。

部分 Feishu/i讯飞 block 格式无法和 Markdown 一一对应。当前转换器优先保证 agent 分析可用，而不是完全还原原始文档视觉效果。

## 支持平台

| 平台 | 状态 | 说明 |
|---|---|---|
| macOS | Tier 1 | 读取 LarkShell Chromium profile，并通过 Keychain 解密 cookie。 |
| Windows | CI-tested / experimental | 读取 LarkShell Chromium profile，并通过 `pywin32` + DPAPI 解密 cookie；还需要真实桌面端验证。 |

Linux 不支持，因为 i讯飞没有 Linux 桌面客户端。

更多细节见 [`docs/supported-platforms.md`](docs/supported-platforms.md)。

## 隐私与安全

- Cookie 导出复用本机桌面端登录态。
- `doctor` 不会打印 cookie 值。
- 生成的 Markdown/TSV 可能包含私有文档内容。
- 不要提交 cookie、生成产物、包含私有链接的日志，或带敏感元数据的诊断输出。
- 本工具仅用于读取你已获授权访问的文档。请遵守所在组织的数据管理要求。

参见 [`PRIVACY.md`](PRIVACY.md) 和 [`SECURITY.md`](SECURITY.md)。

## 开发

```bash
git clone https://github.com/serialq7ic4/ixunfei-docx-reader.git
cd ixunfei-docx-reader
python -m pip install -e ".[crypto,dev]"
python -m compileall -q src
python -m pytest -q
python -m ruff check .
python -m build
scripts/smoke.sh
```

Windows：

```powershell
python -m pip install -e ".[windows,dev]"
scripts\smoke.ps1
```

Release 说明见 [`docs/release.md`](docs/release.md)。JSON 错误契约见 [`docs/error-contract.md`](docs/error-contract.md)。

## 项目状态

已完成：

- 带 JSON error handling 的 CLI package。
- macOS 本地 cookie 导出。
- Windows cookie provider 实现，已有 CI/单元测试覆盖。
- 从原始 skill 迁移的远程私有文档 reader。
- Feishu/i讯飞 docx client-vars 到 Markdown 的转换。
- 嵌入 sheet 展开为 TSV sidecar 文件。
- Codex 和 Claude Code skill 安装。
- GitHub Actions CI 和 tag Release workflow。

已知限制：

- Windows 还没有提升到 Tier 1；需要在真实 Windows i讯飞/LarkShell 桌面端登录环境验证 cookie 导出。

## 许可证

[Apache License 2.0](LICENSE)
