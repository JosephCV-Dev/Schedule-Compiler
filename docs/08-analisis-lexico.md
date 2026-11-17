# Etapa 3: analizador léxico

Implementado con Lark basic y parser=None: solo reconoce terminales. El parser
se incorporó en la [etapa 4](09-analisis-sintactico.md), usando esos mismos tokens.
La semántica corresponde a la etapa 5 y el editor web a la 6.

## Probarlo

Desde la raíz del repositorio:

```sh
backend/.venv/bin/python -m schedule_compiler.cli.lex examples/horario_carolina.hor
```

Dentro de backend, con el entorno virtual activado:

```sh
python -m schedule_compiler.cli.lex ../examples/horario_carolina.hor
python -m schedule_compiler.cli.lex ../examples/horario_carolina.hor --json
```

La tabla muestra token, lexema, patrón, línea y columna. Los lexemas se muestran
escapados para hacer visibles comillas y barras inversas; internamente conservan
los caracteres originales. JSON incluye rangos y diagnósticos. También se admite
texto por stdin. En modo JSON la respuesta va por stdout; en modo tabla los
diagnósticos van por stderr. Los problemas de lectura siempre van por stderr.

Código de salida: 0 si el léxico se completó, 1 ante un error léxico y 2 para
argumentos incorrectos o problemas de lectura/codificación. El éxito léxico no
acredita estructura ni validez del horario. No se genera aún AST, símbolos ni
horario y no se agregó un endpoint HTTP.

## Uso desde Python

```python
from schedule_compiler.compiler.lexer import tokenize

result = tokenize('HORA 12:00 DURACION 2', source_name='editor')
print(result.success)
for token in result.tokens:
    print(token.kind, token.lexeme, token.span.start.line, token.span.start.column)
```

LexicalResult contiene fuente, patrones, tokens y diagnósticos. Es un resultado
de fase distinto del AnalysisResult final; no simula sintaxis ni semántica. Los
diagnósticos se comparten desde domain/diagnostics.py.

## Reglas y posiciones

La fuente de reglas es compiler/terminals.lark. Los patrones se obtienen de los
mismos terminales compilados por Lark; pattern_id enlaza cada token con su regla.

Se reconocen palabras reservadas KW_* —incluidos días y marcadores—, CADENA,
HORA_LITERAL, ENTERO y ambas llaves. MATERIAX, HORA1 y HORARIO_EXTRA no se separan
en palabras reservadas y sufijos. Las palabras reservadas requieren mayúscula sin
acentos; las cadenas admiten Unicode y emojis. Solo se permiten escapes de
comilla doble y barra inversa dentro de cadenas.

HORA_LITERAL tiene prioridad sobre ENTERO. 8:00 y 10:000 son errores de formato;
25:99 es un token de hora que deberá rechazar la semántica. Un entero sin dos
puntos sigue siendo ENTERO incluso después de HORA: el parser revisará el campo.
DURACION 0 y DURACION "dos" pasan léxico, aunque fallen en semántica y sintaxis.

Se ignoran espacios, tabuladores, LF/CRLF y comentarios desde # hasta el fin de
línea. El # dentro de una cadena es texto. El fin de secuencia señala el fin de
entrada; no se emite un EOF artificial ni se decodifican valores de literales.

Rangos con fin exclusivo, offsets desde cero y línea/columna desde uno. Unicode y
tabuladores cuentan como un carácter, no ancho visual ni unidades UTF-16. CRLF
cuenta como dos caracteres en offsets y un cambio de línea. El lexer no modifica
el texto recibido. El adaptador de archivos decodifica UTF-8, retira un BOM inicial
y conserva CRLF. Los rangos corresponden al texto decodificado. Un BOM pegado
directamente como texto no pertenece al lenguaje.

## Errores

| Código | Situación |
| --- | --- |
| CARACTER_NO_PERMITIDO | @, punto y coma u otro carácter no definido |
| LEXEMA_NO_RECONOCIDO | Palabra sin comillas o palabra reservada incorrecta |
| FORMATO_HORA_INVALIDO | Fragmento numérico con dos puntos que no cumple HH:MM |
| CADENA_SIN_CIERRE | Fin del texto con una cadena abierta |
| SALTO_LINEA_EN_CADENA | Otra línea sin cerrar la cadena |
| ESCAPE_INVALIDO | Barra inversa seguida de un carácter no admitido |

Se devuelve el primer error con el prefijo de tokens reconocidos. No se repara el
texto ni se continúa en un contexto posiblemente incorrecto. El diagnóstico tiene
fuente y rango; las fases dependientes deben quedar sin ejecutar.

Ejemplos intencionalmente inválidos, desde backend:

```sh
python -m schedule_compiler.cli.lex ../examples/lexico/error_caracter.hor
python -m schedule_compiler.cli.lex ../examples/lexico/error_cadena.hor
python -m schedule_compiler.cli.lex ../examples/lexico/error_hora.hor
```

Terminan con código 1 por diseño. El de cadena produce SALTO_LINEA_EN_CADENA.

## Verificación

| Ejemplo principal | Tokens | Errores léxicos |
| --- | --- | --- |
| horario_carolina.hor | 276 | 0 |
| horario_carolina_seleccion.hor | 20 | 0 |
| horario_personal.hor | 12 | 0 |
| oferta_compiladores.hor | 32 | 0 |

Las pruebas cubren límites, escapes, comentarios, marcadores, Unicode, posiciones,
invocaciones independientes y CLI. Se verificó también que el paquete wheel
incluye los terminales y que el lexer funciona desde ese paquete distribuido.
El contrato HTTP final y sus fixtures ilustrativos no cambian en esta fase.
