import africastalking
from django.conf import settings


def send_message(phone, message):
    try:
        africastalking.initialize(
            username=settings.AT_USERNAME,
            api_key=settings.AT_API_KEY
        )

        sms = africastalking.SMS

        response = sms.send(message, [phone])
        print("SUCCESS:", response)

        return True, response

    except Exception as e:
        print("ERROR:", e)
        return False, str(e)