import base64
import os
import traceback
from django.conf import settings
from django.shortcuts import render
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def home(request):
    result         = None
    audio_url      = None
    audio_url_hausa = None
    error_message  = None

    if request.method == "POST":
        print("=== POST request received ===")

        try:
            voice_lang = request.POST.get("voice_lang", "en-US")
            is_hausa   = voice_lang == "ha"

            # ── CASE 1: IMAGE UPLOAD ─────────────────────────────────────────
            if request.FILES.get("image"):
                print("Processing image upload...")
                image = request.FILES["image"]
                print(f"Image: {image.name}, {image.size} bytes")

                image_bytes   = image.read()
                base64_image  = base64.b64encode(image_bytes).decode("utf-8")
                ext  = image.name.lower().split(".")[-1]
                mime = "image/png" if ext == "png" else "image/jpeg"

                system_prompt = """
You are an expert plant pathologist and agricultural extension officer specialising in Nigerian crops.

Your job is to carefully diagnose plant diseases from photos. You must:
- Examine EVERY visible symptom: leaf colour changes, spots, lesions, wilting, necrosis, mould, insect damage, stem discolouration
- Be specific — name the exact disease or pest if symptoms are visible
- NEVER say "healthy" if there is ANY sign of discolouration, spots, wilting, curling, lesions, holes, or abnormal growth
- If the image is blurry or unclear, say UNCLEAR and describe what you can see

Always respond in this EXACT format:

Category: HEALTHY or DISEASED or PEST_ATTACK or NUTRIENT_DEFICIENCY or UNCLEAR

Crop: name of the crop (e.g. Tomato, Maize, Cassava, Unknown)

Observation: one sentence describing exactly what you see on the plant

---

If HEALTHY:
Condition: Healthy plant
Care:
- tip 1
- tip 2
- tip 3

If DISEASED:
Disease: exact disease name (e.g. Tomato Late Blight, Cassava Mosaic Disease)
Severity: Mild / Moderate / Severe
Cause: brief cause (fungal, bacterial, viral, etc.)
Treatment:
- step 1 (use specific product names available in Nigeria e.g. Mancozeb, Ridomil)
- step 2
- step 3
Prevention:
- step 1
- step 2

If PEST_ATTACK:
Pest: name of pest
Severity: Mild / Moderate / Severe
Damage: what part of the plant is affected
Treatment:
- step 1
- step 2
Prevention:
- step 1
- step 2

If NUTRIENT_DEFICIENCY:
Deficiency: nutrient name (e.g. Nitrogen, Iron, Magnesium)
Severity: Mild / Moderate / Severe
Symptoms: what you observed
Treatment:
- step 1
- step 2

If UNCLEAR:
Possible issue: your best guess
Advice:
- suggestion 1
- suggestion 2

---

Then translate the FULL response into simple Hausa (as spoken in Northern Nigeria).

Format the translation exactly as:
---HAUSA---
<full Hausa translation here>
---END---

Keep all language short, clear, and practical for a rural farmer.
"""

                print("Calling OpenAI for image analysis...")
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "Carefully examine every part of this plant photo from a Nigerian farm. "
                                        "Look closely at the leaves, stems, spots, colour, texture, and any visible damage. "
                                        "Be very specific — name the exact disease or pest if you can identify symptoms. "
                                        "Do NOT say healthy if you can see any discolouration, spots, wilting, lesions, holes, or abnormal patterns."
                                    )
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime};base64,{base64_image}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=700,
                    timeout=45
                )

                result = response.choices[0].message.content
                print(f"Image response: {len(result)} chars")

            # ── CASE 2: VOICE INPUT ──────────────────────────────────────────
            elif request.POST.get("voice_text"):
                voice_text = request.POST.get("voice_text")
                print(f"Voice input ({voice_lang}): {voice_text}")

                if is_hausa:
                    # Farmer spoke in Hausa — answer primarily in Hausa, add English below
                    system_content = """
Kai ɗan gonar Najeriya ne kuma mai ba da shawara kan aikin gona. Manomi ya tambayi maka tambaya da Hausa.

Ka amsa da Hausa da farko — a taƙaice, a fili, kuma da amfani (ƙalla kalmomi 80).
Ka ba da shawara a kan yanayin aikin gona na Najeriya.
Ka ambaci sunayen kayayyakin sinadarai da ake samu a shagunan aikin gona na Najeriya inda ya dace.

Sa'an nan ka rubuta fassarar Turanci ta cikakken amsarka ta amfani da wannan tsari daidai:
---ENGLISH---
<English translation here>
---END---
"""
                else:
                    # Farmer spoke in English — answer in English, add Hausa translation below
                    system_content = """
You are a Nigerian agricultural extension officer helping smallholder farmers.

Rules:
- Answer immediately and confidently — do NOT ask for more details
- Give practical, actionable advice specific to Nigerian farming conditions
- Mention product names available in Nigerian agro-chemical shops where relevant
- Keep answers short and useful (max 120 words)
- Respond in English first, then add a Hausa translation below using this exact format:
---HAUSA---
<Hausa translation here>
---END---
"""

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user",   "content": voice_text}
                    ],
                    max_tokens=300,
                    timeout=30
                )

                result = response.choices[0].message.content
                print(f"Voice response: {len(result)} chars")

            else:
                error_message = "No image or voice input received"
                print(error_message)

            # ── GENERATE AUDIO ───────────────────────────────────────────────
            if result:
                os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

                # Parse English + Hausa sections (handles both voice directions)
                if is_hausa and "---ENGLISH---" in result and "---END---" in result:
                    # Hausa voice: primary = Hausa, secondary = English
                    hausa_part   = result.split("---ENGLISH---")[0].strip()
                    english_part = result.split("---ENGLISH---")[1].split("---END---")[0].strip()
                elif "---HAUSA---" in result and "---END---" in result:
                    # English voice or image: primary = English, secondary = Hausa
                    english_part = result.split("---HAUSA---")[0].strip()
                    hausa_part   = result.split("---HAUSA---")[1].split("---END---")[0].strip()
                else:
                    # Fallback
                    parts        = result.split("---")
                    english_part = parts[0].strip()
                    hausa_part   = parts[-1].strip() if len(parts) > 1 else ""

                print(f"English ({len(english_part)} chars): {english_part[:80]}...")
                print(f"Hausa   ({len(hausa_part)} chars): {hausa_part[:80]}...")

                # English TTS
                if english_part:
                    try:
                        print("Generating English TTS...")
                        speech_en = client.audio.speech.create(
                            model="tts-1-hd",
                            voice="nova",
                            input=english_part[:4096],
                            speed=0.95
                        )
                        path_en = os.path.join(settings.MEDIA_ROOT, "farmer_voice_en.mp3")
                        with open(path_en, "wb") as f:
                            f.write(speech_en.content)
                        audio_url = settings.MEDIA_URL + "farmer_voice_en.mp3"
                        print(f"English audio saved: {audio_url}")
                    except Exception as e:
                        print(f"English TTS error: {e}")

                # Hausa TTS
                if hausa_part:
                    try:
                        print("Generating Hausa TTS...")
                        speech_ha = client.audio.speech.create(
                            model="tts-1-hd",
                            voice="nova",
                            input=hausa_part[:4096],
                            speed=0.9
                        )
                        path_ha = os.path.join(settings.MEDIA_ROOT, "farmer_voice_ha.mp3")
                        with open(path_ha, "wb") as f:
                            f.write(speech_ha.content)
                        audio_url_hausa = settings.MEDIA_URL + "farmer_voice_ha.mp3"
                        print(f"Hausa audio saved: {audio_url_hausa}")
                    except Exception as e:
                        print(f"Hausa TTS error: {e}")
                else:
                    print("No Hausa text — skipping Hausa audio")

        except Exception as e:
            error_message = f"Error: {str(e)}"
            print(f"Full traceback:\n{traceback.format_exc()}")
            result = f"⚠️ Sorry, an error occurred: {str(e)}. Please try again."

    return render(request, "index.html", {
        "result":           result,
        "audio_url":        audio_url,
        "audio_url_hausa":  audio_url_hausa,
        "error_message":    error_message,
    })