# Schedule Compiler

Proyecto académico: lenguaje para describir y seleccionar clases universitarias,
con análisis léxico, sintáctico y semántico e interfaz web.

## Estado

Etapa 1: estructura y arranque preparados. Hay una API de salud y una página
inicial que comprueba la conexión. El motor, el endpoint de análisis y la interfaz
completa del compilador se construirán por etapas; los archivos `.hor` todavía
no se ejecutan.

Stack confirmado: frontend React con TypeScript y Vite, API en Python con FastAPI
y núcleo de compilación independiente del framework que utilizará Lark.

## Empezar en desarrollo local

Requisitos: Python >=3.12, Node >=22.12 y npm. Dependencias fijadas en
`backend/requirements.lock` y `frontend/package-lock.json`.

Terminal 1, desde la raíz:

```sh
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m uvicorn schedule_compiler.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, desde la raíz:

```sh
cd frontend
npm ci
npm run dev
```

Abrir `http://127.0.0.1:5173`. La página indica si el backend está conectado.
Documentación de la API: `http://127.0.0.1:8000/docs`. Solo está disponible la ruta
de salud; no se ofrecen resultados de compilación simulados.

Organización inicial:

```text
backend/src/schedule_compiler/
  api/              # HTTP
  application/      # Casos de uso
  compiler/         # Tokens, gramática y AST
  domain/           # Entidades y semántica
  infrastructure/   # Datos y política
backend/tests/
frontend/src/
  app/              # Composición inicial
  api/              # Cliente HTTP
  features/editor/
  features/analysis/
  features/schedule/
  components/
```

La lógica de los módulos reservados se añadirá según el roadmap. Instrucciones
adicionales en [backend](backend/README.md) y [frontend](frontend/README.md).

## Documentación

- [Análisis del Excel y del horario personal](docs/01-analisis-fuentes.md).
- [Lenguaje y reglas propuestas](docs/02-lenguaje.md).
- [Arquitectura web y orden de implementación](docs/03-arquitectura.md).
- [Roadmap y criterios por etapa](docs/05-roadmap.md).
- [Referencia visual de la interfaz](docs/06-referencia-frontend.md).

## Datos y ejemplos

- `data/isc_26_1.normalizado.json`: extracción reproducible de 66 ofertas y 131
  sesiones, con las celdas de origen y una auditoría.
- `data/horario_personal.transcrito.json`: transcripción manual del horario de la
  imagen, sin identidad ni matrícula del estudiante. Las equivalencias de nombres
  y aulas se mantienen como candidatas.
- `examples/horario_personal.hor`: selección de cuatro ofertas del catálogo.
- `examples/oferta_compiladores.hor`: definición de una oferta y sus dos sesiones.

## Reproducir el análisis del Excel

La herramienta de preparación de datos usa únicamente la biblioteca estándar de
Python. Desde la raíz del proyecto:

```sh
python scripts/analizar_excel.py "/ruta/ISC HORARIOS 26-1.xlsx" --salida data/isc_26_1.normalizado.json
```

El archivo original no se modifica ni se copia al repositorio. El JSON conserva su
SHA-256 para identificar exactamente qué versión se analizó. No se rellenan
docentes, capacidades ni otros valores que la fuente no proporciona.

## Ejemplo para convertir imágenes (v0.2)

- [Prompt reutilizable](docs/04-convertir-horarios.md).
- [Horario de Carolina completo](examples/horario_carolina.hor): 8 materias,
  16 tramos y 29 horas visibles en la hoja 1 de 2.
- [Selección de Carolina](examples/horario_carolina_seleccion.hor): solo referencias.
- `data/isc_26_1.trabajo.json`: copia de trabajo con las dos sesiones del choque
  conocido sin aula asignada; fuente original conservada.
- `data/politica_proyecto.json`: profesores libres y ocupación de aulas activa.

Son especificaciones y ejemplos; todavía no hay un motor que los ejecute.
