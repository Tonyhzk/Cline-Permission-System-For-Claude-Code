# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **GUI Configuration Editor**: Added graphical user interface for editing permissions.json
  - Chinese version: `src/zh_CN/.claude/permission_gui.py`
  - English version: `src/en_US/.claude/permission_gui.py`
  - Features:
    - Visual mode configuration with checkboxes
    - Notification settings editor
    - Multi-line text boxes for tools and commands lists
    - Import/Export functionality
    - Real-time configuration validation
- Wildcard prefix patterns for risky commands (`*rm *`, `*rmdir *`, `*chmod *`, `*chown *`)

### Changed
- Updated README documentation to include GUI editor usage instructions
- Fixed notification configuration examples in README to match actual config files
- Improved mode configuration examples in usage scenarios
- Updated `.gitignore` to only ignore root `.claude/` directory (not template directories)

### Removed
- Removed unused `enabled` field from modes configuration (was not used in code)

### Fixed
- Fixed `default` mode `readAllFiles` setting (changed from 0 to 1 in documentation)
- Fixed `acceptEdits` mode settings to match template files
- Corrected notification sound settings in README examples
- Fixed risky command patterns to include wildcard prefix versions

## [1.0.0] - 2026-01-26

### Added
- Initial release of Cline Permission System for Claude Code
- Unified Python hook script (`unified-hook.py`) for all platforms
- Cross-platform support (macOS, Linux, Windows)
- Three CLI modes: `plan`, `default`, `acceptEdits`
- Permission categories: read, edit, risky, useWeb, useMcp, globalAllow, globalDeny
- Glob wildcard support for command matching
- Desktop notification system
- UNC path support for Windows
- Smart path detection with three-tier fallback mechanism
- Comprehensive documentation in English and Chinese

### Features
- **Unified Configuration**: Single `permissions.json` file for all settings
- **Workspace Protection**: Distinguish between operations inside and outside workspace
- **No Restart Required**: Configuration changes take effect immediately
- **Debug Logging**: Detailed permission decision logs for troubleshooting
- **Platform-Specific Configurations**: Separate templates for macOS/Linux and Windows

---

## Version History

- **Unreleased**: GUI editor, configuration fixes, documentation improvements
- **1.0.0** (2026-01-26): Initial release with core permission system

---

**Maintainer**: Tony HZK ([@Tonyhzk](https://github.com/Tonyhzk))
**Repository**: [Cline-Permission-System-For-Claude-Code](https://github.com/Tonyhzk/Cline-Permission-System-For-Claude-Code)