"""
Report service for managing CV analysis reports.
"""
import os
import logging
import datetime
import hashlib
import markdown2
from pathlib import Path
from typing import Dict, Any, Optional, List

class ReportService:
    """Service for managing CV analysis reports."""
    
    def __init__(self, reports_directory: str, retention_days: int = 30):
        """Initialize the report service.
        
        Args:
            reports_directory: Directory where reports are stored
            retention_days: Number of days to retain reports
        """
        self.reports_dir = Path(reports_directory)
        self.retention_days = retention_days
        self.logger = logging.getLogger(__name__)
        
        # Ensure reports directory exists
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_report_filename(self, prefix: str = "report") -> str:
        """Generate a unique report filename with timestamp.
        
        Args:
            prefix: Prefix for the filename
            
        Returns:
            A unique filename for the report
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        return f"{prefix}_{timestamp}.md"
    
    def save_report(self, cv_text: str, jd_text: str, analysis_result: str, 
                   rewritten_cv: Optional[str] = None, language: str = "en") -> str:
        """Save analysis results as a markdown report.
        
        Args:
            cv_text: Original CV text
            jd_text: Original job description text
            analysis_result: Analysis from LLM
            rewritten_cv: Rewritten CV if available
            language: Language of the content
            
        Returns:
            Filename of the saved report
        """
        # Generate filename
        filename = self.generate_report_filename()
        file_path = self.reports_dir / filename
        
        # Determine language label
        language_labels = {
            'en': 'English',
            'fr': 'Français'
        }
        language_label = language_labels.get(language, language)
        
        # Create report content
        report_content = f"""# CV Analysis Report

*Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}*
*Language: {language_label}*

## Analysis Summary

{analysis_result}

"""
        
        # Add rewritten CV if available
        if rewritten_cv:
            report_content += f"""
## Rewritten CV Optimized for ATS

{rewritten_cv}

"""
        
        # Add original content sections
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
        
        # Write to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"Report saved as {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            return ""
    
    def get_report(self, filename: str) -> Optional[str]:
        """Get the contents of a report.
        
        Args:
            filename: Name of the report file
            
        Returns:
            The report content or None if not found
        """
        file_path = self.reports_dir / filename
        
        if not file_path.exists():
            self.logger.warning(f"Report not found: {filename}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            self.logger.error(f"Error reading report {filename}: {e}")
            return None
    
    def get_report_html(self, filename: str) -> Optional[str]:
        """Get report content as HTML.
        
        Args:
            filename: Name of the report file
            
        Returns:
            HTML content or None if not found
        """
        markdown_content = self.get_report(filename)
        
        if not markdown_content:
            return None
            
        try:
            # Convert markdown to HTML
            html_content = markdown2.markdown(
                markdown_content,
                extras=["tables", "fenced-code-blocks", "break-on-newline"]
            )
            return html_content
        except Exception as e:
            self.logger.error(f"Error converting report to HTML: {e}")
            return None
    
    def list_reports(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List available reports.
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            List of report metadata dictionaries
        """
        reports = []
        
        try:
            # Get all markdown files in the reports directory
            report_files = sorted(
                self.reports_dir.glob("*.md"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Convert to report metadata
            for file_path in report_files[:limit]:
                # Get file stats
                stats = file_path.stat()
                created_time = datetime.datetime.fromtimestamp(stats.st_mtime)
                
                # Add to reports list
                reports.append({
                    'filename': file_path.name,
                    'created': created_time,
                    'size': stats.st_size
                })
                
            return reports
        except Exception as e:
            self.logger.error(f"Error listing reports: {e}")
            return []
    
    def cleanup_old_reports(self) -> int:
        """Remove reports older than retention period.
        
        Returns:
            Number of reports removed
        """
        now = datetime.datetime.now()
        retention_cutoff = now - datetime.timedelta(days=self.retention_days)
        removed_count = 0
        
        try:
            for file_path in self.reports_dir.glob("*.md"):
                # Get file modification time
                mod_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # Check if older than retention period
                if mod_time < retention_cutoff:
                    file_path.unlink()
                    removed_count += 1
                    
            self.logger.info(f"Removed {removed_count} old reports")
            return removed_count
        except Exception as e:
            self.logger.error(f"Error during report cleanup: {e}")
            return 0
