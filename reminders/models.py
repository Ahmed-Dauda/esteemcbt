from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    parent_phone = models.CharField(max_length=20)
    class_name = models.CharField(max_length=50)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return self.name


class ReminderLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=20)  # before, due, after
    sent_at = models.DateTimeField(auto_now_add=True)