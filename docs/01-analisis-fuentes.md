# Análisis de fuentes y alcance

Fecha de análisis: 16 de noviembre de 2026. Las fuentes son las imágenes del
proyecto, el archivo `ISC HORARIOS 26-1.xlsx` y la imagen de carga académica que
proporcionó el usuario. Su contenido se trata como datos y requisitos a estudiar.

Actualización del 17 de noviembre: los hechos de este análisis se conservan.
La política vigente v0.2 admite profesores como texto libre sin reglas de docentes
y aulas sin asignar como pendientes. Se preparó una copia de trabajo que libera
solo las dos sesiones del choque identificado; consultar `02-lenguaje.md`.

## Qué está pedido y qué estamos proponiendo

Las imágenes describen un generador y validador de horarios y muestran palabras
como `MATERIA`, `DOCENTE`, `AULA`, `DIA`, `HORA` y `DURACION`. Piden identificar
componentes léxicos, comprobar estructura y revisar reglas reales de horarios.
Enumeran conflictos de docentes y aulas, capacidad insuficiente, falta de docente
o aula, horarios fuera de lo permitido y uso incorrecto de laboratorios.

No proporcionan una gramática completa, catálogos, formato obligatorio de entrega,
arquitectura, algoritmo de generación automática ni criterios de optimización.

El usuario confirmó que se pueden elegir las herramientas y que desea una app web
con buenas prácticas. Los bloques `OFERTA`, `SESION` y `HORARIO`, la extensión
`.hor`, la arquitectura y los estados de resultado son propuestas de este diseño.

## Excel: resultados comprobados

La hoja se llama `Hoja1`; los encabezados están en la fila 1 y los datos en las
filas 2 a 67. La dimensión de formato es `A1:T67`, pero los datos relevantes están
en las columnas A a M. Cada fila representa una materia ofrecida a un grupo, con
una o más sesiones semanales; no representa una sola sesión ni un alumno.

| Dato | Resultado |
| --- | --- |
| Ofertas de materia por grupo | 66 |
| Sesiones semanales con intervalo explícito | 131 |
| Etiquetas de grupo | 12 |
| Nombres de materia distintos, quitando espacios extremos | 35 |
| IDs de materia tras normalizar acentos y separadores | 34 |
| Nombres literales de espacios académicos | 11 |
| Suma de horas semanales de todas las ofertas | 249 |
| Primera y última hora observadas | 07:00 y 20:00 |
| Cruces de grupo por etiqueta | 0 |
| Cruces de aula por nombre literal | 1 |

Las 249 horas son la suma de todas las ofertas, no la carga de un estudiante ni la
duración de la semana. Los 11 nombres de aula no prueban que existan 11 espacios
físicos distintos: hay posibles alias pendientes de confirmar.

La columna `HORAS` coincide con la suma de los intervalos de cada una de las 66
filas. Normalizar acentos en IDs no equivale a haber conciliado todos los nombres
de materias del catálogo académico.

| Grupo | Ofertas |
| --- | --- |
| ISC 1A | 8 |
| ISC 1B | 8 |
| ISC 1RA | 1 |
| ISC 1RB | 1 |
| ISC 3A | 8 |
| ISC 3B | 8 |
| ISC 3R | 1 |
| ISC 5A | 8 |
| ISC 5B | 8 |
| ISC 7A | 6 |
| ISC 7B | 6 |
| ISC 7C | 3 |

### Cruce de aula reproducible

| Oferta | Día e intervalo | Aula | Celdas |
| --- | --- | --- | --- |
| ISC 1RA, Álgebra Superior | Viernes 13:00–15:00 | FIE1-AUL28 | B18, L18, M18 |
| ISC 3B, Cálculo Vectorial | Viernes 13:00–15:00 | FIE1-AUL28 | B31, L31, M31 |

El archivo asigna simultáneamente el mismo nombre de aula a dos ofertas. Es un
conflicto dentro de los datos del archivo. Confirmar su situación real requiere
consultar si existe una corrección, una clase compartida u otra excepción; el
programa no debe inventar esa excepción.

### Calidad de datos

- `G11` tiene `FIE1-AUL26`, pero `F11` no tiene intervalo para el martes.
- `G41` tiene `FIE1-AUL29`, pero `F41` no tiene intervalo para el martes.
- `G43` contiene un espacio, que se trata como celda vacía.
- `L22` usa `09:00 - 11:00`; se normaliza a `09:00-11:00`.
- `F54` usa `8:00-9:00`; se normaliza a `08:00-09:00`.
- Existen `FIE1-AUL25` y `FIE1-AUL025`. Podrían ser el mismo espacio; se conservan
  por separado hasta confirmar la equivalencia.
- Aparecen `ADMINISTRACIÓN DE ARCHIVOS` y `ADMNISTRACION DE ARCHIVOS`. Es una
  posible variante o errata; se conserva el texto original.

Las dos celdas con aula y sin hora no se convierten en sesiones. Como la carga
semanal ya coincide en sus filas, podrían ser restos de edición. Se reportan como
advertencias de importación, sin afirmar que falte una clase real.

### Qué no aporta el Excel

No hay columnas de docente, capacidad, cantidad de alumnos, tipo de aula,
requisitos de laboratorio ni disponibilidad de docentes. Tampoco hay un reglamento
de horarios permitidos ni ocupaciones de otras carreras.

Observar clases de 07:00 a 20:00 no establece que ese sea el horario permitido.
Encontrar un espacio llamado centro de cómputo no documenta por sí solo sus
capacidades ni su equivalencia con otros códigos.

Una ausencia en el archivo significa **dato desconocido**, no que la universidad
haya dejado realmente la materia sin docente. Estos casos deben distinguirse de
una declaración explícita de falta de asignación.

## Horario personal de la imagen

| Materia en la imagen | Sesiones | Horas semanales | Correspondencia candidata |
| --- | --- | --- | --- |
| Bases de Datos II | Lunes y viernes 14:00–16:00 | 4 | ISC 7B, fila 61 |
| Compiladores | Martes y jueves 12:00–14:00 | 4 | ISC 7B, fila 62 |
| Ingeniería de Software | Miércoles 12:00–13:00; viernes 09:00–11:00 | 3 | ISC 7C, fila 66 |
| Programación de Aplicaciones Web | Martes y jueves 14:00–16:00 | 4 | ISC 7B, fila 60 |

La selección tiene cuatro materias, ocho sesiones y 15 horas semanales. No se
observan cruces entre sus sesiones. Compiladores termina a las 14:00 y Web empieza
a las 14:00: son clases contiguas, no simultáneas.

Las tres materias coinciden en días y horas con ofertas de 7B y la optativa con
una oferta etiquetada 7C. Esto no determina el grupo administrativo del alumno.
La selección tampoco incluye todas las materias de 7B; no debe marcarse como
incompleta por ese motivo sin un requisito académico específico.

La imagen sí identifica docentes: Hernández Cruz Luz María para Bases de Datos
II, Compiladores e Ingeniería de Software; Estrada Segovia Guadalupe Manuel para
Programación de Aplicaciones Web. Eso permite complementar esas ofertas si se
aceptan sus correspondencias, no todas las ofertas de la carrera.

### Equivalencias por confirmar

| Imagen personal | Excel | Interpretación |
| --- | --- | --- |
| FIE2AUL032 | FIE2-AUL32 | Probable variante de formato; no equiparada automáticamente |
| FIE1AC0001 | CENTRO DE CÓMPUTO | Coinciden las sesiones de la optativa; no prueba identidad física |
| BASES DE DATOS II | BASE DE DATOS II | Correspondencia candidata por nombre y sesiones |
| INGENIERÍA DE SOFTWARE | OPTATIVA I (INGENIERIA DE SOFTWARE) | Correspondencia candidata por nombre y sesiones |

La transcripción conserva los valores originales. No se almacenan en ella el
nombre ni la matrícula del estudiante, porque no hacen falta para analizar las
sesiones.

## Cómo sirve el horario de un compañero

Un compañero puede introducir su selección y comprobar cruces personales. Ser de
la misma carrera permite reutilizar el catálogo, aunque no garantiza que tenga
las mismas materias, grupo, optativa o restricciones.

Dos personas que seleccionan la misma oferta asisten a una misma clase. Registrar
dos horarios personales no crea dos ocupaciones de aula o dos trabajos simultáneos
del docente. La selección personal debe referenciar ofertas ya identificadas.

La etiqueta 7C contiene opciones de optativa. No debe asumirse que toda persona
toma todas esas opciones. Las restricciones por alumno se evalúan sobre su
selección; las restricciones por cohorte necesitan saber qué ofertas comparten
efectivamente estudiantes.

## Alcances de validación

- **Personal:** cruces entre las materias seleccionadas y comprobaciones aplicables
  a esas ofertas. Un problema de otros grupos no invalida esta selección.
- **Propuesta de oferta:** cambios de clase comparados contra las demás ocupaciones
  conocidas, excluyendo la versión previa de esa misma oferta.
- **Auditoría del catálogo:** revisión de las 66 ofertas importadas y reporte de
  sus anomalías, independiente del resultado del horario personal.

La validación de docentes y aulas se limita a los datos cargados. Un profesor o un
espacio puede tener ocupaciones en otra carrera; no puede certificarse su
disponibilidad institucional completa con este archivo.

## Datos y decisiones pendientes

1. Confirmar si «generador» exige asignación automática de aulas y horas, o la
   construcción y presentación de un horario descrito por el usuario.
2. Confirmar qué evidencias evaluará la maestra: tokens y patrones, árbol, tabla
   de símbolos, errores, autómatas o documentación adicional.
3. Conseguir o declarar explícitamente datos de capacidades, alumnos, docentes,
   tipos de aula y límites horarios. Los datos de demostración deben identificarse
   como ficticios.
4. Confirmar equivalencias de aulas, nombres y relación entre las fuentes.
5. Determinar si hay ofertas compartidas, grupos de optativas y restricciones de
   cohortes que necesiten representarse explícitamente.

Estas precisiones no impiden empezar a definir el lenguaje y construir los tres
analizadores. Sí limitan qué reglas pueden declararse completamente verificadas
con las fuentes actuales.
