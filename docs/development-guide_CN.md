# Claude Code 权限系统开发指南

> **注意**：本文档记录权限系统的开发过程和技术决策。
>
> **当前版本特性**：
> - 统一配置文件 `permissions.json`
> - 使用 0/1 开关代替复杂逻辑
> - 支持 Glob 通配符匹配
> - 完整的通知系统
> - **完美支持 Windows UNC 路径**
> - 智能项目路径识别
>
> 用户使用指南请参考 [README.md](README.md)。

## 目录
1. [系统概述](#系统概述)
2. [核心发现](#核心发现)
3. [权限系统架构](#权限系统架构)
4. [实现细节](#实现细节)
5. [常见问题与解决方案](#常见问题与解决方案)
6. [最佳实践](#最佳实践)

---

## 系统概述

本文档记录了 Claude Code 动态权限控制系统的完整开发过程，包括技术调研、问题解决和最终实现方案。

### 目标
实现一个无需重启 Claude Code 就能动态切换权限模式的系统，支持：
- 根据 CLI 模式（plan/普通/acceptEdits）自动调整权限
- 通过配置文件快速切换激进模式
- 区分工作区内外的文件操作
- 分级控制不同风险等级的命令

---

## 核心发现

### 1. 环境变量 `CLAUDE_PERMISSION_MODE` 不可用

**错误认知**：
```bash
# ❌ 这种方式不工作
if [ "$CLAUDE_PERMISSION_MODE" != "acceptEdits" ]; then exit 2; fi
```

**真相**：
- `CLAUDE_PERMISSION_MODE` 环境变量在 hook 执行时**不存在**
- 权限模式信息通过 **stdin 的 JSON 输入**传递给 hook
- 必须从 JSON 中提取 `permission_mode` 字段

**正确方式**：
```bash
hook_input=$(cat)
cli_permission_mode=$(echo "$hook_input" | jq -r '.permission_mode // "default"')
```

### 2. PermissionRequest Hook 的限制

**发现**：
- `PermissionRequest` hook 只支持 `"behavior": "allow"` 或 `"behavior": "deny"`
- **不支持** `"behavior": "ask"` 来显示对话框
- 返回 JSON 决策在 PermissionRequest 中**不生效**

**结论**：
PermissionRequest hook 无法实现"动态显示对话框"的需求。

### 3. PreToolUse Hook 是关键

**发现**：
- `PreToolUse` hook 支持 `"permissionDecision": "ask"` 来显示对话框
- `PreToolUse` hook 支持 `"permissionDecision": "allow"` 来自动批准
- 这发生在权限系统之前，可以完全控制流程

**正确实现**：
```bash
# 自动批准
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow"
  }
}
EOF
exit 0

# 显示对话框
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask"
  }
}
EOF
exit 0
```

### 4. Hook 配置的快照机制

**发现**：
- Hook 脚本本身的修改需要重启 Claude Code
- 但 hook 脚本**读取的外部配置文件**修改无需重启
- 这是实现动态切换的关键

**设计原则**：
- Hook 脚本保持不变（或很少修改）
- 所有可变配置放在外部 JSON 文件中
- Hook 每次执行时读取最新配置

### 5. Exit Code 的含义

**测试结果**：
- `exit 0`：继续正常流程
- `exit 1`：记录错误但不阻止执行
- `exit 2`：完全阻止工具执行（但不显示对话框）

**最佳实践**：
使用 JSON 输出 + `exit 0` 来控制权限决策，而不是依赖 exit code。

### 6. Windows UNC 路径问题

**问题发现**：
- Windows CMD 不支持 UNC 路径（如 `\\Mac\Home\...` 或 `\\server\share\...`）作为当前工作目录
- 使用相对路径调用 hook 脚本会失败，提示 "UNC paths are not supported"
- 这在 Mac 虚拟机中的 Windows、网络共享文件夹等场景下会出现

**根本原因**：
```bash
# ❌ 这种方式在 UNC 路径下失败
"command": "python .claude/hooks/unified-hook.py"
# Windows CMD 无法 cd 到 UNC 路径，导致相对路径失效
```

**解决方案**：
1. **使用环境变量构建绝对路径**：
   ```json
   "command": "python \"%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\unified-hook.py\""
   ```

2. **Python 脚本智能获取项目路径**（三层回退）：
   ```python
   # 优先从 hook_data 的 cwd 字段获取
   project_dir = hook_data.get("cwd") or \
                 os.environ.get("CLAUDE_PROJECT_DIR") or \
                 os.getcwd()

   permissions_file = os.path.join(project_dir, ".claude", "permissions.json")
   ```

3. **处理编码问题**：
   ```python
   # 使用 buffer.read() 处理中文路径
   hook_input = sys.stdin.buffer.read().decode('utf-8', errors='replace')
   ```

**适用场景**：
- ✅ Windows UNC 路径（`\\server\share\path`）
- ✅ Mac 虚拟机中的 Windows（Parallels、VMware）
- ✅ 网络共享文件夹
- ✅ 普通 Windows 本地路径（`C:\Users\...`）

### 7. macOS Python 命令问题

**问题发现**：
- macOS 系统中默认没有 `python` 命令，只有 `python3`
- 在非交互式环境（hook 执行）中，`python` 别名不生效
- 导致 hook 执行失败，提示 "python: command not found"

**根本原因**：
```bash
# ❌ 这种方式在 macOS 上失败
"command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/unified-hook.py\""
# macOS 非交互式 shell 中没有 python 命令
```

**解决方案**：
1. **直接执行脚本，利用 shebang**：
   ```json
   "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/unified-hook.py\""
   ```

2. **确保脚本有正确的 shebang 和执行权限**：
   ```python
   #!/usr/bin/env python3
   # 脚本内容...
   ```
   ```bash
   chmod +x .claude/hooks/unified-hook.py
   ```

3. **使用平台专用配置文件**：
   - macOS/Linux: 使用 `settings.local_mac.json`（直接执行脚本）
   - Windows: 使用 `settings.local_win.json`（通过 `python` 命令）

**适用场景**：
- ✅ macOS（所有版本）
- ✅ Linux（大多数发行版）
- ✅ WSL（Windows Subsystem for Linux）

---

## 权限系统架构

### 文件结构
```
.claude/
├── permissions.json              # 统一权限配置（可随时修改）
├── settings.local.json           # Claude Code 配置（需重启生效，根据平台复制）
├── settings.local_mac.json       # macOS/Linux 配置模板
├── settings.local_win.json       # Windows 配置模板
└── hooks/
    └── unified-hook.py           # 统一 Python Hook 脚本（处理所有事件）
```

### 配置文件设计

**permissions.json**（外部配置，无需重启）：
```json
{
  "modes": {
    "default": {
      "read": 1,
      "readAllFiles": 0,
      "edit": 0,
      "editAllFiles": 0,
      "risky": 0,
      "riskyAllFiles": 0,
      "useWeb": 1,
      "useMcp": 1,
      "allowUnknownCommand": 0,
      "globalAllow": 1,
      "globalDeny": 1
    }
  },
  "categories": {
    "read": {
      "tools": ["Read", "Glob", "Grep"],
      "commands": ["ls", "cat", "git status", ...]
    }
  }
}
```

**settings.local.json**（需重启，根据平台选择配置）：

由于不同操作系统对 Python 命令和路径格式的要求不同，需要使用平台专用的配置。

**平台差异**：

| 项目 | macOS/Linux | Windows |
|------|-------------|---------|
| 配置文件 | `settings.local_mac.json` | `settings.local_win.json` |
| 环境变量 | `$CLAUDE_PROJECT_DIR` | `%CLAUDE_PROJECT_DIR%` |
| 路径分隔符 | `/` | `\` |
| 执行方式 | 直接执行脚本（shebang） | `python` 命令 |
| 特殊支持 | - | UNC 路径（`\\server\share`） |

**初始化配置**：
```bash
# macOS/Linux
cp .claude/settings.local_mac.json .claude/settings.local.json

# Windows
copy .claude\settings.local_win.json .claude\settings.local.json
```

**关键改进**：
- 提供平台专用配置模板，避免跨平台兼容性问题
- macOS 使用直接执行方式，解决 `python` 命令不存在的问题
- Windows 使用 `%CLAUDE_PROJECT_DIR%` 环境变量支持 UNC 路径
- 统一的 Python 脚本处理所有平台
- 脚本内部智能获取项目路径（三层回退机制）

### Hook 脚本架构

**统一 Python 脚本**（`unified-hook.py`）：

```python
#!/usr/bin/env python3
import sys
import json
import os

def main():
    # 1. 读取 stdin 的 JSON 输入（处理编码问题）
    hook_input = sys.stdin.buffer.read().decode('utf-8', errors='replace')
    hook_data = json.loads(hook_input)

    # 2. 提取事件类型
    hook_event_name = hook_data.get("hook_event_name", "")

    # 3. 智能获取项目路径（三层回退）
    project_dir = hook_data.get("cwd") or \
                  os.environ.get("CLAUDE_PROJECT_DIR") or \
                  os.getcwd()

    # 4. 读取权限配置文件
    permissions_file = os.path.join(project_dir, ".claude", "permissions.json")
    with open(permissions_file, "r", encoding="utf-8") as f:
        permissions = json.load(f)

    # 5. 根据事件类型分发处理
    if hook_event_name == "PreToolUse":
        handle_pre_tool_use(hook_data, permissions)
    elif hook_event_name == "Stop":
        handle_stop(hook_data, permissions)
    elif hook_event_name == "PermissionRequest":
        handle_permission_request(hook_data, permissions)

def handle_pre_tool_use(hook_data, permissions):
    # 提取 CLI 权限模式
    cli_permission_mode = hook_data.get("permission_mode", "default")

    # 获取当前模式配置
    mode = permissions.get("modes", {}).get(cli_permission_mode, {})

    # 权限决策逻辑...
    decision = "ask"  # 默认询问

    # 输出决策
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision
        }
    }))
```

**关键改进**：
- 使用 `sys.stdin.buffer.read()` 处理编码问题
- 三层回退机制获取项目路径
- 使用 `os.path.join()` 构建跨平台路径
- 单一脚本处理所有事件类型

---

## 实现细节

### 命令分类系统

#### 1. 读取获取类命令
**特征**：只读操作，不修改系统状态

**Bash 命令**：
- `ls`, `cat`, `head`, `tail`, `grep`, `find`
- `git status`, `git log`, `git diff`, `git show`
- `ps`, `top`, `env`, `printenv`
- `curl -s`, `wget --spider`

**Claude 工具**：
- `Read`, `Glob`, `Grep`
- `WebFetch`, `WebSearch`

#### 2. 编辑创建类命令
**特征**：修改文件系统，但风险可控

**Bash 命令**：
- `echo >`, `cat >`, `touch`, `mkdir`
- `mv`, `cp`
- `git add`, `git commit`

**Claude 工具**：
- `Edit`, `Write`

#### 3. 高风险操作类命令
**特征**：不可逆操作或影响远程系统

**Bash 命令**：
- `rm`, `rmdir`
- `chmod`, `chown`
- `git push`, `git pull`, `git reset`, `git rebase`
- `npm install`, `pip install`

### 工作区检测

```bash
# 获取当前工作区路径
WORKSPACE_DIR=$(pwd)

# 从 hook 输入中提取文件路径
file_path=$(echo "$hook_input" | jq -r '.tool_input.file_path // ""')

# 检查是否在工作区内
if [[ "$file_path" == "$WORKSPACE_DIR"* ]]; then
    is_in_workspace=true
else
    is_in_workspace=false
fi
```

### 权限决策逻辑

```bash
# 伪代码示例
function decide_permission() {
    cli_mode = get_cli_mode()           # plan/default/acceptEdits
    aggressive = get_aggressive_mode()   # 0/1
    command_type = classify_command()    # read/edit/risky
    in_workspace = check_workspace()     # true/false

    # Plan 模式
    if cli_mode == "plan":
        if command_type == "read":
            return "allow"
        else:
            return "deny"

    # 普通模式
    if cli_mode == "default":
        if aggressive == 1 && command_type == "read":
            return "allow"
        else:
            return "ask"

    # AcceptEdits 模式
    if cli_mode == "acceptEdits":
        if command_type == "read":
            return "allow"
        if command_type == "edit" && in_workspace:
            return "allow"
        if aggressive == 1:
            return "allow"  # 激进模式：一切允许
        else:
            return "ask"
}
```

---

## 常见问题与解决方案

### Q1: 为什么修改配置后需要重启？

**A**: 分两种情况：
- **Hook 脚本本身**：需要重启（Claude Code 启动时快照化）
- **Hook 读取的配置文件**：无需重启（每次执行时读取）

**解决方案**：
把所有可变配置放在外部 JSON 文件中，hook 脚本保持稳定。

### Q2: 为什么 PermissionRequest hook 不工作？

**A**: PermissionRequest hook 有以下限制：
1. 不支持 `"ask"` 决策
2. 返回的 JSON 决策可能不生效
3. 只能用于简单的 allow/deny 逻辑

**解决方案**：
使用 PreToolUse hook 代替，它支持完整的权限控制。

### Q3: 如何区分工作区内外的文件？

**A**: 从 hook 输入的 JSON 中提取文件路径：

```bash
# 对于 Edit/Write 工具
file_path=$(echo "$hook_input" | jq -r '.tool_input.file_path // ""')

# 对于 Bash 命令
command=$(echo "$hook_input" | jq -r '.tool_input.command // ""')
# 需要解析命令字符串提取路径
```

### Q4: 如何处理 Edit/Write 等内置工具？

**A**: 两种方案：
1. **为每个工具添加 PreToolUse hook**（推荐）
2. **依赖 Claude Code 的内置 acceptEdits 模式**（简单但不够灵活）

### Q5: Hook 脚本如何调试？

**A**: 添加日志输出：

```python
# Python 版本
import os
import platform

# 确定日志路径
if platform.system() == "Windows":
    DEBUG_LOG = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "claude-hook-debug.log")
else:
    DEBUG_LOG = "/tmp/claude-hook-debug.log"

def log_debug(message):
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")

# 使用
log_debug(f"CLI Mode: {cli_permission_mode}")
log_debug(f"Decision: {decision}")
```

**查看日志**：
```bash
# macOS/Linux
tail -f /tmp/claude-hook-debug.log

# Windows
Get-Content $env:TEMP\claude-hook-debug.log -Tail 20 -Wait
```

### Q6: Windows UNC 路径下 Hook 执行失败怎么办？

**A**: 使用 Windows 专用配置文件。

**问题症状**：
- 错误信息：`UNC paths are not supported`
- 工作目录是 `\\server\share\...` 格式

**解决方案**：
```bash
# 复制 Windows 配置模板
copy .claude\settings.local_win.json .claude\settings.local.json
```
然后重启 Claude Code。

**技术细节**：参见"核心发现"第 6 点。

### Q7: macOS 上提示 "python: command not found" 怎么办？

**A**: 使用 macOS 专用配置文件。

**问题症状**：
- 错误信息：`/bin/sh: python: command not found`
- 在 macOS 或 Linux 系统上

**解决方案**：
```bash
# 复制 macOS 配置模板
cp .claude/settings.local_mac.json .claude/settings.local.json
```
然后重启 Claude Code。

**技术细节**：参见"核心发现"第 7 点。

---

## 最佳实践

### 1. 配置文件设计

✅ **推荐**：
```json
{
  "_comment": "清晰的注释说明",
  "aggressiveMode": 0,
  "customSettings": {
    "enableDebug": false
  }
}
```

❌ **避免**：
```json
{
  "mode": 2,  // 不清楚含义
  "flag": true  // 没有注释
}
```

### 2. Hook 脚本编写

✅ **推荐**：
- 使用 `jq` 解析 JSON（可靠）
- 明确的错误处理
- 清晰的注释
- 统一的输出格式

❌ **避免**：
- 使用 `grep`/`sed` 解析 JSON（不可靠）
- 依赖环境变量
- 复杂的嵌套逻辑

### 3. 权限分级

✅ **推荐**：
- 明确的命令分类
- 渐进式的权限提升
- 工作区内外区分

❌ **避免**：
- 一刀切的权限控制
- 过于复杂的规则
- 不区分风险等级

### 4. 用户体验

✅ **推荐**：
- 提供清晰的状态提示
- 支持快速切换模式
- 无需重启的配置更新

❌ **避免**：
- 频繁的权限询问
- 不清楚的错误信息
- 需要重启才能生效

### 5. 安全考虑

✅ **推荐**：
- 默认保守的权限设置
- 高风险操作需要明确确认
- 记录关键操作日志

❌ **避免**：
- 默认开启激进模式
- 跳过高风险操作确认
- 没有操作审计

---

## 测试清单

### 基础功能测试
- [ ] 普通模式下所有命令显示对话框
- [ ] acceptEdits 模式下工作区内文件自动通过
- [ ] acceptEdits 模式下工作区外文件显示对话框
- [ ] 激进模式下所有命令自动通过

### 配置切换测试
- [ ] 修改 aggressiveMode 无需重启立即生效
- [ ] CLI 模式切换（Shift+Tab）立即生效
- [ ] 配置文件格式错误时有合理的降级行为

### 边界情况测试
- [ ] 配置文件不存在时的默认行为
- [ ] jq 命令不可用时的降级方案
- [ ] 超长命令字符串的处理
- [ ] 特殊字符路径的处理

### 性能测试
- [ ] Hook 执行时间 < 100ms
- [ ] 不影响正常命令执行速度
- [ ] 大量连续命令时的稳定性

---

## 版本历史

### v1.0 - 初始实现
- 基础的 PermissionRequest hook（后证明不可行）
- 使用环境变量 `CLAUDE_PERMISSION_MODE`（不存在）

### v2.0 - 重大重构
- 切换到 PreToolUse hook
- 从 JSON 输入读取权限模式
- 支持 `"ask"` 决策显示对话框

### v3.0 - 统一配置版本
- 完整的命令分类系统
- 工作区内外区分
- 激进模式开关
- 无需重启的配置更新

### v3.1 - 功能增强
- 新增 `allowUnknownCommand` 开关控制未分类命令
- 合并文档到 README.md
- 更新脚本文件名为 `check-permissions.sh`

### v3.2 - 统一 Python 脚本版本
- 使用单一 Python 脚本 `unified-hook.py` 替代多平台脚本
- 完美支持 Windows UNC 路径
- 智能项目路径识别（三层回退机制）
- 自动处理中文路径编码问题
- 所有平台使用统一配置

### v3.3 - 当前版本
- 优化路径获取策略
- 完善 UNC 路径支持文档
- 添加详细的故障排查指南
- 更新所有示例代码为 Python 版本
- 添加平台专用配置文件（`settings.local_mac.json` 和 `settings.local_win.json`）
- 解决 macOS 上 `python: command not found` 问题
- 解决 Windows UNC 路径下的执行问题
- 提供跨平台切换指南

---

## 参考资源

### 官方文档
- [Claude Code Hooks 文档](https://docs.anthropic.com/claude-code/hooks)
- [Permission System 说明](https://docs.anthropic.com/claude-code/permissions)

### 关键发现来源
- PreToolUse hook 支持 `"ask"` 决策：官方文档确认
- Hook 输入 JSON 格式：通过实际测试和日志分析
- 配置快照机制：官方文档说明

### 社区资源
- GitHub Issues: claude-code 权限相关讨论
- Discord: Claude Code 开发者频道

---

## 附录

### A. Hook 输入 JSON 格式示例

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../transcript.jsonl",
  "cwd": "/Users/.../project",
  "permission_mode": "acceptEdits",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "chmod +x script.sh",
    "description": "给脚本添加执行权限"
  }
}
```

### B. 完整的 Hook 脚本模板

见项目文件：`.claude/hooks/unified-hook.py`

**关键特性**：
- 统一处理 PreToolUse、Stop、PermissionRequest 三种事件
- 智能项目路径识别（支持 UNC 路径）
- 完整的命令分类和权限决策逻辑
- 跨平台桌面通知支持
- 详细的调试日志

**路径获取策略**：
```python
# 三层回退机制
project_dir = hook_data.get("cwd") or \
              os.environ.get("CLAUDE_PROJECT_DIR") or \
              os.getcwd()

# 构建配置文件路径
permissions_file = os.path.join(project_dir, ".claude", "permissions.json")
```

**编码处理**：
```python
# 处理中文路径和特殊字符
hook_input = sys.stdin.buffer.read().decode('utf-8', errors='replace')
```

### C. 权限矩阵完整版

见下一节的详细权限矩阵设计。

---

**文档维护者**: Claude Code 权限系统开发团队
**最后更新**: 2026-01-26
**文档版本**: 3.3

**主要更新内容**：
- 添加 Windows UNC 路径问题解决方案
- 更新为统一 Python 脚本架构
- 完善跨平台配置说明
- 添加智能路径识别机制文档