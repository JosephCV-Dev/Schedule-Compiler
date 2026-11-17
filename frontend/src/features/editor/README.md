# Editor — etapa 6

Edición y carga de código .hor, selección de ejemplos y navegación a posiciones
de diagnósticos. La sintaxis y la semántica pertenecen al backend.

Requisito confirmado: recuadro para escribir/pegar y botón «Subir .hor». El archivo
se lee como UTF-8 y su texto aparece en el mismo editor, editable antes de compilar.
Ambos caminos envían `source` en el contrato JSON; el archivo no es obligatorio.
Conservar el texto previo si se cancela la selección o falla la lectura.
