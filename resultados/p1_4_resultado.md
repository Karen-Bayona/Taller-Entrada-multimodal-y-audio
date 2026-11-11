# 1.4 Error provocado

- **Fecha:** 2026-11-09 00:35
- **Modelo:** `qwen/qwen3.8-27b`
- **Imágenes enviadas:** 4 (límite: 3)

## Qué se hizo para provocarlo

Se envió una sola solicitud con 4 imágenes:

1. `derivada_1.jpeg`
2. `derivada_2.jpeg`
3. `derivada_3.jpeg`
4. `derivada_4.jpeg`

## Capa 1: validación local (nuestro código)

```text
Tipo: builtins.ValueError
Estado: sin código HTTP
Mensaje: Se permiten entre 1 y 3 imágenes
```

## Capa 2: respuesta real de la API (sin validación local)

```text
Tipo: groq.BadRequestError
Estado: HTTP 400
Mensaje: Error code: 400 - {'error': {'message': 'Too many images provided.  This model supports up to 3 images', 'type': 'invalid_request_error'}}
```

## Causa del error

Groq permite como máximo 3 imágenes por solicitud en los modelos de visión. Al superar ese límite, la API rechaza la petición. Nuestro código también lo valida antes de enviar para evitar gastar una llamada.
