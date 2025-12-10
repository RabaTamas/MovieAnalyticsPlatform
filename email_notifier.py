import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

# SMTP settings (Gmail példa, de bármilyen SMTP szolgáltató használható)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')  # Email cím
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')  # App password (nem a gmail jelszó!)
ALERT_RECIPIENTS = os.getenv('ALERT_RECIPIENTS', '').split(',')  # Vesszővel elválasztott címek

# =============================================================================
# EMAIL FUNCTIONS
# =============================================================================

def send_email_alert(job_name, error_message, error_details=None):
    """
    Send email alert for ETL job failure
    
    Args:
        job_name (str): Name of the failed ETL job
        error_message (str): Brief error description
        error_details (str): Detailed error information (optional)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    # Check if email is configured
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("⚠️  Email alerting not configured (SMTP credentials missing)")
        return False
    
    if not ALERT_RECIPIENTS or ALERT_RECIPIENTS == ['']:
        print("⚠️  Email alerting not configured (no recipients)")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🚨 ETL Job Failed: {job_name}'
        msg['From'] = SMTP_USERNAME
        msg['To'] = ', '.join(ALERT_RECIPIENTS)
        
        # Email body (HTML)
        html_body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background-color: #d32f2f; color: white; padding: 20px; }}
                    .content {{ padding: 20px; }}
                    .error-box {{ background-color: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 20px 0; }}
                    .details {{ background-color: #f5f5f5; padding: 15px; font-family: monospace; font-size: 12px; overflow-x: auto; }}
                    .footer {{ color: #666; font-size: 12px; padding: 20px; border-top: 1px solid #ddd; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🚨 ETL Job Failure Alert</h1>
                </div>
                
                <div class="content">
                    <h2>Job Information</h2>
                    <p><strong>Job Name:</strong> {job_name}</p>
                    <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Status:</strong> <span style="color: #d32f2f; font-weight: bold;">FAILED</span></p>
                    
                    <div class="error-box">
                        <h3>Error Message:</h3>
                        <p>{error_message}</p>
                    </div>
                    
                    {f'<h3>Error Details:</h3><div class="details">{error_details}</div>' if error_details else ''}
                    
                    <h3>Recommended Actions:</h3>
                    <ul>
                        <li>Check ETL_Log table in Azure SQL Database for full details</li>
                        <li>Review error logs in the application</li>
                        <li>Verify Azure SQL Database connectivity</li>
                        <li>Check data source availability (TMDB API, Blob Storage)</li>
                        <li>Retry the job manually if issue is transient</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>This is an automated alert from Movie Analytics Platform ETL system.</p>
                    <p>Azure SQL Database: {os.getenv('AZURE_SQL_SERVER')}</p>
                </div>
            </body>
        </html>
        """
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        print(f"\n📧 Sending email alert to {len(ALERT_RECIPIENTS)} recipient(s)...")
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email alert sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email alert: {e}")
        return False


def send_success_email(job_name, summary_stats):
    """
    Send success notification email (optional)
    
    Args:
        job_name (str): Name of the successful ETL job
        summary_stats (dict): Job statistics (rows processed, duration, etc.)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    # Check if email is configured
    if not SMTP_USERNAME or not SMTP_PASSWORD or not ALERT_RECIPIENTS or ALERT_RECIPIENTS == ['']:
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'✅ ETL Job Completed: {job_name}'
        msg['From'] = SMTP_USERNAME
        msg['To'] = ', '.join(ALERT_RECIPIENTS)
        
        # Email body (HTML)
        html_body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background-color: #4caf50; color: white; padding: 20px; }}
                    .content {{ padding: 20px; }}
                    .stats {{ background-color: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin: 20px 0; }}
                    .footer {{ color: #666; font-size: 12px; padding: 20px; border-top: 1px solid #ddd; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>✅ ETL Job Completed Successfully</h1>
                </div>
                
                <div class="content">
                    <h2>Job Information</h2>
                    <p><strong>Job Name:</strong> {job_name}</p>
                    <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Status:</strong> <span style="color: #4caf50; font-weight: bold;">SUCCESS</span></p>
                    
                    <div class="stats">
                        <h3>Job Statistics:</h3>
                        <ul>
                            {''.join([f'<li><strong>{k}:</strong> {v}</li>' for k, v in summary_stats.items()])}
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from Movie Analytics Platform ETL system.</p>
                </div>
            </body>
        </html>
        """
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"⚠️  Failed to send success email: {e}")
        return False


# =============================================================================
# TEST FUNCTION
# =============================================================================

def test_email_configuration():
    """Test if email alerting is properly configured"""
    
    print("=" * 80)
    print("📧 Testing Email Configuration")
    print("=" * 80)
    
    print(f"\n📋 Current Configuration:")
    print(f"   SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"   SMTP Username: {SMTP_USERNAME if SMTP_USERNAME else '❌ NOT SET'}")
    print(f"   SMTP Password: {'✅ SET' if SMTP_PASSWORD else '❌ NOT SET'}")
    print(f"   Alert Recipients: {', '.join(ALERT_RECIPIENTS) if ALERT_RECIPIENTS != [''] else '❌ NOT SET'}")
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("\n❌ Email alerting is NOT configured!")
        print("\nTo enable email alerts:")
        print("1. Add to .env file:")
        print("   SMTP_USERNAME=your.email@gmail.com")
        print("   SMTP_PASSWORD=your_app_password")
        print("   ALERT_RECIPIENTS=recipient1@example.com,recipient2@example.com")
        print("\n2. For Gmail, create an App Password:")
        print("   https://myaccount.google.com/apppasswords")
        return False
    
    print("\n✅ Email configuration looks good!")
    print("\n📧 Sending test email...")
    
    success = send_email_alert(
        job_name='Email_Configuration_Test',
        error_message='This is a test email to verify email alerting setup.',
        error_details='If you receive this email, email alerting is working correctly!'
    )
    
    if success:
        print("\n✅ Test email sent! Check your inbox.")
    else:
        print("\n❌ Failed to send test email.")
    
    return success


if __name__ == '__main__':
    test_email_configuration()