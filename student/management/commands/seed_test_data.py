"""Local-only seeder. Delete when done testing."""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from quiz.models import School, Course
from sms.models import Session, Term, ExamType, Courses
from users.models import Profile
from student.models import Result

User = get_user_model()


SUBJECT_TITLES = [
    'MATHS JSS1', 'MATHS JSS2', 'MATHS JSS3', 'MATHS SS1', 'MATHS SS2',
    'ENGLISH JSS1', 'ENGLISH JSS2', 'ENGLISH JSS3', 'ENGLISH SS1', 'ENGLISH SS2',
    'BASIC SCIENCE JSS1', 'BASIC SCIENCE JSS2', 'BASIC SCIENCE JSS3',
    'BASIC SCIENCE SS1',
]

STUDENTS = [
    (1, "Yusuf", "Ahmad", "JSS1", "Alh.", "YUSUF BOBI ABDULLAHI",
     "NO. 13, Jebba Close, Garki, Area 2, Abuja.",
     {'MATHS JSS1': 78, 'ENGLISH JSS1': 65, 'BASIC SCIENCE JSS1': 55}),
    (2, "Mohammed", "Garba", "JSS1", "Alh.", "MOHAMMED SIRAJU GARBA",
     "NO. 7, Maccido Dahlatu Str, Katampe, Abuja.",
     {'MATHS JSS1': 60, 'ENGLISH JSS1': 45, 'BASIC SCIENCE JSS1': 50}),
    (3, "Ade", "Bello", "JSS1", "Mr.", "ADE BELLO",
     "12 Lagos Street, Ikeja, Lagos.",
     {'MATHS JSS1': 40, 'ENGLISH JSS1': 35, 'BASIC SCIENCE JSS1': 45}),
    (4, "Usman", "Eshan", "SS1", "Maj. Gen.", "U. A. YUSUF",
     "Ipent 7 Estate, Abuja.",
     {'MATHS SS1': 60, 'ENGLISH SS1': 55, 'BASIC SCIENCE SS1': 52}),
    (5, "Sadiq", "Bala", "SS1", "Engr.", "SHEHU BELLO",
     "No. 127, Ozonma 'N' Abba Str, Apo, Abuja.",
     {'MATHS SS1': 50, 'ENGLISH SS1': 55, 'BASIC SCIENCE SS1': 50}),
    (6, "Ahmad", "Furyam", "JSS2", "Mal.", "MUHAMMED UZAIRU FURYAM",
     "No.16 First Avenue, Hilcrest Estate, Lokogoma.",
     {'MATHS JSS2': 72, 'ENGLISH JSS2': 80}),
]


class Command(BaseCommand):
    help = "Seed local test data for admission-letter testing."

    def handle(self, *args, **opts):
        self.stdout.write("=== SEEDING TEST DATA ===\n")

        session = Session.objects.filter(name='2025-2026').first()
        term = Term.objects.filter(name__iexact='First').first()
        exam_type = ExamType.objects.filter(name__iexact='Exam').first()

        if not (session and term and exam_type):
            self.stderr.write("Missing Session/Term/ExamType. Create manually first.")
            return

        self.stdout.write(f"Session={session} Term={term} ExamType={exam_type}")

        entrance, _ = School.objects.get_or_create(
            school_name='Esteem Entrance Exam',
            defaults={'name': 'Esteem Entrance Exam', 'customer': False},
        )
        boys, _ = School.objects.get_or_create(
            school_name='Esteem Boys College',
            defaults={
                'name': 'Esteem Boys College',
                'next_term_date': date(2025, 9, 7),
                'principal_name': 'Abubakar Ilani',
                'school_address': 'Lokogoma, Abuja',
            },
        )
        self.stdout.write(f"Entrance school id={entrance.id}")
        self.stdout.write(f"Boys College id={boys.id}\n")

        # sms.Courses
        courses = {}
        for t in SUBJECT_TITLES:
            c, _ = Courses.objects.get_or_create(title=t)
            courses[t] = c
        self.stdout.write(f"sms.Courses rows created/ensured: {len(courses)}\n")

        # quiz.Course (entrance exams)
        exam_ids = {}
        for t in SUBJECT_TITLES:
            c, _ = Course.objects.get_or_create(
                course_name=courses[t],
                session=session, term=term, exam_type=exam_type,
                schools=entrance,
                defaults={'total_marks': 100, 'show_questions': 100,
                          'duration_minutes': 60},
            )
            exam_ids[t] = c.id
        self.stdout.write("Entrance exams:")
        for t, i in exam_ids.items():
            self.stdout.write(f"  {i:>4}  {t}")
        self.stdout.write("")

        # Students + Results
        for idx, first, last, cls, gtitle, gname, gaddr, scores in STUDENTS:
            email = f"teststudent{idx}@example.com"
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={'username': email, 'first_name': first,
                          'last_name': last, 'student_class': cls,
                          'is_active': True},
            )
            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={'first_name': first, 'last_name': last,
                          'student_class': cls},
            )
            Profile.objects.filter(id=profile.id).update(
                first_name=first, last_name=last, student_class=cls,
                guardian_title=gtitle, guardian_name=gname,
                guardian_address=gaddr, guardian_email=f"parent{idx}@example.com",
            )
            for subject_title, marks in scores.items():
                Result.objects.update_or_create(
                    student=profile,
                    exam_id=exam_ids[subject_title],
                    session=session, term=term,
                    result_class='Entrance', exam_type=exam_type,
                    defaults={'marks': marks, 'schools': entrance},
                )
            self.stdout.write(f"  student id={profile.id} {first} {last} [{cls}] "
                              f"{list(scores.keys())}")

        self.stdout.write("\n=== SEED COMPLETE ===")
        self.stdout.write("Expected dry-run: Passed=3 Failed=2 Missing=1\n")