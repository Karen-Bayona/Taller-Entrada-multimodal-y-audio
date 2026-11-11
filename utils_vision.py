"""
  - LLM cargado con cargar_llm() de utils/load_model.py (LangChain + Groq)
  - imagen enviada como bloque {"type": "image", "base64": ..., "mime_type": ...}
"""
import base64
import mimetypes
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from utils.load_model import cargar_llm

load_dotenv()  # lee GROQ_API_KEY (y demás) desde .env

MODELO_VISION = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")

# Límites: máx. 3 imágenes por solicitud. Para base64 se usa un tope prudente de 4 MB por imagen.
MAX_BYTES = 4 * 1024 * 1024
MAX_IMAGENES = 3
TIPOS_VALIDOS = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/jpg"}


def crear_llm(max_tokens: int = 999, reasoning_effort: str = "low"):
    """Carga el modelo de visión."""
    return cargar_llm(
        model_name=MODELO_VISION,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort,
    )


def imagen_a_bloque(ruta: str | Path) -> dict:
    """Lee una imagen local y devuelve el bloque de contenido en base64."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe la imagen: {ruta}")

    mime, _ = mimetypes.guess_type(ruta)
    if mime not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo de imagen no soportado ({mime}) en {ruta.name}")

    datos = ruta.read_bytes()
    if len(datos) > MAX_BYTES:
        raise ValueError(f"{ruta.name} supera {MAX_BYTES // 1024 // 1024} MB")

    b64 = base64.b64encode(datos).decode("utf-8")
    return {"type": "image", "base64": b64, "mime_type": mime}


def consultar_vision(llm, imagenes: list[str | Path], prompt: str) -> str:
    """Envía prompt + 1..3 imágenes al modelo y devuelve el texto limpio."""
    if not 1 <= len(imagenes) <= MAX_IMAGENES:
        raise ValueError(f"Se permiten entre 1 y {MAX_IMAGENES} imágenes")

    contenido = [{"type": "text", "text": prompt}]
    contenido += [imagen_a_bloque(r) for r in imagenes]

    respuesta = llm.invoke([HumanMessage(content=contenido)])
    return limpiar_respuesta(str(respuesta.content))


def limpiar_respuesta(texto: str) -> str:
    """Quita bloques <think>...</think> y cercos ```json que algunos modelos añaden."""
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL)
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto.strip())
    return texto.strip()
