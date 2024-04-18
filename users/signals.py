# signals.py

# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from users.models import Profile
# from .models import ReferrerProfile

# @receiver(post_save, sender=Profile)
# def assign_referrer(sender, instance, created, **kwargs):
#     if created:
#         referral_code = instance.referrerprofile.referral_code
#         if referral_code:
#             try:
#                 referrer = Profile.objects.get(referrerprofile__referral_code=referral_code)
#                 referrer_profile, created = ReferrerProfile.objects.get_or_create(user=instance)
#                 referrer_profile.referrer = referrer
#                 referrer_profile.save()
#             except Profile.DoesNotExist:
#                 pass
