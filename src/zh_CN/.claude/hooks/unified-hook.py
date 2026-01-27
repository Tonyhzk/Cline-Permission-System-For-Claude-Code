#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code 统一 Hook 脚本 - Python 版本
支持 PreToolUse、Stop、PermissionRequest 三种事件
解决跨平台兼容性问题（特别是 Mac 虚拟机中的 Windows UNC 路径）
"""

import sys
import json
import re
import os
import subprocess
from datetime import datetime
import platform

# 调试日志路径
if platform.system() == "Windows":
    DEBUG_LOG = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "claude-hook-debug.log")
else:
    DEBUG_LOG = "/tmp/claude-hook-debug.log"


def log_debug(message):
    """写入调试日志"""
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
    except Exception:
        pass


def output_result(hook_event_name, **kwargs):
    """输出 Hook 结果"""
    result = {
        "hookSpecificOutput": {
            "hookEventName": hook_event_name,
            **kwargs
        }
    }
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


def match_glob(text, pattern):
    """
    Glob 模式匹配
    支持 * (匹配任意字符) 和 ? (匹配单个字符)
    """
    regex_pattern = re.escape(pattern)
    regex_pattern = regex_pattern.replace(r'\*', '.*').replace(r'\?', '.')
    return bool(re.match(f"^{regex_pattern}$", text))


def check_in_list(item, permissions, category, list_type):
    """检查工具或命令是否在指定列表中（支持 Glob）"""
    try:
        item_list = permissions.get("categories", {}).get(category, {}).get(list_type, [])
        for pattern in item_list:
            if match_glob(item, pattern):
                log_debug(f"  匹配到模式: {pattern}")
                return True
    except Exception as e:
        log_debug(f"  检查列表时出错: {e}")
    return False


def extract_paths_from_command(command):
    """从命令中提取路径参数"""
    args = re.sub(r'^[^\s]+\s+', '', command)

    path_patterns = [
        r'[A-Za-z]:[/\\][^\s]*',      # Windows 绝对路径
        r'\\\\[^\s]+\\[^\s]*',         # UNC 路径 (反斜杠)
        r'//[^\s]+/[^\s]*',            # UNC 路径 (正斜杠)
        r'/[^\s]*',                    # Unix 绝对路径
        r'~[^\s]*',                    # 用户目录
        r'\./[^\s]*',                  # 相对路径 ./
        r'\.\./[^\s]*'                 # 相对路径 ../
    ]

    paths = []
    for pattern in path_patterns:
        matches = re.findall(pattern, args)
        paths.extend(matches)

    return paths


def normalize_path(path):
    """标准化路径"""
    normalized = path.replace('\\', '/')

    if normalized.startswith('//'):
        return normalized

    if re.match(r'^[A-Za-z]:', normalized):
        return normalized.lower()

    return normalized


def is_path_outside_workspace(path, work_dir):
    """检查路径是否在工作区外"""
    normalized_path = normalize_path(path)
    normalized_workdir = normalize_path(work_dir)

    log_debug(f"  检查路径: {normalized_path}")
    log_debug(f"  工作目录: {normalized_workdir}")

    # UNC 路径检测
    if normalized_path.startswith('//'):
        if normalized_workdir.startswith('//'):
            if normalized_path.startswith(normalized_workdir):
                return False
        return True

    # Windows 绝对路径检测
    if re.match(r'^[a-z]:', normalized_path):
        if re.match(r'^[a-z]:', normalized_workdir):
            if normalized_path.startswith(normalized_workdir):
                return False
        return True

    # WSL 路径检测
    if normalized_path.startswith('/mnt/'):
        if normalized_workdir.startswith('/mnt/'):
            if normalized_path.startswith(normalized_workdir):
                return False
        return True

    # Unix 绝对路径检测
    if normalized_path.startswith('/'):
        if normalized_path.startswith(normalized_workdir):
            return False

        # 系统目录检测
        system_dirs = [
            '/etc/', '/usr/', '/var/', '/tmp/',
            '/system/', '/library/',
            'c:/windows', 'c:/program files', 'c:/programdata', 'c:/temp'
        ]
        for sys_dir in system_dirs:
            if normalized_path.lower().startswith(sys_dir):
                return True

        return True

    # 相对路径默认视为工作区内
    return False


def send_notification(title, message, sound=""):
    """发送桌面通知"""
    system = platform.system()
    log_debug(f"发送通知 - 系统: {system}, 标题: {title}, 声音: {sound}")

    try:
        if system == "Darwin":  # macOS
            script = f'display notification "{message}" with title "{title}"'
            if sound:
                script += f' sound name "{sound}"'
            subprocess.run(["osascript", "-e", script], check=False, capture_output=True)

        elif system == "Linux":
            subprocess.run(["notify-send", title, message, "-u", "normal", "-t", "5000"],
                         check=False, capture_output=True)
            # 尝试播放声音
            if subprocess.run(["which", "paplay"], capture_output=True).returncode == 0:
                subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                             check=False, capture_output=True)

        elif system == "Windows":
            # Windows 使用 PowerShell 发送通知
            ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$notification = New-Object System.Windows.Forms.NotifyIcon
$notification.Icon = [System.Drawing.SystemIcons]::Information
$notification.BalloonTipTitle = "{title}"
$notification.BalloonTipText = "{message}"
$notification.Visible = $true
$notification.ShowBalloonTip(5000)
'''
            subprocess.run(["powershell", "-Command", ps_script], check=False, capture_output=True)

            # 播放 Windows 声音文件
            if sound:
                # 将声音名称转换为小写的 .wav 文件名
                sound_file = sound.lower() + ".wav"
                sound_path = f"C:\\Windows\\Media\\{sound_file}"
                log_debug(f"尝试播放声音文件: {sound_path}")

                sound_script = f'''
$soundPath = "{sound_path}"
if (Test-Path $soundPath) {{
    $player = New-Object System.Media.SoundPlayer $soundPath
    $player.PlaySync()
}} else {{
    Write-Host "Sound file not found: $soundPath"
}}
'''
                result = subprocess.run(["powershell", "-Command", sound_script],
                                      check=False, capture_output=True, text=True)
                log_debug(f"声音播放结果: stdout={result.stdout}, stderr={result.stderr}")

    except Exception as e:
        log_debug(f"发送通知失败: {e}")


def handle_stop_hook(hook_data, permissions):
    """处理 Stop 事件"""
    log_debug("处理 Stop 事件")

    # 检查通知是否启用
    notifications = permissions.get("notifications", {})
    if notifications.get("enabled") != 1:
        log_debug("通知未启用")
        sys.exit(0)

    on_completion = notifications.get("onCompletion", {})
    if on_completion.get("enabled") != 1:
        log_debug("完成通知未启用")
        sys.exit(0)

    # 发送通知
    title = on_completion.get("title", "Claude Code")
    message = on_completion.get("message", "任务完成")

    # 根据系统选择声音
    if platform.system() == "Windows":
        sound = on_completion.get("soundWindows", "SystemNotification")
    else:
        sound = on_completion.get("sound", "Glass")

    log_debug(f"发送完成通知: {title} - {message}")
    send_notification(title, message, sound)
    sys.exit(0)


def handle_permission_request_hook(hook_data, permissions):
    """处理 PermissionRequest 事件"""
    log_debug("处理 PermissionRequest 事件")

    # 检查通知是否启用
    notifications = permissions.get("notifications", {})
    if notifications.get("enabled") != 1:
        log_debug("通知未启用")
        sys.exit(0)

    on_permission = notifications.get("onPermissionRequest", {})
    if on_permission.get("enabled") != 1:
        log_debug("权限请求通知未启用")
        sys.exit(0)

    # 提取工具名称
    tool_name = hook_data.get("tool_name", "")
    title = on_permission.get("title", "Claude Code")
    message = on_permission.get("message", "需要您的批准")

    # 根据系统选择声音
    if platform.system() == "Windows":
        sound = on_permission.get("soundWindows", "SystemNotification")
    else:
        sound = on_permission.get("sound", "Tink")

    if tool_name:
        message = f"{tool_name} - {message}"

    log_debug(f"发送权限请求通知: {title} - {message}")
    send_notification(title, message, sound)
    sys.exit(0)


def handle_pre_tool_use_hook(hook_data, permissions):
    """处理 PreToolUse 事件 - 权限检查"""
    log_debug("处理 PreToolUse 事件")

    tool_name = hook_data.get("tool_name", "")
    cli_permission_mode = hook_data.get("permission_mode", "default")
    work_dir = hook_data.get("cwd", "")

    log_debug(f"Tool: {tool_name}")
    log_debug(f"CLI Mode: {cli_permission_mode}")
    log_debug(f"Work Dir: {work_dir}")

    # 获取当前模式的配置
    mode = permissions.get("modes", {}).get(cli_permission_mode, {})
    if not mode:
        log_debug(f"错误: 找不到模式 {cli_permission_mode}")
        output_result("PreToolUse", permissionDecision="ask")

    # 提取命令（如果是 Bash）
    command = ""
    if tool_name == "Bash":
        command = hook_data.get("tool_input", {}).get("command", "")

    log_debug(f"Command: {command}")

    # 1. 检查 globalDeny（最高优先级）
    if mode.get("globalDeny") == 1:
        if check_in_list(tool_name, permissions, "globalDeny", "tools"):
            log_debug("决策: globalDeny 工具匹配 = deny")
            output_result("PreToolUse", permissionDecision="deny")

        if command and check_in_list(command, permissions, "globalDeny", "commands"):
            log_debug("决策: globalDeny 命令匹配 = deny")
            output_result("PreToolUse", permissionDecision="deny")

    # 2. 检查 globalAllow
    if mode.get("globalAllow") == 1:
        if check_in_list(tool_name, permissions, "globalAllow", "tools"):
            log_debug("决策: globalAllow 工具匹配 = allow")
            output_result("PreToolUse", permissionDecision="allow")

        if command and check_in_list(command, permissions, "globalAllow", "commands"):
            log_debug("决策: globalAllow 命令匹配 = allow")
            output_result("PreToolUse", permissionDecision="allow")

    # 3. 判断命令类别和工作区位置
    command_category = ""
    is_in_workspace = True

    if tool_name == "Bash":
        # 判断命令类别（按优先级）
        if check_in_list(command, permissions, "risky", "commands"):
            command_category = "risky"
        elif check_in_list(command, permissions, "edit", "commands"):
            command_category = "edit"
        elif check_in_list(command, permissions, "read", "commands"):
            command_category = "read"
        elif check_in_list(command, permissions, "useWeb", "commands"):
            command_category = "useWeb"
        else:
            command_category = "unknown"

        # 判断是否在工作区内
        paths = extract_paths_from_command(command)
        if paths:
            log_debug(f"提取到的路径: {paths}")
            for path in paths:
                if is_path_outside_workspace(path, work_dir):
                    is_in_workspace = False
                    break
    else:
        # 非 Bash 工具
        if check_in_list(tool_name, permissions, "useMcp", "tools"):
            command_category = "useMcp"
        elif check_in_list(tool_name, permissions, "useWeb", "tools"):
            command_category = "useWeb"
        elif check_in_list(tool_name, permissions, "risky", "tools"):
            command_category = "risky"
        elif check_in_list(tool_name, permissions, "edit", "tools"):
            command_category = "edit"
        elif check_in_list(tool_name, permissions, "read", "tools"):
            command_category = "read"
        else:
            log_debug("决策: 未分类工具 = ask")
            output_result("PreToolUse", permissionDecision="ask")

        # 判断工具操作的文件是否在工作区内
        tool_input = hook_data.get("tool_input", {})
        file_path = tool_input.get("file_path") or tool_input.get("path") or ""
        if file_path:
            if is_path_outside_workspace(file_path, work_dir):
                is_in_workspace = False

    log_debug(f"Category: {command_category}")
    log_debug(f"In Workspace: {is_in_workspace}")

    # 4. 根据类别和工作区位置查询权限开关
    decision = "ask"  # 默认询问

    if command_category == "read":
        if is_in_workspace:
            if mode.get("read") == 1:
                decision = "allow"
                log_debug("决策: read + 工作区内 = allow")
            else:
                log_debug("决策: read + 工作区内 + 开关关闭 = ask")
        else:
            if mode.get("readAllFiles") == 1:
                decision = "allow"
                log_debug("决策: read + 工作区外 = allow")
            else:
                log_debug("决策: read + 工作区外 + 开关关闭 = ask")

    elif command_category == "edit":
        if is_in_workspace:
            if mode.get("edit") == 1:
                decision = "allow"
                log_debug("决策: edit + 工作区内 = allow")
            else:
                log_debug("决策: edit + 工作区内 + 开关关闭 = ask")
        else:
            if mode.get("editAllFiles") == 1:
                decision = "allow"
                log_debug("决策: edit + 工作区外 = allow")
            else:
                log_debug("决策: edit + 工作区外 + 开关关闭 = ask")

    elif command_category == "risky":
        if is_in_workspace:
            if mode.get("risky") == 1:
                decision = "allow"
                log_debug("决策: risky + 工作区内 = allow")
            else:
                log_debug("决策: risky + 工作区内 + 开关关闭 = ask")
        else:
            if mode.get("riskyAllFiles") == 1:
                decision = "allow"
                log_debug("决策: risky + 工作区外 = allow")
            else:
                log_debug("决策: risky + 工作区外 + 开关关闭 = ask")

    elif command_category == "useWeb":
        if mode.get("useWeb") == 1:
            decision = "allow"
            log_debug("决策: useWeb = allow")
        else:
            log_debug("决策: useWeb + 开关关闭 = ask")

    elif command_category == "useMcp":
        if mode.get("useMcp") == 1:
            decision = "allow"
            log_debug("决策: useMcp = allow")
        else:
            log_debug("决策: useMcp + 开关关闭 = ask")

    elif command_category == "unknown":
        if mode.get("allowUnknownCommand") == 1:
            decision = "allow"
            log_debug("决策: unknown command + 开关开启 = allow")
        else:
            log_debug("决策: unknown command + 开关关闭 = ask")

    # 5. 输出最终决策
    log_debug(f"最终决策: {decision}")
    output_result("PreToolUse", permissionDecision=decision)


def main():
    """主函数 - 根据事件类型分发处理"""
    log_debug(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    # 从 stdin 读取 JSON 输入
    try:
        # 使用 utf-8 编码读取，并处理可能的编码错误
        hook_input = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        log_debug(f"接收到的 JSON: {hook_input[:200]}...")
        hook_data = json.loads(hook_input)
    except json.JSONDecodeError as e:
        log_debug(f"JSON 解析失败: {e}")
        # 对于非 JSON 输入，尝试从环境变量或参数获取事件类型
        event_type = sys.argv[1] if len(sys.argv) > 1 else "unknown"
        hook_data = {"hook_event_name": event_type}
    except Exception as e:
        log_debug(f"读取输入失败: {e}")
        sys.exit(0)

    # 获取事件类型
    hook_event_name = hook_data.get("hook_event_name", "")
    log_debug(f"Hook Event: {hook_event_name}")

    # 读取权限配置
    # 优先从 hook_data 的 cwd 字段获取项目路径，其次从环境变量获取
    project_dir = hook_data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    log_debug(f"项目目录: {project_dir}")

    permissions_file = os.path.join(project_dir, ".claude", "permissions.json")
    log_debug(f"权限配置文件路径: {permissions_file}")

    if not os.path.exists(permissions_file):
        log_debug(f"警告: 找不到配置文件 {permissions_file}")
        # 对于通知事件，没有配置文件就直接退出
        if hook_event_name in ["Stop", "PermissionRequest"]:
            sys.exit(0)
        # 对于权限检查，返回 ask
        output_result("PreToolUse", permissionDecision="ask")

    try:
        with open(permissions_file, "r", encoding="utf-8") as f:
            permissions = json.load(f)
    except Exception as e:
        log_debug(f"读取配置文件失败: {e}")
        if hook_event_name in ["Stop", "PermissionRequest"]:
            sys.exit(0)
        output_result("PreToolUse", permissionDecision="ask")

    # 根据事件类型分发处理
    if hook_event_name == "PreToolUse":
        handle_pre_tool_use_hook(hook_data, permissions)
    elif hook_event_name == "Stop":
        handle_stop_hook(hook_data, permissions)
    elif hook_event_name == "PermissionRequest":
        handle_permission_request_hook(hook_data, permissions)
    else:
        log_debug(f"未知的事件类型: {hook_event_name}")
        sys.exit(0)


if __name__ == "__main__":
    main()