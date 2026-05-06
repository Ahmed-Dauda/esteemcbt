import json
from openai import OpenAI
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings


def index(request):
    return render(request, 'reminders/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def analyze_fraud(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        message_type = data.get('type', 'text')

        if not message:
            return JsonResponse({'error': 'No message provided'}, status=400)

        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            return JsonResponse({'error': 'OPENAI_API_KEY not set in settings'}, status=500)

        client = OpenAI(api_key=api_key)

        system_prompt = """You are FraudShield AI, an expert fraud detection system trained specifically for Nigerian financial fraud patterns.

You must respond with ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{
  "verdict": "FRAUD" | "SUSPICIOUS" | "SAFE",
  "confidence": <number 0-100>,
  "risk_score": <number 0-100>,
  "fraud_type": "<specific fraud type or 'None'>",
  "red_flags": ["<flag1>", "<flag2>"],
  "explanation": "<clear explanation in plain English>",
  "advice": "<specific actionable advice for a Nigerian user>",
  "similar_scams": ["<known scam name 1>", "<known scam name 2>"]
}

Known Nigerian fraud patterns: OTP phishing (GTBank, Access, UBA, Zenith, Opay, Moniepoint), advance fee fraud (419), lottery scams, job offer scams, Ponzi investment schemes, romance scams, fake CBN/EFCC alerts, BEC, crypto rug pulls, fake real estate, loan shark traps. Be specific and culturally aware."""

        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this for fraud (type: {message_type}):\n\n{message}"}
            ]
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if model wraps in ```json ... ```
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return JsonResponse(result)

    except json.JSONDecodeError as e:
        return JsonResponse({'error': f'Invalid JSON from model: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)