# Etapa 5: semántica y API de análisis

El caso de uso ejecuta léxico, sintaxis y semántica, conserva los resultados de
cada fase y entrega tokens, AST, símbolos, comprobaciones y horarios normalizados.
El editor, el botón Subir .hor y las pestañas de resultados se construirán en la
etapa 6 según la referencia visual. La API ya permite probar el motor completo.

## Probar por terminal

Desde backend, con el entorno virtual activado:

```sh
python -m schedule_compiler.cli.analyze ../examples/horario_carolina.hor
python -m schedule_compiler.cli.analyze ../examples/horario_carolina.hor --json
python -m schedule_compiler.cli.analyze ../examples/oferta_compiladores.hor --scope PROPUESTA
```

Sin archivo admite stdin. El alcance predeterminado es PERSONAL y requiere un
HORARIO. PROPUESTA requiere una OFERTA y revisa sus sesiones contra las demás
ocupaciones conocidas. Si el texto contiene HORARIO, sus referencias y cruces
personales también se comprueban. No se modifica ningún catálogo en disco.

Opciones: --catalog isc-26-1-trabajo o isc-26-1-original, --policy proyecto-v0.2 y
--data-dir para indicar otra carpeta de recursos con la misma estructura.
Códigos de salida: 0 para VALIDO; 1 para INVALIDO o INCOMPLETO; 2 para errores de
argumentos, lectura o configuración. JSON usa el contrato HTTP final; la tabla de
terminal muestra fases y sesiones y envía diagnósticos de la entrada por stderr.

## Probar por HTTP

Arrancar desde backend:

```sh
python -m uvicorn schedule_compiler.main:app --reload --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000/docs y usar POST /api/v1/analyses, Try it out y Execute:

```json
{
  "source": "HORARIO \"Prueba\" { INSCRIBIR \"ISC_7B_COMPILADORES\" }",
  "source_name": "editor",
  "language_version": "0.2",
  "catalog_id": "isc-26-1-trabajo",
  "policy_id": "proyecto-v0.2",
  "scope": "PERSONAL"
}
```

Es el mismo contrato para texto pegado y contenido de un archivo leído por la
interfaz. source_name es una etiqueta no vacía, nunca una ruta que el servidor
deba abrir. source vacío es una entrada de programa válida para transporte y
produce el diagnóstico sintáctico PROGRAMA_VACIO.

| Ruta | Resultado |
| --- | --- |
| GET /api/v1/health | Salud; compiler_available ahora es true |
| POST /api/v1/analyses | Resultado completo de las fases |
| GET /api/v1/catalogs | Catálogos disponibles con huella y cantidades |
| GET /api/v1/catalogs/{id} | Entidades, ofertas, sesiones, procedencia y limitaciones |
| GET /api/v1/catalogs/{id}/audit | Auditoría recalculada y ajustes documentados |
| GET /api/v1/policies/proyecto-v0.2 | Política efectiva y reglas no configuradas |
| GET /api/v1/examples | IDs de ejemplos, nombres y alcance sugerido |
| GET /api/v1/examples/{id} | Texto fuente y alcance sugerido para cargar en el editor |

El ejemplo carolina contiene sus ocho ofertas y horario. compiladores es una
propuesta; aula-ocupada y aula-pendiente demuestran INVALIDO e INCOMPLETO. Para
analizar un ejemplo obtenido por GET, enviar solo source, source_name y scope del
recurso, junto con las opciones de análisis que se deseen. id y title no son
campos de AnalysisRequest.

Respuestas: HTTP 200 para resultados del programa, incluidos errores léxicos,
sintácticos y semánticos; 422 para solicitudes mal formadas u opciones no válidas;
404 para recursos GET desconocidos; 503 si los archivos de datos o su configuración
no están disponibles o no son compatibles. Los errores internos inesperados no se
convierten en falsos diagnósticos del usuario.

## Reglas aplicadas

- Hora entre 00:00 y 23:59; duración positiva en horas enteras; fin hasta 24:00 en
  el mismo día. Una sesión inválida conserva su AST, pero no inventa un intervalo.
- IDs de oferta no vacíos y sin duplicados dentro del texto; materia con nombre.
- Horarios con nombres no vacíos y sin duplicados; inscripciones únicas y
  referencias a ofertas existentes o declaradas. Se admiten referencias adelantadas.
- Cruces personales dentro de cada HORARIO, sin comparar horarios de personas
  distintas entre sí. Dos personas pueden asistir a la misma oferta.
- Aulas asignadas, conocidas o pendientes. Los nombres de aula nuevos se aceptan
  en la política actual, pero se comprueba su ocupación conocida.
- Cruces de aula entre sesiones distintas, incluso de una misma oferta, con
  intervalos [inicio, fin). Clases contiguas no se cruzan.

Una OFERTA con ID ya cargado sustituye temporalmente su versión completa en ese
análisis. No se compara contra sus propias sesiones anteriores. Las declaraciones
duplicadas se diagnostican antes de la superposición, sin aceptar ambiguamente
la última. IDs distintos siguen representando ofertas distintas: no se fusionan
automáticamente por compartir nombre, profesor, hora o salón.

Los símbolos incluyen ofertas, materias, grupos conocidos, sesiones, aulas con
clave de comparación y horarios. El docente es un atributo informativo; no se
crea un catálogo de profesores ni se aplica ninguna regla de docentes. Los valores
de capacidad/matrícula desconocidos permanecen como null, no se reemplazan por cero.
Las etiquetas de las materias pueden consultarse en símbolos OFERTA; el atributo
identificador las vincula con offer_id de las sesiones del horario.

## Estados y límites

INVALIDO prevalece cuando hay un incumplimiento. INCOMPLETO indica que no se
demostró un error, pero quedó una comprobación requerida pendiente: por ejemplo
un aula SIN_ASIGNAR/DESCONOCIDO o una posible equivalencia física que afecte a dos
sesiones simultáneas. VALIDO significa que pasan las reglas requeridas de la
política dentro del alcance y las ocupaciones cargadas, no de toda la universidad.

Los códigos AUL normalizan separadores y ceros; AC conserva el número. CENTRO DE
CÓMPUTO y FIE1AC0001 siguen sin equipararse. Si dos sesiones simultáneas usan esas
etiquetas, se informa IDENTIDAD_AULA_PENDIENTE y la comprobación queda no evaluable,
sin inventar un choque. Si no se superponen no limita esa comparación temporal.

Profesores: DESACTIVADA. Capacidad, laboratorio y horario permitido: NO_EVALUABLE
pero no requeridas, porque su política está NO_CONFIGURADA/NO_CONFIGURADO. Siempre
se muestran en checks; no vuelven incompleto por sí solas el análisis actual.
Activarlas requiere ampliar datos y política; un valor no soportado se rechaza
como configuración en vez de simular una comprobación. La carga semanal del
catálogo se contrasta informativamente y sus diferencias son advertencias.

## Auditoría y asignaciones pendientes

La auditoría se recalcula sobre el catálogo cargado. El original conserva el
choque de las filas 18/31; el de trabajo reporta las dos sesiones sin aula y sus
ajustes, sin afirmar que el choque quedó resuelto con otra asignación.
stored_audit_scope indica que el bloque de auditoría guardado en las fuentes
pertenece al Excel original. No se reutiliza ese bloque como auditoría actual.

catalog_diagnostics está separado del resultado de la selección. Un conflicto
de otros grupos solo invalida la entrada si ocupa un recurso de las sesiones
analizadas; en ese caso también hay diagnóstico semántico y comprobación fallida.
Una sesión ajena SIN_ASIGNAR no reserva todos los salones ni impide proponer un
salón libre; su propia asignación se mantiene pendiente.

## Archivos y configuración

Las capas de dominio y aplicación no importan FastAPI ni acceden al disco para
validar. Reciben catálogo y política explícitos. Cada análisis usa estado local y
los objetos de fuente son inmutables; no se guardan propuestas entre solicitudes.

La app local encuentra data/ y examples/ junto al repositorio aunque se arranque
desde otro directorio. En otra distribución se pueden indicar:

```sh
export SCHEDULE_COMPILER_DATA_DIR=/ruta/absoluta/data
export SCHEDULE_COMPILER_EXAMPLES_DIR=/ruta/absoluta/examples
```

create_app(data_dir=..., examples_dir=...) permite inyectar recursos para pruebas.
Los clientes HTTP solo eligen IDs permitidos. No pueden especificar rutas de
archivos ni cambiar los datos del catálogo mediante el endpoint de análisis.

Las pruebas cubren los ejemplos reales, normalización, reglas de alcance,
estados pendientes, símbolos, inmutabilidad, consultas y errores HTTP, así como
los flujos por CLI. El análisis completo de Carolina conserva 16 tramos y 29 h.
