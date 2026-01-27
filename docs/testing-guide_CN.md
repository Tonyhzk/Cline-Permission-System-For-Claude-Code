# Claude Code 权限系统测试提示词

## 直接发送给大模型的测试指令

```
你好！我需要测试当前项目的 Claude Code 权限系统（Hook 系统）。

## 测试目标
验证权限系统是否正常工作，包括：
1. Hook 脚本能否正常执行
2. 权限配置文件能否正确读取
3. 不同类别的命令是否按预期处理（自动允许/询问）

## 测试规则
**重要**：在执行每个测试命令前，你必须：
1. 先说明这个命令属于什么类别（read/edit/risky/useWeb/unknown）
2. 根据当前权限配置（`.claude/permissions.json`），预判是否应该自动通过
3. 说明预判依据（例如："ls 属于 read 类别，且在工作区内，配置中 read=1，应该自动通过"）
4. 然后再执行命令
5. 执行后确认实际结果是否符合预期

## 测试步骤

### 第一步：确认环境
1. 读取 `.claude/permissions.json` 文件，了解当前权限配置
2. 读取 `.claude/settings.local.json` 文件，确认 hook 配置
3. 说明当前 CLI 模式（通常是 default）

### 第二步：测试 read 类命令（应该自动通过）
依次测试以下命令，每个命令前先预判：
- `ls` - 列出当前目录文件
- `cat .claude/permissions.json` - 读取配置文件
- `git status` - 查看 git 状态（如果是 git 仓库）

### 第三步：测试 edit 类命令（应该询问）
依次测试以下命令，每个命令前先预判：
- `echo "test" > test-hook.txt` - 创建测试文件
- `mkdir test-hook-dir` - 创建测试目录

### 第四步：测试 unknown 类命令（应该询问）
测试一个未分类的命令，例如：
- `python --version` - 查看 Python 版本

### 第五步：查看调试日志
根据操作系统读取日志文件：
- Windows: 读取 `C:\Users\<用户名>\AppData\Local\Temp\claude-hook-debug.log` 最后 50 行
- macOS/Linux: 读取 `/tmp/claude-hook-debug.log` 最后 50 行

分析日志中的权限决策过程。

### 第六步：总结测试结果
汇总测试结果，说明：
1. 哪些命令按预期自动通过了
2. 哪些命令按预期询问了
3. 是否有不符合预期的情况
4. Hook 系统是否正常工作

## 注意事项
- 如果某个命令被询问权限，请选择"允许"以继续测试
- 测试过程中创建的文件可以在测试结束后删除
- 如果遇到错误，请查看调试日志分析原因

现在开始测试吧！
```

---

## 简化版（快速测试）

如果只想快速验证 hook 是否工作，可以使用这个简化版：

```
测试当前项目的 Claude Code 权限系统：

1. 先读取 `.claude/permissions.json` 了解配置
2. 执行 `ls` 命令（应该自动通过，因为是 read 类）
3. 执行 `echo "test" > test-hook.txt`（应该询问，因为是 edit 类）
4. 查看调试日志确认决策过程

每个命令执行前，先预判是否应该自动通过，并说明理由。
```

---

## 高级测试版（完整验证）

```
完整测试 Claude Code 权限系统，包括所有命令类别和边界情况：

## 准备工作
1. 读取 `.claude/permissions.json` 和 `.claude/settings.local.json`
2. 确认当前 CLI 模式和权限配置

## 测试矩阵

### Read 类（应该自动通过）
- `ls` - 基础读取
- `cat .claude/permissions.json` - 读取配置
- `git status` - Git 只读命令
- `pwd` - 显示当前路径

### Edit 类（应该询问）
- `touch test-file.txt` - 创建文件
- `mkdir test-dir` - 创建目录
- `echo "test" > test.txt` - 写入文件

### Risky 类（应该询问）
- `rm test-file.txt` - 删除文件（如果存在）
- `chmod +x test.sh` - 修改权限（如果文件存在）

### Unknown 类（应该询问）
- `python --version` - 未分类命令
- `node --version` - 未分类命令

### 工作区外测试（应该询问）
- `cat /etc/hosts` - 读取系统文件（macOS/Linux）
- `cat C:\Windows\System32\drivers\etc\hosts` - 读取系统文件（Windows）

## 每个命令执行前必须：
1. 说明命令类别
2. 预判是否自动通过
3. 说明预判依据
4. 执行命令
5. 确认实际结果

## 最后
1. 查看完整调试日志
2. 总结测试结果
3. 评估 hook 系统是否正常工作
```

---

## 使用说明

1. **选择合适的版本**：
   - 首次测试：使用"完整版"
   - 快速验证：使用"简化版"
   - 深度测试：使用"高级测试版"

2. **直接复制粘贴**：
   - 将上述提示词复制到 Claude Code 对话框
   - 大模型会自动开始测试

3. **观察测试过程**：
   - 注意大模型是否在每个命令前进行了预判
   - 确认实际结果是否符合预期
   - 查看是否有权限询问弹窗

4. **分析测试结果**：
   - 如果所有预判都正确，说明 hook 系统工作正常
   - 如果有不符合预期的情况，查看调试日志分析原因