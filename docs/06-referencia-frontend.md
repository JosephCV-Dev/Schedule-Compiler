# Referencia visual del frontend

Referencia: imagen enviada por el usuario en la conversación el 17 de noviembre
de 2026. No hay un archivo local de esa imagen; este documento registra sus
características para implementarlas en la etapa 6.

## Distribución

- Encabezado con nombre de la aplicación y acciones Compilar/Limpiar.
- Navegación lateral compacta para Editor y Resultados.
- Área de trabajo con código fuente a la izquierda.
- Resultados a la derecha en pestañas: Tokens, Árbol sintáctico, Tabla de símbolos,
  Errores y advertencias, Horario resultante.
- Consola inferior con mensajes de fases y filtros de errores/advertencias.
- Tema oscuro, bordes suaves, paneles contrastados y acento violeta.
- Tabla de tokens con token, lexema, patrón, línea y columna.

## Adaptación a la app web

Mantener esa jerarquía visual, con paneles apilados en ventanas pequeñas y
navegación accesible por teclado. Usar estados reales de análisis; no mostrar
mensajes de éxito antes de recibir resultados del backend. Los emblemas
institucionales se incorporarán cuando exista un archivo adecuado para usarlos.

El código visible en la referencia usa punto y coma y campos como ALUMNOS dentro
de HORARIO. Se toma como referencia visual, no como cambio de gramática: el
proyecto conserva OFERTA/SESION/HORARIO, DURACION en horas y ausencia de puntos y
coma, según la especificación .hor v0.2. No se añaden ALUMNOS ni reglas de docentes
solo porque aparezcan en la imagen.

La etapa 1 ofrece una página mínima para verificar la conexión, con los colores
base. El editor y los paneles todavía no forman parte de esa página.
