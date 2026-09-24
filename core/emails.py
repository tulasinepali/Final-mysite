import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail.backends.smtp import EmailBackend
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import SiteSettings, Subscriber

logger = logging.getLogger(__name__)


def get_mail_connection():
    """
    Returns an EmailBackend connection. If custom SMTP is configured in
    SiteSettings, uses those credentials; otherwise falls back to Django default.
    """
    try:
        s = SiteSettings.objects.first()
        if s and s.email_host and s.email_host_user:
            return EmailBackend(
                host=s.email_host,
                port=s.email_port or 587,
                username=s.email_host_user,
                password=s.email_host_password or '',
                use_tls=s.email_use_tls,
                timeout=10,
                fail_silently=False,
            )
    except Exception as e:
        logger.warning(f"Error initializing custom SMTP backend, falling back to default: {e}")
    
    return get_connection()


def get_sender_address():
    """
    Returns a formatted 'From' address like 'Tulasi Nepali <info@domain.com>'.
    """
    s = SiteSettings.objects.first()
    email_addr = ''
    display_name = 'Tulasi Nepali'
    
    if s:
        display_name = s.owner_name or s.site_name or display_name
        email_addr = s.sender_email or s.contact_email or s.email_host_user
        
    if not email_addr:
        email_addr = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@tulasinepali.com.np')
        
    return f"{display_name} <{email_addr}>"


def send_broadcast_to_subscribers(subject, headline, body_html, cta_text=None, cta_url=None, recipient_list=None):
    """
    Sends an email newsletter or announcement to active subscribers.
    Returns (success: bool, sent_count: int, error_message: str)
    """
    s = SiteSettings.objects.first()
    sender = get_sender_address()

    if recipient_list is None:
        recipients = list(Subscriber.objects.filter(is_active=True).values_list('email', flat=True))
    else:
        recipients = list(recipient_list)

    if not recipients:
        return False, 0, "No active subscribers found."

    context = {
        'site_settings': s,
        'subject': subject,
        'headline': headline,
        'body_html': body_html,
        'cta_text': cta_text,
        'cta_url': cta_url,
    }

    try:
        html_message = render_to_string('emails/subscriber_newsletter.html', context)
    except Exception:
        # Fallback inline template if file is not rendered
        html_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e1e7f0; border-radius: 8px;">
            <h2 style="color: #0559b7; margin-bottom: 15px;">{headline}</h2>
            <div style="color: #333; line-height: 1.6; margin-bottom: 25px;">{body_html}</div>
            {f'<p><a href="{cta_url}" style="display:inline-block; padding: 12px 24px; background: #0559b7; color: #fff; text-decoration: none; border-radius: 50px; font-weight: bold;">{cta_text}</a></p>' if cta_url and cta_text else ''}
            <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">
            <p style="font-size: 12px; color: #888;">You received this email because you subscribed to updates on {s.site_name if s else 'Learning Platform'}.</p>
        </div>
        """

    text_message = strip_tags(html_message)
    connection = get_mail_connection()
    sent_count = 0
    errors = []

    # Send in batches of 50 to avoid SMTP rate limiting
    batch_size = 50
    for i in range(0, len(recipients), batch_size):
        batch = recipients[i:i + batch_size]
        try:
            # Send with BCC so recipients' addresses remain private
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=sender,
                to=[sender], # To header
                bcc=batch,   # Hidden list
                connection=connection,
            )
            msg.attach_alternative(html_message, "text/html")
            sent = msg.send(fail_silently=False)
            sent_count += len(batch) if sent else 0
        except Exception as e:
            logger.error(f"Failed to send email batch to subscribers: {e}")
            errors.append(str(e))

    if sent_count > 0:
        return True, sent_count, None
    else:
        err_msg = "; ".join(errors) if errors else "Failed to send email."
        return False, 0, err_msg


def trigger_auto_email_notification(content_type, title, description, url, site_url=None):
    """
    Trigger automated email to subscribers if the corresponding toggle is turned on in SiteSettings.
    content_type: 'quiz', 'note', 'blog', 'download'
    """
    s = SiteSettings.objects.first()
    if not s:
        return False, 0, "No site settings found."

    should_send = False
    if content_type == 'quiz' and s.auto_email_on_quiz:
        should_send = True
        type_label = "New Practice Quiz Available"
        cta_label = "Start MCQ Quiz Now"
    elif content_type == 'note' and s.auto_email_on_note:
        should_send = True
        type_label = "New Study Note Published"
        cta_label = "Read Study Note"
    elif content_type == 'blog' and s.auto_email_on_blog:
        should_send = True
        type_label = "New Article & Guide Published"
        cta_label = "Read Full Guide"
    elif content_type == 'download' and s.auto_email_on_download:
        should_send = True
        type_label = "New Download Resource Available"
        cta_label = "Download PDF Resource"

    if not should_send:
        return False, 0, f"Auto-email notification for '{content_type}' is disabled in settings."

    if not site_url:
        site_url = getattr(settings, 'SITE_URL', 'https://tulasinepali.com.np')
        if getattr(settings, 'DEBUG', False) and not getattr(settings, 'SITE_URL', None):
            site_url = 'http://127.0.0.1:8000'

    full_url = url
    if site_url and not url.startswith('http'):
        full_url = f"{site_url.rstrip('/')}/{url.lstrip('/')}"

    subject = f"[{s.site_name}] {type_label}: {title}"
    headline = f"📢 {type_label}"
    body_html = f"""
    <p>Hello Learner,</p>
    <p>A new <strong>{type_label.lower()}</strong> has just been published on <strong>{s.site_name}</strong>:</p>
    <div style="background: #edf2f8; padding: 16px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #0559b7;">
        <h3 style="margin-top: 0; color: #0559b7;">{title}</h3>
        <p style="margin-bottom: 0; color: #555;">{description or 'Access this resource directly on the platform for free.'}</p>
    </div>
    """

    return send_broadcast_to_subscribers(
        subject=subject,
        headline=headline,
        body_html=body_html,
        cta_text=cta_label,
        cta_url=full_url,
    )
