import boto3
import httpx
from botocore.config import Config
from openai import OpenAI
from .config import settings
from .retrieve import Hit


SYSTEM = """Eres un asistente de una empresa de transporte. Responde únicamente con la evidencia proporcionada. Escribe en español. Cita cada afirmación relevante con [documento, p. N]. Si la evidencia no basta, dilo explícitamente. No inventes procedimientos, plazos ni responsabilidades."""


def build_prompt(question: str, hits: list[Hit]) -> str:
    evidence = "\n\n".join(f"EVIDENCIA {i+1} [{h.document}, p. {h.page}]\n{h.content}" for i, h in enumerate(hits))
    return f"PREGUNTA:\n{question}\n\nEVIDENCIA:\n{evidence}\n\nRESPUESTA:"


def generate_answer(question: str, hits: list[Hit]) -> tuple[str, str]:
    if not hits:
        return "No se encontró evidencia suficiente en los documentos procesados.", "sin_evidencia"
    prompt = build_prompt(question, hits)
    if settings.generator_provider == "bedrock":
        client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            config=Config(retries={"max_attempts": 5, "mode": "adaptive"}),
        )
        response = client.converse(
            modelId=settings.bedrock_model,
            system=[{"text": SYSTEM}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={
                "maxTokens": settings.bedrock_max_tokens,
                "temperature": 0,
            },
        )
        text = "".join(
            block.get("text", "")
            for block in response["output"]["message"]["content"]
            if "text" in block
        )
        return text or "Sin respuesta", "bedrock"
    if settings.generator_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY no está configurada")
        response = OpenAI(api_key=settings.openai_api_key).chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or "Sin respuesta", "openai"
    if settings.generator_provider == "ollama":
        response = httpx.post(
            f"{settings.ollama_url.rstrip('/')}/api/chat",
            timeout=120,
            json={"model": settings.ollama_model, "stream": False, "options": {"temperature": 0}, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]},
        )
        response.raise_for_status()
        return response.json()["message"]["content"], "ollama"
    citations = " ".join(f"[{h.document}, p. {h.page}]" for h in hits)
    return f"No se configuró un modelo generativo. La evidencia recuperada para responder se encuentra en: {citations}", "solo_recuperacion"
