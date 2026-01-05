import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


async def send_email(to_email: str, subject: str, body: str, html: bool = False):
    """Send email notification"""
    try:
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        smtp_from = os.getenv('SMTP_FROM', 'noreply@expensetracker.com')
        
        # Create message
        message = MIMEMultipart('alternative')
        message['From'] = smtp_from
        message['To'] = to_email
        message['Subject'] = subject
        
        # Add body
        if html:
            message.attach(MIMEText(body, 'html'))
        else:
            message.attach(MIMEText(body, 'plain'))
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True
        )
        
        print(f"✅ Email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def get_welcome_email_template(username: str) -> str:
    """Get welcome email template"""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">Welcome to Smart Expense Tracker! 🎉</h2>
                <p>Hi {username},</p>
                <p>Thank you for registering with Smart Expense Tracker. We're excited to help you manage your expenses efficiently!</p>
                <p>Here's what you can do:</p>
                <ul>
                    <li>Track your daily expenses</li>
                    <li>Categorize spending</li>
                    <li>Set budgets and get alerts</li>
                    <li>View detailed analytics and trends</li>
                </ul>
                <p>Get started by adding your first expense!</p>
                <p>Best regards,<br>Smart Expense Tracker Team</p>
            </div>
        </body>
    </html>
    """


def get_budget_alert_template(budget_amount: float, spent_amount: float, category: str = "Overall") -> str:
    """Get budget alert email template"""
    percentage = (spent_amount / budget_amount * 100) if budget_amount > 0 else 0
    
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #f44336;">Budget Alert! ⚠️</h2>
                <p>Your {category} budget has been exceeded!</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Budget Amount:</strong> ${budget_amount:.2f}</p>
                    <p><strong>Spent Amount:</strong> ${spent_amount:.2f}</p>
                    <p><strong>Percentage Used:</strong> {percentage:.1f}%</p>
                    <p><strong>Over Budget:</strong> ${(spent_amount - budget_amount):.2f}</p>
                </div>
                <p>Consider reviewing your expenses to stay within budget.</p>
                <p>Best regards,<br>Smart Expense Tracker Team</p>
            </div>
        </body>
    </html>
    """


def get_expense_confirmation_template(amount: float, category: str, description: str) -> str:
    """Get expense confirmation email template"""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2196F3;">Expense Recorded ✓</h2>
                <p>Your expense has been successfully recorded:</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Amount:</strong> ${amount:.2f}</p>
                    <p><strong>Category:</strong> {category}</p>
                    <p><strong>Description:</strong> {description or 'N/A'}</p>
                </div>
                <p>View your analytics dashboard for detailed insights.</p>
                <p>Best regards,<br>Smart Expense Tracker Team</p>
            </div>
        </body>
    </html>
    """
