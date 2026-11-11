"""
Punto 2.2 - Respuesta del modelo a partir de la transcripción.

Flujo: audio -> transcripción (resultado de 2.1) -> LLM -> respuesta.
Lee resultados/p2_1_transcripciones.json (generado por p2_1_transcripcion.py),
envía cada transcripción al modelo y guarda resultados/p2_2_resultado.md.

Uso:  python p2_2_respuesta_transcripcion.py
Sigue el estilo de audio_input.py (cargar_llm + HumanMessage).
"""
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from utils.load_model import cargar_llm
from utils_vision import limpiar_respuesta

load_dotenv()

# ---------------------------------------------------------------- configuración
MODELO = "qwen/qwen3.8-27b"  # el mismo que usa audio_input.py en clase
ARCHIVO_TRANSCRIPCIONES = Path("resultados/p2_1_transcripciones.json")
ARCHIVO_SALIDA = Path("resultados/p2_2_resultado.md")

# Audios a enviar al modelo (la plantilla tiene 4 filas en 2.2)
AUDIOS = ["audio_1.wav", "audio_2.wav", "audio_4.wav", "audio_5.wav"]

SISTEMA = (
    "Eres un tutor de cálculo diferencial. Responde en español, de forma clara "
    "y breve, mostrando los pasos de la derivación en notación de texto "
    "(por ejemplo x^2, sin(x))."
)


def celda(texto: str, limite: int = 350) -> str:
    """Una sola línea, sin '|', y recortada para que la tabla sea legible."""
    texto = " ".join(str(texto).replace("|", "/").split())
    return texto if len(texto) <= limite else texto[:limite] + "…"


def main() -> None:
    transcripciones = json.loads(ARCHIVO_TRANSCRIPCIONES.read_text(encoding="utf-8"))
    llm = cargar_llm(model_name=MODELO, max_tokens=4096, reasoning_effort="low")
    print(f"Modelo: {MODELO}\n")

    filas, detalle = [], []
    for audio in AUDIOS:
        datos = transcripciones.get(audio)
        if not datos or not datos.get("transcripcion"):
            print(f"--- {audio}: sin transcripción, se omite ---\n")
            continue

        transcripcion = datos["transcripcion"]
        print(f"--- {audio} ({datos['hablante']}, {datos['condicion']}) ---")
        print(f"Transcripción: {transcripcion}")

        try:
            r = llm.invoke([SystemMessage(SISTEMA), HumanMessage(transcripcion)])
            respuesta = limpiar_respuesta(str(r.content))
        except Exception as e:  # el programa informa y continúa
            respuesta = f"ERROR: {e}"
        print(f"Respuesta:\n{respuesta}\n")

        filas.append(
            f"| {audio} | {celda(transcripcion)} | {celda(respuesta)} | (completar Sí/No) |"
        )
        detalle.append(
            f"### {audio} ({datos['hablante']}, {datos['condicion']})\n\n"
            f"**Transcripción enviada:** {transcripcion}\n\n"
            f"**Respuesta completa del modelo:**\n\n{respuesta}\n"
        )

    contenido = (
        "# 2.2 Respuesta del modelo a partir de la transcripción\n\n"
        f"- **Fecha:** {datetime.now():%Y-%m-%d %H:%M}\n- **Modelo:** `{MODELO}`\n\n"
        "| Audio | Transcripción enviada al modelo | Respuesta del modelo (resumen) | ¿Respuesta correcta y pertinente? (Sí/No) |\n"
        "| :--- | :--- | :--- | :--- |\n" + "\n".join(filas) +
        "\n\n## Respuestas completas\n\n" + "\n".join(detalle)
    )
    ARCHIVO_SALIDA.write_text(contenido, encoding="utf-8")
    print(f"Guardado: {ARCHIVO_SALIDA}")


if __name__ == "__main__":
    main()