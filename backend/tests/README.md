# Pruebas del backend

Pruebas actuales de la etapa 2, usando pytest:

- `test_models.py`: invariantes, fases dependientes y núcleo sin frameworks.
- `test_catalogs.py`: carga real, procedencia, política, identidad y reemplazo.
- `test_contract.py`: transporte, fixtures y árbol visual.

Se ampliarán con las siguientes etapas:

- compiler: tokens, posiciones, gramática y construcción del AST.
- domain: intervalos, cruces, identidad de ofertas y reglas de aulas.
- application: integración con catálogo y política, sin HTTP.
- api: contrato de análisis y errores de transporte.

Todavía no hay pruebas de reconocimiento léxico, parsing ni reglas semánticas de
horarios: esas implementaciones comienzan en las etapas 3, 4 y 5.
