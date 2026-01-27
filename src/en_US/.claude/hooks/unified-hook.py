#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Unified Hook Script - Python Version
Supports three event types: PreToolUse, Stop, PermissionRequest
Solves cross-platform compatibility issues (especially Windows UNC paths in Mac VMs)
"""

import sys
import json
import re
import os
import subprocess
from datetime import datetime
import platform

# Debug log path
if platform.system() == "Windows":
    DEBUG_LOG = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "claude-hook-debug.log")
else:
    DEBUG_LOG = "/tmp/claude-hook-debug.log"


def log_debug(message):
    """Write debug log"""
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
    except Exception:
        pass


def output_result(hook_event_name, **kwargs):
    """Output Hook result"""
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
    Glob pattern matching
    Supports * (match any characters) and ? (match single character)
    """
    regex_pattern = re.escape(pattern)
    regex_pattern = regex_pattern.replace(r'\*', '.*').replace(r'\?', '.')
    return bool(re.match(f"^{regex_pattern}$", text))


def check_in_list(item, permissions, category, list_type):
    """Check if tool or command is in specified list (supports Glob)"""
    try:
        item_list = permissions.get("categories", {}).get(category, {}).get(list_type, [])
        for pattern in item_list:
            if match_glob(item, pattern):
                log_debug(f"  Matched pattern: {pattern}")
                return True
    except Exception as e:
        log_debug(f"  Error checking list: {e}")
    return False


def extract_paths_from_command(command):
    """Extract path arguments from command"""
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
    """Normalize path"""
    normalized = path.replace('\\', '/')

    if normalized.startswith('//'):
        return normalized

    if re.match(r'^[A-Za-z]:', normalized):
        return normalized.lower()

    return normalized


def is_path_outside_workspace(path, work_dir):
    """Check if path is outside workspace"""
    normalized_path = normalize_path(path)
    normalized_workdir = normalize_path(work_dir)

    log_debug(f"  Checking path: {normalized_path}")
    log_debug(f"  Work directory: {normalized_workdir}")

    # UNC path detection
    if normalized_path.startswith('//'):
        if normalized_workdir.startswith('//'):
            if normalized_path.startswith(normalized_workdir):
                return False
        return True

    # Windows absolute path detection
    if re.match(r'^[a-z]:', normalized_path):
        if re.match(r'^[a-z]:', normalized_workdir):
            if normalized_path.startswith(normalized_workdir):
                return False
        return True

    # WSL path detection
    if normalized_path.startswith('/mnt/'):
        if normalized_workdir.startswith('/mnt/'):
            if normalized_path.startswith(normalized_workdir):
                return False
        return True

    # Unix absolute path detection
    if normalized_path.startswith('/'):
        if normalized_path.startswith(normalized_workdir):
            return False

        # System directory detection
        system_dirs = [
            '/etc/', '/usr/', '/var/', '/tmp/',
            '/system/', '/library/',
            'c:/windows', 'c:/program files', 'c:/programdata', 'c:/temp'
        ]
        for sys_dir in system_dirs:
            if normalized_path.lower().startswith(sys_dir):
                return True

        return True

    # Relative paths default to inside workspace
    return False


def send_notification(title, message, sound=""):
    """Send desktop notification"""
    system = platform.system()
    log_debug(f"Sending notification - System: {system}, Title: {title}, Sound: {sound}")

    try:
        if system == "Darwin":  # macOS
            script = f'display notification "{message}" with title "{title}"'
            if sound:
                script += f' sound name "{sound}"'
            subprocess.run(["osascript", "-e", script], check=False, capture_output=True)

        elif system == "Linux":
            subprocess.run(["notify-send", title, message, "-u", "normal", "-t", "5000"],
                         check=False, capture_output=True)
            # Try to play sound
            if subprocess.run(["which", "paplay"], capture_output=True).returncode == 0:
                subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                             check=False, capture_output=True)

        elif system == "Windows":
            # Windows uses PowerShell to send notifications
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

            # Play Windows sound file
            if sound:
                # Convert sound name to lowercase .wav filename
                sound_file = sound.lower() + ".wav"
                sound_path = f"C:\\Windows\\Media\\{sound_file}"
                log_debug(f"Trying to play sound file: {sound_path}")

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
                log_debug(f"Sound playback result: stdout={result.stdout}, stderr={result.stderr}")

    except Exception as e:
        log_debug(f"Failed to send notification: {e}")


def handle_stop_hook(hook_data, permissions):
    """Handle Stop event"""
    log_debug("Processing Stop event")

    # Check if notifications are enabled
    notifications = permissions.get("notifications", {})
    if notifications.get("enabled") != 1:
        log_debug("Notifications not enabled")
        sys.exit(0)

    on_completion = notifications.get("onCompletion", {})
    if on_completion.get("enabled") != 1:
        log_debug("Completion notification not enabled")
        sys.exit(0)

    # Send notification
    title = on_completion.get("title", "Claude Code")
    message = on_completion.get("message", "Task completed")

    # Select sound based on system
    if platform.system() == "Windows":
        sound = on_completion.get("soundWindows", "SystemNotification")
    else:
        sound = on_completion.get("sound", "Glass")

    log_debug(f"Sending completion notification: {title} - {message}")
    send_notification(title, message, sound)
    sys.exit(0)


def handle_permission_request_hook(hook_data, permissions):
    """Handle PermissionRequest event"""
    log_debug("Processing PermissionRequest event")

    # Check if notifications are enabled
    notifications = permissions.get("notifications", {})
    if notifications.get("enabled") != 1:
        log_debug("Notifications not enabled")
        sys.exit(0)

    on_permission = notifications.get("onPermissionRequest", {})
    if on_permission.get("enabled") != 1:
        log_debug("Permission request notification not enabled")
        sys.exit(0)

    # Extract tool name
    tool_name = hook_data.get("tool_name", "")
    title = on_permission.get("title", "Claude Code")
    message = on_permission.get("message", "Approval required")

    # Select sound based on system
    if platform.system() == "Windows":
        sound = on_permission.get("soundWindows", "SystemNotification")
    else:
        sound = on_permission.get("sound", "Tink")

    if tool_name:
        message = f"{tool_name} - {message}"

    log_debug(f"Sending permission request notification: {title} - {message}")
    send_notification(title, message, sound)
    sys.exit(0)


def handle_pre_tool_use_hook(hook_data, permissions):
    """Handle PreToolUse event - Permission check"""
    log_debug("Processing PreToolUse event")

    tool_name = hook_data.get("tool_name", "")
    cli_permission_mode = hook_data.get("permission_mode", "default")
    work_dir = hook_data.get("cwd", "")

    log_debug(f"Tool: {tool_name}")
    log_debug(f"CLI Mode: {cli_permission_mode}")
    log_debug(f"Work Dir: {work_dir}")

    # Get current mode configuration
    mode = permissions.get("modes", {}).get(cli_permission_mode, {})
    if not mode:
        log_debug(f"Error: Mode {cli_permission_mode} not found")
        output_result("PreToolUse", permissionDecision="ask")

    # Extract command (if Bash)
    command = ""
    if tool_name == "Bash":
        command = hook_data.get("tool_input", {}).get("command", "")

    log_debug(f"Command: {command}")

    # 1. Check globalDeny (highest priority)
    if mode.get("globalDeny") == 1:
        if check_in_list(tool_name, permissions, "globalDeny", "tools"):
            log_debug("Decision: globalDeny tool matched = deny")
            output_result("PreToolUse", permissionDecision="deny")

        if command and check_in_list(command, permissions, "globalDeny", "commands"):
            log_debug("Decision: globalDeny command matched = deny")
            output_result("PreToolUse", permissionDecision="deny")

    # 2. Check globalAllow
    if mode.get("globalAllow") == 1:
        if check_in_list(tool_name, permissions, "globalAllow", "tools"):
            log_debug("Decision: globalAllow tool matched = allow")
            output_result("PreToolUse", permissionDecision="allow")

        if command and check_in_list(command, permissions, "globalAllow", "commands"):
            log_debug("Decision: globalAllow command matched = allow")
            output_result("PreToolUse", permissionDecision="allow")

    # 3. Determine command category and workspace location
    command_category = ""
    is_in_workspace = True

    if tool_name == "Bash":
        # Determine command category (by priority)
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

        # Check if inside workspace
        paths = extract_paths_from_command(command)
        if paths:
            log_debug(f"Extracted paths: {paths}")
            for path in paths:
                if is_path_outside_workspace(path, work_dir):
                    is_in_workspace = False
                    break
    else:
        # Non-Bash tools
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
            log_debug("Decision: Unclassified tool = ask")
            output_result("PreToolUse", permissionDecision="ask")

        # Check if tool operates on files inside workspace
        tool_input = hook_data.get("tool_input", {})
        file_path = tool_input.get("file_path") or tool_input.get("path") or ""
        if file_path:
            if is_path_outside_workspace(file_path, work_dir):
                is_in_workspace = False

    log_debug(f"Category: {command_category}")
    log_debug(f"In Workspace: {is_in_workspace}")

    # 4. Query permission switch based on category and workspace location
    decision = "ask"  # Default ask

    if command_category == "read":
        if is_in_workspace:
            if mode.get("read") == 1:
                decision = "allow"
                log_debug("Decision: read + inside workspace = allow")
            else:
                log_debug("Decision: read + inside workspace + switch off = ask")
        else:
            if mode.get("readAllFiles") == 1:
                decision = "allow"
                log_debug("Decision: read + outside workspace = allow")
            else:
                log_debug("Decision: read + outside workspace + switch off = ask")

    elif command_category == "edit":
        if is_in_workspace:
            if mode.get("edit") == 1:
                decision = "allow"
                log_debug("Decision: edit + inside workspace = allow")
            else:
                log_debug("Decision: edit + inside workspace + switch off = ask")
        else:
            if mode.get("editAllFiles") == 1:
                decision = "allow"
                log_debug("Decision: edit + outside workspace = allow")
            else:
                log_debug("Decision: edit + outside workspace + switch off = ask")

    elif command_category == "risky":
        if is_in_workspace:
            if mode.get("risky") == 1:
                decision = "allow"
                log_debug("Decision: risky + inside workspace = allow")
            else:
                log_debug("Decision: risky + inside workspace + switch off = ask")
        else:
            if mode.get("riskyAllFiles") == 1:
                decision = "allow"
                log_debug("Decision: risky + outside workspace = allow")
            else:
                log_debug("Decision: risky + outside workspace + switch off = ask")

    elif command_category == "useWeb":
        if mode.get("useWeb") == 1:
            decision = "allow"
            log_debug("Decision: useWeb = allow")
        else:
            log_debug("Decision: useWeb + switch off = ask")

    elif command_category == "useMcp":
        if mode.get("useMcp") == 1:
            decision = "allow"
            log_debug("Decision: useMcp = allow")
        else:
            log_debug("Decision: useMcp + switch off = ask")

    elif command_category == "unknown":
        if mode.get("allowUnknownCommand") == 1:
            decision = "allow"
            log_debug("Decision: unknown command + switch on = allow")
        else:
            log_debug("Decision: unknown command + switch off = ask")

    # 5. Output final decision
    log_debug(f"Final decision: {decision}")
    output_result("PreToolUse", permissionDecision=decision)


def main():
    """Main function - Dispatch handling based on event type"""
    log_debug(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    # Read JSON input from stdin
    try:
        # Read using utf-8 encoding and handle possible encoding errors
        hook_input = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        log_debug(f"Received JSON: {hook_input[:200]}...")
        hook_data = json.loads(hook_input)
    except json.JSONDecodeError as e:
        log_debug(f"JSON parsing failed: {e}")
        # For non-JSON input, try to get event type from environment variable or arguments
        event_type = sys.argv[1] if len(sys.argv) > 1 else "unknown"
        hook_data = {"hook_event_name": event_type}
    except Exception as e:
        log_debug(f"Failed to read input: {e}")
        sys.exit(0)

    # Get event type
    hook_event_name = hook_data.get("hook_event_name", "")
    log_debug(f"Hook Event: {hook_event_name}")

    # Read permission configuration
    # Priority: get project path from hook_data's cwd field, then from environment variable
    project_dir = hook_data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    log_debug(f"Project directory: {project_dir}")

    permissions_file = os.path.join(project_dir, ".claude", "permissions.json")
    log_debug(f"Permission config file path: {permissions_file}")

    if not os.path.exists(permissions_file):
        log_debug(f"Warning: Config file not found {permissions_file}")
        # For notification events, exit directly if no config file
        if hook_event_name in ["Stop", "PermissionRequest"]:
            sys.exit(0)
        # For permission check, return ask
        output_result("PreToolUse", permissionDecision="ask")

    try:
        with open(permissions_file, "r", encoding="utf-8") as f:
            permissions = json.load(f)
    except Exception as e:
        log_debug(f"Failed to read config file: {e}")
        if hook_event_name in ["Stop", "PermissionRequest"]:
            sys.exit(0)
        output_result("PreToolUse", permissionDecision="ask")

    # Dispatch handling based on event type
    if hook_event_name == "PreToolUse":
        handle_pre_tool_use_hook(hook_data, permissions)
    elif hook_event_name == "Stop":
        handle_stop_hook(hook_data, permissions)
    elif hook_event_name == "PermissionRequest":
        handle_permission_request_hook(hook_data, permissions)
    else:
        log_debug(f"Unknown event type: {hook_event_name}")
        sys.exit(0)


if __name__ == "__main__":
    main()