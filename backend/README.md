# Backend

Python 3.12 o superior. FastAPI adapta HTTP; Lark basic reconoce tokens y LALR
reconoce la estructura. Hay modelos, cargadores, contrato, lexer y parser con AST.
La semántica y el caso de uso completo están disponibles con catálogo y política.
Motor y API: `docs/10-semantica-y-api.md`.
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

`compiler_available: true` indica que el motor está implementado. La API expone
POST /api/v1/analyses y consultas GET de catálogos, auditorías, política y ejemplos.
El motor se puede usar sin HTTP; la interfaz completa sigue pendiente.

## Análisis completo

Con el entorno activado:

```sh
python -m schedule_compiler.cli.analyze ../examples/horario_carolina.hor
python -m schedule_compiler.cli.analyze ../examples/horario_carolina.hor --json
python -m schedule_compiler.cli.analyze ../examples/oferta_compiladores.hor --scope PROPUESTA
```

Resultado VALIDO/INVALIDO/INCOMPLETO con tokens, AST, símbolos, reglas y sesiones.
Código 0 para válido, 1 para inválido o incompleto y 2 para lectura/configuración.
Profesores libres sin reglas; capacidad/laboratorio/límites no configurados y
no requeridos en esta política. Aulas pendientes y equivalencias físicas que
impidan una comprobación requerida producen INCOMPLETO.

PERSONAL valida selecciones HORARIO; PROPUESTA valida las OFERTA declaradas.
Las referencias y los cruces de cualquier HORARIO presente se comprueban en ambos.
En HTTP los errores del programa son resultados 200; un JSON mal formado es 422,
un recurso desconocido 404 y la configuración no disponible 503.
Los directorios se pueden configurar con SCHEDULE_COMPILER_DATA_DIR y
SCHEDULE_COMPILER_EXAMPLES_DIR; por defecto no dependen del cwd.

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
de identidad de aulas. Application coordina las tres fases; domain contiene reglas
sin dependencias web y api adapta sus resultados. Terminales y gramática .lark
se incluyen en el paquete.
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
la separación de valores que deben comprobarse en semántica. También hay pruebas
de cruces, pendientes, referencias, símbolos, inmutabilidad y HTTP/CLI completos.
httpx2 es una dependencia de desarrollo usada por TestClient.

El generador `scripts/exportar_contratos.py`, ejecutado desde la raíz con este
entorno, exporta el JSON Schema y casos obtenidos del motor real. Su modo `--check`
comprueba que los archivos siguen sincronizados con los modelos.
