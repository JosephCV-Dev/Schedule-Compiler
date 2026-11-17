# Lenguaje de horarios: propuesta v0.2

Estado: especificación y ejemplos, con analizador léxico implementado en etapa 3.
El parser y las reglas semánticas todavía están pendientes.
Actualización solicitada por el usuario el 17 de noviembre de 2026: profesor como
texto libre sin reglas semánticas de profesores; aulas arbitrarias sujetas a
ocupación; sesiones del choque conocido liberadas en una copia de trabajo.

## Entrada y usos

El editor recibe texto UTF-8 con extensión opcional `.hor`. El backend recibe
además catálogo, política y alcance. Hay dos formas de entrada:

- Completa: bloques OFERTA con los datos transcritos y un HORARIO que los selecciona.
  Es la apropiada para convertir imágenes y revisar lo que realmente muestran.
- Selección: solo HORARIO e INSCRIBIR con IDs existentes en el catálogo. Reutiliza
  los datos cargados; no compara los detalles de una imagen que no se transcribió.

Una oferta es una materia ofrecida a un grupo y puede tener varias sesiones. El
horario personal referencia ofertas; compartir una oferta no duplica la clase.
Se conserva el mismo ID para la misma oferta, incluso entre horarios de amigos.

Ejemplo mínimo completo:

```text
OFERTA "ISC_7B_COMPILADORES" {
    MATERIA "COMPILADORES"
    GRUPO "ISC 7B"
    DOCENTE "HERNANDEZ CRUZ LUZ MARIA"
    SESION {
        AULA "FIE2AUL032"
        DIA MARTES
        HORA 12:00
        DURACION 2
    }
    SESION {
        AULA "FIE2AUL032"
        DIA JUEVES
        HORA 12:00
        DURACION 2
    }
}
HORARIO "Ejemplo" {
    INSCRIBIR "ISC_7B_COMPILADORES"
}
```

## Convenciones y gramática

Palabras reservadas y días en mayúsculas sin acentos. Cadenas entre comillas
dobles, con escapes de comilla y barra inversa; sin saltos reales dentro de una
cadena. Espacios y saltos se ignoran pero se conservan posiciones. Comentarios
con `#` fuera de cadenas. Los campos tienen orden fijo y no hay puntos y coma.

HORA_LITERAL reconoce `[0-9]{2}:[0-9]{2}` antes que ENTERO (`[0-9]+`).
DURACION se mide en horas enteras, no en minutos. Las duraciones fraccionarias
quedan fuera de v0.2; la conversión debe señalarlas, sin redondearlas. La hora de
inicio sí puede contener minutos, por ejemplo 10:30. La semántica verifica los
rangos, duración positiva y fin dentro del mismo día.

```ebnf
programa = declaracion, { declaracion }, EOF ;
declaracion = oferta | horario ;
oferta = "OFERTA", CADENA, "{",
         "MATERIA", CADENA,
         "GRUPO", dato_grupo,
         "DOCENTE", dato_docente,
         sesion, { sesion }, "}" ;
sesion = "SESION", "{",
         "AULA", dato_aula,
         "DIA", dia,
         "HORA", HORA_LITERAL,
         "DURACION", ENTERO, "}" ;
horario = "HORARIO", CADENA, "{",
          inscripcion, { inscripcion }, "}" ;
inscripcion = "INSCRIBIR", CADENA ;
dato_grupo = CADENA | "DESCONOCIDO" ;
dato_docente = CADENA | "DESCONOCIDO" | "SIN_ASIGNAR" ;
dato_aula = CADENA | "DESCONOCIDO" | "SIN_ASIGNAR" ;
dia = "LUNES" | "MARTES" | "MIERCOLES" | "JUEVES"
    | "VIERNES" | "SABADO" | "DOMINGO" ;
```

DESCONOCIDO indica que la fuente no permite conocer el dato; SIN_ASIGNAR indica
falta explícita de asignación. No se escriben entre comillas. Si falta día, hora
o duración, no se inventa una sesión: se reporta la limitación fuera del código.
Los campos siguen siendo sintácticamente obligatorios, aunque algunos permitan
estos marcadores. MATERIA es un nombre descriptivo; no necesita coincidir en
ortografía con un catálogo. GRUPO puede ser desconocido sin bloquear la revisión
personal. INSCRIBIR sí requiere un ID declarado o conocido.

## Reglas activas y alcance

- Referencias a ofertas existentes y declaraciones/inscripciones sin duplicados.
- Horas válidas, duración positiva y sesiones dentro del día.
- Cruces entre sesiones seleccionadas por una persona.
- Ocupación de aulas por sesiones diferentes en el mismo día e intervalo.
- Reglas de capacidad, laboratorio, carga y límites horarios solo cuando exista
  una política y datos explícitos para evaluarlas.

DOCENTE se conserva como texto informativo: no hay catálogo obligatorio, búsqueda
por nombre, comprobación de asignación, disponibilidad ni cruces de docentes.
También se permiten sus marcadores sin error semántico. Esto reduce la cobertura
respecto de las reglas de profesores del enunciado original de la maestra; debe
quedar documentado en la entrega.

Cualquier nombre de aula es aceptable sin pertenecer a un catálogo cerrado, pero
su disponibilidad se compara con las ocupaciones cargadas. Un aula nueva no tiene
ocupaciones conocidas, lo que no acredita disponibilidad fuera de esos datos.
DESCONOCIDO o SIN_ASIGNAR produce una asignación pendiente y una comprobación de
ocupación no evaluable; no es un fallo de sintaxis ni una asignación resuelta.
No se asigna automáticamente un salón. Un aula ocupada introducida por un usuario
produce un diagnóstico; no se borra silenciosamente para ocultar ese nuevo choque.

Los intervalos son `[inicio, fin)`: se cruzan cuando inicio_A < fin_B e
inicio_B < fin_A. Dos clases que terminan y empiezan a las 14:00 son contiguas.
Si ambas referencias son a la misma oferta y sesión, es una misma clase compartida.

Una OFERTA con ID existente sustituye temporalmente a esa oferta en este análisis,
sin modificar las fuentes ni comparar la clase contra su propia versión anterior.
Dos declaraciones del mismo ID en el texto son un error. Los tramos consecutivos
pueden conservarse separados, como aparecen en la fuente.

## Catálogos, aulas y procedencia

`data/isc_26_1.normalizado.json` conserva la extracción y auditoría del Excel.
`data/isc_26_1.trabajo.json` es la copia de trabajo con dos sesiones SIN_ASIGNAR:
viernes 13:00–15:00 de las filas 18 y 31. Solo se libera ese encuentro de cada
oferta, conservando sus demás sesiones. La auditoría incluida en esa copia sigue
siendo evidencia de la fuente original; `ajustes_proyecto` documenta los cambios.
La política propuesta está en `data/politica_proyecto.json`.

Para comparar ocupaciones se conservan nombres originales y se normaliza el
formato de códigos AUL: `FIE2AUL032` y `FIE2-AUL32` representan la misma clave de
comparación, edificio FIE2 y aula 32. Se aplica el mismo criterio a ceros iniciales
y separadores del resto de códigos AUL. Esto es una convención del proyecto;
las etiquetas originales no se borran. Variantes de separadores en un código AC
se comparan igualmente, sin cambiar su número.

No se equipara automáticamente CENTRO DE CÓMPUTO con FIE1AC0001: la equivalencia
física no está documentada. Un resultado debe advertir cuando una identidad de
espacio pendiente pueda limitar la revisión contra el catálogo. El prompt de
transcripción conserva los códigos tal como aparecen; la normalización pertenece
al motor, no a la IA conversora.

## Salidas y errores

Las fases entregarán tokens con lexema, patrón y posición; AST con nodos Programa,
Oferta, Sesión, Horario e Inscripción; símbolos y referencias resueltas; diagnósticos
con origen; comprobaciones y horario estructurado. Los profesores pueden ser
atributos informativos y no requieren símbolos de un catálogo de docentes.

Estados: INVALIDO ante un incumplimiento demostrado; INCOMPLETO si faltan datos de
una regla requerida o un aula pendiente; VALIDO cuando pasan todas las reglas
requeridas del alcance. Las comprobaciones indican CUMPLE, INCUMPLE, NO_EVALUABLE,
NO_APLICA o DESACTIVADA según corresponda. Las reglas de docentes desactivadas no
convierten por sí solas el resultado en incompleto y siempre quedan visibles.

Una cadena sin cierre es error léxico; DURACION "dos" es sintáctico; DURACION 0
y HORA 25:00 son semánticos. Un fallo léxico o sintáctico bloquea los resultados
posteriores que dependan de una estructura completa. Las advertencias del catálogo
se muestran separadas de los cruces personales.
