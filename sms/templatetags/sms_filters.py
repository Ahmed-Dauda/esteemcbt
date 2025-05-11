from django import template
from student.models import Payment


register = template.Library()

# sms/templatetags/sms_filters.py
from django import template
from urllib.parse import urlparse, parse_qs

register = template.Library()

@register.filter
def youtube_embed_url(value):
    try:
        parsed_url = urlparse(value)
        video_id = ""

        if 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path.strip('/')
        elif 'youtube.com' in parsed_url.netloc:
            query = parse_qs(parsed_url.query)
            video_id = query.get('v', [None])[0]

        if video_id:
            return f"https://www.youtube.com/embed/{video_id}?theme=dark&autoplay=1&keyboard=1&autohide=2&cc_load_policy=1&modestbranding=1&fs=0&showinfo=0&rel=0&iv_load_policy=3&mute=0&loop=0&controls=0"
    except Exception as e:
        return value  # fallback to original if parsing fails

    return value



@register.filter
def has_payment_for_course(user, course):
    return Payment.objects.filter(payment_user=user.profile, courses=course).exists()
