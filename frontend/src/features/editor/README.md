# Editor

`SourceEditor.tsx` integra CodeMirror: edición de texto, resaltado visual,
Ctrl/⌘+Enter y selección/desplazamiento a un rango. `positions.ts` normaliza saltos
de línea y convierte offsets Unicode del backend a UTF-16 del editor.

`app/useCompiler.ts` coordina carga UTF-8 de `.hor`, ejemplos y borrador local.
Cancelar o fallar la lectura conserva la edición anterior. Texto y archivo
alimentan el mismo `source` de la API. La gramática y semántica se validan en Python;
el resaltado del editor es solo una ayuda visual.
