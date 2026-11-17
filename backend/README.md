# Backend

Python 3.12 o superior. FastAPI adapta HTTP; Lark basic reconoce tokens y LALR
reconoce la estructura. Hay modelos, cargadores, contrato, lexer y parser con AST.
La semántica está pendiente.
Contrato: `docs/07-contrato-analisis.md`; léxico: `docs/08-analisis-lexico.md`, en la
raíz del repositorio. Sintaxis y AST: `docs/09-analisis-sintactico.md`.

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
motor completo aún no está construido. Lexer y parser se prueban por terminal; no se
expone una compilación de muestra.

## Probar el léxico

Desde esta carpeta, con el entorno activado:

```sh
python -m schedule_compiler.cli.lex ../examples/horario_carolina.hor
python -m schedule_compiler.cli.lex ../examples/horario_carolina.hor --json
python -m schedule_compiler.cli.lex ../examples/lexico/error_caracter.hor
```

El último ejemplo es inválido intencionalmente y termina con código 1. Se muestran
los tokens anteriores al primer error con su ubicación. Código 0 significa éxito
léxico; código 2, error de lectura/argumentos. Sin archivo, se puede recibir texto
por stdin. La salida por defecto es una tabla; --json muestra el resultado de fase.

## Probar sintaxis y AST

Desde esta carpeta, con el entorno activado:

```sh
python -m schedule_compiler.cli.parse ../examples/horario_carolina.hor
python -m schedule_compiler.cli.parse ../examples/horario_carolina.hor --json
python -m schedule_compiler.cli.parse ../examples/sintactico/error_tipo.hor
```

La salida por defecto es un árbol con nodos y ramas; JSON contiene la misma
jerarquía con IDs y rangos para la futura interfaz. Si falla el léxico no se ejecuta
el parser. Si falla la sintaxis se devuelven tokens y diagnóstico, sin AST parcial.
El tercer ejemplo termina con código 1 por diseño. El éxito sintáctico no acredita
validez de las reglas del horario.

## Módulos

- `api`: rutas y modelos HTTP.
- `application`: coordinación de casos de uso.
- `compiler`: léxico, gramática y AST.
- `domain`: entidades y reglas semánticas.
- `infrastructure`: lectura de catálogos y políticas.

Los módulos ya contienen modelos, contrato, carga de catálogos y normalización
de identidad de aulas. Lexer y parser ya están implementados; la semántica se
añadirá según el roadmap. Terminales y gramática .lark se incluyen en el paquete.
No hay base de datos ni autenticación en esta etapa.

## Pruebas

```sh
.venv/bin/python -m pytest
```

Se comprueban invariantes de modelos y resultados, lectura sin modificar fuentes,
procedencia de las dos sesiones sin aula, reemplazo temporal de ofertas, claves
de aula, política de profesores libres y conversión del AST a nodos visuales.
Se comprueban además el léxico de los ejemplos, límites de tokens, cadenas,
errores, posiciones Unicode/LF/CRLF, reuso del lexer y salidas CLI. Las pruebas del
parser cubren AST reales, errores de estructura, bloqueo por errores léxicos y
la separación de valores que deben comprobarse en semántica.

El generador `scripts/exportar_contratos.py`, ejecutado desde la raíz con este
entorno, exporta el JSON Schema y fixtures de resultados. Su modo `--check`
comprueba que los archivos siguen sincronizados con los modelos.
