import base64
import os
import traceback
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def home(request):
    result = None
    audio_url = None
    error_message = None

    if request.method == "POST":
        print("=== POST request received ===")  # Debug log
        
        try:
            # 🟢 CASE 1: IMAGE UPLOAD (from camera or gallery)
            if request.FILES.get("image"):
                print("Processing image upload...")
                image = request.FILES["image"]
                print(f"Image name: {image.name}, Size: {image.size} bytes")

                image_bytes = image.read()
                base64_image = base64.b64encode(image_bytes).decode("utf-8")

                system_prompt = """
You are an expert agricultural assistant for farmers in Nigeria.

Always respond in this format:

Category: HEALTHY or DISEASED or UNCLEAR
Observation: short description

If HEALTHY:
Condition: Healthy plant
Care:
- tip 1
- tip 2
- tip 3

If DISEASED:
Disease: name
Cause: short cause
Treatment:
- step 1
- step 2
- step 3
Prevention:
- step 1
- step 2
- step 3

If UNCLEAR:
Possible issue: short guess
Advice:
- suggestion 1
- suggestion 2

Then translate the FULL response into simple Hausa.

Format:
---
Hausa:
<translation here>

Keep everything short and clear.
"""

                print("Calling OpenAI API for image analysis...")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Analyze this plant image from a farm in Nigeria."},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500,
                    timeout=30  # Add timeout
                )

                result = response.choices[0].message.content
                print(f"API Response received: {len(result)} characters")

            # 🟢 CASE 2: VOICE INPUT (TEXT FROM JS)
            elif request.POST.get("voice_text"):
                voice_text = request.POST.get("voice_text")
                print(f"Processing voice input: {voice_text}")

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": """
You are a Nigerian agricultural assistant.

Answer farmer questions directly and confidently.

Rules:
- Do NOT ask for more details
- Give practical advice immediately
- Keep answers short and useful (max 100 words)
"""
                        },
                        {
                            "role": "user",
                            "content": voice_text
                        }
                    ],
                    max_tokens=200,
                    timeout=30
                )

                result = response.choices[0].message.content
                print(f"Voice response received: {len(result)} characters")
            
            else:
                error_message = "No image or voice input received"
                print(error_message)
            
            # 🔊 Convert ANY result to speech
            if result:
                try:
                    print("Generating TTS audio...")
                    speech = client.audio.speech.create(
                        model="tts-1",
                        voice="alloy",
                        input=result[:4096]
                    )

                    # Ensure media directory exists
                    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
                    
                    audio_path = os.path.join(settings.MEDIA_ROOT, "farmer_voice.mp3")
                    with open(audio_path, "wb") as f:
                        f.write(speech.content)

                    audio_url = settings.MEDIA_URL + "farmer_voice.mp3"
                    print(f"Audio generated: {audio_url}")
                except Exception as e:
                    print(f"Audio generation error: {str(e)}")
                    # Don't fail if audio doesn't work
                    
        except Exception as e:
            error_message = f"Error: {str(e)}"
            print(f"Full error: {traceback.format_exc()}")
            result = f"⚠️ Sorry, an error occurred: {str(e)}. Please try again."

    return render(request, "index.html", {
        "result": result,
        "audio_url": audio_url,
        "error_message": error_message
    })