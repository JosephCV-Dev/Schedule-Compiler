# Schedule Compiler

Proyecto académico: lenguaje para describir y seleccionar clases universitarias,
con análisis léxico, sintáctico y semántico e interfaz web.

## Estado

Etapa 4: lexer y parser disponibles por Python y terminal. Reconocen .hor v0.2 y
entregan tokens, AST propio y diagnósticos con posiciones. Se conservan los modelos,
catálogos y contrato previos. La semántica y la interfaz completa siguen pendientes.
La API ofrece solo salud; ambas fases se prueban mediante CLI.

Stack confirmado: frontend React con TypeScript y Vite, API en Python con FastAPI
y modelos del núcleo independientes del framework; lexer basic y parser LALR de Lark.

## Probar la sintaxis y ver el árbol

Desde la raíz, con las dependencias del backend instaladas:

```sh
backend/.venv/bin/python -m schedule_compiler.cli.parse examples/horario_carolina.hor
backend/.venv/bin/python -m schedule_compiler.cli.parse examples/horario_carolina.hor --json
```

La primera salida dibuja el AST con ramas y nodos. JSON incluye hijos, etiquetas,
rangos y diagnósticos. Los cuatro ejemplos principales completan sintaxis.
Esto todavía no valida cruces, referencias ni otras reglas de horarios.

Para probar un error sintáctico intencional:

```sh
backend/.venv/bin/python -m schedule_compiler.cli.parse examples/sintactico/error_tipo.hor
```

Los errores léxicos bloquean el parser; un fallo de sintaxis conserva los tokens
pero no produce AST. Código 0 indica éxito de sintaxis, 1 error de programa y 2
problema de lectura/argumentos.

## Probar el analizador léxico

Desde la raíz, con las dependencias del backend instaladas:

```sh
backend/.venv/bin/python -m schedule_compiler.cli.lex examples/horario_carolina.hor
backend/.venv/bin/python -m schedule_compiler.cli.lex examples/horario_carolina.hor --json
```

La tabla muestra token, lexema, patrón, línea y columna. Los cuatro ejemplos
principales pasan léxico. Probar solo esta fase no acredita sintaxis ni validez.
Para provocar un error intencional:

```sh
backend/.venv/bin/python -m schedule_compiler.cli.lex examples/lexico/error_caracter.hor
```

Ese ejemplo devuelve código 1, con los tokens previos y la ubicación del primer
error. El código 0 indica éxito léxico y el 2 un problema de lectura o argumentos.

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
- [Contrato de análisis y modelos de la etapa 2](docs/07-contrato-analisis.md).
- [Analizador léxico y comandos de prueba](docs/08-analisis-lexico.md).
- [Analizador sintáctico y árbol AST](docs/09-analisis-sintactico.md).

## Verificar modelos y contrato

```sh
cd backend
.venv/bin/python -m pytest
```

Desde la raíz, comprobar que los esquemas y ejemplos exportados están al día:

```sh
backend/.venv/bin/python scripts/exportar_contratos.py --check
```

Los fixtures en `contracts/examples/` son ilustraciones del contrato, no salidas
de un compilador implementado. La entrada futura admite escribir/pegar texto y
cargar un `.hor` en el mismo editor. El AST exportado tiene nodos e hijos para
dibujar el árbol, sin imponer su distribución gráfica.

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

Lexer y parser ya procesan los ejemplos. Las reglas de horarios se incorporarán
en la etapa 5; la interfaz completa se construirá en la 6.
