"""
Punto 1.1 - Pregunta sobre una imagen.
Uso:  python p1_1_pregunta_imagen.py
Ajusta IMAGEN y PREGUNTA a su dominio.
"""
from pathlib import Path

from utils_vision import MODELO_VISION, consultar_vision, crear_llm

IMAGEN = Path("imagenes/derivada_1.jpeg")
PREGUNTA = (
    "Analiza este ejercicio de derivadas de forma directa y concisa. "
    "Indica: 1) La función a derivar. "
    "2) Las reglas de derivación necesarias. "
    "3) Explica de forma breve y clara únicamente el primer paso de la solución."
)

def main() -> None:
    llm = crear_llm()
    print(f"Modelo   : {MODELO_VISION}")
    print(f"Imagen   : {IMAGEN}")
    print(f"Pregunta : {PREGUNTA}\n")

    respuesta = consultar_vision(llm, [IMAGEN], PREGUNTA)
    print("Respuesta del modelo:\n")
    print(respuesta)

    Path("resultados").mkdir(exist_ok=True)
    Path("resultados/p1_1_resultado.md").write_text(
        f"IMAGEN: {IMAGEN}\nPREGUNTA: {PREGUNTA}\n\nRESPUESTA:\n{respuesta}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
