"""
Alert Manager for ETL Movilidad Medellín
Sends alerts for high/critical severity news via multiple channels
"""
import os
import smtplib
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alerts for high-severity news
    Supports: Email, Console, and File-based alerts
    """

    def __init__(
        self,
        email_enabled: bool = False,
        smtp_host: str = None,
        smtp_port: int = 587,
        smtp_user: str = None,
        smtp_password: str = None,
        alert_recipients: List[str] = None,
        console_alerts: bool = True,
        file_alerts: bool = True,
        alerts_file: str = "logs/alerts.json"
    ):
        """
        Initialize Alert Manager

        Args:
            email_enabled: Enable email alerts
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            alert_recipients: List of recipient emails
            console_alerts: Enable console output
            file_alerts: Enable JSON file logging
            alerts_file: Path to alerts log file
        """
        self.email_enabled = email_enabled
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.alert_recipients = alert_recipients or []
        self.console_alerts = console_alerts
        self.file_alerts = file_alerts
        self.alerts_file = alerts_file

        # Create logs directory if needed
        if self.file_alerts:
            Path(alerts_file).parent.mkdir(parents=True, exist_ok=True)

        # Validate email config
        if self.email_enabled:
            if not all([smtp_host, smtp_user, smtp_password, alert_recipients]):
                logger.warning("Email alerts enabled but configuration incomplete. Disabling email.")
                self.email_enabled = False

    def send_alert(self, news_item: Dict) -> bool:
        """
        Send alert for a news item

        Args:
            news_item: News item dict with severity, title, body, etc.

        Returns:
            True if alert sent successfully, False otherwise
        """
        severity = news_item.get('severity', 'unknown')

        # Only alert for high/critical severity
        if severity not in ['high', 'critical']:
            return False

        alert_data = self._prepare_alert_data(news_item)

        success = True

        # Console alert
        if self.console_alerts:
            self._send_console_alert(alert_data)

        # File alert
        if self.file_alerts:
            success = success and self._send_file_alert(alert_data)

        # Email alert
        if self.email_enabled:
            success = success and self._send_email_alert(alert_data)

        return success

    def send_batch_alert(self, news_items: List[Dict]) -> int:
        """
        Send alerts for multiple news items

        Args:
            news_items: List of news items

        Returns:
            Number of alerts sent successfully
        """
        count = 0
        for item in news_items:
            if self.send_alert(item):
                count += 1
        return count

    def _prepare_alert_data(self, news_item: Dict) -> Dict:
        """Prepare structured alert data"""
        return {
            'timestamp': datetime.now().isoformat(),
            'severity': news_item.get('severity'),
            'title': news_item.get('title'),
            'summary': news_item.get('summary', news_item.get('body', '')[:200]),
            'area': news_item.get('area'),
            'tags': news_item.get('tags', []),
            'source': news_item.get('source'),
            'url': news_item.get('url'),
            'published_at': news_item.get('published_at'),
            'relevance_score': news_item.get('relevance_score')
        }

    def _send_console_alert(self, alert_data: Dict):
        """Print alert to console"""
        severity_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': 'ℹ️',
            'low': '📝'
        }

        emoji = severity_emoji.get(alert_data['severity'], '📢')

        print(f"\n{emoji} ALERTA DE MOVILIDAD - {alert_data['severity'].upper()}")
        print(f"{'='*60}")
        print(f"Título: {alert_data['title']}")
        print(f"Área: {alert_data['area']}")
        print(f"Resumen: {alert_data['summary']}")
        print(f"Fuente: {alert_data['source']}")
        print(f"URL: {alert_data['url']}")
        print(f"Tags: {', '.join(alert_data['tags'])}")
        print(f"{'='*60}\n")

    def _send_file_alert(self, alert_data: Dict) -> bool:
        """Append alert to JSON file"""
        try:
            # Read existing alerts
            alerts = []
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r', encoding='utf-8') as f:
                    try:
                        alerts = json.load(f)
                    except json.JSONDecodeError:
                        alerts = []

            # Append new alert
            alerts.append(alert_data)

            # Write back
            with open(self.alerts_file, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, indent=2, ensure_ascii=False)

            logger.debug(f"Alert logged to file: {self.alerts_file}")
            return True
        except Exception as e:
            logger.error(f"Error writing alert to file: {e}")
            return False

    def _send_email_alert(self, alert_data: Dict) -> bool:
        """Send alert via email"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert_data['severity'].upper()}] Alerta Movilidad: {alert_data['title'][:50]}"
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(self.alert_recipients)

            # Plain text version
            text_body = f"""
ALERTA DE MOVILIDAD - {alert_data['severity'].upper()}

Título: {alert_data['title']}
Área: {alert_data['area']}
Fuente: {alert_data['source']}
Fecha publicación: {alert_data['published_at']}

Resumen:
{alert_data['summary']}

Tags: {', '.join(alert_data['tags'])}

Más información: {alert_data['url']}

---
Score de relevancia: {alert_data['relevance_score']}
Timestamp alerta: {alert_data['timestamp']}
"""

            # HTML version
            html_body = f"""
<html>
<head>
    <style>
        .alert-critical {{ background-color: #ff4444; color: white; }}
        .alert-high {{ background-color: #ff9944; color: white; }}
        .alert-medium {{ background-color: #ffcc44; }}
        .alert-low {{ background-color: #e8e8e8; }}
    </style>
</head>
<body>
    <div class="alert-{alert_data['severity']}" style="padding: 20px; border-radius: 5px;">
        <h2>🚨 ALERTA DE MOVILIDAD - {alert_data['severity'].upper()}</h2>
    </div>

    <h3>{alert_data['title']}</h3>

    <p><strong>Área afectada:</strong> {alert_data['area']}</p>
    <p><strong>Fuente:</strong> {alert_data['source']}</p>
    <p><strong>Fecha publicación:</strong> {alert_data['published_at']}</p>

    <h4>Resumen:</h4>
    <p>{alert_data['summary']}</p>

    <p><strong>Tags:</strong> {', '.join(alert_data['tags'])}</p>

    <p><a href="{alert_data['url']}">Ver noticia completa</a></p>

    <hr>
    <small>
        Score de relevancia: {alert_data['relevance_score']}<br>
        Timestamp alerta: {alert_data['timestamp']}
    </small>
</body>
</html>
"""

            # Attach both versions
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email alert sent to {len(self.alert_recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False

    def get_recent_alerts(self, limit: int = 20) -> List[Dict]:
        """Get recent alerts from file"""
        if not os.path.exists(self.alerts_file):
            return []

        try:
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
                return alerts[-limit:]
        except Exception as e:
            logger.error(f"Error reading alerts file: {e}")
            return []


class ConsoleOnlyAlertManager(AlertManager):
    """Simplified alert manager that only prints to console"""

    def __init__(self):
        super().__init__(
            email_enabled=False,
            console_alerts=True,
            file_alerts=True,
            alerts_file="logs/alerts.json"
        )
