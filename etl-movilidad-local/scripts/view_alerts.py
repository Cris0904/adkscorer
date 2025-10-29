"""
View recent alerts from the alerts log file
"""
import os
import json
from datetime import datetime


def main():
    alerts_file = os.path.join(
        os.path.dirname(__file__),
        '..',
        'logs',
        'alerts.json'
    )

    if not os.path.exists(alerts_file):
        print("No alerts file found. No alerts have been sent yet.")
        return

    try:
        with open(alerts_file, 'r', encoding='utf-8') as f:
            alerts = json.load(f)
    except Exception as e:
        print(f"Error reading alerts file: {e}")
        return

    if not alerts:
        print("No alerts in file.")
        return

    print("="*60)
    print(f"ALERTS LOG ({len(alerts)} total)")
    print("="*60)

    # Show last 20 alerts
    recent_alerts = alerts[-20:]

    for i, alert in enumerate(reversed(recent_alerts), 1):
        severity_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': 'ℹ️',
            'low': '📝'
        }
        emoji = severity_emoji.get(alert.get('severity', ''), '📢')

        print(f"\n{i}. {emoji} [{alert.get('severity', 'N/A').upper()}] {alert.get('title', 'N/A')[:70]}")
        print(f"   Timestamp: {alert.get('timestamp', 'N/A')[:19]}")
        print(f"   Area: {alert.get('area', 'N/A')}")
        print(f"   Source: {alert.get('source', 'N/A')}")

        if alert.get('summary'):
            summary = alert['summary'][:150]
            print(f"   Summary: {summary}{'...' if len(alert['summary']) > 150 else ''}")

        if alert.get('tags'):
            tags = alert['tags'][:5]
            print(f"   Tags: {', '.join(tags)}")

        print(f"   URL: {alert.get('url', 'N/A')}")

    print("\n" + "="*60)
    print(f"Showing last {len(recent_alerts)} of {len(alerts)} total alerts")
    print("="*60)


if __name__ == "__main__":
    main()
