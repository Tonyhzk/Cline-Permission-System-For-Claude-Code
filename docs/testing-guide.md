# Claude Code Permission System Testing Guide

## Direct Testing Instructions for AI Model

```
Hello! I need to test the Claude Code permission system (Hook system) in the current project.

## Testing Objectives
Verify that the permission system is working correctly, including:
1. Hook script can execute normally
2. Permission configuration file can be read correctly
3. Different categories of commands are handled as expected (auto-allow/ask)

## Testing Rules
**Important**: Before executing each test command, you must:
1. State what category this command belongs to (read/edit/risky/useWeb/unknown)
2. Predict whether it should auto-pass based on current permission config (`.claude/permissions.json`)
3. Explain the prediction basis (e.g., "ls belongs to read category, inside workspace, config has read=1, should auto-pass")
4. Then execute the command
5. Confirm if actual result matches expectation after execution

## Testing Steps

### Step 1: Confirm Environment
1. Read `.claude/permissions.json` file to understand current permission configuration
2. Read `.claude/settings.local.json` file to confirm hook configuration
3. State current CLI mode (usually default)

### Step 2: Test read Category Commands (Should Auto-Pass)
Test the following commands in sequence, predict before each:
- `ls` - List files in current directory
- `cat .claude/permissions.json` - Read configuration file
- `git status` - Check git status (if it's a git repository)

### Step 3: Test edit Category Commands (Should Ask)
Test the following commands in sequence, predict before each:
- `echo "test" > test-hook.txt` - Create test file
- `mkdir test-hook-dir` - Create test directory

### Step 4: Test unknown Category Commands (Should Ask)
Test an unclassified command, for example:
- `python --version` - Check Python version

### Step 5: View Debug Logs
Read log file based on operating system:
- Windows: Read last 50 lines of `C:\Users\<username>\AppData\Local\Temp\claude-hook-debug.log`
- macOS/Linux: Read last 50 lines of `/tmp/claude-hook-debug.log`

Analyze the permission decision process in the logs.

### Step 6: Summarize Test Results
Summarize test results, stating:
1. Which commands auto-passed as expected
2. Which commands asked as expected
3. Any unexpected situations
4. Whether Hook system is working normally

## Notes
- If a command asks for permission, please select "Allow" to continue testing
- Files created during testing can be deleted after testing
- If errors occur, check debug logs to analyze the cause

Start testing now!
```

---

## Simplified Version (Quick Test)

If you just want to quickly verify if the hook is working, use this simplified version:

```
Test the Claude Code permission system in the current project:

1. First read `.claude/permissions.json` to understand configuration
2. Execute `ls` command (should auto-pass, because it's read category)
3. Execute `echo "test" > test-hook.txt` (should ask, because it's edit category)
4. View debug logs to confirm decision process

Before executing each command, predict whether it should auto-pass and explain why.
```

---

## Advanced Testing Version (Complete Verification)

```
Complete test of Claude Code permission system, including all command categories and edge cases:

## Preparation
1. Read `.claude/permissions.json` and `.claude/settings.local.json`
2. Confirm current CLI mode and permission configuration

## Test Matrix

### Read Category (Should Auto-Pass)
- `ls` - Basic read
- `cat .claude/permissions.json` - Read configuration
- `git status` - Git read-only command
- `pwd` - Show current path

### Edit Category (Should Ask)
- `touch test-file.txt` - Create file
- `mkdir test-dir` - Create directory
- `echo "test" > test.txt` - Write to file

### Risky Category (Should Ask)
- `rm test-file.txt` - Delete file (if exists)
- `chmod +x test.sh` - Modify permissions (if file exists)

### Unknown Category (Should Ask)
- `python --version` - Unclassified command
- `node --version` - Unclassified command

### Outside Workspace Test (Should Ask)
- `cat /etc/hosts` - Read system file (macOS/Linux)
- `cat C:\Windows\System32\drivers\etc\hosts` - Read system file (Windows)

## Before Each Command Must:
1. State command category
2. Predict if it will auto-pass
3. Explain prediction basis
4. Execute command
5. Confirm actual result

## Finally
1. View complete debug logs
2. Summarize test results
3. Evaluate if hook system is working normally
```

---

## Usage Instructions

1. **Choose Appropriate Version**:
   - First test: Use "Complete Version"
   - Quick verification: Use "Simplified Version"
   - Deep testing: Use "Advanced Testing Version"

2. **Direct Copy-Paste**:
   - Copy the above prompts to Claude Code dialog
   - AI model will automatically start testing

3. **Observe Testing Process**:
   - Note if AI model makes predictions before each command
   - Confirm if actual results match expectations
   - Check if permission request dialogs appear

4. **Analyze Test Results**:
   - If all predictions are correct, hook system is working normally
   - If there are unexpected situations, check debug logs to analyze the cause
