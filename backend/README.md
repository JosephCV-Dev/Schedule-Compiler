# Backend

Python 3.12 o superior. FastAPI adapta HTTP; Lark se utilizará para el lenguaje.
Hay modelos del núcleo, cargadores y contrato; las fases de análisis todavía no
están implementadas. El contrato se documenta en `docs/07-contrato-analisis.md`.

## Instalación

Desde la carpeta `backend`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
```

`requirements.lock` fija dependencias directas y transitivas, incluyendo herramientas
de desarrollo. `pyproject.toml` declara el paquete y las dependencias directas.
Si cambian dependencias, regenerar el lock desde un entorno limpio instalado con
`pip install -e '.[dev]'` y
`pip list --format=freeze --exclude-editable --exclude pip`.

## Arranque

```sh
.venv/bin/python -m uvicorn schedule_compiler.main:app --reload --host 127.0.0.1 --port 8000
```

- Salud: `http://127.0.0.1:8000/api/v1/health`.
- Documentación: `http://127.0.0.1:8000/docs`.
- OpenAPI: `http://127.0.0.1:8000/openapi.json`.

Por ahora solo existe la ruta de salud. `compiler_available: false` indica que el
motor aún no está construido. No se expone una compilación de muestra.

## Módulos

- `api`: rutas y modelos HTTP.
- `application`: coordinación de casos de uso.
- `compiler`: léxico, gramática y AST.
- `domain`: entidades y reglas semánticas.
- `infrastructure`: lectura de catálogos y políticas.

Los módulos ya contienen modelos, contrato, carga de catálogos y normalización
de identidad de aulas. Las fases del compilador se añadirán según el roadmap.
No hay base de datos ni autenticación en esta etapa.

## Pruebas

```sh
.venv/bin/python -m pytest
```

Se comprueban invariantes de modelos y resultados, lectura sin modificar fuentes,
procedencia de las dos sesiones sin aula, reemplazo temporal de ofertas, claves
de aula, política de profesores libres y conversión del AST a nodos visuales.

El generador `scripts/exportar_contratos.py`, ejecutado desde la raíz con este
entorno, exporta el JSON Schema y fixtures de resultados. Su modo `--check`
comprueba que los archivos siguen sincronizados con los modelos.
