# Pruebas del backend

Pruebas actuales hasta la etapa 4, usando pytest:

- `test_models.py`: invariantes, fases dependientes y núcleo sin frameworks.
- `test_catalogs.py`: carga real, procedencia, política, identidad y reemplazo.
- `test_contract.py`: transporte, fixtures y árbol visual.
- `test_lexer.py`: ejemplos, límites de tokens, cadenas, errores y posiciones.
- `test_lexer_cli.py`: entrada de archivo/stdin, tabla/JSON y códigos de salida.
- `test_parser.py`: gramática, AST, tipos, marcadores, posiciones y errores.
- `test_parser_cli.py`: árbol/JSON, estados por fase y errores de entrada.

Se ampliarán con las siguientes etapas:

- compiler: tokens, posiciones, gramática y construcción del AST.
- domain: intervalos, cruces, identidad de ofertas y reglas de aulas.
- application: integración con catálogo y política, sin HTTP.
- api: contrato de análisis y errores de transporte.

Todavía no hay pruebas de reglas semánticas de horarios: se implementarán en la
etapa 5. Tener AST no significa haber validado choques o asignaciones.
