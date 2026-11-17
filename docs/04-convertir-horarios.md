# Convertir un horario a .hor

El formato vigente es v0.2. Su compilador todavía no está implementado. Para
convertir imágenes se recomienda la entrada completa: conserva las sesiones
reales para revisarlas. La selección abreviada solo reutiliza el catálogo.

Adjuntar a la IA la imagen y, si está disponible, la lista de ofertas del catálogo
con sus IDs, materias y sesiones. Copiar este prompt:

```text
Convierte el horario de la imagen al lenguaje de horarios .hor v0.2.
Transcribe lo visible sin corregir conflictos ni inventar información.

Devuelve primero un bloque de código con este formato exacto y después, fuera
del código, las dudas, datos faltantes y páginas no proporcionadas.

OFERTA "ID_DE_LA_OFERTA" {
    MATERIA "Nombre de la materia"
    GRUPO DESCONOCIDO
    DOCENTE "Nombre del profesor tal como aparece"
    SESION {
        AULA "Código o nombre del aula tal como aparece"
        DIA MARTES
        HORA 12:00
        DURACION 2
    }
}
HORARIO "Horario personal" {
    INSCRIBIR "ID_DE_LA_OFERTA"
}

Reglas:
1. Crea un bloque OFERTA por materia/oferta y un bloque SESION por cada tramo
   semanal. Repite SESION para días distintos o varios tramos de un mismo día.
   Conserva tramos consecutivos separados cuando así aparecen en la imagen.
2. Repite INSCRIBIR para seleccionar una vez cada oferta transcrita. El ID debe
   coincidir exactamente con el de OFERTA. No incluyas nombre completo, matrícula
   ni otros datos personales del estudiante; usa una etiqueta para HORARIO.
3. Si proporciono un catálogo, reutiliza sus IDs únicamente cuando puedas asociar
   materia y sesiones de forma inequívoca. Señala diferencias fuera del código.
   Si no hay correspondencia, usa un ID provisional único como PROV_MATERIA_01;
   no inventes un ID oficial ni asumas que dos amigos crean clases distintas.
4. Conserva los nombres y códigos de aula originales. No sustituyas un código por
   CENTRO DE CÓMPUTO ni normalices guiones o ceros: eso corresponde al compilador.
5. No infieras el grupo del semestre. Si no se ve, escribe GRUPO DESCONOCIDO.
   Solo puedes tomarlo de un catálogo con correspondencia clara y debes indicarlo
   fuera del código. Para un profesor ilegible escribe DOCENTE DESCONOCIDO.
6. Si no se puede conocer el aula, escribe AULA DESCONOCIDO. Si la fuente indica
   explícitamente que no hay salón, escribe AULA SIN_ASIGNAR. Los marcadores
   DESCONOCIDO y SIN_ASIGNAR se escriben sin comillas.
7. Usa horas de 24 horas HH:MM. DURACION es la diferencia entre fin e inicio en
   HORAS ENTERAS: 12:00–14:00 da HORA 12:00 y DURACION 2. No pongas hora final.
   No redondees duraciones fraccionarias: señala que v0.2 necesita ampliarse y no
   generes una sesión falsa para ese tramo. Si falta día u hora, repórtalo fuera
   del código en vez de inventarlo y declara que la conversión es parcial.
8. Días permitidos: LUNES, MARTES, MIERCOLES, JUEVES, VIERNES, SABADO, DOMINGO.
   Palabras reservadas en mayúsculas, sin acentos. Textos entre comillas dobles.
   Escapa comillas y barras inversas dentro de textos. Usa llaves y el orden de
   campos del ejemplo. No uses puntos y coma ni campos adicionales.
9. No compruebes si un profesor existe ni cambies nombres por profesores conocidos.
   No cambies días, horas ni aulas para resolver choques. El compilador se encargará
   de los diagnósticos. No elimines materias porque creas que son optativas.
10. Indica fuera del código cuántas materias, tramos y horas pudiste transcribir.
    Si dice hoja 1 de 2 y falta la otra página, no afirmes haber convertido todo.
```

Una conversión por IA se revisa contra la imagen. No se puede detectar un error de
transcripción con seguridad si el texto resultante es coherente pero distinto de
la fuente.

## Caso Carolina

Se transcribió la página visible: ocho materias, 16 tramos y 29 horas semanales.
No hay cruces personales en esos tramos. El encabezado indica hoja 1 de 2; no se
infiere el contenido de la segunda página. Los profesores se conservaron como texto.

Los IDs de las seis ofertas 7B y las dos optativas 7C se asociaron por materias y
sesiones con el Excel. La pertenencia de grupo proviene de esa asociación, no de
un campo explícito de la imagen. No se impone tomar solo una optativa porque no se
ha proporcionado ese reglamento.

Metodología se conserva como viernes 16:00–18:00 y 18:00–19:00, ambos en el mismo
código de aula. El catálogo los representa unidos como 16:00–19:00: tienen la
misma cobertura de tiempo aunque diferente cantidad de tramos.

Archivos:

- [Conversión completa](../examples/horario_carolina.hor).
- [Selección abreviada](../examples/horario_carolina_seleccion.hor).

Para comprobar salones se considerarán las demás ofertas conocidas, excluyendo
la versión previa de la oferta transcrita. No debe detectarse un choque por el
simple hecho de que Carolina y otra persona asistan a la misma clase.

Las sesiones sin asignar de la copia de trabajo son las del cruce previo de
Álgebra Superior y Cálculo Vectorial. No pertenecen al horario de Carolina. En
su transcripción se mantienen todos los salones que la imagen muestra.
