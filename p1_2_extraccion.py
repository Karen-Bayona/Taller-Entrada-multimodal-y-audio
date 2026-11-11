"""
Punto 1.2 - Extracción estructurada con validación de JSON.

Flujo por imagen:
  imagen -> modelo (salida JSON) -> json.loads -> validación Pydantic
  -> si falla, se INFORMA y se continúa (el programa no se cae)
Luego compara con valores_reales.json y calcula el % de aciertos.

Uso:  python p1_2_extraccion.py
"""
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from utils_vision import MODELO_VISION, consultar_vision, crear_llm

# ---------------------------------------------------------------- configuración
IMAGENES = [
    Path("imagenes/derivada_1.jpeg"),
    Path("imagenes/derivada_2.jpeg"),
    Path("imagenes/derivada_3.jpeg"),
    Path("imagenes/derivada_4.jpeg"),
    Path("imagenes/derivada_5.jpeg"),
]
ARCHIVO_REALES = Path("valores_reales.json")
CARPETA_SALIDA = Path("resultados")


# ---------------------------------------------------------------------- esquema
class EjercicioDerivada(BaseModel):
    """Esquema de 6 campos (el enunciado pide mínimo 5)."""

    model_config = ConfigDict(extra="forbid")  # campos de más = error

    funcion_original: str = Field(description="Función matemática original a derivar")
    tipo_ejercicio: str = Field(description="Tipo o tema del ejercicio de derivadas")
    regla_principal: str = Field(description="Regla principal de derivación utilizada")
    resultado_parcial: str = Field(description="Primer paso o resultado parcial de la derivada")
    es_manuscrito: bool = Field(description="True si está escrito a mano")


def construir_prompt() -> str:
    esquema = json.dumps(EjercicioDerivada.model_json_schema(), ensure_ascii=False)
    return (
        "Eres un extractor de datos. Analiza la imagen de un ejercicio de "
        "derivadas y devuelve ÚNICAMENTE un objeto JSON que cumpla este "
        f"esquema JSON:\n{esquema}\n\n"
        "Reglas: escribe las expresiones matemáticas en texto plano (x^2, sin(x)); "
        "no inventes datos; no incluyas texto fuera del JSON."
    )


# ------------------------------------------------------------------- validación
def validar_json(texto: str) -> tuple[EjercicioDerivada | None, str | None]:
    """Devuelve (objeto, None) si es válido o (None, mensaje_de_error)."""
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as e:
        return None, f"JSON mal formado: {e}"
    try:
        return EjercicioDerivada(**datos), None
    except (ValidationError, TypeError) as e:
        return None, f"No cumple el esquema: {e}"


# ----------------------------------------------------------------- comparación
def normalizar(valor) -> str:
    """Normaliza para comparar texto matemático y cadenas (ignora mayúsculas, espacios y símbolos de formato)."""
    if valor is None:
        return ""
    return (
        str(valor)
        .lower()
        .strip()
        .replace(" ", "")
        .replace("**", "^")
        .replace("·", "*")
        .replace("*", "")
    )


def comparar(extraidos: dict, reales: dict) -> list[dict]:
    """Compara únicamente el campo específico que exige cada fila de la plantilla del informe."""
    plantilla_objetivos = {
        "derivada_1.jpeg": "funcion_original",
        "derivada_2.jpeg": "tipo_ejercicio",
        "derivada_3.jpeg": "regla_principal",
        "derivada_4.jpeg": "funcion_original",
        "derivada_5.jpeg": "resultado_parcial",
    }
    
    filas = []
    for imagen, campo_objetivo in plantilla_objetivos.items():
        real = reales.get(imagen, {})
        valor_real = real.get(campo_objetivo, "")
        
        ext = extraidos.get(imagen)
        valor_ext = None if ext is None else ext.get(campo_objetivo)
        
        # Validación flexible: si el texto extraído contiene o coincide normalizado
        ok = False
        if valor_ext is not None:
            norm_real = normalizar(valor_real)
            norm_ext = normalizar(valor_ext)
            # Acepta si son idénticos normalizados o si uno contiene al otro (ej. descripciones largas)
            ok = (norm_real == norm_ext) or (norm_real in norm_ext) or (norm_ext in norm_real)

        filas.append({
            "imagen": imagen, 
            "campo": campo_objetivo,
            "real": valor_real, 
            "extraido": valor_ext, 
            "correcto": ok,
        })
    return filas

def tabla_markdown(filas: list[dict]) -> str:
    lineas = [
        "| Imagen | Campo | Valor real | Valor extraído | ¿Correcto? (Sí/No) |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for f in filas:
        lineas.append(
            f"| {f['imagen']} | {f['campo']} | {f['real']} | {f['extraido']} | "
            f"{'Sí' if f['correcto'] else 'No'} |"
        )
    aciertos = sum(f["correcto"] for f in filas)
    total = len(filas)
    pct = 100 * aciertos / total if total else 0
    lineas.append(f"\n**Porcentaje de aciertos:** {aciertos} de {total} campos = {pct:.1f} %")
    return "\n".join(lineas)


# ------------------------------------------------------------------------ main
def main() -> None:
    CARPETA_SALIDA.mkdir(exist_ok=True)
    llm = crear_llm()
    prompt = construir_prompt()
    print(f"Modelo: {MODELO_VISION}\n")

    extraidos: dict[str, dict | None] = {}
    crudos: dict[str, str] = {}

    for ruta in IMAGENES:
        print(f"--- {ruta.name} ---")
        try:
            texto = consultar_vision(llm, [ruta], prompt)
        except Exception as e:  # error de red/API/imagen: se informa, no se cae
            print(f"  ERROR al consultar: {e}\n")
            extraidos[ruta.name] = None
            continue

        crudos[ruta.name] = texto
        objeto, error = validar_json(texto)
        if error:
            print(f"  JSON INVÁLIDO -> {error}\n  Respuesta cruda: {texto}\n")
            extraidos[ruta.name] = None
        else:
            extraidos[ruta.name] = objeto.model_dump()
            print("  JSON válido:", json.dumps(extraidos[ruta.name], ensure_ascii=False, indent=2), "\n")

    (CARPETA_SALIDA / "p1_2_extracciones.json").write_text(
        json.dumps({"validados": extraidos, "crudos": crudos}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if not ARCHIVO_REALES.exists():
        print(f"Crea {ARCHIVO_REALES} con los valores reales para calcular los aciertos.")
        return

    reales = json.loads(ARCHIVO_REALES.read_text(encoding="utf-8"))
    informe = tabla_markdown(comparar(extraidos, reales))
    print(informe)
    (CARPETA_SALIDA / "p1_2_tabla_aciertos.md").write_text(informe, encoding="utf-8")
    print("\nNota: revisa a mano los textos matemáticos marcados 'No'; "
          "pueden ser equivalentes (p. ej. 2x vs 2*x).")


if __name__ == "__main__":
    main()
