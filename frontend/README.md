# Frontend

Interfaz React + TypeScript + Vite del compilador `.hor`. Requiere Node >=22.12 y
npm. Desde `frontend`:

```sh
npm ci
npm run dev
```

Abrir `http://127.0.0.1:5173` y encender también el backend en el puerto 8000.
**Ctrl+C** detiene Vite. El editor funciona sin API, pero compilar y cargar
recursos requiere conexión. [Guía completa de uso](../docs/11-interfaz.md).

Editor CodeMirror para texto o archivos UTF-8 `.hor`, pestañas de resultados
reales, árbol interactivo, símbolos, diagnósticos, calendario/lista y consola.
Borrador local, carga de ejemplos y descargas de fuente y JSON. Los componentes
presentan resultados del backend; la validación del lenguaje pertenece a Python.

## Conexión

Vite envía `/api` al backend local en el puerto 8000. Para cambiar el destino,
copiar `.env.example` a `.env` y editar API_TARGET; reiniciar Vite. La variable
configura el servidor de desarrollo. No se requiere CORS para este flujo con proxy.

`npm run preview` sirve `dist/` para inspección local. La publicación y el
alojamiento de Python quedan para una decisión posterior; el servidor publicado
deberá enrutar `/api` al backend correspondiente.

## Verificar

```sh
npm run check:types
npm run test:unit
npm run build
npx playwright install chromium
npm run test:e2e
```

`build` comprueba TypeScript y genera `dist/`. `test:unit` comprueba conversión de
rangos Unicode y distribución visual de sesiones. Playwright levanta FastAPI en
18765 y Vite en 15173; usa Chromium con API real y detiene ambos servidores al
terminar. Requiere el entorno `../backend/.venv` instalado y esos puertos libres.
Las trazas y capturas de fallos se guardan en `test-results/`, excluido de Git.

Después de cambiar los modelos HTTP, exportar los contratos desde la raíz:

```sh
backend/.venv/bin/python scripts/exportar_contratos.py
```

Después, desde `frontend`, ejecutar `npm run generate:types`. `check:types`
comprueba que los cinco archivos generados coincidan con sus JSON Schema. El
cliente valida también las respuestas en ejecución mediante Ajv.

Organización: `app` coordina estado, peticiones y estilos; `api` contiene cliente
y tipos generados; `features/editor`, `features/analysis` y `features/schedule`
contienen las vistas; `components` contiene piezas compartidas.
