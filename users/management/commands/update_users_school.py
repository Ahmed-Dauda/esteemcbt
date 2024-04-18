# management/commands/update_users_school.py

from django.core.management.base import BaseCommand
from quiz.models import NewUser, School

class Command(BaseCommand):
    help = 'Update existing user records with default school value'

    def handle(self, *args, **options):
        default_school = School.objects.get(school_name='Codethinkers Academy')
        users_without_school = NewUser.objects.filter(school__isnull=True)
        for user in users_without_school:
            user.school = default_school
            user.save()
        self.stdout.write(self.style.SUCCESS('Successfully updated user records with default school value'))
