"""Alert system for notifying about detected threats."""

from datetime import datetime
from typing import Dict, List
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from pathlib import Path

from ..utils.config_loader import ConfigLoader
from ..utils.logger import SystemLogger


class Severity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertSystem:
    """System for generating and sending alerts."""
    
    def __init__(self, config: ConfigLoader = None, logger: SystemLogger = None):
        """Initialize alert system.
        
        Args:
            config: Configuration loader instance
            logger: Logger instance
        """
        self.config = config or ConfigLoader()
        if logger is None:
            logger = SystemLogger(
                self.config.get('system', 'log_dir', default='./logs')
            )
        self.logger = logger.get_logger() if hasattr(logger, 'get_logger') else logger
        
        self.alert_history = []
        self.max_history = 1000
        
        # Alert settings
        self.console_enabled = self.config.get('alerting', 'console_enabled', default=True)
        self.email_enabled = self.config.get('alerting', 'email_enabled', default=False)
        self.min_severity = self.config.get('alerting', 'min_severity', default='medium')
        
        # Email settings
        if self.email_enabled:
            self.smtp_server = self.config.get('alerting', 'email_smtp_server', default='')
            self.smtp_port = self.config.get('alerting', 'email_smtp_port', default=587)
            self.email_from = self.config.get('alerting', 'email_from', default='')
            self.email_to = self.config.get('alerting', 'email_to', default='')
    
    def send_alert(self, threat_details: Dict, severity: str = 'medium'):
        """Send alert for detected threat.
        
        Args:
            threat_details: Dictionary with threat detection details
            severity: Severity level (low, medium, high, critical)
        """
        # Check if severity meets minimum threshold
        severity_levels = ['low', 'medium', 'high', 'critical']
        if severity_levels.index(severity) < severity_levels.index(self.min_severity):
            return
        
        alert = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'details': threat_details
        }
        
        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        # Send console alert
        if self.console_enabled:
            self._send_console_alert(alert)
        
        # Send email alert
        if self.email_enabled and severity in ['high', 'critical']:
            self._send_email_alert(alert)
        
        # Save alert to file
        self._save_alert(alert)
    
    def _send_console_alert(self, alert: Dict):
        """Send alert to console.
        
        Args:
            alert: Alert dictionary
        """
        details = alert['details']
        log_entry = details.get('log_entry', {})
        
        severity = alert['severity'].upper()
        timestamp = alert['timestamp']
        source_ip = log_entry.get('source_ip', 'unknown')
        message = log_entry.get('message', '')[:200]
        confidence = details.get('overall_confidence', 0.0)
        
        # Color coding based on severity
        from colorama import Fore, Style
        
        color_map = {
            'low': Fore.CYAN,
            'medium': Fore.YELLOW,
            'high': Fore.RED,
            'critical': Fore.RED + Style.BRIGHT
        }
        
        color = color_map.get(alert['severity'], '')
        reset = Style.RESET_ALL
        
        alert_msg = f"""
{color}{'='*80}
ALERT: {severity} THREAT DETECTED
{'='*80}{reset}
Timestamp: {timestamp}
Severity: {color}{severity}{reset}
Confidence: {confidence:.2%}
Source IP: {source_ip}
Message: {message}
{color}{'='*80}{reset}
"""
        
        print(alert_msg)
        self.logger.warning(f"ALERT: {severity} threat detected from {source_ip}")
    
    def _send_email_alert(self, alert: Dict):
        """Send alert via email.
        
        Args:
            alert: Alert dictionary
        """
        if not all([self.smtp_server, self.email_from, self.email_to]):
            self.logger.warning("Email alerting configured but missing SMTP settings")
            return
        
        try:
            details = alert['details']
            log_entry = details.get('log_entry', {})
            
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = f"Zero-Day Threat Alert: {alert['severity'].upper()}"
            
            body = f"""
Zero-Day Attack Detection System Alert

Severity: {alert['severity'].upper()}
Timestamp: {alert['timestamp']}
Confidence: {details.get('overall_confidence', 0.0):.2%}

Source IP: {log_entry.get('source_ip', 'unknown')}
User: {log_entry.get('user', 'unknown')}
Message: {log_entry.get('message', '')}

Detection Details:
{json.dumps(details.get('detections', {}), indent=2)}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            # Note: In production, use environment variables for credentials
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent to {self.email_to}")
        
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def _clean_for_json(self, obj):
        """Clean object for JSON serialization."""
        import numpy as np
        if isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_for_json(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (bool, int, float, str)) or obj is None:
            return obj
        else:
            return str(obj)
    
    def _save_alert(self, alert: Dict):
        """Save alert to file.
        
        Args:
            alert: Alert dictionary
        """
        report_dir = Path(self.config.get('system', 'report_dir', default='./reports'))
        report_dir.mkdir(parents=True, exist_ok=True)
        
        alert_file = report_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            # Load existing alerts
            if alert_file.exists():
                try:
                    with open(alert_file, 'r') as f:
                        alerts = json.load(f)
                except json.JSONDecodeError:
                    alerts = []
            else:
                alerts = []
            
            # Clean alert for JSON serialization
            clean_alert = self._clean_for_json(alert)
            alerts.append(clean_alert)
            
            # Save updated alerts
            with open(alert_file, 'w') as f:
                json.dump(alerts, f, indent=2, default=str)
        
        except Exception as e:
            self.logger.error(f"Failed to save alert: {e}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent alerts.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alert dictionaries
        """
        return self.alert_history[-limit:]
    
    def get_alerts_by_severity(self, severity: str) -> List[Dict]:
        """Get alerts filtered by severity.
        
        Args:
            severity: Severity level to filter by
            
        Returns:
            List of alert dictionaries
        """
        return [alert for alert in self.alert_history if alert['severity'] == severity]
    
    def generate_report(self, output_path: str = None) -> str:
        """Generate alert report.
        
        Args:
            output_path: Path to save report (optional)
            
        Returns:
            Report content as string
        """
        report_dir = Path(self.config.get('system', 'report_dir', default='./reports'))
        if output_path is None:
            output_path = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        report_lines = [
            "=" * 80,
            "Zero-Day Attack Detection System - Alert Report",
            "=" * 80,
            f"Generated: {datetime.now().isoformat()}",
            f"Total Alerts: {len(self.alert_history)}",
            "",
        ]
        
        # Severity breakdown
        severity_counts = {}
        for alert in self.alert_history:
            sev = alert['severity']
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        report_lines.append("Severity Breakdown:")
        for severity in ['critical', 'high', 'medium', 'low']:
            count = severity_counts.get(severity, 0)
            report_lines.append(f"  {severity.upper()}: {count}")
        
        report_lines.append("")
        report_lines.append("Recent Alerts:")
        report_lines.append("-" * 80)
        
        for alert in self.alert_history[-20:]:  # Last 20 alerts
            details = alert['details']
            log_entry = details.get('log_entry', {})
            report_lines.append(f"Time: {alert['timestamp']}")
            report_lines.append(f"Severity: {alert['severity'].upper()}")
            report_lines.append(f"Source: {log_entry.get('source_ip', 'unknown')}")
            report_lines.append(f"Confidence: {details.get('overall_confidence', 0.0):.2%}")
            report_lines.append(f"Message: {log_entry.get('message', '')[:100]}")
            report_lines.append("-" * 80)
        
        report_content = "\n".join(report_lines)
        
        # Save to file
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report_content)
            self.logger.info(f"Report saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
        
        return report_content

