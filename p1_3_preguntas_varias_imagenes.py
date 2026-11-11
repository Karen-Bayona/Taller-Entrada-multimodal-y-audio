
from datetime import datetime
from pathlib import Path

from utils_vision import MAX_IMAGENES, MODELO_VISION, consultar_vision, crear_llm

# ---------------------------------------------------------------- configuración
CARPETA_IMAGENES = Path("imagenes")
IMAGENES = [
    CARPETA_IMAGENES / "derivada_2.jpeg",
    CARPETA_IMAGENES / "derivada_3.jpeg",
]  # máximo 3 imágenes por solicitud
CARPETA_SALIDA = Path("resultados")
ARCHIVO_SALIDA = CARPETA_SALIDA / "p1_3_resultado.md"

PREGUNTA = (
    "Compara las dos imágenes de derivadas de forma muy concisa: "
    "1) ¿Qué función se debe derivar en cada una?, "
    "2) ¿Qué regla(s) de derivación requiere cada ejercicio?, "
    "3) ¿Cuál es más compleja y por qué? "
    "Sé breve y directo en español."
)


def guardar_markdown(respuesta: str) -> None:
    """Guarda pregunta, imágenes (rutas relativas) y respuesta en un .md."""
    CARPETA_SALIDA.mkdir(exist_ok=True)

    # Las rutas son relativas a resultados/ para que el .md muestre las imágenes
    imagenes_md = "\n".join(
        f"**Imagen {i}: `{ruta.name}`**\n\n![{ruta.name}](../{ruta.as_posix()})\n"
        for i, ruta in enumerate(IMAGENES, start=1)
    )

    contenido = (
        "# 1.3 Varias imágenes en una solicitud\n\n"
        f"- **Fecha:** {datetime.now():%Y-%m-%d %H:%M}\n"
        f"- **Modelo:** `{MODELO_VISION}`\n"
        f"- **Imágenes enviadas:** {len(IMAGENES)}\n\n"
        f"## Imágenes\n\n{imagenes_md}\n"
        f"## Pregunta\n\n> {PREGUNTA}\n\n"
        f"## Respuesta del modelo\n\n{respuesta}\n"
    )
    ARCHIVO_SALIDA.write_text(contenido, encoding="utf-8")


def main() -> None:
    if len(IMAGENES) > MAX_IMAGENES:
        raise ValueError(f"Máximo {MAX_IMAGENES} imágenes por solicitud")

    llm = crear_llm()
    print(f"Modelo    : {MODELO_VISION}")
    print(f"Imágenes  : {', '.join(r.name for r in IMAGENES)}")
    print(f"Pregunta  : {PREGUNTA}\n")

    respuesta = consultar_vision(llm, IMAGENES, PREGUNTA)
    print("Respuesta del modelo:\n")
    print(respuesta)
    guardar_markdown(respuesta)
    print(f"\nInforme guardado en: {ARCHIVO_SALIDA}")


if __name__ == "__main__":
    main()