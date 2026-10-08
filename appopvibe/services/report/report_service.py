"""
Report service for managing CV analysis reports.
"""
import os
import logging
import datetime
import secrets
from pathlib import Path
from typing import Dict, Any, Optional, List

import markdown2


class ReportService:
    """Service for managing CV analysis reports."""

    def __init__(self, reports_directory: str, retention_days: int = 30):
        self.reports_dir = Path(reports_directory)
        self.retention_days = retention_days
        self.logger = logging.getLogger(__name__)
        self.reports_dir.mkdir(exist_ok=True)

    def generate_report_filename(self, prefix: str = "report") -> str:
        """Return an unguessable id. The file is stored as <id>.md."""
        return f"{prefix}_{secrets.token_hex(8)}"

    def _path_for(self, report_id: str) -> Path:
        safe = os.path.basename(report_id).removesuffix(".md")
        return self.reports_dir / f"{safe}.md"

    def save_report(self, cv_text: str, jd_text: str, analysis_result: str,
                    rewritten_cv: Optional[str] = None, language: str = "en") -> str:
        report_id = self.generate_report_filename()
        file_path = self._path_for(report_id)
        language_labels = {'en': 'English', 'fr': 'Français'}
        language_label = language_labels.get(language, language)

        report_content = f"""# CV Analysis Report

*Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}*
*Language: {language_label}*

## Analysis Summary

{analysis_result}

"""
        if rewritten_cv:
            report_content += f"""
## Rewritten CV Optimized for ATS

{rewritten_cv}

"""
        report_content += f"""
## Original CV

```
{cv_text}
```

## Original Job Description

```
{jd_text}
```
"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info("Report saved as %s", file_path.name)
            return report_id
        except Exception as e:
            self.logger.error("Error saving report: %s", e)
            return ""

    def get_report(self, report_id: str) -> Optional[str]:
        file_path = self._path_for(report_id)
        if not file_path.exists():
            self.logger.warning("Report not found: %s", report_id)
            return None
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.logger.error("Error reading report %s: %s", report_id, e)
            return None

    def get_report_html(self, report_id: str) -> Optional[str]:
        markdown_content = self.get_report(report_id)
        if not markdown_content:
            return None
        try:
            return markdown2.markdown(
                markdown_content,
                extras=["tables", "fenced-code-blocks", "break-on-newline"]
            )
        except Exception as e:
            self.logger.error("Error converting report to HTML: %s", e)
            return None

    def list_reports(self, limit: int = 100) -> List[Dict[str, Any]]:
        reports = []
        try:
            report_files = sorted(
                self.reports_dir.glob("*.md"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            for file_path in report_files[:limit]:
                stats = file_path.stat()
                reports.append({
                    'filename': file_path.stem,
                    'created': datetime.datetime.fromtimestamp(stats.st_mtime),
                    'size': stats.st_size
                })
            return reports
        except Exception as e:
            self.logger.error("Error listing reports: %s", e)
            return []

    def cleanup_old_reports(self) -> int:
        now = datetime.datetime.now()
        retention_cutoff = now - datetime.timedelta(days=self.retention_days)
        removed_count = 0
        try:
            for file_path in self.reports_dir.glob("*.md"):
                mod_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                if mod_time < retention_cutoff:
                    file_path.unlink()
                    removed_count += 1
            self.logger.info("Removed %s old reports", removed_count)
            return removed_count
        except Exception as e:
            self.logger.error("Error during report cleanup: %s", e)
            return 0
