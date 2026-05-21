from celery import shared_task
from django.db import transaction
from quiz import models as QMODEL
from student.models import Profile

@shared_task(bind=True)
def save_result_and_answers_task(self, course_id, student_id, total_marks, answers_data):
    try:
        course = QMODEL.Course.objects.select_related('schools', 'session', 'term', 'exam_type').get(id=course_id)
        student = Profile.objects.select_related('user').get(id=student_id)

        if QMODEL.Result.objects.filter(
            student=student,
            exam=course,
            session=course.session,
            term=course.term,
            exam_type=course.exam_type,
            result_class=student.student_class
        ).exists():
            return 'Result already exists'

        with transaction.atomic():
            result = QMODEL.Result.objects.create(
                schools=course.schools,
                marks=total_marks,
                exam=course,
                session=course.session,
                term=course.term,
                exam_type=course.exam_type,
                student=student,
                result_class=student.student_class
            )

            answer_objs = [
                QMODEL.StudentAnswer(
                    result=result,
                    question_id=ans['question_id'],
                    selected_answer=ans['selected_answer'],
                    is_correct=ans['is_correct']
                )
                for ans in answers_data
            ]
            QMODEL.StudentAnswer.objects.bulk_create(answer_objs)

        return 'Result and answers saved ✅'

    except Exception as e:
        return f'Failed: {str(e)}'
