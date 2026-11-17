# Resultados del análisis

`ResultsPanel` organiza pestañas accesibles para tokens, AST, símbolos,
diagnósticos y horario. Cada panel consume la respuesta real de la API. La consola
presenta estados de fases y diagnósticos; la auditoría del catálogo se consulta
aparte de los errores de entrada.

`AstTree` dibuja nodos y ramas con React Flow y Dagre: enfoque por declaración,
campos opcionales, expansión, zoom, desplazamiento y selección del código a partir
de rangos del AST. Se carga al abrir su pestaña. Los contratos están en
`contracts/`, en la raíz; los tipos TypeScript se generan en `src/api/generated/`.
