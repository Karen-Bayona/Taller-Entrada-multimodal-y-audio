# Taller: Entrada multimodal y audio

**Asignatura:** Desarrollo de Aplicaciones con IA
**Integrantes:** Karen Bayona Romero, Laura Sofía Franco Mateus
**Dominio:** ejercicios de derivadas / cálculo (proyecto Tutor de Cálculo)

Visión sobre imágenes de ejercicios y transcripción de audio con preguntas de cálculo, usando la API de Groq.

| Tarea | Modelo |
| :--- | :--- |
| Visión (imágenes) | `qwen/qwen3.8-27b` |
| Transcripción de audio | `whisper-large-v3-turbo` |
| Respuesta a partir de la transcripción | `qwen/qwen3.8-27b` |

## Estructura

```
taller_multimodal/
├── imagenes/                  # derivada_1.jpeg ... derivada_5.jpeg
├── audios/                    # audio_1.wav ... audio_5.wav
├── resultados/                # salidas generadas (.md y .json)
├── utils/                     # load_model.py (cargador del repo de la clase)
├── utils_vision.py            # utilidades compartidas de visión (base64, validaciones)
├── valores_reales.json        # valores reales de cada imagen (para el % de aciertos)
├── audios_info.json           # hablante, condición y texto dicho de cada audio
├── p1_1_pregunta_imagen.py
├── p1_2_extraccion.py
├── p1_3_preguntas_varias_imagenes.py
├── p1_4_error_provocado.py
├── p2_1_transcripcion.py
├── p2_2_respuesta_transcripcion.py
├── requirements.txt
└── .env                       # NO se sube al repositorio
```

## Requisitos

- Python 3.10 o superior
- Una clave de API de Groq
- La carpeta `utils/` del repositorio de la clase (`tools_rags`), que contiene `load_model.py` con la función `cargar_llm`

## Instalación

```bash
pip install -r requirements.txt
```

## Variables de entorno

Crea un archivo `.env` en la raíz de la carpeta (el `.gitignore` ya lo excluye del repositorio):

```
GROQ_API_KEY=tu_clave_aqui
```

Opcional: `GROQ_VISION_MODEL` para cambiar el modelo de visión sin tocar el código (por defecto `qwen/qwen3.8-27b`).

> Nunca subas la clave al código ni al historial de commits.

## Cómo ejecutar

Todos los comandos se ejecutan desde esta carpeta. Cada script guarda su salida en `resultados/`.

### Parte 1. Visión

| Punto | Comando | Salida |
| :--- | :--- | :--- |
| 1.1 Pregunta sobre una imagen | `python p1_1_pregunta_imagen.py` | `resultados/p1_1_resultado.md` |
| 1.2 Extracción estructurada | `python p1_2_extraccion.py` | `resultados/p1_2_extracciones.json`, `resultados/p1_2_tabla_aciertos.md` |
| 1.3 Varias imágenes en una solicitud | `python p1_3_preguntas_varias_imagenes.py` | `resultados/p1_3_resultado.md` |
| 1.4 Error provocado (4 imágenes) | `python p1_4_error_provocado.py` | `resultados/p1_4_resultado.md` |

Notas:
- En 1.2 los valores reales leídos de cada imagen están en `valores_reales.json`. El JSON devuelto por el modelo se valida con un esquema Pydantic de 6 campos; si no cumple, el programa informa el error y continúa.
- 1.4 prueba dos capas: la validación local (máximo 3 imágenes) y el envío directo a la API para capturar el mensaje real de error.

### Parte 2. Audio

Ejecutar en este orden, porque 2.2 usa la salida de 2.1:

| Punto | Comando | Salida |
| :--- | :--- | :--- |
| 2.1 Transcripción desde archivo | `python p2_1_transcripcion.py` | `resultados/p2_1_transcripciones.json`, `resultados/p2_1_resultado.md` |
| 2.2 Respuesta a partir de la transcripción | `python p2_2_respuesta_transcripcion.py` | `resultados/p2_2_resultado.md` |

Notas:
- `audios_info.json` indica, para cada audio, el hablante, la condición (con/sin ruido) y el texto realmente dicho. Con ese texto se calcula el WER (porcentaje de palabras erradas) de cada transcripción.
- Formatos de audio admitidos: `wav`, `mp3`, `m4a`, `ogg`, `webm` (hasta 25 MB).

## Límites tenidos en cuenta

- Visión: máximo 3 imágenes por solicitud. El código valida un tope de 4 MB por imagen en base64.
- Audio: archivos de hasta 25 MB, con cobro mínimo de 10 segundos por solicitud.
