#!/usr/bin/env python3
"""
Daily Log Generator - Generate work reports from Claude-Mem data

Usage:
    python daily_log.py [--date DATE] [--output FILE] [--config CONFIG] [--format FORMAT]

Examples:
    python daily_log.py                                    # Today's log
    python daily_log.py --date yesterday                   # Yesterday's log
    python daily_log.py --date 2026-03-01                  # Specific date
    python daily_log.py --date "last week"                 # Date range
    python daily_log.py --output report.md                 # Save to file
"""

import argparse
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from collections import defaultdict
import re


class DateParser:
    """Parse natural language date expressions into date ranges"""

    @staticmethod
    def parse(date_str: str) -> Tuple[datetime, datetime]:
        """
        Parse date string and return (start_date, end_date) tuple

        Supported formats:
        - "today"
        - "yesterday"
        - "YYYY-MM-DD"
        - "last week"
        - "last month"
        - "YYYY-MM-DD to YYYY-MM-DD"
        """
        date_str = date_str.lower().strip()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if date_str == "today":
            return today, today + timedelta(days=1)

        elif date_str == "yesterday":
            yesterday = today - timedelta(days=1)
            return yesterday, today

        elif "to" in date_str:
            # Date range: "2026-03-01 to 2026-03-03"
            parts = date_str.split("to")
            start = datetime.strptime(parts[0].strip(), "%Y-%m-%d")
            end = datetime.strptime(parts[1].strip(), "%Y-%m-%d")
            return start, end + timedelta(days=1)

        elif date_str == "last week":
            start = today - timedelta(days=7)
            return start, today + timedelta(days=1)

        elif date_str == "last month":
            start = today - timedelta(days=30)
            return start, today + timedelta(days=1)

        else:
            # Try to parse as single date: YYYY-MM-DD
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                return date, date + timedelta(days=1)
            except ValueError:
                raise ValueError(f"Unable to parse date: {date_str}")


class ClaudeMemClient:
    """Client for fetching data from Claude-Mem API or SQLite database"""

    def __init__(self, api_url: str = "http://localhost:37778", db_path: Optional[str] = None):
        self.api_url = api_url
        self.db_path = db_path or str(Path.home() / ".claude-mem" / "claude-mem.db")

    def fetch_observations(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch observations for the given date range"""
        # Skip API and use SQLite directly for now (API format uncertain)
        return self._fetch_observations_sqlite(start_date, end_date)

    def _parse_api_response(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse observations from API response"""
        observations = []

        # API returns different format based on endpoint
        # This is a simplified parser - adjust based on actual API response
        if "results" in data:
            for item in data["results"]:
                obs = {
                    "id": item.get("id"),
                    "project": item.get("project", "Unknown"),
                    "type": item.get("type", "discovery"),
                    "title": item.get("title", ""),
                    "created_at": item.get("created_at", ""),
                    "narrative": item.get("narrative", ""),
                }
                observations.append(obs)

        return observations

    def _fetch_observations_sqlite(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch observations directly from SQLite database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        # Use ISO date string comparison instead of epoch
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT
                o.id,
                o.memory_session_id,
                o.project,
                o.type,
                o.title,
                o.created_at,
                o.created_at_epoch,
                o.narrative,
                o.facts,
                o.files_read,
                o.files_modified
            FROM observations o
            WHERE date(o.created_at) >= ?
            AND date(o.created_at) < ?
            ORDER BY o.created_at ASC
        """, (start_str, end_str))

        rows = cursor.fetchall()
        conn.close()

        observations = []
        for row in rows:
            obs = {
                "id": row["id"],
                "memory_session_id": row["memory_session_id"],
                "project": row["project"],
                "type": row["type"],
                "title": row["title"],
                "created_at": row["created_at"],
                "created_at_epoch": row["created_at_epoch"],
                "narrative": row["narrative"],
                "facts": row["facts"],
                "files_read": row["files_read"],
                "files_modified": row["files_modified"],
            }
            observations.append(obs)

        return observations

    def fetch_sessions(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch session data for the given date range"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    memory_session_id,
                    project,
                    started_at,
                    completed_at,
                    status
                FROM sdk_sessions
                WHERE date(started_at) >= ?
                AND date(started_at) < ?
                ORDER BY started_at ASC
            """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

            rows = cursor.fetchall()
            conn.close()

            sessions = []
            for row in rows:
                session = {
                    "memory_session_id": row["memory_session_id"],
                    "project": row["project"],
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"],
                    "status": row["status"],
                }
                sessions.append(session)

            return sessions
        except Exception as e:
            print(f"Error fetching sessions: {e}")
            return []


class DataAggregator:
    """Aggregate observations and sessions by project with time windows"""

    @staticmethod
    def aggregate_by_project(observations: List[Dict], sessions: List[Dict]) -> Dict[str, Dict]:
        """
        Aggregate data by project with time windows and statistics

        Returns:
        {
            "project_name": {
                "observations": [...],
                "sessions": [...],
                "time_windows": [(start, end), ...],
                "total_duration_minutes": int,
                "observation_count": int
            }
        }
        """
        # Group observations by project
        project_data = defaultdict(lambda: {
            "observations": [],
            "sessions": [],
            "time_windows": []
        })

        for obs in observations:
            project = obs.get("project", "Unknown")
            project_data[project]["observations"].append(obs)

        for session in sessions:
            project = session.get("project", "Unknown")
            project_data[project]["sessions"].append(session)

        # Calculate time windows for each project
        for project, data in project_data.items():
            data["observation_count"] = len(data["observations"])
            data["time_windows"] = DataAggregator._calculate_time_windows(data["observations"])
            data["total_duration_minutes"] = DataAggregator._calculate_total_duration(data["time_windows"])

        return dict(project_data)

    @staticmethod
    def _calculate_time_windows(observations: List[Dict], gap_minutes: int = 30) -> List[Tuple[datetime, datetime]]:
        """
        Calculate time windows from observations
        Gaps > gap_minutes are treated as separate windows
        """
        if not observations:
            return []

        # Sort by created_at
        sorted_obs = sorted(observations, key=lambda x: x.get("created_at_epoch", 0))

        windows = []
        # Convert milliseconds to seconds for datetime
        first_epoch = sorted_obs[0].get("created_at_epoch", 0)
        window_start = datetime.fromtimestamp(first_epoch / 1000) if first_epoch else datetime.now()
        last_time = window_start

        for obs in sorted_obs[1:]:
            obs_epoch = obs.get("created_at_epoch", 0)
            obs_time = datetime.fromtimestamp(obs_epoch / 1000) if obs_epoch else datetime.now()
            gap = (obs_time - last_time).total_seconds() / 60

            if gap > gap_minutes:
                # Close current window
                windows.append((window_start, last_time))
                # Start new window
                window_start = obs_time

            last_time = obs_time

        # Close last window
        windows.append((window_start, last_time))

        return windows

    @staticmethod
    def _calculate_total_duration(windows: List[Tuple[datetime, datetime]]) -> int:
        """Calculate total duration in minutes from time windows"""
        total = 0
        for start, end in windows:
            duration = (end - start).total_seconds() / 60
            total += duration
        return int(total)


class ReportGenerator:
    """Generate Markdown reports from aggregated data"""

    @staticmethod
    def generate_simple_report(project_data: Dict, date_range: Tuple[datetime, datetime]) -> str:
        """Generate concise daily log report"""
        start_date, end_date = date_range
        date_str = start_date.strftime("%Y-%m-%d")

        report_lines = []

        # Header
        report_lines.append(f"# 工作日报 - {date_str}")
        report_lines.append("")

        # Overview
        report_lines.append("## 📊 概览")
        active_projects = len([p for p in project_data.values() if p["observation_count"] > 0])
        total_observations = sum(p["observation_count"] for p in project_data.values())
        total_sessions = sum(len(p["sessions"]) for p in project_data.values())

        # Calculate overall time range
        all_times = []
        for data in project_data.values():
            for obs in data["observations"]:
                epoch = obs.get("created_at_epoch")
                if epoch:
                    # Convert milliseconds to seconds
                    all_times.append(datetime.fromtimestamp(epoch / 1000))

        if all_times:
            min_time = min(all_times).strftime("%H:%M")
            max_time = max(all_times).strftime("%H:%M")
            report_lines.append(f"- **活跃项目**: {active_projects}个")
            report_lines.append(f"- **工作时段**: {min_time} - {max_time}")
            report_lines.append(f"- **会话总数**: {total_sessions}次")
        else:
            report_lines.append("- 无活跃数据")

        report_lines.append("")

        # Projects
        for project, data in sorted(project_data.items(), key=lambda x: x[1]["observation_count"], reverse=True):
            if data["observation_count"] == 0:
                continue

            report_lines.append("---")
            report_lines.append("")
            report_lines.append(f"## 🎯 项目：{project}")
            report_lines.append("")

            # Time windows
            if data["time_windows"]:
                time_strs = []
                for start, end in data["time_windows"]:
                    time_strs.append(f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
                report_lines.append(f"**工作时段**: {', '.join(time_strs)}")
                report_lines.append(f"**观察记录**: {data['observation_count']}条")
                report_lines.append("")

            # Main work items
            report_lines.append("### 主要工作事项")
            work_items = ReportGenerator._extract_work_items(data["observations"])
            for item in work_items:
                report_lines.append(f"- {item}")
            report_lines.append("")

            # Key achievements
            achievements = ReportGenerator._extract_achievements(data["observations"])
            if achievements:
                report_lines.append("### 关键成果")
                for achievement in achievements:
                    report_lines.append(f"- ✅ {achievement}")
                report_lines.append("")

            # Problems and solutions
            problems = ReportGenerator._extract_problems(data["observations"])
            if problems:
                report_lines.append("### 问题与解决方案")
                for problem, solution in problems:
                    report_lines.append(f"**问题**: {problem}")
                    report_lines.append(f"**解决**: {solution}")
                    report_lines.append("")

        # Summary
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("## 📌 工作总结")
        summary = ReportGenerator._generate_summary(project_data)
        report_lines.append(summary)

        return "\n".join(report_lines)

    @staticmethod
    def _extract_work_items(observations: List[Dict]) -> List[str]:
        """Extract main work items from observations"""
        items = []

        # Group by type
        type_groups = defaultdict(list)
        for obs in observations:
            type_groups[obs.get("type", "discovery")].append(obs)

        # Generate work items for each type
        for obs_type, obs_list in type_groups.items():
            if obs_type == "bugfix":
                titles = [obs.get("title", "") for obs in obs_list[:3]]  # Top 3
                if titles:
                    items.append(f"**{obs_type.upper()}**: {', '.join(titles)}")

            elif obs_type == "feature":
                titles = [obs.get("title", "") for obs in obs_list[:3]]
                if titles:
                    items.append(f"**{obs_type.upper()}**: {', '.join(titles)}")

            elif obs_type == "discovery":
                # Group discoveries by topic
                topics = set()
                for obs in obs_list:
                    title = obs.get("title", "")
                    if title:
                        topics.add(title.split()[0] if " " in title else title)
                if topics:
                    items.append(f"**探索研究**: {', '.join(list(topics)[:5])}")

            elif obs_type == "change":
                titles = [obs.get("title", "") for obs in obs_list[:3]]
                if titles:
                    items.append(f"**配置变更**: {', '.join(titles)}")

        return items[:10]  # Limit to top 10 items

    @staticmethod
    def _extract_achievements(observations: List[Dict]) -> List[str]:
        """Extract key achievements from observations"""
        achievements = []

        # Look for feature and bugfix types
        for obs in observations:
            if obs.get("type") in ["feature", "bugfix"]:
                title = obs.get("title", "")
                if title and len(achievements) < 5:
                    achievements.append(title)

        return achievements

    @staticmethod
    def _extract_problems(observations: List[Dict]) -> List[Tuple[str, str]]:
        """Extract problems and solutions from observations"""
        problems = []

        for obs in observations:
            if obs.get("type") == "bugfix":
                title = obs.get("title", "")
                narrative = obs.get("narrative", "")

                # Simple extraction: use title as problem, first sentence of narrative as solution
                if title and narrative:
                    # Extract first sentence
                    sentences = narrative.split(". ")
                    solution = sentences[0] if sentences else narrative
                    if len(problems) < 5:
                        problems.append((title, solution[:200]))  # Limit solution length

        return problems

    @staticmethod
    def _generate_summary(project_data: Dict) -> str:
        """Generate overall work summary"""
        # Simple summary based on observation types
        type_counts = defaultdict(int)
        for data in project_data.values():
            for obs in data["observations"]:
                type_counts[obs.get("type", "discovery")] += 1

        if not type_counts:
            return "今日无工作记录"

        summary_parts = []
        total = sum(type_counts.values())

        summary_parts.append(f"今天共处理 {total} 个工作事项，包括：")

        for obs_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"- {obs_type}: {count}个")

        return "\n".join(summary_parts)


def main():
    parser = argparse.ArgumentParser(description="Fetch daily work data from Claude-Mem")
    parser.add_argument("--date", default="today", help="Date or date range (default: today)")
    parser.add_argument("--output", help="Output file path (optional, defaults to console)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                        help="Output format (default: json)")

    args = parser.parse_args()

    # Parse date
    date_parser = DateParser()
    start_date, end_date = date_parser.parse(args.date)

    # Fetch data
    client = ClaudeMemClient()
    observations = client.fetch_observations(start_date, end_date)
    sessions = client.fetch_sessions(start_date, end_date)

    # Aggregate data
    aggregator = DataAggregator()
    project_data = aggregator.aggregate_by_project(observations, sessions)

    # Prepare structured output
    structured_data = {
        "date_range": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        },
        "summary": {
            "total_observations": len(observations),
            "total_sessions": len(sessions),
            "active_projects": len([p for p in project_data.values() if p["observation_count"] > 0])
        },
        "projects": {}
    }

    # Add project details
    for project, data in project_data.items():
        if data["observation_count"] == 0:
            continue

        project_info = {
            "observation_count": data["observation_count"],
            "session_count": len(data["sessions"]),
            "time_windows": [
                {
                    "start": start.strftime("%H:%M"),
                    "end": end.strftime("%H:%M")
                }
                for start, end in data["time_windows"]
            ],
            "observations": []
        }

        # Add observation details
        for obs in data["observations"]:
            narrative = obs.get("narrative") or ""  # Handle None
            project_info["observations"].append({
                "id": obs.get("id"),
                "time": obs.get("created_at", "")[11:16] if obs.get("created_at") else "",
                "type": obs.get("type"),
                "title": obs.get("title"),
                "narrative": narrative[:300]  # Truncate for readability
            })

        structured_data["projects"][project] = project_info

    # Output
    if args.format == "json":
        output = json.dumps(structured_data, indent=2, ensure_ascii=False)
    else:
        # Simple markdown format
        output_lines = []
        output_lines.append(f"# 工作数据 - {start_date.strftime('%Y-%m-%d')}")
        output_lines.append("")
        output_lines.append(f"## 统计信息")
        output_lines.append(f"- 观察记录总数: {structured_data['summary']['total_observations']}")
        output_lines.append(f"- 会话总数: {structured_data['summary']['total_sessions']}")
        output_lines.append(f"- 活跃项目数: {structured_data['summary']['active_projects']}")
        output_lines.append("")

        for project, info in structured_data["projects"].items():
            output_lines.append(f"## 项目: {project}")
            output_lines.append(f"- 观察记录: {info['observation_count']}条")

            # Format time windows
            time_strs = [f"{w['start']}-{w['end']}" for w in info['time_windows']]
            output_lines.append(f"- 工作时段: {', '.join(time_strs)}")
            output_lines.append("")

            for obs in info["observations"]:
                output_lines.append(f"- [{obs['time']}] [{obs['type']}] {obs['title']}")

        output = "\n".join(output_lines)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output, encoding="utf-8")
        print(f"Data saved to {output_path}")
    else:
        # For JSON format, always save to temp file to avoid Windows console encoding issues
        if args.format == "json":
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            output_path = temp_dir / "daily-cc-log-data.json"

            output_path.write_text(output, encoding="utf-8")
            print(f"JSON data saved to: {output_path}")
        else:
            # Markdown format can be safely printed to console
            try:
                print(output)
            except UnicodeEncodeError:
                # Fallback for Windows: save to temp file
                import tempfile
                temp_dir = Path(tempfile.gettempdir())
                output_path = temp_dir / "daily-cc-log-output.md"

                output_path.write_text(output, encoding="utf-8")
                print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
