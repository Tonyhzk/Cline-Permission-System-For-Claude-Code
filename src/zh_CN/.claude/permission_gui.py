#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code 权限配置编辑器
图形化界面用于编辑 permissions.json 配置文件
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path
from datetime import datetime


class PermissionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Code 权限配置编辑器")
        self.root.geometry("700x900")

        # 配置文件路径（相对路径）
        self.config_file = Path(__file__).parent / "permissions.json"

        # 默认配置
        self.default_config = self.get_default_config()

        # 当前配置
        self.config = {}

        # 初始化状态变量（必须在 load_config 之前）
        self.status_var = tk.StringVar(value="初始化中...")

        # 创建界面
        self.create_widgets()

        # 加载配置
        self.load_config()

        # 加载数据到界面
        self.load_data_to_ui()

    def get_default_config(self):
        """获取默认配置"""
        return {
            "_comment": "Claude Code 权限系统统一配置",
            "_description": {
                "modes": "三种 CLI 模式的权限开关配置",
                "categories": "命令分类定义（支持 Glob 通配符 * 和 ?）",
                "notifications": "通知系统配置"
            },
            "modes": {
                "plan": {
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
                },
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
                },
                "acceptEdits": {
                    "read": 1,
                    "readAllFiles": 0,
                    "edit": 1,
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
                    "commands": []
                },
                "edit": {
                    "tools": ["Edit", "Write"],
                    "commands": []
                },
                "risky": {
                    "tools": [],
                    "commands": []
                },
                "useWeb": {
                    "tools": ["WebFetch", "WebSearch"],
                    "commands": ["curl *", "wget *"]
                },
                "useMcp": {
                    "tools": ["mcp__*"],
                    "commands": []
                },
                "globalAllow": {
                    "tools": [
                        "Task", "TaskGet", "TaskList", "TaskOutput", "TaskUpdate", "TaskCreate",
                        "AskUserQuestion", "EnterPlanMode", "ExitPlanMode"
                    ],
                    "commands": []
                },
                "globalDeny": {
                    "tools": [],
                    "commands": [
                        "git push --force*",
                        "rm -rf /*",
                        "rm -rf /etc*",
                        "rm -rf /usr*",
                        "rm -rf /var*",
                        "chmod -R 777 /*"
                    ]
                }
            },
            "notifications": {
                "_soundOptions": {
                    "macOS": ["Basso", "Blow", "Bottle", "Frog", "Funk", "Glass", "Hero", "Morse", "Ping", "Pop", "Purr", "Sosumi", "Submarine", "Tink"],
                    "windows": ["tada", "chimes", "chord", "ding", "notify", "recycle", "ringout"]
                },
                "enabled": 1,
                "onCompletion": {
                    "enabled": 1,
                    "title": "Claude Code",
                    "message": "任务完成，等待下一步指令",
                    "sound": "Glass",
                    "soundWindows": "Tada"
                },
                "onPermissionRequest": {
                    "enabled": 1,
                    "title": "Claude Code",
                    "message": "需要您的批准",
                    "sound": "Submarine",
                    "soundWindows": "Notify"
                }
            }
        }

    def load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.update_status(f"配置已加载: {self.config_file}")
            except Exception as e:
                messagebox.showerror("错误", f"加载配置文件失败: {e}")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.update_status("使用默认配置（文件不存在）")

    def save_config(self):
        """保存配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

            self.update_status(f"配置已保存: {datetime.now().strftime('%H:%M:%S')}")
            messagebox.showinfo("成功", "配置已成功保存！")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败: {e}")

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # 左侧导航栏
        nav_frame = ttk.LabelFrame(main_frame, text="导航", padding="5")
        nav_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # 创建 Notebook（标签页）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 创建各个标签页
        self.create_modes_tab()
        self.create_notifications_tab()
        self.create_categories_tab()

        # 底部按钮栏
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        ttk.Button(button_frame, text="💾 保存配置", command=self.on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 重置", command=self.on_reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📤 导出", command=self.on_export).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📥 导入", command=self.on_import).pack(side=tk.LEFT, padx=5)

        # 状态栏（使用已初始化的 status_var）
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

    def create_modes_tab(self):
        """创建模式配置标签页"""
        modes_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(modes_frame, text="📋 模式配置")

        # 模式选择
        mode_select_frame = ttk.Frame(modes_frame)
        mode_select_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(mode_select_frame, text="当前模式:").pack(side=tk.LEFT, padx=(0, 10))
        self.mode_var = tk.StringVar(value="default")
        mode_combo = ttk.Combobox(mode_select_frame, textvariable=self.mode_var,
                                   values=["plan", "default", "acceptEdits"], state="readonly", width=20)
        mode_combo.pack(side=tk.LEFT)
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_changed)

        # 创建滚动框架
        canvas = tk.Canvas(modes_frame)
        scrollbar = ttk.Scrollbar(modes_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 权限开关
        self.mode_vars = {}

        # 读取权限
        read_frame = ttk.LabelFrame(scrollable_frame, text="读取权限", padding="10")
        read_frame.pack(fill=tk.X, pady=5)

        self.mode_vars['read'] = tk.IntVar()
        ttk.Checkbutton(read_frame, text="工作区内读取 (read)", variable=self.mode_vars['read']).pack(anchor=tk.W)

        self.mode_vars['readAllFiles'] = tk.IntVar()
        ttk.Checkbutton(read_frame, text="工作区外读取 (readAllFiles)", variable=self.mode_vars['readAllFiles']).pack(anchor=tk.W)

        # 编辑权限
        edit_frame = ttk.LabelFrame(scrollable_frame, text="编辑权限", padding="10")
        edit_frame.pack(fill=tk.X, pady=5)

        self.mode_vars['edit'] = tk.IntVar()
        ttk.Checkbutton(edit_frame, text="工作区内编辑 (edit)", variable=self.mode_vars['edit']).pack(anchor=tk.W)

        self.mode_vars['editAllFiles'] = tk.IntVar()
        ttk.Checkbutton(edit_frame, text="工作区外编辑 (editAllFiles)", variable=self.mode_vars['editAllFiles']).pack(anchor=tk.W)

        # 高风险权限
        risky_frame = ttk.LabelFrame(scrollable_frame, text="高风险权限", padding="10")
        risky_frame.pack(fill=tk.X, pady=5)

        self.mode_vars['risky'] = tk.IntVar()
        ttk.Checkbutton(risky_frame, text="工作区内高风险 (risky)", variable=self.mode_vars['risky']).pack(anchor=tk.W)

        self.mode_vars['riskyAllFiles'] = tk.IntVar()
        ttk.Checkbutton(risky_frame, text="工作区外高风险 (riskyAllFiles)", variable=self.mode_vars['riskyAllFiles']).pack(anchor=tk.W)

        # 其他权限
        other_frame = ttk.LabelFrame(scrollable_frame, text="其他权限", padding="10")
        other_frame.pack(fill=tk.X, pady=5)

        self.mode_vars['useWeb'] = tk.IntVar()
        ttk.Checkbutton(other_frame, text="网络访问 (useWeb)", variable=self.mode_vars['useWeb']).pack(anchor=tk.W)

        self.mode_vars['useMcp'] = tk.IntVar()
        ttk.Checkbutton(other_frame, text="MCP 工具 (useMcp)", variable=self.mode_vars['useMcp']).pack(anchor=tk.W)

        self.mode_vars['allowUnknownCommand'] = tk.IntVar()
        ttk.Checkbutton(other_frame, text="未知命令 (allowUnknownCommand)", variable=self.mode_vars['allowUnknownCommand']).pack(anchor=tk.W)

        self.mode_vars['globalAllow'] = tk.IntVar()
        ttk.Checkbutton(other_frame, text="启用全局白名单 (globalAllow)", variable=self.mode_vars['globalAllow']).pack(anchor=tk.W)

        self.mode_vars['globalDeny'] = tk.IntVar()
        ttk.Checkbutton(other_frame, text="启用全局黑名单 (globalDeny)", variable=self.mode_vars['globalDeny']).pack(anchor=tk.W)

    def create_notifications_tab(self):
        """创建通知配置标签页"""
        notif_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(notif_frame, text="🔔 通知配置")

        # 通知总开关
        self.notif_enabled_var = tk.IntVar()
        ttk.Checkbutton(notif_frame, text="启用通知系统", variable=self.notif_enabled_var).pack(anchor=tk.W, pady=5)

        # 任务完成通知
        completion_frame = ttk.LabelFrame(notif_frame, text="任务完成通知", padding="10")
        completion_frame.pack(fill=tk.X, pady=10)

        self.completion_enabled_var = tk.IntVar()
        ttk.Checkbutton(completion_frame, text="启用", variable=self.completion_enabled_var).pack(anchor=tk.W)

        ttk.Label(completion_frame, text="标题:").pack(anchor=tk.W, pady=(5, 0))
        self.completion_title_var = tk.StringVar()
        ttk.Entry(completion_frame, textvariable=self.completion_title_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(completion_frame, text="消息:").pack(anchor=tk.W, pady=(5, 0))
        self.completion_message_var = tk.StringVar()
        ttk.Entry(completion_frame, textvariable=self.completion_message_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(completion_frame, text="声音 (macOS):").pack(anchor=tk.W, pady=(5, 0))
        self.completion_sound_var = tk.StringVar()
        ttk.Entry(completion_frame, textvariable=self.completion_sound_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(completion_frame, text="声音 (Windows):").pack(anchor=tk.W, pady=(5, 0))
        self.completion_sound_win_var = tk.StringVar()
        ttk.Entry(completion_frame, textvariable=self.completion_sound_win_var, width=40).pack(fill=tk.X, pady=2)

        # 权限请求通知
        permission_frame = ttk.LabelFrame(notif_frame, text="权限请求通知", padding="10")
        permission_frame.pack(fill=tk.X, pady=10)

        self.permission_enabled_var = tk.IntVar()
        ttk.Checkbutton(permission_frame, text="启用", variable=self.permission_enabled_var).pack(anchor=tk.W)

        ttk.Label(permission_frame, text="标题:").pack(anchor=tk.W, pady=(5, 0))
        self.permission_title_var = tk.StringVar()
        ttk.Entry(permission_frame, textvariable=self.permission_title_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(permission_frame, text="消息:").pack(anchor=tk.W, pady=(5, 0))
        self.permission_message_var = tk.StringVar()
        ttk.Entry(permission_frame, textvariable=self.permission_message_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(permission_frame, text="声音 (macOS):").pack(anchor=tk.W, pady=(5, 0))
        self.permission_sound_var = tk.StringVar()
        ttk.Entry(permission_frame, textvariable=self.permission_sound_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(permission_frame, text="声音 (Windows):").pack(anchor=tk.W, pady=(5, 0))
        self.permission_sound_win_var = tk.StringVar()
        ttk.Entry(permission_frame, textvariable=self.permission_sound_win_var, width=40).pack(fill=tk.X, pady=2)

    def create_categories_tab(self):
        """创建命令分类标签页"""
        cat_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(cat_frame, text="📝 命令分类")

        # 分类选择
        cat_select_frame = ttk.Frame(cat_frame)
        cat_select_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(cat_select_frame, text="选择分类:").pack(side=tk.LEFT, padx=(0, 10))
        self.category_var = tk.StringVar(value="read")
        cat_combo = ttk.Combobox(cat_select_frame, textvariable=self.category_var,
                                 values=["read", "edit", "risky", "useWeb", "useMcp", "globalAllow", "globalDeny"],
                                 state="readonly", width=20)
        cat_combo.pack(side=tk.LEFT)
        cat_combo.bind("<<ComboboxSelected>>", self.on_category_changed)

        # Tools 列表
        tools_frame = ttk.LabelFrame(cat_frame, text="工具列表 (Tools)", padding="10")
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(tools_frame, text="每行一个工具名称:").pack(anchor=tk.W)
        self.tools_text = tk.Text(tools_frame, height=8, width=60)
        self.tools_text.pack(fill=tk.BOTH, expand=True, pady=5)

        tools_scroll = ttk.Scrollbar(tools_frame, command=self.tools_text.yview)
        tools_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tools_text.config(yscrollcommand=tools_scroll.set)

        # Commands 列表
        commands_frame = ttk.LabelFrame(cat_frame, text="命令列表 (Commands)", padding="10")
        commands_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(commands_frame, text="每行一个命令（支持 Glob 通配符 * 和 ?）:").pack(anchor=tk.W)
        self.commands_text = tk.Text(commands_frame, height=8, width=60)
        self.commands_text.pack(fill=tk.BOTH, expand=True, pady=5)

        commands_scroll = ttk.Scrollbar(commands_frame, command=self.commands_text.yview)
        commands_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.commands_text.config(yscrollcommand=commands_scroll.set)

    def load_data_to_ui(self):
        """加载数据到界面"""
        # 加载模式配置
        self.on_mode_changed()

        # 加载通知配置
        notif = self.config.get("notifications", {})
        self.notif_enabled_var.set(notif.get("enabled", 1))

        completion = notif.get("onCompletion", {})
        self.completion_enabled_var.set(completion.get("enabled", 1))
        self.completion_title_var.set(completion.get("title", ""))
        self.completion_message_var.set(completion.get("message", ""))
        self.completion_sound_var.set(completion.get("sound", ""))
        self.completion_sound_win_var.set(completion.get("soundWindows", ""))

        permission = notif.get("onPermissionRequest", {})
        self.permission_enabled_var.set(permission.get("enabled", 1))
        self.permission_title_var.set(permission.get("title", ""))
        self.permission_message_var.set(permission.get("message", ""))
        self.permission_sound_var.set(permission.get("sound", ""))
        self.permission_sound_win_var.set(permission.get("soundWindows", ""))

        # 加载命令分类
        self.on_category_changed()

    def on_mode_changed(self, _event=None):
        """模式切换事件"""
        mode_name = self.mode_var.get()
        mode_config = self.config.get("modes", {}).get(mode_name, {})

        for key, var in self.mode_vars.items():
            var.set(mode_config.get(key, 0))

    def on_category_changed(self, _event=None):
        """分类切换事件"""
        cat_name = self.category_var.get()
        cat_config = self.config.get("categories", {}).get(cat_name, {})

        # 加载 tools
        tools = cat_config.get("tools", [])
        self.tools_text.delete("1.0", tk.END)
        self.tools_text.insert("1.0", "\n".join(tools))

        # 加载 commands
        commands = cat_config.get("commands", [])
        self.commands_text.delete("1.0", tk.END)
        self.commands_text.insert("1.0", "\n".join(commands))

    def save_ui_to_config(self):
        """保存界面数据到配置"""
        # 记录当前模式和分类
        current_mode = self.mode_var.get()
        current_cat = self.category_var.get()

        # 先保存当前正在编辑的模式配置
        if "modes" not in self.config:
            self.config["modes"] = {}
        if current_mode not in self.config["modes"]:
            self.config["modes"][current_mode] = {}

        for key, var in self.mode_vars.items():
            self.config["modes"][current_mode][key] = var.get()

        # 先保存当前正在编辑的分类配置
        if "categories" not in self.config:
            self.config["categories"] = {}
        if current_cat not in self.config["categories"]:
            self.config["categories"][current_cat] = {}

        # 读取当前分类的 tools
        tools_text = self.tools_text.get("1.0", tk.END).strip()
        tools = [line.strip() for line in tools_text.split("\n") if line.strip()]
        self.config["categories"][current_cat]["tools"] = tools

        # 读取当前分类的 commands
        commands_text = self.commands_text.get("1.0", tk.END).strip()
        commands = [line.strip() for line in commands_text.split("\n") if line.strip()]
        self.config["categories"][current_cat]["commands"] = commands

        # 保存通知配置
        if "notifications" not in self.config:
            self.config["notifications"] = {}

        self.config["notifications"]["enabled"] = self.notif_enabled_var.get()

        self.config["notifications"]["onCompletion"] = {
            "enabled": self.completion_enabled_var.get(),
            "title": self.completion_title_var.get(),
            "message": self.completion_message_var.get(),
            "sound": self.completion_sound_var.get(),
            "soundWindows": self.completion_sound_win_var.get()
        }

        self.config["notifications"]["onPermissionRequest"] = {
            "enabled": self.permission_enabled_var.get(),
            "title": self.permission_title_var.get(),
            "message": self.permission_message_var.get(),
            "sound": self.permission_sound_var.get(),
            "soundWindows": self.permission_sound_win_var.get()
        }

    def on_save(self):
        """保存按钮事件"""
        self.save_ui_to_config()
        self.save_config()

    def on_reset(self):
        """重置按钮事件"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗？"):
            self.config = self.default_config.copy()
            self.load_data_to_ui()
            self.update_status("已重置为默认配置")

    def on_export(self):
        """导出按钮事件"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.save_ui_to_config()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"配置已导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def on_import(self):
        """导入按钮事件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.load_data_to_ui()
                messagebox.showinfo("成功", f"配置已从 {file_path} 导入")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")

    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(f"{message} | 配置文件: {self.config_file.name}")


def main():
    root = tk.Tk()
    PermissionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()