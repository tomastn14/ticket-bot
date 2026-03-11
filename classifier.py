import os
import json
import base64
import httpx
from rules import SYSTEM_PROMPT, ADJUST_PROMPT

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def _clean_json(text: str) -> str:
    """Limpia el texto de Gemini para extraer JSON puro."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Quitar primera y última línea (``` y ```)
        text = "\n".join(lines[1:-1])
    return text.strip()


async def classify_ticket(image_bytes: bytes) -> dict:
    """Manda la imagen del ticket a Gemini y devuelve la clasificación."""
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_b64
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        clean = _clean_json(raw_text)
        return json.loads(clean)

    except httpx.HTTPStatusError as e:
        return {"error": f"Error API Gemini: {e.response.status_code}"}
    except json.JSONDecodeError as e:
        return {"error": f"No pude parsear la respuesta: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


async def adjust_item(current_result: dict, instruction: str) -> dict:
    """Ajusta la clasificación según la instrucción del usuario."""
    prompt = ADJUST_PROMPT.format(
        current_result=json.dumps(current_result, ensure_ascii=False, indent=2),
        instruction=instruction
    )

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        clean = _clean_json(raw_text)
        return json.loads(clean)

    except httpx.HTTPStatusError as e:
        return {"error": f"Error API Gemini: {e.response.status_code}"}
    except json.JSONDecodeError:
        return {"error": "No entendí la instrucción, prueba a ser más específico"}
    except Exception as e:
        return {"error": str(e)}
