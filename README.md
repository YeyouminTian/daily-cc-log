# Daily-CC-Log

🤖 **智能工作日志生成器** - 基于 Claude-Mem 记忆系统的自动化工作日报/周报生成skill

[License: MIT](https://opensource.org/licenses/MIT)
[Python 3.7+](https://www.python.org/downloads/)
[Claude Code](https://github.com/anthropics/claude-code)

## ✨ 功能特性

- 🎯 **智能分析** - 基于 Claude AI 的自然语言处理能力，生成流畅、有洞察力的工作日志
- 📅 **灵活查询** - 支持多种时间范围：今天、昨天、特定日期、日期范围（"last week", "last month"等）
- 🔄 **自动聚合** - 按项目自动分组工作内容，识别工作时段和会话
- 📊 **丰富统计** - 提供观察记录数、会话数、活跃项目数等关键指标
- 🌐 **跨平台** - 完美支持 Windows、macOS 和 Linux
- 🧹 **自动清理** - 智能临时文件管理，避免磁盘空间浪费
- 🎨 **双格式输出** - 支持 JSON（供 AI 处理）和 Markdown（供人类阅读）

## 📋 工作原理

Daily-CC-Log 采用创新的两步式工作流：

1. **数据收集阶段**：Python 脚本从 Claude-Mem API 获取观察记录和会话数据，生成结构化 JSON
2. **智能撰写阶段**：Claude AI 读取 JSON 数据，生成自然、简洁、有洞察力的工作日报/周报

这种设计充分发挥了各自优势：

- Python 擅长数据处理和 API 调用
- Claude AI 擅长自然语言生成和内容组织

## 🚀 快速开始

### 前置要求

- [Claude-Mem](https://github.com/anthropics/claude-mem) 记忆系统运行在 `http://localhost:37778`
- Python 3.7 或更高版本
- `requests` 库（`pip install requests`）

### 安装

1. 克隆仓库到你的 Claude skills 目录：

```bash
cd ~/.claude/skills
git clone https://github.com/YeyouminTian/daily-cc-log.git
```

1. 验证安装：

```bash
ls daily-cc-log/scripts/daily_log.py
```

### 使用方法

在 Claude Code 中使用以下命令：

```bash
# 今日工作日志
/daily-cc-log

# 昨日工作日志
/daily-cc-log yesterday

# 特定日期
/daily-cc-log 2026-03-01

# 日期范围
/daily-cc-log last week
/daily-cc-log "2026-03-01 to 2026-03-07"
```

## 📖 使用示例

### 示例输出

```markdown
# 工作日报 - 2026年3月3日

## 📊 概览
- **活跃项目数**: 2个
- **工作时段**: 下午13:33-14:28，晚上20:00-21:17
- **会话总数**: 4个
- **观察记录**: 226条

## 🎯 项目详情

### 项目：0. 周期笔记

**工作时段**: 13:33-14:28, 20:00-21:17
**观察记录**: 213条

#### 主要工作事项

**学术检索工具集成与优化** (13:33-14:28)
完成了多源学术检索工具链的建设。测试了 Semantic Scholar、arXiv、Jina AI 和 AMiner 四个平台的 API...

#### 关键成果
- ✅ 成功集成多源学术检索工具
- ✅ 完全修复了 Claude-Mem 记忆系统问题
- ✅ 开发并部署了功能完整的 daily-cc-log skill

#### 问题与解决方案
- **问题**: Semantic Scholar API 遇到 429 限流错误
  - **解决**: 切换到 arXiv 作为替代方案
```

### 直接使用 Python 脚本

```bash
# JSON 格式（默认）
python scripts/daily_log.py --date today --format json

# Markdown 格式
python scripts/daily_log.py --date today --format markdown

# 自定义输出文件
python scripts/daily_log.py --date "last week" --output report.md
```

## ⚙️ 配置

### Claude-Mem API 端点

默认配置：

- **API 地址**: `http://localhost:37778`
- **数据库路径**: `~/.claude-mem/claude-mem.db`

如需修改，编辑 `scripts/daily_log.py` 中的 `BASE_URL` 常量。

### 观察类型

Daily-CC-Log 识别以下观察类型：

- 🔵 **discovery** - 发现、探索
- 🔴 **bugfix** - 问题修复
- 🟣 **feature** - 新功能开发
- 🔄 **refactor** - 代码重构
- ✅ **change** - 配置变更
- ⚖️ **decision** - 架构决策

## 🛠️ 技术栈

- **Python 3.7+** - 数据收集和处理
- **Claude API** - 自然语言生成
- **Claude-Mem** - 记忆系统和数据源
- **SQLite** - 数据存储
- **Requests** - HTTP 客户端

## 📁 项目结构

```
daily-cc-log/
├── README.md           # 本文件
├── SKILL.md           # Claude skill 定义
├── LICENSE            # MIT 许可证
└── scripts/
    └── daily_log.py   # 核心脚本
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

**如果这个项目对你有帮助，请给一个 ⭐ Star！**