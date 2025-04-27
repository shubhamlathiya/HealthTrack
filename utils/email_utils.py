from flask_mail import Message, Mail
from flask import current_app

mail = Mail()


def send_email(subject, recipient_email, body_html):
    try:
        # Create the Flask-Mail message object
        msg = Message(subject=subject,
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[recipient_email])

        # Attach the HTML body to the message
        msg.html = body_html

        # Send the email using Flask-Mail
        mail.send(msg)

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_email_with_attachment(subject, recipient_email, body_html, pdf_attachment=None, filename=None):
    try:
        msg = Message(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[recipient_email]
        )
        msg.html = body_html

        if pdf_attachment is not None:
            msg.attach(
                filename=filename,
                content_type='application/pdf',
                data=pdf_attachment
            )

        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending email: {e}")
        return False
