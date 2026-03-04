---
name: daily-cc-log
description: Generate daily work reports from Claude-Mem memory data. Use when user asks for daily log, work log, journal, or wants to review work activities for today, a specific date, or date range. Triggers: "daily log", "work log", "journal", "今天的工作", "日报", "工作日志", "/daily-cc-log".
license: MIT
---

# Daily Log Generator

Generate intelligent daily work reports by analyzing Claude-Mem observations and sessions data.

## How It Works

This skill uses a two-step process:

1. **Data Collection**: Python script fetches and structures raw data from Claude-Mem
2. **AI Analysis**: Claude reads the structured data and writes a natural, insightful daily log

## Quick Start

```bash
# Fetch today's data
/daily-cc-log

# Fetch yesterday's data
/daily-cc-log yesterday

# Fetch specific date
/daily-cc-log 2026-03-01

# Fetch date range
/daily-cc-log last week
```

## Workflow

When the skill triggers:

### Step 1: Collect Data

Run the data collection script:

```bash
python scripts/daily_log.py --date <date> --format json
```

**Important**: On Windows, the script will automatically save JSON output to a temp file to avoid console encoding issues. The script will print the file path like:
```
JSON data saved to: C:\Users\{username}\AppData\Local\Temp\daily-cc-log-data.json
```

Read this file to get the structured data containing:
- **Summary statistics** (total observations, sessions, projects)
- **Project breakdown** (time windows, observation counts)
- **Observation details** (time, type, title, narrative excerpt)

**Cleanup**: After reading the JSON file, delete the temporary file to keep the temp directory clean:
```bash
rm <temp-file-path>
```

### Step 2: Analyze and Write

After reading the structured data, write a concise daily log following these guidelines:

#### Calculate Working Hours

**IMPORTANT**: Calculate the total working hours for each project based on time windows.

For each project, parse the `time_windows` array and calculate total duration:

**Example**:
```
Time windows: [
  {"start": "11:36", "end": "11:59"},
  {"start": "13:18", "end": "15:16"},
  {"start": "16:28", "end": "16:30"},
  {"start": "19:05", "end": "20:15"}
]
```

Calculation:
- 11:36 → 11:59 = 23 minutes
- 13:18 → 15:16 = 1 hour 58 minutes
- 16:28 → 16:30 = 2 minutes
- 19:05 → 20:15 = 1 hour 10 minutes

**Total**: 23m + 1h58m + 2m + 1h10m = **3 hours 33 minutes** (or 3h 33m or 3.55h)

Include this duration in the project section header:
```markdown
**工作时段**: 11:36-11:59, 13:18-15:16, 16:28-16:30, 19:05-20:15
**工作时长**: 3小时33分钟
**观察记录**: 259条
```

#### Report Structure

```markdown
# 工作日报 - {日期}

## 📊 概览
- 活跃项目数
- 总工作时长（所有项目时长之和）
- 工作时段
- 会话总数

## 🎯 项目详情（按项目分组）

### 项目：{项目名}

**工作时段**: {时间段}
**工作时长**: {计算得出的总时长，如：3小时33分钟}
**观察记录**: {数量}条

#### 主要工作事项
- 聚合同类型工作，用自然语言描述
- 例如："完成AMiner API集成和配置（验证、环境变量设置、测试）"

#### 关键成果
- ✅ 突出完成的重点

#### 问题与解决方案
- 问题：{简述}
- 解决：{方案}

---

## 📌 工作总结
- 总结今日主要工作方向
- 列出各类型观察的数量统计
```

#### Writing Guidelines

**DO:**
- ✅ Use natural, flowing language (not robotic bullet points)
- ✅ Group related observations into coherent work items
- ✅ Highlight achievements and problem-solving
- ✅ Keep it concise (2-3 sentences per section)
- ✅ Use active voice: "Configured API key" not "API key was configured"

**DON'T:**
- ❌ List every observation individually
- ❌ Copy narrative text verbatim - synthesize and summarize
- ❌ Include technical jargon without context
- ❌ Make the report longer than necessary

#### Example Transformation

**Raw Data (JSON)**:
```json
{
  "observations": [
    {"time": "05:33", "type": "bugfix", "title": "Semantic Scholar API Rate Limiting"},
    {"time": "05:33", "type": "discovery", "title": "arXiv Search for LLM Research"},
    {"time": "05:45", "type": "feature", "title": "AMiner API Validation"}
  ]
}
```

**Written Report**:
```markdown
### 主要工作事项

**学术检索工具集成** (05:33-05:45)
- 测试 Semantic Scholar API 遇到限流问题，切换到 arXiv 成功检索10篇相关论文
- 完成 AMiner API 配置和验证，实现学术文献多源检索能力
```

## Date Format Support

The script understands natural language dates:

- `today` - Today's data
- `yesterday` - Yesterday's data
- `2026-03-01` - Specific date
- `last week` - Last 7 days
- `last month` - Last 30 days
- `2026-03-01 to 2026-03-03` - Date range

## Output Options

```bash
# JSON format (default, for AI processing)
python scripts/daily_log.py --date today --format json

# Markdown format (for human review)
python scripts/daily_log.py --date today --format markdown

# Save to file
python scripts/daily_log.py --date today --output data.json
```

## Advanced Usage

### For Complex Reports

If the user requests a detailed or specialized report format:

1. Collect the data as usual
2. Ask the user for specific requirements:
   - "Should I focus on any particular aspect?"
   - "What level of detail do you need?"
   - "Is this for personal review or team sharing?"
3. Tailor the writing style accordingly

### For Multi-Day Analysis

When analyzing date ranges:

- Group observations by theme/project across days
- Identify patterns and progress over time
- Highlight milestones and blockers

## Requirements

- Claude-Mem plugin running on `http://localhost:37778`
- Python 3.7+ with `requests` library
- SQLite database access at `~/.claude-mem/claude-mem.db`

## Troubleshooting

If no data appears:
- Verify Claude-Mem is running: `curl http://localhost:37778/api/health`
- Check observations exist in database
- Confirm date range is correct

## Notes

- Time windows: Gaps >30 minutes treated as separate work sessions
- Observation types: discovery, bugfix, feature, refactor, decision, change
- The AI-written report should be more natural and insightful than template-generated text
- **Working hours calculation**: Sum all time window durations for accurate time tracking

## Working Hours Calculation Examples

### Single Project Example
```json
"time_windows": [
  {"start": "09:15", "end": "11:42"},
  {"start": "14:00", "end": "16:30"}
]
```
**Calculation**:
- 09:15 → 11:42 = 2 hours 27 minutes
- 14:00 → 16:30 = 2 hours 30 minutes
- **Total**: 4 hours 57 minutes

**Report format**: "4小时57分钟" or "4h 57m"

### Multi-Project Daily Summary
```
Project A: 3h 33m
Project B: 1h 45m
Project C: 2h 15m
-------------------
Total: 7h 33m
```

Include in 📊 概览 section:
```markdown
## 📊 概览
- 活跃项目数: 3个
- 总工作时长: 7小时33分钟
- 工作时段: 09:00-12:00, 14:00-18:30, 20:00-21:15
- 会话总数: 4个
```

