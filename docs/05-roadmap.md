# Roadmap del proyecto

La implementación avanza por etapas. El usuario revisa el resultado e indica
cuándo pasar a la siguiente; completar una etapa no autoriza a implementar las
demás automáticamente. Se pueden corregir y verificar problemas de la etapa
actual sin abrir una etapa nueva.

Stack confirmado: React + TypeScript + Vite, Python + FastAPI y Lark. Formato del
lenguaje: .hor v0.2. Profesor como texto libre, sin reglas de profesores; aulas
nuevas admitidas y sujetas a ocupación conocida. SIN_ASIGNAR significa pendiente.

## Estado de las etapas

| Etapa | Resultado | Estado |
| --- | --- | --- |
| 0. Alcance y fuentes | Análisis del Excel, lenguaje v0.2 y ejemplos personales | Completada |
| 1. Estructura y arranque | Carpetas, dependencias, API de salud y página inicial | Completada |
| 2. Modelos y contrato | Tipos de tokens, AST, diagnósticos, resultados y catálogo | Completada |
| 3. Análisis léxico | Tokens, patrones, ubicaciones y errores léxicos | Pendiente |
| 4. Análisis sintáctico | Gramática ejecutable, AST y errores de estructura | Pendiente |
| 5. Semántica y API de análisis | Reglas, catálogo, selección e integración HTTP | Pendiente |
| 6. Interfaz del compilador | Editor, pestañas, consola y horario según referencia | Pendiente |
| 7. Verificación y entrega | Casos completos, documentación y demostración | Pendiente |

## 0. Alcance y fuentes — completada

- Catálogo original extraído con procedencia; copia de trabajo con las dos
  sesiones del choque conocido sin aula asignada.
- Lenguaje v0.2 y prompt para convertir imágenes.
- Ejemplos personales y de Carolina, con limitaciones de las fuentes documentadas.

## 1. Estructura y arranque — completada

Entregables: paquete Python bajo `backend/src`, módulos separados por función,
proyecto React bajo `frontend/src`, herramientas configuradas y dependencias
fijadas. Endpoint `GET /api/v1/health` y página inicial que consulta su estado.

Criterio de término: backend importable e instalable; endpoint de salud y esquema
OpenAPI accesibles; TypeScript y build de producción correctos; proxy local
frontend/backend comprobado. Las instrucciones deben permitir repetir el arranque.

Fuera de esta etapa: motor de compilación, endpoint de análisis, tablas con
resultados, editor completo, persistencia y despliegue. La página inicial debe
decir que el motor aún no está disponible.

Verificación realizada: instalación del paquete, consistencia de dependencias,
build de React/TypeScript y comprobaciones HTTP de salud, OpenAPI, documentación,
página de desarrollo y proxy Vite → FastAPI. No se realizó inspección visual en
un navegador. La siguiente etapa permanece pendiente de indicación del usuario.

## 2. Modelos y contrato — completada

Definir dataclasses o tipos propios para posiciones, tokens, AST, oferta, sesión,
horario, diagnósticos y comprobaciones. Separar tipos del dominio de los modelos
HTTP. Acordar IDs, reemplazo temporal de ofertas existentes y normalización de
códigos de aula. Definir cómo cargar catálogo de trabajo y política.

Criterio: contrato de análisis documentado con ejemplos de resultado válido,
inválido e incompleto; procedencia del Excel y marcadores desconocidos preservados.
Los modelos del núcleo se utilizan sin importar FastAPI ni React.

Entregado: modelos Python sin frameworks en el núcleo, carga explícita del
catálogo/política, claves de comparación de aulas y reemplazo temporal de ofertas.
Contrato Pydantic separado, JSON Schema exportado y tres fixtures ilustrativos.
El AST se adapta a nodos con hijos, etiquetas y rangos para dibujarlo en la interfaz.
Documentación: [contrato de análisis](07-contrato-analisis.md).

Verificación: 32 pruebas del backend, sincronización de esquemas/fixtures y build
del frontend. La etapa 3 permanece pendiente de indicación del usuario.

## 3. Análisis léxico

Definir terminales en Lark con lexer basic; reconocer palabras completas, cadenas,
horas, enteros, llaves y comentarios. Conservar lexema y posición, con patrones
identificables para la tabla de tokens.

Criterio: tokenizar los ejemplos .hor y señalar caracteres desconocidos y cadenas
sin cierre con línea y columna. `12:00` debe ser una hora, no un entero parcial.
La comprobación se ejecuta sin navegador.

## 4. Análisis sintáctico

Completar reglas LALR de OFERTA, SESION, HORARIO e INSCRIBIR. Transformar el árbol
de Lark a un AST propio. Interpretar marcadores DESCONOCIDO y SIN_ASIGNAR conforme
a v0.2; no realizar búsquedas ni reglas de horarios en el parser.

Criterio: ejemplos personales generan AST; `DURACION "dos"`, campos omitidos o
llaves faltantes producen diagnósticos sintácticos. `DURACION 0` pasa sintaxis y
queda para semántica. Si una fase falla, las dependientes no simulan éxito.

## 5. Semántica y API de análisis

Construir el caso de uso de análisis; resolver ofertas y selecciones, leer los
datos y aplicar política. Validar horas, duración, referencias, duplicados,
cruces personales y ocupación de aulas. Identificar una clase compartida para
evitar comparar una oferta contra su propia versión cargada.

Implementar `POST /api/v1/analyses`, consulta de catálogos y ejemplos. Separar
errores del programa .hor de errores HTTP y del servidor. Mantener desactivadas
las reglas de docentes. Capacidad, laboratorio y límites horarios se muestran
como no configurados hasta que se incorporen datos y política explícitos.

Criterio: sesiones contiguas no se cruzan; un aula ocupada genera error; sin aula
hay pendiente; nombres arbitrarios de docentes son aceptados. Carolina tiene 29 h
en los tramos visibles y no presenta cruces personales. La auditoría del catálogo
original conserva el choque histórico; la copia de trabajo no lo oculta como si
fuera una nueva asignación resuelta. Un aula con identidad física no conciliada
expresa la limitación de la comprobación.

## 6. Interfaz del compilador

Construir la pantalla conforme a [la referencia visual](06-referencia-frontend.md):
tema oscuro y violeta; editor a la izquierda; pestañas a la derecha para tokens,
árbol, símbolos, diagnósticos y horario; consola inferior.

Agregar recuadro de texto editable y botón «Subir .hor» que carga el archivo en ese
mismo recuadro. Representar el AST como árbol visual de nodos y ramas con niveles,
zoom/desplazamiento y conexión con el editor mediante sus rangos. Agregar carga de
ejemplos, Compilar y Limpiar, estados de espera y error,
ubicaciones navegables y diseño adaptable. Consumir resultados reales de la API.

Criterio: completar desde el navegador un flujo válido y otro con errores; no
perder código ante un fallo de conexión; teclado y paneles utilizables en ventanas
pequeñas. No duplicar reglas semánticas dentro de componentes React.

## 7. Verificación y entrega

Completar pruebas del motor y contrato, comprobar los flujos visuales y preparar
casos de demostración léxicos, sintácticos y semánticos. Revisar instalación,
limitaciones y documentación para presentar a la maestra.

Criterio: verificaciones del alcance acordado pasan; cada requisito tiene una
evidencia o una exclusión explícita. La reducción de las reglas de profesores
respecto del enunciado original permanece visible.

## Decisión futura: generación automática y publicación

Generar un calendario a partir de ofertas conocidas forma parte de la interfaz.
Buscar automáticamente nuevas asignaciones de días, horas o aulas necesita un
requisito adicional y un módulo de búsqueda. No se considera implementado por
mostrar el horario ni por dejar sesiones SIN_ASIGNAR.

La publicación y el alojamiento del backend se abordan después de la app local.
La etapa 1 solicitada prepara el repositorio y no publica un sitio.
