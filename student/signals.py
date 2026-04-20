# signals.py (in your quiz app)
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from quiz.models import Course

@receiver(post_save, sender=Course)
@receiver(post_delete, sender=Course)
def bust_course_cache(sender, instance, **kwargs):
    if instance.schools and instance.course_grade_set.exists():
        for grade in instance.course_grade_set.all():
            cache.delete(f"courses:{instance.schools_id}:{grade.name}")