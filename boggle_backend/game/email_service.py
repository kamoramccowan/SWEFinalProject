"""
SendGrid email service for sending challenge invites.
Requires SENDGRID_API_KEY environment variable to be set.
"""
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Default sender email - should be configured in environment
DEFAULT_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@boggleboost.com')

def send_challenge_invite(to_email: str, challenge_code: str, inviter_name: str = "A friend") -> dict:
    """
    Send a challenge invite email to a user.
    
    Args:
        to_email: Recipient's email address
        challenge_code: The challenge ID/code to join
        inviter_name: Name of the person sending the invite
    
    Returns:
        dict with 'success' and 'message' keys
    """
    api_key = os.environ.get('SENDGRID_API_KEY')
    
    if not api_key:
        # Return mock success for demo if API key not configured
        return {
            'success': True,
            'message': f'Demo mode: Email would be sent to {to_email} with code {challenge_code}',
            'demo_mode': True
        }
    
    # Build the email content
    subject = f"{inviter_name} has challenged you to Boggle Boost!"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background: #f0f4ff;">
        <div style="max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; border: 2px solid #2c3e50;">
            <h1 style="color: #1a1a2e; margin-top: 0;">🎲 Boggle Boost Challenge!</h1>
            <p style="color: #4a5568; font-size: 16px;">
                <strong>{inviter_name}</strong> has invited you to play a Boggle challenge!
            </p>
            <div style="background: #e8eeff; padding: 20px; border-radius: 4px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; color: #4a5568;">Your Challenge Code:</p>
                <h2 style="margin: 10px 0; color: #4a69bd; font-size: 32px; letter-spacing: 2px;">{challenge_code}</h2>
            </div>
            <p style="color: #4a5568;">
                Enter this code on the Play page to join the challenge and compete!
            </p>
            <p style="color: #718096; font-size: 12px; margin-top: 30px;">
                Don't have an account? Sign up at Boggle Boost to play!
            </p>
        </div>
    </body>
    </html>
    """
    
    plain_content = f"""
{inviter_name} has challenged you to Boggle Boost!

Your Challenge Code: {challenge_code}

Enter this code on the Play page to join the challenge and compete!

Don't have an account? Sign up at Boggle Boost to play!
"""

    message = Mail(
        from_email=DEFAULT_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=plain_content,
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        if response.status_code in (200, 201, 202):
            return {
                'success': True,
                'message': f'Challenge invite sent to {to_email}'
            }
        else:
            return {
                'success': False,
                'message': f'Failed to send email: Status {response.status_code}'
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Email sending failed: {str(e)}'
        }
