# custom_filters.py
from django import template
from student.models import Payment

register = template.Library()

@register.filter
def has_payment_for_course(user, course):
    return Payment.objects.filter(payment_user=user.profile, courses=course).exists()
