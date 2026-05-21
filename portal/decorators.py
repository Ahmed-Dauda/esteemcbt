# portal/decorators.py

from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from .models import SchoolSubscription


def ensure_subscription_exists(school):
    """
    Ensures a SchoolSubscription exists even if the signal failed.
    """
    if not hasattr(school, "subscription"):
        subscription, created = SchoolSubscription.objects.get_or_create(school=school)
        return subscription
    return school.subscription


def require_feature(feature):
    """
    Generic decorator for protecting modules like:
    - CBT  -> "cbt"
    - Report Card -> "report_card"

    Checks:
    - User authenticated
    - School assigned to user
    - Subscription exists
    - Feature active
    - Feature not expired
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            user = request.user

            # 1️⃣ Must be logged in
            if not user.is_authenticated:
                return redirect(f"/login/?next={request.path}")

            # 2️⃣ User must belong to a school
            school = getattr(user, "school", None)
            if not school:
                return redirect(reverse("portal:payment_required"))

            # 3️⃣ Ensure subscription exists (auto-create)
            subscription = ensure_subscription_exists(school)

            # 4️⃣ Dynamic field access
            is_active = getattr(subscription, f"{feature}_active")
            expiry = getattr(subscription, f"{feature}_expiry")

            today = timezone.localdate()

            # 5️⃣ Not active
            if not is_active:
                return redirect(reverse("portal:payment_required"))

            # 6️⃣ Expired
            if expiry and expiry < today:
                return redirect(reverse("portal:payment_required"))

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Ready-made decorators
require_cbt_subscription = require_feature("cbt")
require_reportcard_subscription = require_feature("report_card")
