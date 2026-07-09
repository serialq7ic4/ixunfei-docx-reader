# 贡献指南

**简体中文** | [English](CONTRIBUTING.en.md)

感谢你帮助改进 `ixunfei-docx-reader`。这个项目处理私有文档工作流，因此贡献质量不仅包括代码正确性，也包括数据安全纪律。

## 适用范围

适合贡献的方向通常包括：

- 支持更多已授权的 i讯飞/LarkShell 来源类型读取。
- 更安全的本地诊断能力和更清晰的错误契约。
- 提升已支持载荷的 Markdown/TSV 转换保真度。
- 提升 macOS/Windows 本地 cookie 导出可靠性。
- 改进文档、安装、更新和发布流程。

除非先讨论清楚，否则以下方向不在默认范围内：

- 托管服务、遥测、后台守护进程或浏览器扩展。
- Linux 桌面会话支持，因为 i讯飞没有发布 Linux 桌面客户端。
- 没有明确权限模型和维护者共识的开放平台 / OpenAPI 鉴权模式。

## 隐私规则

不要在 issue、pull request、commit、测试、日志或截图中包含私有数据。

不要分享：

- Cookie 文件或 cookie 值。
- CSRF token。
- 完整私有文档 URL 或文档 token。
- 来自私有文档的原始内部 API 响应。
- 包含私有内容的生成 Markdown/TSV/manifest。

报告诊断信息时，请先检查并脱敏输出。`ixfdoc doctor --json` 和 `ixfdoc inspect <source> --json` 旨在提供更安全的摘要，但贡献者仍然需要自行确认粘贴内容是否安全。

## 提交 Issue 前

1. 搜索已有 issue 和近期 release。
2. 如条件允许，先升级到最新 GitHub Release wheel。
3. 运行：

```bash
ixfdoc --version
ixfdoc doctor --json
ixfdoc inspect "<redacted-source>" --json
```

4. 只提供脱敏后的输出和最小复现。

如果是渲染问题，优先使用合成的 `client_vars` fixture 或精简脱敏后的 block payload，而不是私有源数据。

## Pull Request 检查清单

提交 PR 前请运行：

```bash
python -m compileall -q src
python -m pytest -q
python -m ruff check .
```

如果改动影响打包或发布行为，也请运行：

```bash
python -m build
scripts/smoke.sh
ixfdoc update skills --runtimes none --json
ixfdoc update check --json
```

PR 应包含：

- 清晰的问题说明和用户可感知的行为变化。
- 行为变更对应的测试，尤其是 parser、converter、CLI、cookie 或诊断相关改动。
- 当命令、安全行为、支持来源或安装/更新流程变化时，同步更新文档。
- 面向用户的变化需要更新 `CHANGELOG.md`。

## 代码规范

- 以 `ixfdoc` 作为事实来源；skill 应保持为 CLI 的轻量包装。
- 保持本地优先行为：不做遥测、不引入托管服务、不静默上传。
- 优先提交小而可审查的变更，并配套聚焦测试。
- 除非 PR 明确修改并记录错误契约，否则保持 JSON 错误契约稳定。
- 不要在错误、诊断、测试或日志中打印 secret。
- 对派生输出，优先使用确定性的文件名、稳定的 manifest 和可复现的转换行为。

## 测试 Fixture

尽量使用合成 fixture。如果真实文档暴露了 bug，请将其缩减为最小的脱敏 payload 来复现问题。

推荐的 fixture 风格：

- 使用 `doxfixturetoken`、`wiki_fixture` 或 `okr_fixture` 等假 token。
- 使用 `tenant.xfchat.iflytek.com` 等通用 host。
- 保持文档文本短小且不敏感。
- 断言命令输出中不会出现私有 token 或 cookie 值。

## Release Notes

维护者发布版本时应遵循 `docs/release.md`。每个 release 都必须包含从 `CHANGELOG.md` 派生的非空 GitHub Release notes，并附带 wheel 和 source distribution 产物。
