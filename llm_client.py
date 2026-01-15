import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY)
MODEL_NAME = "llama-3.3-70b-versatile"
def _create_client() -> Groq:
    return Groq(api_key=API_KEY)
def generate_plan(prompt: str) -> str:
    client = _create_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a certified fitness trainer and dietitian for college students. "
                    "Always generate safe, realistic, and budget-friendly workout and diet plans. "
                    "Avoid medical claims and add a short disclaimer at the end."
                ),
            },
            {
                "role": "system",
                "content": (
                    "For this task, you MUST respond with ONLY valid JSON, no markdown, "
                    "no explanation, and no text before or after the JSON. "
                    "If you are unsure, still respond with best-effort JSON following the schema."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content
