# Etapa 2: modelos y contrato de análisis v1

Estado: implementados los modelos, carga de fuentes y adaptadores de datos.
El reconocimiento léxico se incorporó posteriormente en la
[etapa 3](08-analisis-lexico.md); parser y validación de horarios están pendientes.
El endpoint POST se implementará en la etapa 5; la API actual solo ofrece salud.

## Entrada única para editor y archivo

El lenguaje es texto; `.hor` es su extensión de archivo. El usuario podrá escribir
o pegarlo en el recuadro, o pulsar «Subir .hor» para cargarlo en el mismo editor.
El frontend leerá el archivo en UTF-8, permitirá editarlo y enviará el contenido.
No se necesita un archivo para compilar texto escrito directamente.

Propuesta para `POST /api/v1/analyses`:

```json
{
  "source": "HORARIO \"Ejemplo\" { INSCRIBIR \"ISC_7B_COMPILADORES\" }",
  "source_name": "editor",
  "language_version": "0.2",
  "catalog_id": "isc-26-1-trabajo",
  "policy_id": "proyecto-v0.2",
  "scope": "PERSONAL"
}
```

Para un archivo solo cambia `source_name`, por ejemplo `carolina.hor`; `source`
sigue siendo texto. El nombre es una etiqueta de procedencia, no una ruta que el
servidor deba abrir. Una entrada vacía es una solicitud de transporte válida:
su diagnóstico de programa vacío corresponde al analizador, no a HTTP.

El catálogo y la política usan IDs de una lista explícita, no rutas del cliente.
Catálogos disponibles: `isc-26-1-trabajo` e `isc-26-1-original`. Política:
`proyecto-v0.2`. En el despliegue futuro se inyectará la carpeta de datos al
repositorio; su lectura no depende del directorio de trabajo del servidor.

Alcances del endpoint de análisis:

- PERSONAL: revisar las selecciones HORARIO del texto y sus ofertas referenciadas.
- PROPUESTA: revisar las OFERTA declaradas contra el resto de ocupaciones conocidas.

Si el alcance no tiene las declaraciones necesarias, el motor futuro devolverá
un diagnóstico explícito. Con varios HORARIO, se entregará una vista por selección
y el estado general reflejará los incumplimientos de las selecciones analizadas.
La auditoría global del catálogo tendrá un flujo separado; no se trata como una
ejecución del compilador sin léxico ni parser.

## Separación de modelos

| Módulo | Contenido |
| --- | --- |
| `domain/models.py` | Valores conocidos/desconocidos, procedencia, intervalos, sesiones, ofertas, catálogos y política |
| `compiler/models.py` | Patrones, tokens y AST tipado independiente de Lark |
| `application/contracts.py` | Fases, comprobaciones, símbolos y resultado interno |
| `domain/diagnostics.py` | Diagnósticos compartidos sin dependencias de aplicación |
| `api/schemas/analysis.py` | Modelos Pydantic de transporte y JSON Schema |
| `api/tree.py` | Conversión del AST existente a nodos dibujables |
| `infrastructure/catalogs.py` | Carga de archivos permitidos a modelos del dominio |

El núcleo usa dataclasses y enums de Python; no importa FastAPI, Pydantic ni Lark.
El adaptador HTTP convierte un resultado interno a JSON, no ejecuta fases.

El AST conserva horas como texto y duraciones como enteros sin validar su
significado. `HORA 25:00` y `DURACION 0` se pueden representar para diagnosticarlos
en semántica. Los intervalos del dominio ya normalizados exigen inicio anterior
al fin, minutos entre 0 y 1440 y duración positiva. El fin 1440 representa medianoche
al terminar el día; el inicio no puede ser 1440.

## Posiciones y procedencia

Los offsets cuentan caracteres Unicode de Python desde cero. Líneas y columnas
comienzan en 1; los fines de los rangos son exclusivos. No son bytes ni unidades
UTF-16: el frontend deberá convertirlos cuando su editor lo requiera, especialmente
ante emojis. Un token mantiene su lexema original, sin retirar comillas, junto
con `pattern_id`; el patrón se encuentra en la colección `patterns`.

Un origen puede ser TEXTO con rango, EXCEL con libro/hoja/celdas o JSON con archivo
y JSON Pointer. Las sesiones del catálogo conservan celdas originales y ubicación
en el JSON cargado. Los cambios de aula tienen su procedencia adicional en
`catalog.adjustments`.

Se conservan dos huellas diferentes: `catalog.source.sha256` identifica el Excel
original; `catalog.snapshot_sha256` identifica los bytes del JSON cargado. La
respuesta usa la segunda como `metadata.catalog_sha256`. Una superposición temporal
de ofertas mantiene esa huella como identidad del catálogo base; sus propuestas
proceden del texto de la solicitud.

La auditoría guardada en ambos JSON se considera evidencia de la FUENTE_ORIGINAL,
no una auditoría recalculada del catálogo ajustado. El cargador no la presenta
como comprobaciones nuevas de aulas.

## Identidad de ofertas y salones

Los IDs de ofertas se comparan exactamente; no cambian por cada alumno. Una
propuesta con ID existente reemplaza esa oferta en una copia temporal. Un ID nuevo
se añade; dos propuestas del mismo ID se rechazan antes de construir esa copia.
La selección personal mantiene referencias y no clona sesiones compartidas.

Los IDs de sesión importados se conservan. Para las nuevas sesiones declaradas
en texto se reserva la forma `<offer_id>:sesion:<indice>`, con índice desde cero
en orden de declaración. Las dos sesiones de un mismo día mantienen IDs distintos.
La exclusión de la versión previa del catálogo se hace por ID de oferta completo,
no por similitud de horarios ni por nombre del alumno.

`room_identity` produce una clave de comparación y conserva el nombre original:

| Entradas | Clave |
| --- | --- |
| FIE2AUL032 / FIE2-AUL32 | AUL:FIE2:32 |
| FIE1-AUL025 / FIE1-AUL25 | AUL:FIE1:25 |
| FIE1AC0001 / FIE1-AC0001 | AC:FIE1:0001 |
| Aula nueva / AULA NUEVA | NOMBRE:AULA NUEVA |

Los códigos AC conservan los ceros de su número. No se equipara CENTRO DE CÓMPUTO
con FIE1AC0001. Una clave de comparación no demuestra disponibilidad física.

Un campo combina `state` con `value`: CONOCIDO lleva texto; DESCONOCIDO y SIN_ASIGNAR
llevan null. La cadena literal `"DESCONOCIDO"` es un valor conocido, diferente del
marcador sin comillas. Un aula sin asignar sigue pendiente. Los docentes se
conservan como atributos informativos; la política exige sus reglas desactivadas.

## Respuesta para las pestañas

| Campo | Uso en la interfaz |
| --- | --- |
| `metadata` | Lenguaje, catálogo/huella, política, alcance y nombre de entrada |
| `phases` | Consola: fase completada, con errores o no ejecutada |
| `patterns`, `tokens` | Tabla de token, lexema, patrón, línea y columna |
| `ast` | Árbol visual de nodos y ramas, o null si no pudo construirse |
| `symbols` | Tabla de entidades, atributos y procedencia |
| `diagnostics` | Errores y advertencias del texto o propuesta analizada |
| `catalog_diagnostics` | Hallazgos del catálogo separados del resultado personal |
| `checks` | Resultado y alcance requerido de cada comprobación |
| `schedules` | Sesiones normalizadas de cada horario para tabla/calendario |

Cada nodo visual tiene `id`, `kind`, `label`, `value`, `value_state`, `span` y
`children`. Los IDs son únicos y deterministas para el mismo AST, no identificadores
persistentes entre todas las ediciones. El frontend distribuye niveles y ramas,
colorea tipos y maneja zoom/desplazamiento. Al seleccionar un nodo, `span` permite
señalar el texto correspondiente. No se envían coordenadas gráficas del backend.

Los estados del resultado son VALIDO, INVALIDO e INCOMPLETO. Los modelos impiden
un éxito si hubo errores, fases no ejecutadas o comprobaciones requeridas pendientes.
Una fase posterior no puede ejecutarse si su dependencia falló. La sintaxis
completada requiere un AST; si no se completó, `ast` es null. Las reglas desactivadas
se muestran, no se declaran requeridas ni vuelven incompleto el resultado por sí solas.

Un fallo semántico puede conservar un AST y sesiones normalizables, con su estado
inválido explícito. Los errores ajenos de auditoría no invalidan una selección
personal. Los esquemas JSON describen la forma del transporte; las invariantes
entre campos se comprueban en el modelo interno de resultado.

## Esquemas y ejemplos reproducibles

- [Esquema de solicitud](../contracts/analysis-request.schema.json).
- [Esquema de respuesta](../contracts/analysis-response.schema.json).
- [Ejemplo válido](../contracts/examples/valido.json).
- [Ejemplo inválido](../contracts/examples/invalido.json).
- [Ejemplo incompleto](../contracts/examples/incompleto.json).

Son fixtures construidos a mano: no prueban que el compilador ya analice esos
textos. No se publican como una compilación exitosa en la interfaz. El ejemplo
incompleto usa una oferta que efectivamente tiene una sesión pendiente en la copia
de trabajo. El inválido ilustra una cadena sin cierre y fases dependientes no
ejecutadas.

Desde la raíz del repositorio:

```sh
backend/.venv/bin/python scripts/exportar_contratos.py
backend/.venv/bin/python scripts/exportar_contratos.py --check
```

El primer comando regenera los esquemas y fixtures a partir de los modelos; el
segundo detecta diferencias sin modificar archivos. Para usarlo desde otra copia
se instala primero el backend con las instrucciones de su README.
