#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Permission Configuration Editor
GUI for editing permissions.json configuration file
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path
from datetime import datetime


class PermissionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude Code Permission Configuration Editor")
        self.root.geometry("700x900")

        # Configuration file path (relative path)
        self.config_file = Path(__file__).parent / "permissions.json"

        # Default configuration
        self.default_config = self.get_default_config()

        # Current configuration
        self.config = {}

        # Initialize status variable (must be before load_config)
        self.status_var = tk.StringVar(value="Initializing...")

        # Create widgets
        self.create_widgets()

        # Load configuration
        self.load_config()

        # Load data to UI
        self.load_data_to_ui()

    def get_default_config(self):
        """Get default configuration"""
        return {
            "_comment": "Claude Code Permission System Unified Configuration",
            "_description": {
                "modes": "Permission switch configuration for three CLI modes",
                "categories": "Command classification definitions (supports Glob wildcards * and ?)",
                "notifications": "Notification system configuration"
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
                    "message": "Task completed, waiting for next instruction",
                    "sound": "Glass",
                    "soundWindows": "Tada"
                },
                "onPermissionRequest": {
                    "enabled": 1,
                    "title": "Claude Code",
                    "message": "Approval required",
                    "sound": "Submarine",
                    "soundWindows": "Notify"
                }
            }
        }

    def load_config(self):
        """Load configuration file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.update_status(f"Configuration loaded: {self.config_file}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration file: {e}")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.update_status("Using default configuration (file does not exist)")

    def save_config(self):
        """Save configuration file"""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Save configuration
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

            self.update_status(f"Configuration saved: {datetime.now().strftime('%H:%M:%S')}")
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration file: {e}")

    def create_widgets(self):
        """Create UI widgets"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Left navigation bar
        nav_frame = ttk.LabelFrame(main_frame, text="Navigation", padding="5")
        nav_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # Create Notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create tabs
        self.create_modes_tab()
        self.create_notifications_tab()
        self.create_categories_tab()

        # Bottom button bar
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        ttk.Button(button_frame, text="💾 Save Config", command=self.on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Reset", command=self.on_reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📤 Export", command=self.on_export).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📥 Import", command=self.on_import).pack(side=tk.LEFT, padx=5)

        # Status bar (using initialized status_var)
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

    def create_modes_tab(self):
        """Create modes configuration tab"""
        modes_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(modes_frame, text="📋 Modes Config")

        # Mode selection
        mode_select_frame = ttk.Frame(modes_frame)
        mode_select_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(mode_select_frame, text="Current Mode:").pack(side=tk.LEFT, padx=(0, 10))
        self.mode_var = tk.StringVar(value="default")
        mode_combo = ttk.Combobox(mode_select_frame, textvariable=self.mode_var,
                                   values=["plan", "default", "acceptEdits"], state="readonly", width=20)
        mode_combo.pack(side=tk.LEFT)
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_changed)

        # Create scrollable frame
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

        # Permission switches
        self.mode_vars = {}

        # Read permissions
        read_frame = ttk.LabelFrame(scrollable_frame, text="Read Permissions", padding="10")
        read_frame.pack(fill=tk.X, pady=5)

        self.mode_vars['read'] = tk.IntVar()
        ttk.Checkbutton(read_frame, text="Read inside workspace (read)", variable=self.mode_vars['read']).pack(anchor=tk.W)

        self.mode_vars['readAllFiles'] = tk.IntVar()
        ttk.Checkbutton(read_frame, text="Read outside workspace (readAllFiles)", variable=self.mode_vars['readAllFiles']).pack(anchor=tk.W)

        # Edit permissions
        edit_frame = ttk.LabelFrame(scrollable_frame, text="Edit Permissions", padding="10")
        edit_frame.pack(fill=tk.X, pady=5)

        self.mode_vars['edit'] = tk.IntVar()
        ttk.Checkbutton(edit_frame, text="Edit inside workspace (edit)", variable=self.mode_vars['edit']).pack(anchor=tk.W)

        self.mode_vars['editAllFiles'] = tk.IntVar()
        ttk.Checkbutton(edit_frame, text="Edit outside workspace (editAllFiles)", variable=self.mode_vars['editAllFiles']).pack(anchor=tk.W)

        # Risky permissions
        risky_frame = ttk.LabelFrame(scrollable_frame, text="Risky Permissions", padding="10")
        risky_frame.pack(fill=tk.X, pady=5)

        self.mode_vars['risky'] = tk.IntVar()
        ttk.Checkbutton(risky_frame, text="Risky inside workspace (risky)", variable=self.mode_vars['risky']).pack(anchor=tk.W)

        self.mode_vars['riskyAllFiles'] = tk.IntVar()
        ttk.Checkbutton(risky_frame, text="Risky outside workspace (riskyAllFiles)", variable=self.mode_vars['riskyAllFiles']).pack(anchor=tk.W)

        # Other permissions
        other_frame = ttk.LabelFrame(scrollable_frame, text="Other Permissions", padding="10")
        other_frame.pack(fill=tk.X, pady=5)

        self.mode_vars['useWeb'] = tk.IntVar()
        ttk.Checkbutton(other_frame, text="Web access (useWeb)", variable=self.mode_vars['useWeb']).pack(anchor=tk.W)

        self.mode_vars['useMcp'] = tk.IntVar()
        ttk.Checkbutton(other_frame, text="MCP tools (useMcp)", variable=self.mode_vars['useMcp']).pack(anchor=tk.W)

        self.mode_vars['allowUnknownCommand'] = tk.IntVar()
        ttk.Checkbutton(other_frame, text="Unknown commands (allowUnknownCommand)", variable=self.mode_vars['allowUnknownCommand']).pack(anchor=tk.W)

        self.mode_vars['globalAllow'] = tk.IntVar()
        ttk.Checkbutton(other_frame, text="Enable global whitelist (globalAllow)", variable=self.mode_vars['globalAllow']).pack(anchor=tk.W)

        self.mode_vars['globalDeny'] = tk.IntVar()
        ttk.Checkbutton(other_frame, text="Enable global blacklist (globalDeny)", variable=self.mode_vars['globalDeny']).pack(anchor=tk.W)

    def create_notifications_tab(self):
        """Create notifications configuration tab"""
        notif_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(notif_frame, text="🔔 Notifications")

        # Notification master switch
        self.notif_enabled_var = tk.IntVar()
        ttk.Checkbutton(notif_frame, text="Enable notification system", variable=self.notif_enabled_var).pack(anchor=tk.W, pady=5)

        # Task completion notification
        completion_frame = ttk.LabelFrame(notif_frame, text="Task Completion Notification", padding="10")
        completion_frame.pack(fill=tk.X, pady=10)

        self.completion_enabled_var = tk.IntVar()
        ttk.Checkbutton(completion_frame, text="Enable", variable=self.completion_enabled_var).pack(anchor=tk.W)

        ttk.Label(completion_frame, text="Title:").pack(anchor=tk.W, pady=(5, 0))
        self.completion_title_var = tk.StringVar()
        ttk.Entry(completion_frame, textvariable=self.completion_title_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(completion_frame, text="Message:").pack(anchor=tk.W, pady=(5, 0))
        self.completion_message_var = tk.StringVar()
        ttk.Entry(completion_frame, textvariable=self.completion_message_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(completion_frame, text="Sound (macOS):").pack(anchor=tk.W, pady=(5, 0))
        self.completion_sound_var = tk.StringVar()
        ttk.Entry(completion_frame, textvariable=self.completion_sound_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(completion_frame, text="Sound (Windows):").pack(anchor=tk.W, pady=(5, 0))
        self.completion_sound_win_var = tk.StringVar()
        ttk.Entry(completion_frame, textvariable=self.completion_sound_win_var, width=40).pack(fill=tk.X, pady=2)

        # Permission request notification
        permission_frame = ttk.LabelFrame(notif_frame, text="Permission Request Notification", padding="10")
        permission_frame.pack(fill=tk.X, pady=10)

        self.permission_enabled_var = tk.IntVar()
        ttk.Checkbutton(permission_frame, text="Enable", variable=self.permission_enabled_var).pack(anchor=tk.W)

        ttk.Label(permission_frame, text="Title:").pack(anchor=tk.W, pady=(5, 0))
        self.permission_title_var = tk.StringVar()
        ttk.Entry(permission_frame, textvariable=self.permission_title_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(permission_frame, text="Message:").pack(anchor=tk.W, pady=(5, 0))
        self.permission_message_var = tk.StringVar()
        ttk.Entry(permission_frame, textvariable=self.permission_message_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(permission_frame, text="Sound (macOS):").pack(anchor=tk.W, pady=(5, 0))
        self.permission_sound_var = tk.StringVar()
        ttk.Entry(permission_frame, textvariable=self.permission_sound_var, width=40).pack(fill=tk.X, pady=2)

        ttk.Label(permission_frame, text="Sound (Windows):").pack(anchor=tk.W, pady=(5, 0))
        self.permission_sound_win_var = tk.StringVar()
        ttk.Entry(permission_frame, textvariable=self.permission_sound_win_var, width=40).pack(fill=tk.X, pady=2)

    def create_categories_tab(self):
        """Create command categories tab"""
        cat_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(cat_frame, text="📝 Categories")

        # Category selection
        cat_select_frame = ttk.Frame(cat_frame)
        cat_select_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(cat_select_frame, text="Select Category:").pack(side=tk.LEFT, padx=(0, 10))
        self.category_var = tk.StringVar(value="read")
        cat_combo = ttk.Combobox(cat_select_frame, textvariable=self.category_var,
                                 values=["read", "edit", "risky", "useWeb", "useMcp", "globalAllow", "globalDeny"],
                                 state="readonly", width=20)
        cat_combo.pack(side=tk.LEFT)
        cat_combo.bind("<<ComboboxSelected>>", self.on_category_changed)

        # Tools list
        tools_frame = ttk.LabelFrame(cat_frame, text="Tools List", padding="10")
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(tools_frame, text="One tool name per line:").pack(anchor=tk.W)
        self.tools_text = tk.Text(tools_frame, height=8, width=60)
        self.tools_text.pack(fill=tk.BOTH, expand=True, pady=5)

        tools_scroll = ttk.Scrollbar(tools_frame, command=self.tools_text.yview)
        tools_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tools_text.config(yscrollcommand=tools_scroll.set)

        # Commands list
        commands_frame = ttk.LabelFrame(cat_frame, text="Commands List", padding="10")
        commands_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(commands_frame, text="One command per line (supports Glob wildcards * and ?):").pack(anchor=tk.W)
        self.commands_text = tk.Text(commands_frame, height=8, width=60)
        self.commands_text.pack(fill=tk.BOTH, expand=True, pady=5)

        commands_scroll = ttk.Scrollbar(commands_frame, command=self.commands_text.yview)
        commands_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.commands_text.config(yscrollcommand=commands_scroll.set)

    def load_data_to_ui(self):
        """Load data to UI"""
        # Load mode configuration
        self.on_mode_changed()

        # Load notification configuration
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

        # Load command categories
        self.on_category_changed()

    def on_mode_changed(self, _event=None):
        """Mode change event"""
        mode_name = self.mode_var.get()
        mode_config = self.config.get("modes", {}).get(mode_name, {})

        for key, var in self.mode_vars.items():
            var.set(mode_config.get(key, 0))

    def on_category_changed(self, _event=None):
        """Category change event"""
        cat_name = self.category_var.get()
        cat_config = self.config.get("categories", {}).get(cat_name, {})

        # Load tools
        tools = cat_config.get("tools", [])
        self.tools_text.delete("1.0", tk.END)
        self.tools_text.insert("1.0", "\n".join(tools))

        # Load commands
        commands = cat_config.get("commands", [])
        self.commands_text.delete("1.0", tk.END)
        self.commands_text.insert("1.0", "\n".join(commands))

    def save_ui_to_config(self):
        """Save UI data to configuration"""
        # Record current mode and category
        current_mode = self.mode_var.get()
        current_cat = self.category_var.get()

        # First save the currently edited mode configuration
        if "modes" not in self.config:
            self.config["modes"] = {}
        if current_mode not in self.config["modes"]:
            self.config["modes"][current_mode] = {}

        for key, var in self.mode_vars.items():
            self.config["modes"][current_mode][key] = var.get()

        # First save the currently edited category configuration
        if "categories" not in self.config:
            self.config["categories"] = {}
        if current_cat not in self.config["categories"]:
            self.config["categories"][current_cat] = {}

        # Read current category's tools
        tools_text = self.tools_text.get("1.0", tk.END).strip()
        tools = [line.strip() for line in tools_text.split("\n") if line.strip()]
        self.config["categories"][current_cat]["tools"] = tools

        # Read current category's commands
        commands_text = self.commands_text.get("1.0", tk.END).strip()
        commands = [line.strip() for line in commands_text.split("\n") if line.strip()]
        self.config["categories"][current_cat]["commands"] = commands

        # Save notification configuration
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
        """Save button event"""
        self.save_ui_to_config()
        self.save_config()

    def on_reset(self):
        """Reset button event"""
        if messagebox.askyesno("Confirm", "Are you sure you want to reset to default configuration?"):
            self.config = self.default_config.copy()
            self.load_data_to_ui()
            self.update_status("Reset to default configuration")

    def on_export(self):
        """Export button event"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.save_ui_to_config()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Success", f"Configuration exported to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")

    def on_import(self):
        """Import button event"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.load_data_to_ui()
                messagebox.showinfo("Success", f"Configuration imported from {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {e}")

    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(f"{message} | Config file: {self.config_file.name}")


def main():
    root = tk.Tk()
    PermissionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()