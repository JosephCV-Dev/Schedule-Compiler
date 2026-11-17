# Pruebas del backend

Se añadirán con las etapas del motor, usando pytest:

- compiler: tokens, posiciones, gramática y construcción del AST.
- domain: intervalos, cruces, identidad de ofertas y reglas de aulas.
- application: integración con catálogo y política, sin HTTP.
- api: contrato de análisis y errores de transporte.

En la etapa 1 solo se comprueba el arranque y la ruta de salud. Todavía no hay
pruebas del motor ni una implementación que puedan verificar.
