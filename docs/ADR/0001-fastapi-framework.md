# ADR-0001: Uso de FastAPI como Framework de API

## Estado
Aceptado

## Contexto
Necesitábamos un framework moderno, rápido y con validación automática de datos para la interfaz de servicios.

## Decisión
Seleccionamos **FastAPI** debido a su rendimiento superior (basado en Starlette y Pydantic) y su excelente soporte para programación asíncrona.

## Consecuencias
- Mejora en la velocidad de desarrollo gracias a la generación automática de OpenAPI (Swagger).
- Validación robusta de datos de entrada.
- Curva de aprendizaje baja para desarrolladores de Python.
