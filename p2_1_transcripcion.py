"""
Punto 2.1 - Transcripción desde archivo (Groq Whisper).

Para cada audio listado en audios_info.json:
  archivo -> Whisper -> transcripción -> comparación con lo que se dijo (WER)
Guarda:
  resultados/p2_1_transcripciones.json  (lo reutiliza el punto 2.2)
  resultados/p2_1_resultado.md          (tabla de la plantilla 2.1)

Uso:  python p2_1_transcripcion.py
Sigue el estilo de audio_input.py de la clase (Groq().audio.transcriptions).
"""
import json
import re
import wave
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # lee GROQ_API_KEY desde .env

# ---------------------------------------------------------------- configuración
CARPETA_AUDIOS = Path("audios")
ARCHIVO_INFO = Path("audios_info.json")
CARPETA_SALIDA = Path("resultados")

MODELO_AUDIO = "whisper-large-v3-turbo"  # alternativa: whisper-large-v3
IDIOMA = "es"
# Opcional: pista de vocabulario para Whisper. Déjalo vacío en la 1.ª corrida
# y pruébalo después para comparar (sirve para el análisis de términos técnicos).
PROMPT_TECNICO = ""  # p. ej. "derivada, regla de la cadena, regla del cociente, seno, logaritmo natural"

FORMATOS = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}
MAX_BYTES = 25 * 1024 * 1024  # 25 MB (plan gratuito)


# ------------------------------------------------------------------- utilidades
def duracion_wav(ruta: Path) -> float | None:
    """Duración en segundos para .wav (respaldo si la API no la informa)."""
    if ruta.suffix.lower() != ".wav":
        return None
    with wave.open(str(ruta), "rb") as w:
        return w.getnframes() / w.getframerate()


def normalizar(texto: str) -> list[str]:
    """Minúsculas y sin puntuación, para comparar palabra por palabra."""
    return re.sub(r"[^\w\s]", "", texto.lower()).split()


def wer(referencia: str, hipotesis: str) -> float:
    """Word Error Rate (%) con distancia de edición sobre palabras."""
    r, h = normalizar(referencia), normalizar(hipotesis)
    if not r:
        return 0.0
    d = list(range(len(h) + 1))
    for i, pr in enumerate(r, start=1):
        previo, d[0] = d[0], i
        for j, ph in enumerate(h, start=1):
            actual = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, previo + (pr != ph))
            previo = actual
    return 100 * d[len(h)] / len(r)


def transcribir(cliente: Groq, ruta: Path) -> tuple[str, float | None]:
    """Transcribe un archivo y devuelve (texto, duración en segundos)."""
    if ruta.suffix.lower() not in FORMATOS:
        raise ValueError(f"Formato no soportado: {ruta.suffix}")
    datos = ruta.read_bytes()
    if len(datos) > MAX_BYTES:
        raise ValueError(f"{ruta.name} supera 25 MB")

    kwargs = dict(
        file=(ruta.name, datos),
        model=MODELO_AUDIO,
        language=IDIOMA,
        response_format="verbose_json",  # incluye la duración
        temperature=0.0,
    )
    if PROMPT_TECNICO:
        kwargs["prompt"] = PROMPT_TECNICO

    res = cliente.audio.transcriptions.create(**kwargs)
    duracion = getattr(res, "duration", None) or duracion_wav(ruta)
    return res.text.strip(), duracion


def celda(texto) -> str:
    """Evita que | y saltos de línea rompan la tabla Markdown."""
    return str(texto).replace("|", "/").replace("\n", " ")


# ------------------------------------------------------------------------ main
def main() -> None:
    CARPETA_SALIDA.mkdir(exist_ok=True)
    info = json.loads(ARCHIVO_INFO.read_text(encoding="utf-8"))
    cliente = Groq()  # toma GROQ_API_KEY del entorno, como en audio_input.py
    print(f"Modelo: {MODELO_AUDIO} | idioma: {IDIOMA}\n")

    resultados = {}
    for nombre, datos in info.items():
        ruta = CARPETA_AUDIOS / nombre
        print(f"--- {nombre} ({datos['hablante']}, {datos['condicion']}) ---")
        try:
            texto, duracion = transcribir(cliente, ruta)
        except Exception as e:  # archivo faltante, formato, red, API...
            print(f"  ERROR: {e}\n")
            resultados[nombre] = {**datos, "transcripcion": None, "error": str(e)}
            continue

        error_wer = wer(datos["lo_que_se_dijo"], texto)
        print(f"  Dijo         : {datos['lo_que_se_dijo']}")
        print(f"  Transcripción: {texto}")
        print(f"  Duración: {duracion and round(duracion, 1)} s | WER: {error_wer:.1f} %\n")
        resultados[nombre] = {
            **datos,
            "duracion_s": round(duracion, 1) if duracion else None,
            "transcripcion": texto,
            "wer_pct": round(error_wer, 1),
        }

    (CARPETA_SALIDA / "p2_1_transcripciones.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Tabla Markdown con las columnas de la plantilla 2.1 (+ WER)
    filas = [
        "| Audio | Hablante | Condición (con/sin ruido) | Duración (s) | Lo que se dijo | Transcripción | WER (%) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for nombre, r in resultados.items():
        filas.append(
            f"| {nombre} | {r['hablante']} | {r['condicion']} | {r.get('duracion_s', '-')} | "
            f"{celda(r['lo_que_se_dijo'])} | {celda(r['transcripcion'] or 'ERROR: ' + r['error'])} | "
            f"{r.get('wer_pct', '-')} |"
        )
    prompt_txt = f"`{PROMPT_TECNICO}`" if PROMPT_TECNICO else "(sin prompt)"
    (CARPETA_SALIDA / "p2_1_resultado.md").write_text(
        f"# 2.1 Transcripción desde archivo\n\n- **Modelo:** `{MODELO_AUDIO}`\n"
        f"- **Idioma:** {IDIOMA}\n- **Prompt de vocabulario:** {prompt_txt}\n\n"
        + "\n".join(filas) + "\n",
        encoding="utf-8",
    )
    print("Guardado: resultados/p2_1_resultado.md y p2_1_transcripciones.json")


if __name__ == "__main__":
    main()