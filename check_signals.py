import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school.settings')
django.setup()

from django.db.models.signals import post_save, pre_save, post_delete
import gc

for name, signal in [('post_save', post_save), ('pre_save', pre_save), ('post_delete', post_delete)]:
    print(f'\n=== {name} ({len(signal.receivers)} receivers) ===')
    for lookup in signal.receivers:
        ref = lookup[1]
        try:
            func = ref()
            if func:
                print(f'  {func.__module__} -> {func.__qualname__}')
            else:
                print(f'  (dead weakref) {lookup}')
        except Exception:
            print(f'  {lookup}')