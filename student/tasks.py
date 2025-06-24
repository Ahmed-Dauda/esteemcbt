from celery import shared_task
from quiz import models as QMODEL
from users.models import Profile

@shared_task
def save_result_and_answers(user_id, course_id, total_marks, answers_dict):
    try:
        student = Profile.objects.select_related('user').get(user_id=user_id)
        course = QMODEL.Course.objects.select_related(
            'schools', 'course_name', 'session', 'term', 'exam_type'
        ).get(id=course_id)

        # Create or get the result object
        result, created = QMODEL.Result.objects.get_or_create(
            student=student,
            exam=course,
            session=course.session,
            term=course.term,
            exam_type=course.exam_type,
            result_class=student.student_class,
            defaults={
                'schools': course.schools,
                'marks': total_marks,
            }
        )

        # Save individual answers
        for q_id, info in answers_dict.items():
            try:
                question = QMODEL.Question.objects.get(id=int(q_id))
                QMODEL.StudentAnswer.objects.create(
                    result=result,
                    question=question,
                    selected_answer=info['selected'],
                    is_correct=(info['selected'] == info['correct'])
                )
            except QMODEL.Question.DoesNotExist:
                continue  # Skip if question not found

        return {'status': 'success'}


    except Exception as e:
        return {'status': 'error', 'message': str(e)}
