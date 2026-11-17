# Pruebas del backend

Pruebas actuales hasta la etapa 5, usando pytest:

- `test_models.py`: invariantes, fases dependientes y núcleo sin frameworks.
- `test_catalogs.py`: carga real, procedencia, política, identidad y reemplazo.
- `test_contract.py`: transporte, fixtures y árbol visual.
- `test_lexer.py`: ejemplos, límites de tokens, cadenas, errores y posiciones.
- `test_lexer_cli.py`: entrada de archivo/stdin, tabla/JSON y códigos de salida.
- `test_parser.py`: gramática, AST, tipos, marcadores, posiciones y errores.
- `test_parser_cli.py`: árbol/JSON, estados por fase y errores de entrada.
- `test_semantics.py`: reglas, datos reales, pendientes, identidad e inmutabilidad.
- `test_analysis_api.py`: contrato real HTTP, recursos y errores.
- `test_analyze_cli.py`: análisis completo por terminal y códigos de salida.

Se ampliarán con las siguientes etapas:

- compiler: tokens, posiciones, gramática y construcción del AST.
- domain: intervalos, cruces, identidad de ofertas y reglas de aulas.
- application: integración con catálogo y política, sin HTTP.
- api: contrato de análisis y errores de transporte.

La interfaz y sus pruebas se incorporarán desde etapa 6. Capacidad, laboratorio y
límites no configurados se verifican como exclusiones explícitas de la política;
no se presentan como reglas cumplidas.
