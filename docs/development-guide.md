# Claude Code Permission System Development Guide

> **Note**: This document records the development process and technical decisions of the permission system.
>
> **Current Version Features**:
> - Unified configuration file `permissions.json`
> - Use 0/1 switches instead of complex logic
> - Support Glob wildcard matching
> - Complete notification system
> - **Perfect Windows UNC path support**
> - Smart project path identification
>
> For user guide, please refer to [README.md](../README.md).

## Table of Contents
1. [System Overview](#system-overview)
2. [Core Discoveries](#core-discoveries)
3. [Permission System Architecture](#permission-system-architecture)
4. [Implementation Details](#implementation-details)
5. [Common Issues and Solutions](#common-issues-and-solutions)
6. [Best Practices](#best-practices)

---

## System Overview

This document records the complete development process of the Claude Code dynamic permission control system, including technical research, problem-solving, and final implementation.

### Goals
Implement a system that can dynamically switch permission modes without restarting Claude Code, supporting:
- Automatically adjust permissions based on CLI mode (plan/normal/acceptEdits)
- Quickly switch aggressive mode through configuration file
- Distinguish file operations inside and outside workspace
- Hierarchical control of commands with different risk levels

---

## Core Discoveries

### 1. Environment Variable `CLAUDE_PERMISSION_MODE` Not Available

**Misconception**:
```bash
# ❌ This doesn't work
if [ "$CLAUDE_PERMISSION_MODE" != "acceptEdits" ]; then exit 2; fi
```

**Truth**:
- `CLAUDE_PERMISSION_MODE` environment variable **does not exist** during hook execution
- Permission mode information is passed to hook via **JSON input from stdin**
- Must extract `permission_mode` field from JSON

**Correct Way**:
```bash
hook_input=$(cat)
cli_permission_mode=$(echo "$hook_input" | jq -r '.permission_mode // "default"')
```

### 2. Limitations of PermissionRequest Hook

**Discovery**:
- `PermissionRequest` hook only supports `"behavior": "allow"` or `"behavior": "deny"`
- **Does not support** `"behavior": "ask"` to show dialog
- JSON decision return does not work in PermissionRequest

**Conclusion**:
PermissionRequest hook cannot implement "dynamically show dialog" requirement.

### 3. PreToolUse Hook is Key

**Discovery**:
- `PreToolUse` hook supports `"permissionDecision": "ask"` to show dialog
- `PreToolUse` hook supports `"permissionDecision": "allow"` to auto-approve
- This happens before the permission system, can fully control the flow

**Correct Implementation**:
```bash
# Auto-approve
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow"
  }
}
EOF
exit 0

# Show dialog
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

### 4. Hook Configuration Snapshot Mechanism

**Discovery**:
- Modifications to hook script itself require restarting Claude Code
- But **external configuration files read by hook script** don't require restart
- This is key to implementing dynamic switching

**Design Principle**:
- Keep hook script unchanged (or rarely modified)
- Put all variable configuration in external JSON file
- Hook reads latest configuration on each execution

### 5. Meaning of Exit Codes

**Test Results**:
- `exit 0`: Continue normal flow
- `exit 1`: Log error but don't block execution
- `exit 2`: Completely block tool execution (but don't show dialog)

**Best Practice**:
Use JSON output + `exit 0` to control permission decisions, rather than relying on exit codes.

### 6. Windows UNC Path Issues

**Problem Discovery**:
- Windows CMD doesn't support UNC paths (like `\\Mac\Home\...` or `\\server\share\...`) as current working directory
- Calling hook script with relative path fails with "UNC paths are not supported"
- This occurs in Windows in Mac VMs, network shared folders, etc.

**Root Cause**:
```bash
# ❌ This fails under UNC paths
"command": "python .claude/hooks/unified-hook.py"
# Windows CMD cannot cd to UNC path, causing relative path to fail
```

**Solution**:
1. **Use environment variable to build absolute path**:
   ```json
   "command": "python \"%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\unified-hook.py\""
   ```

2. **Python script intelligently gets project path** (three-tier fallback):
   ```python
   # Priority: get from hook_data's cwd field
   project_dir = hook_data.get("cwd") or \
                 os.environ.get("CLAUDE_PROJECT_DIR") or \
                 os.getcwd()

   permissions_file = os.path.join(project_dir, ".claude", "permissions.json")
   ```

3. **Handle encoding issues**:
   ```python
   # Use buffer.read() to handle Chinese paths
   hook_input = sys.stdin.buffer.read().decode('utf-8', errors='replace')
   ```

**Applicable Scenarios**:
- ✅ Windows UNC paths (`\\server\share\path`)
- ✅ Windows in Mac VMs (Parallels, VMware)
- ✅ Network shared folders
- ✅ Normal Windows local paths (`C:\Users\...`)

### 7. macOS Python Command Issues

**Problem Discovery**:
- macOS systems don't have `python` command by default, only `python3`
- In non-interactive environments (hook execution), `python` alias doesn't work
- Causes hook execution to fail with "python: command not found"

**Root Cause**:
```bash
# ❌ This fails on macOS
"command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/unified-hook.py\""
# macOS non-interactive shell doesn't have python command
```

**Solution**:
1. **Execute script directly, using shebang**:
   ```json
   "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/unified-hook.py\""
   ```

2. **Ensure script has correct shebang and execute permission**:
   ```python
   #!/usr/bin/env python3
   # Script content...
   ```
   ```bash
   chmod +x .claude/hooks/unified-hook.py
   ```

3. **Use platform-specific configuration files**:
   - macOS/Linux: Use `settings.local_mac.json` (execute script directly)
   - Windows: Use `settings.local_win.json` (via `python` command)

**Applicable Scenarios**:
- ✅ macOS (all versions)
- ✅ Linux (most distributions)
- ✅ WSL (Windows Subsystem for Linux)

---

## Permission System Architecture

### File Structure
```
.claude/
├── permissions.json              # Unified permission config (can be modified anytime)
├── settings.local.json           # Claude Code config (requires restart, copy based on platform)
├── settings.local_mac.json       # macOS/Linux config template
├── settings.local_win.json       # Windows config template
└── hooks/
    └── unified-hook.py           # Unified Python Hook script (handles all events)
```

### Configuration File Design

**permissions.json** (external config, no restart required):
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

**settings.local.json** (requires restart, choose config based on platform):

Due to different OS requirements for Python commands and path formats, platform-specific configurations are needed.

**Platform Differences**:

| Item | macOS/Linux | Windows |
|------|-------------|---------|
| Config File | `settings.local_mac.json` | `settings.local_win.json` |
| Environment Variable | `$CLAUDE_PROJECT_DIR` | `%CLAUDE_PROJECT_DIR%` |
| Path Separator | `/` | `\` |
| Execution Method | Direct script execution (shebang) | `python` command |
| Special Support | - | UNC paths (`\\server\share`) |

**Initialize Configuration**:
```bash
# macOS/Linux
cp .claude/settings.local_mac.json .claude/settings.local.json

# Windows
copy .claude\settings.local_win.json .claude\settings.local.json
```

**Key Improvements**:
- Provide platform-specific config templates to avoid cross-platform compatibility issues
- macOS uses direct execution to solve `python` command not found issue
- Windows uses `%CLAUDE_PROJECT_DIR%` environment variable to support UNC paths
- Unified Python script handles all platforms
- Script internally gets project path intelligently (three-tier fallback mechanism)

### Hook Script Architecture

**Unified Python Script** (`unified-hook.py`):

```python
#!/usr/bin/env python3
import sys
import json
import os

def main():
    # 1. Read JSON input from stdin (handle encoding issues)
    hook_input = sys.stdin.buffer.read().decode('utf-8', errors='replace')
    hook_data = json.loads(hook_input)

    # 2. Extract event type
    hook_event_name = hook_data.get("hook_event_name", "")

    # 3. Intelligently get project path (three-tier fallback)
    project_dir = hook_data.get("cwd") or \
                  os.environ.get("CLAUDE_PROJECT_DIR") or \
                  os.getcwd()

    # 4. Read permission config file
    permissions_file = os.path.join(project_dir, ".claude", "permissions.json")
    with open(permissions_file, "r", encoding="utf-8") as f:
        permissions = json.load(f)

    # 5. Dispatch handling based on event type
    if hook_event_name == "PreToolUse":
        handle_pre_tool_use(hook_data, permissions)
    elif hook_event_name == "Stop":
        handle_stop(hook_data, permissions)
    elif hook_event_name == "PermissionRequest":
        handle_permission_request(hook_data, permissions)

def handle_pre_tool_use(hook_data, permissions):
    # Extract CLI permission mode
    cli_permission_mode = hook_data.get("permission_mode", "default")

    # Get current mode config
    mode = permissions.get("modes", {}).get(cli_permission_mode, {})

    # Permission decision logic...
    decision = "ask"  # Default ask

    # Output decision
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision
        }
    }))
```

**Key Improvements**:
- Use `sys.stdin.buffer.read()` to handle encoding issues
- Three-tier fallback mechanism to get project path
- Use `os.path.join()` to build cross-platform paths
- Single script handles all event types

---

## Implementation Details

### Command Classification System

#### 1. Read/Retrieve Commands
**Characteristics**: Read-only operations, don't modify system state

**Bash Commands**:
- `ls`, `cat`, `head`, `tail`, `grep`, `find`
- `git status`, `git log`, `git diff`, `git show`
- `ps`, `top`, `env`, `printenv`
- `curl -s`, `wget --spider`

**Claude Tools**:
- `Read`, `Glob`, `Grep`
- `WebFetch`, `WebSearch`

#### 2. Edit/Create Commands
**Characteristics**: Modify file system, but controllable risk

**Bash Commands**:
- `echo >`, `cat >`, `touch`, `mkdir`
- `mv`, `cp`
- `git add`, `git commit`

**Claude Tools**:
- `Edit`, `Write`

#### 3. High-Risk Operation Commands
**Characteristics**: Irreversible operations or affect remote systems

**Bash Commands**:
- `rm`, `rmdir`
- `chmod`, `chown`
- `git push`, `git pull`, `git reset`, `git rebase`
- `npm install`, `pip install`

### Workspace Detection

```bash
# Get current workspace path
WORKSPACE_DIR=$(pwd)

# Extract file path from hook input
file_path=$(echo "$hook_input" | jq -r '.tool_input.file_path // ""')

# Check if inside workspace
if [[ "$file_path" == "$WORKSPACE_DIR"* ]]; then
    is_in_workspace=true
else
    is_in_workspace=false
fi
```

### Permission Decision Logic

```bash
# Pseudocode example
function decide_permission() {
    cli_mode = get_cli_mode()           # plan/default/acceptEdits
    aggressive = get_aggressive_mode()   # 0/1
    command_type = classify_command()    # read/edit/risky
    in_workspace = check_workspace()     # true/false

    # Plan mode
    if cli_mode == "plan":
        if command_type == "read":
            return "allow"
        else:
            return "deny"

    # Normal mode
    if cli_mode == "default":
        if aggressive == 1 && command_type == "read":
            return "allow"
        else:
            return "ask"

    # AcceptEdits mode
    if cli_mode == "acceptEdits":
        if command_type == "read":
            return "allow"
        if command_type == "edit" && in_workspace:
            return "allow"
        if aggressive == 1:
            return "allow"  # Aggressive mode: allow everything
        else:
            return "ask"
}
```

---

## Common Issues and Solutions

### Q1: Why does configuration require restart after modification?

**A**: Two cases:
- **Hook script itself**: Requires restart (snapshotted at Claude Code startup)
- **Config files read by hook**: No restart required (read on each execution)

**Solution**:
Put all variable configuration in external JSON file, keep hook script stable.

### Q2: Why doesn't PermissionRequest hook work?

**A**: PermissionRequest hook has the following limitations:
1. Doesn't support `"ask"` decision
2. Returned JSON decision may not work
3. Can only be used for simple allow/deny logic

**Solution**:
Use PreToolUse hook instead, which supports full permission control.

### Q3: How to distinguish files inside and outside workspace?

**A**: Extract file path from hook input JSON:

```bash
# For Edit/Write tools
file_path=$(echo "$hook_input" | jq -r '.tool_input.file_path // ""')

# For Bash commands
command=$(echo "$hook_input" | jq -r '.tool_input.command // ""')
# Need to parse command string to extract path
```

### Q4: How to handle built-in tools like Edit/Write?

**A**: Two approaches:
1. **Add PreToolUse hook for each tool** (recommended)
2. **Rely on Claude Code's built-in acceptEdits mode** (simple but less flexible)

### Q5: How to debug hook scripts?

**A**: Add log output:

```python
# Python version
import os
import platform

# Determine log path
if platform.system() == "Windows":
    DEBUG_LOG = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "claude-hook-debug.log")
else:
    DEBUG_LOG = "/tmp/claude-hook-debug.log"

def log_debug(message):
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")

# Usage
log_debug(f"CLI Mode: {cli_permission_mode}")
log_debug(f"Decision: {decision}")
```

**View logs**:
```bash
# macOS/Linux
tail -f /tmp/claude-hook-debug.log

# Windows
Get-Content $env:TEMP\claude-hook-debug.log -Tail 20 -Wait
```

### Q6: What to do when Hook execution fails under Windows UNC paths?

**A**: Use Windows-specific configuration file.

**Problem Symptoms**:
- Error message: `UNC paths are not supported`
- Working directory is in `\\server\share\...` format

**Solution**:
```bash
# Copy Windows config template
copy .claude\settings.local_win.json .claude\settings.local.json
```
Then restart Claude Code.

**Technical Details**: See Core Discoveries point 6.

### Q7: What to do when "python: command not found" on macOS?

**A**: Use macOS-specific configuration file.

**Problem Symptoms**:
- Error message: `/bin/sh: python: command not found`
- On macOS or Linux systems

**Solution**:
```bash
# Copy macOS config template
cp .claude/settings.local_mac.json .claude/settings.local.json
```
Then restart Claude Code.

**Technical Details**: See Core Discoveries point 7.

---

## Best Practices

### 1. Configuration File Design

✅ **Recommended**:
```json
{
  "_comment": "Clear explanatory comments",
  "aggressiveMode": 0,
  "customSettings": {
    "enableDebug": false
  }
}
```

❌ **Avoid**:
```json
{
  "mode": 2,  // Unclear meaning
  "flag": true  // No comments
}
```

### 2. Hook Script Writing

✅ **Recommended**:
- Use `jq` to parse JSON (reliable)
- Explicit error handling
- Clear comments
- Unified output format

❌ **Avoid**:
- Use `grep`/`sed` to parse JSON (unreliable)
- Rely on environment variables
- Complex nested logic

### 3. Permission Hierarchy

✅ **Recommended**:
- Clear command classification
- Progressive permission elevation
- Distinguish inside/outside workspace

❌ **Avoid**:
- One-size-fits-all permission control
- Overly complex rules
- No risk level distinction

### 4. User Experience

✅ **Recommended**:
- Provide clear status indicators
- Support quick mode switching
- Configuration updates without restart

❌ **Avoid**:
- Frequent permission prompts
- Unclear error messages
- Require restart to take effect

### 5. Security Considerations

✅ **Recommended**:
- Default conservative permission settings
- High-risk operations require explicit confirmation
- Log critical operations

❌ **Avoid**:
- Default aggressive mode enabled
- Skip high-risk operation confirmation
- No operation audit

---

## Test Checklist

### Basic Function Tests
- [ ] All commands show dialog in normal mode
- [ ] Files inside workspace auto-approved in acceptEdits mode
- [ ] Files outside workspace show dialog in acceptEdits mode
- [ ] All commands auto-approved in aggressive mode

### Configuration Switching Tests
- [ ] Modifying aggressiveMode takes effect immediately without restart
- [ ] CLI mode switching (Shift+Tab) takes effect immediately
- [ ] Reasonable fallback behavior when config file format is wrong

### Edge Case Tests
- [ ] Default behavior when config file doesn't exist
- [ ] Fallback plan when jq command unavailable
- [ ] Handling of very long command strings
- [ ] Handling of special character paths

### Performance Tests
- [ ] Hook execution time < 100ms
- [ ] Doesn't affect normal command execution speed
- [ ] Stability with many consecutive commands

---

## Version History

### v1.0 - Initial Implementation
- Basic PermissionRequest hook (later proved unfeasible)
- Use environment variable `CLAUDE_PERMISSION_MODE` (doesn't exist)

### v2.0 - Major Refactor
- Switch to PreToolUse hook
- Read permission mode from JSON input
- Support `"ask"` decision to show dialog

### v3.0 - Unified Configuration Version
- Complete command classification system
- Distinguish inside/outside workspace
- Aggressive mode switch
- Configuration updates without restart

### v3.1 - Feature Enhancement
- Add `allowUnknownCommand` switch to control unclassified commands
- Merge documentation into README.md
- Update script filename to `check-permissions.sh`

### v3.2 - Unified Python Script Version
- Use single Python script `unified-hook.py` to replace multi-platform scripts
- Perfect Windows UNC path support
- Smart project path identification (three-tier fallback mechanism)
- Automatically handle Chinese path encoding issues
- All platforms use unified configuration

### v3.3 - Current Version
- Optimize path retrieval strategy
- Improve UNC path support documentation
- Add detailed troubleshooting guide
- Update all example code to Python version
- Add platform-specific config files (`settings.local_mac.json` and `settings.local_win.json`)
- Solve `python: command not found` issue on macOS
- Solve execution issues under Windows UNC paths
- Provide cross-platform switching guide

---

## Reference Resources

### Official Documentation
- [Claude Code Hooks Documentation](https://docs.anthropic.com/claude-code/hooks)
- [Permission System Description](https://docs.anthropic.com/claude-code/permissions)

### Key Discovery Sources
- PreToolUse hook supports `"ask"` decision: Confirmed by official documentation
- Hook input JSON format: Through actual testing and log analysis
- Configuration snapshot mechanism: Official documentation explanation

### Community Resources
- GitHub Issues: Claude Code permission-related discussions
- Discord: Claude Code developer channel

---

## Appendix

### A. Hook Input JSON Format Example

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
    "description": "Add execute permission to script"
  }
}
```

### B. Complete Hook Script Template

See project file: `.claude/hooks/unified-hook.py`

**Key Features**:
- Unified handling of PreToolUse, Stop, PermissionRequest three event types
- Smart project path identification (supports UNC paths)
- Complete command classification and permission decision logic
- Cross-platform desktop notification support
- Detailed debug logging

**Path Retrieval Strategy**:
```python
# Three-tier fallback mechanism
project_dir = hook_data.get("cwd") or \
              os.environ.get("CLAUDE_PROJECT_DIR") or \
              os.getcwd()

# Build config file path
permissions_file = os.path.join(project_dir, ".claude", "permissions.json")
```

**Encoding Handling**:
```python
# Handle Chinese paths and special characters
hook_input = sys.stdin.buffer.read().decode('utf-8', errors='replace')
```

### C. Complete Permission Matrix

See next section for detailed permission matrix design.

---

**Document Maintainer**: Claude Code Permission System Development Team
**Last Updated**: 2026-01-26
**Document Version**: 3.3

**Major Updates**:
- Add Windows UNC path issue solutions
- Update to unified Python script architecture
- Improve cross-platform configuration instructions
- Add smart path identification mechanism documentation
