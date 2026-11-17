# Etapa 4: sintaxis y AST

El parser LALR reconoce el lenguaje .hor v0.2 y construye un AST propio. Los
terminales siguen siendo los del lexer basic de la etapa 3. No comprueba docentes,
cruces, referencias ni otras reglas del horario; eso corresponde a la etapa 5.

## Probarlo

Desde la raíz del repositorio:

```sh
backend/.venv/bin/python -m schedule_compiler.cli.parse examples/horario_carolina.hor
backend/.venv/bin/python -m schedule_compiler.cli.parse examples/horario_carolina.hor --json
```

Desde backend, con el entorno activado:

```sh
python -m schedule_compiler.cli.parse ../examples/oferta_compiladores.hor
```

Por defecto imprime un árbol con ramas, nodos y valores. --json entrega los tokens
léxicos, el AST visual con IDs/etiquetas/hijos/rangos y los diagnósticos. El AST
visual usa el adaptador ya previsto para la futura interfaz web. La distribución
gráfica del editor, colores, zoom y pestañas se implementará en la etapa 6.

Como en el CLI léxico, se puede omitir el archivo y proporcionar texto por stdin.
Ambos comandos comparten lectura UTF-8 con BOM inicial opcional, conservación de
CRLF y presentación de diagnósticos. Código 0: sintaxis completada; 1: error del
programa léxico o sintáctico; 2: argumentos o lectura incorrectos.

En JSON los errores de programa están en stdout, dentro del resultado de su fase;
en modo árbol se muestran en stderr junto a fuente, línea y columna.

## Flujo y separación de fases

1. Tokenizar toda la entrada con el lexer existente.
2. Si hay un error léxico, conservar sus tokens/diagnósticos y no ejecutar sintaxis.
3. Alimentar el parser interactivo LALR con esos mismos tokens y sus posiciones.
4. Comprobar el fin de entrada explícitamente, sin crear un token visible de EOF.
5. Transformar la estructura reconocida a Program, OfferDeclaration,
   SessionDeclaration, ScheduleDeclaration y EnrollmentDeclaration.

La gramática está en compiler/grammar.lark y reutiliza terminals.lark. No hay una
segunda tokenización dependiente del contexto. El parser no carga el catálogo ni
la política; un INSCRIBIR a una oferta inexistente sigue siendo sintaxis válida.

ParseResult conserva LexicalResult, AST opcional y diagnósticos sintácticos. Su
propiedad executed indica que el léxico permitió ejecutar sintaxis; success exige
un AST sin errores. En la salida CLI, la fase sintáctica puede ser COMPLETADA,
CON_ERRORES o NO_EJECUTADA. Ninguno equivale a declarar válido un horario.

## Estructura reconocida

- Un programa contiene una o más OFERTA/HORARIO, en cualquier orden.
- Una OFERTA requiere identificador, materia, grupo, docente y al menos una SESION.
- Una SESION requiere aula, día, hora y duración, en el orden especificado.
- Un HORARIO tiene nombre y al menos una inscripción.
- GRUPO admite cadena o DESCONOCIDO.
- DOCENTE y AULA admiten cadena, DESCONOCIDO o SIN_ASIGNAR.
- Los valores de materia, identificador, nombre e inscripción son cadenas.
- La hora requiere HORA_LITERAL y la duración ENTERO, sin puntos y coma.

Las cadenas se decodifican en una pasada: solo comillas y barras inversas
escapadas. Se conserva Unicode y el resto de caracteres admitidos, incluidos
tabuladores. Las cadenas del AST ya no incluyen las comillas delimitadoras; los
tokens léxicos conservan el lexema original. El marcador DESCONOCIDO tiene valor
null y estado propio; la cadena "DESCONOCIDO" sigue siendo texto conocido.

Cada nodo conserva su rango. El Program abarca todo el texto recibido, incluidos
comentarios iniciales/finales. Las declaraciones incluyen palabras reservadas y
llaves; los literales señalan sus tokens. Los offsets son caracteres Unicode desde
cero, las líneas/columnas comienzan en uno y los extremos finales son exclusivos.

## Diagnósticos

| Código | Significado |
| --- | --- |
| PROGRAMA_VACIO | No hay declaraciones, aunque existan espacios o comentarios |
| TOKEN_INESPERADO | Hay un token reconocido que no encaja; informa qué se esperaba |
| FIN_INESPERADO | Se acabó la entrada cuando aún faltaban elementos |
| ENTERO_NO_REPRESENTABLE | El literal entero supera el límite de conversión del intérprete |

El token inesperado conserva su rango exacto. Ante fin de entrada, la ubicación
es un rango vacío al final real del texto, incluidos los comentarios finales.
Se reporta el primer error de sintaxis, sin reparar ni producir AST parcial.

La conversión de enteros respeta el límite del intérprete Python: no modifica
configuración global para eludirlo. Un literal que exceda ese límite produce un
diagnóstico localizado, sin interrumpir el proceso con una excepción sin manejar.
Esto es un límite de representación, no una comprobación de la duración permitida.

Ejemplos desde backend:

```sh
python -m schedule_compiler.cli.parse ../examples/sintactico/error_tipo.hor
python -m schedule_compiler.cli.parse ../examples/sintactico/error_llave.hor
python -m schedule_compiler.cli.parse ../examples/sintactico/valores_para_semantica.hor
```

Los primeros dos terminan con código 1 por diseño. El tercero completa sintaxis:
HORA 25:00 y DURACION 0 se representan en el AST para que la etapa 5 los rechace.
También quedan para semántica las referencias desconocidas, duplicados, aulas
pendientes u ocupadas y horas no permitidas.

## Verificación

Los cuatro ejemplos principales generan AST. El archivo completo de Carolina
contiene ocho ofertas, 16 sesiones y un horario con ocho inscripciones; conserva
los dos tramos consecutivos de Metodología y las 29 horas de la página transcrita.

Las pruebas cubren las posiciones y jerarquía reales, orden y obligatoriedad de
campos, días, marcadores, escapes, bloqueos entre fases, EOF, errores de tipos,
conversión de enteros y la salida CLI en árbol/JSON. Se verificó el parser desde
un wheel que incluye ambos recursos .lark. El contrato HTTP final sigue sin cambios
y el caso de uso completo está integrado desde [etapa 5](10-semantica-y-api.md).
