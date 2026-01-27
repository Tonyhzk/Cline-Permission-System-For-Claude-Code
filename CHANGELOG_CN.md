# 更新日志

本项目的所有重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 新增
- **图形化配置编辑器**：添加了用于编辑 permissions.json 的图形用户界面
  - 中文版本：`src/zh_CN/.claude/permission_gui.py`
  - 英文版本：`src/en_US/.claude/permission_gui.py`
  - 功能特性：
    - 使用复选框进行可视化模式配置
    - 通知设置编辑器
    - 工具和命令列表的多行文本框
    - 导入/导出功能
    - 实时配置验证
- 为高风险命令添加通配符前缀模式（`*rm *`、`*rmdir *`、`*chmod *`、`*chown *`）

### 变更
- 更新 README 文档，添加 GUI 编辑器使用说明
- 修正 README 中的通知配置示例，使其与实际配置文件一致
- 改进使用场景中的模式配置示例
- 更新 `.gitignore`，仅忽略根目录的 `.claude/` 目录（不影响模板目录）

### 移除
- 移除模式配置中未使用的 `enabled` 字段（代码中未实际使用）

### 修复
- 修正 `default` 模式的 `readAllFiles` 设置（文档中从 0 改为 1）
- 修正 `acceptEdits` 模式设置，使其与模板文件一致
- 更正 README 示例中的通知声音设置
- 修正高风险命令模式，添加通配符前缀版本

## [1.0.0] - 2026-01-26

### 新增
- Cline Permission System for Claude Code 首次发布
- 统一的 Python Hook 脚本（`unified-hook.py`），支持所有平台
- 跨平台支持（macOS、Linux、Windows）
- 三种 CLI 模式：`plan`、`default`、`acceptEdits`
- 权限分类：read、edit、risky、useWeb、useMcp、globalAllow、globalDeny
- 命令匹配的 Glob 通配符支持
- 桌面通知系统
- Windows UNC 路径支持
- 智能路径检测，三层回退机制
- 中英文完整文档

### 功能特性
- **统一配置**：单一 `permissions.json` 文件管理所有设置
- **工作区保护**：区分工作区内外操作
- **无需重启**：配置更改立即生效
- **调试日志**：详细的权限决策日志，便于故障排查
- **平台专用配置**：为 macOS/Linux 和 Windows 提供独立模板

---

## 版本历史

- **未发布**：GUI 编辑器、配置修复、文档改进
- **1.0.0**（2026-01-26）：核心权限系统首次发布

---

**维护者**：Tony HZK ([@Tonyhzk](https://github.com/Tonyhzk))
**项目地址**：[Cline-Permission-System-For-Claude-Code](https://github.com/Tonyhzk/Cline-Permission-System-For-Claude-Code)