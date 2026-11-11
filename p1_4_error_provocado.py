"""
Punto 1.4 - Error provocado: más imágenes de las permitidas.

Se envían 4 imágenes (el límite es 3 por solicitud) y se prueban DOS capas:
  1) Validación local de nuestro código (utils_vision.consultar_vision).
  2) Envío directo a la API saltándose esa validación, para capturar el
     mensaje REAL que devuelve Groq (es lo que pide el enunciado).
El resultado queda en resultados/p1_4_resultado.md.

Uso:  python p1_4_error_provocado.py
"""
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage

from utils_vision import (
    MAX_IMAGENES,
    MODELO_VISION,
    consultar_vision,
    crear_llm,
    imagen_a_bloque,
)

# ---------------------------------------------------------------- configuración
CARPETA_IMAGENES = Path("imagenes")
CARPETA_SALIDA = Path("resultados")
ARCHIVO_SALIDA = CARPETA_SALIDA / "p1_4_resultado.md"

# 4 imágenes: una más que el máximo permitido. Si alguna no existe, se
# reutiliza la primera disponible para poder completar la prueba.
NOMBRES = ["derivada_1.jpeg", "derivada_2.jpeg", "derivada_3.jpeg", "derivada_4.jpeg"]
PREGUNTA = "Analiza estas derivadas."


def preparar_imagenes() -> list[Path]:
    """Devuelve 4 rutas existentes (repite la primera si falta alguna)."""
    rutas = [CARPETA_IMAGENES / n for n in NOMBRES]
    existentes = [r for r in rutas if r.is_file()]
    if not existentes:
        raise FileNotFoundError(f"No hay imágenes de prueba en {CARPETA_IMAGENES}/")
    return [r if r.is_file() else existentes[0] for r in rutas]


def describir_error(e: Exception) -> dict:
    """Extrae del error lo útil para el informe: tipo, código HTTP y mensaje."""
    return {
        "tipo": f"{type(e).__module__}.{type(e).__name__}",
        "status": getattr(e, "status_code", None),
        "mensaje": str(e),
    }


def prueba_local(llm, imagenes: list[Path]) -> dict:
    """Capa 1: nuestra validación debe frenar la solicitud ANTES de la API."""
    try:
        consultar_vision(llm, imagenes, PREGUNTA)
        return {"error": None}
    except Exception as e:
        return {"error": describir_error(e)}


def prueba_api(llm, imagenes: list[Path]) -> dict:
    """Capa 2: se salta la validación local y se envía directo a la API."""
    contenido = [{"type": "text", "text": PREGUNTA}]
    contenido += [imagen_a_bloque(r) for r in imagenes]
    try:
        respuesta = llm.invoke([HumanMessage(content=contenido)])
        return {"error": None, "respuesta": str(respuesta.content)[:500]}
    except Exception as e:
        return {"error": describir_error(e)}


def bloque(resultado: dict) -> str:
    """Formatea el resultado de una prueba para consola y Markdown."""
    err = resultado["error"]
    if err is None:
        return "No hubo error."
    estado = f"HTTP {err['status']}" if err["status"] else "sin código HTTP"
    return f"Tipo: {err['tipo']}\nEstado: {estado}\nMensaje: {err['mensaje']}"


def guardar_markdown(imagenes: list[Path], local: dict, api: dict) -> None:
    CARPETA_SALIDA.mkdir(exist_ok=True)
    lista = "\n".join(f"{i}. `{r.name}`" for i, r in enumerate(imagenes, start=1))
    api_ok = (
        "**La API NO rechazó la solicitud** (respondió normalmente). "
        "Prueba con más imágenes o con otro tipo de error.\n"
        if api["error"] is None
        else f"```text\n{bloque(api)}\n```\n"
    )
    contenido = (
        "# 1.4 Error provocado\n\n"
        f"- **Fecha:** {datetime.now():%Y-%m-%d %H:%M}\n"
        f"- **Modelo:** `{MODELO_VISION}`\n"
        f"- **Imágenes enviadas:** {len(imagenes)} (límite: {MAX_IMAGENES})\n\n"
        "## Qué se hizo para provocarlo\n\n"
        f"Se envió una sola solicitud con {len(imagenes)} imágenes:\n\n{lista}\n\n"
        "## Capa 1: validación local (nuestro código)\n\n"
        f"```text\n{bloque(local)}\n```\n\n"
        "## Capa 2: respuesta real de la API (sin validación local)\n\n"
        f"{api_ok}\n"
        "## Causa del error\n\n"
        f"Groq permite como máximo {MAX_IMAGENES} imágenes por solicitud en los "
        "modelos de visión. Al superar ese límite, la API rechaza la petición. "
        "Nuestro código también lo valida antes de enviar para evitar gastar "
        "una llamada.\n"
    )
    ARCHIVO_SALIDA.write_text(contenido, encoding="utf-8")


def main() -> None:
    imagenes = preparar_imagenes()
    print(f"Modelo: {MODELO_VISION}")
    print(f"Enviando {len(imagenes)} imágenes (máximo permitido: {MAX_IMAGENES})\n")
    llm = crear_llm()
    print("=== Capa 1: validación local ===")
    local = prueba_local(llm, imagenes)
    print(bloque(local), "\n")
    print("=== Capa 2: respuesta real de la API ===")
    api = prueba_api(llm, imagenes)
    print(bloque(api), "\n")
    guardar_markdown(imagenes, local, api)
    print(f"Informe guardado en: {ARCHIVO_SALIDA}")


if __name__ == "__main__":
    main()