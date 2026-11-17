# Horario resultante

`SchedulePanel` dibuja el calendario semanal y una tabla a partir de las sesiones
normalizadas de la API, incluidas asignaciones pendientes. Permite seleccionar
horarios y navegar al texto o al origen de una sesión. Conserva totales reales.

`layout.ts` distribuye bloques superpuestos en columnas para poder verlos.
Esa distribución es visual: las reglas y los diagnósticos de cruces pertenecen
exclusivamente al backend.
