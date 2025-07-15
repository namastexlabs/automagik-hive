#!/usr/bin/env python3
"""
Test script for email notifications via Resend SMTP
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from api.monitoring.alert_manager import AlertManager, Alert, AlertSeverity, AlertStatus


async def test_email_notification():
    """Test email notification functionality"""
    print("🧪 Testing email notification system...")
    
    # Initialize alert manager
    alert_manager = AlertManager()
    
    # Check if email is configured
    email_config = alert_manager.config.get('email', {})
    print(f"📧 Email enabled: {email_config.get('enabled', False)}")
    print(f"📧 SMTP server: {email_config.get('smtp_server', 'Not set')}")
    print(f"📧 Recipients: {email_config.get('recipients', [])}")
    
    if not email_config.get('enabled', False):
        print("❌ Email notifications are not enabled!")
        print("Make sure RESEND_API_KEY and EMAIL_RECIPIENT are set in .env")
        return False
    
    if not email_config.get('recipients'):
        print("❌ No email recipients configured!")
        return False
    
    # Create a test alert
    test_alert = Alert(
        id=f"test_alert_{int(datetime.now().timestamp())}",
        rule_name="email_test",
        severity=AlertSeverity.MEDIUM,
        message="🧪 Test email notification from Genie Agents system",
        timestamp=datetime.now(),
        status=AlertStatus.ACTIVE,
        metadata={
            "test": True,
            "source": "manual_test",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    )
    
    print(f"📨 Sending test alert: {test_alert.id}")
    
    try:
        # Send the test email
        await alert_manager._deliver_email(test_alert)
        print("✅ Test email sent successfully!")
        print(f"📬 Check {email_config['recipients'][0]} for the test email")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False


async def test_smtp_connection():
    """Test basic SMTP connection to Resend"""
    print("\n🔌 Testing SMTP connection...")
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        # Get credentials from environment
        api_key = os.getenv('RESEND_API_KEY')
        recipient = os.getenv('EMAIL_RECIPIENT')
        
        if not api_key:
            print("❌ RESEND_API_KEY not found in environment")
            return False
            
        if not recipient:
            print("❌ EMAIL_RECIPIENT not found in environment")
            return False
        
        print(f"🔑 Using API key: {api_key[:10]}...")
        print(f"📧 Sending to: {recipient}")
        
        # Create test message
        msg = MIMEText("This is a test message from Genie Agents SMTP configuration.")
        msg['From'] = 'resend'
        msg['To'] = recipient
        msg['Subject'] = 'Genie Agents SMTP Test'
        
        # Connect and send
        server = smtplib.SMTP_SSL('smtp.resend.com', 465)
        server.login('resend', api_key)
        server.send_message(msg)
        server.quit()
        
        print("✅ SMTP connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Genie Agents Email Notification Test")
    print("=" * 50)
    
    # Test SMTP connection first
    smtp_ok = await test_smtp_connection()
    
    if smtp_ok:
        # Test full alert system
        alert_ok = await test_email_notification()
        
        if alert_ok:
            print("\n🎉 All tests passed! Email notifications are working.")
        else:
            print("\n⚠️ Alert system test failed.")
    else:
        print("\n❌ SMTP connection failed. Check your configuration.")
    
    print("\n📋 Configuration checklist:")
    print(f"   - RESEND_API_KEY: {'✅' if os.getenv('RESEND_API_KEY') else '❌'}")
    print(f"   - EMAIL_RECIPIENT: {'✅' if os.getenv('EMAIL_RECIPIENT') else '❌'}")
    print(f"   - Alert config exists: {'✅' if Path('logs/alerts/alert_config.json').exists() else '❌'}")


if __name__ == "__main__":
    asyncio.run(main())