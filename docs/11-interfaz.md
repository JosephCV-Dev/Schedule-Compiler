# Etapa 6: interfaz del compilador

La app local permite escribir, pegar o subir código `.hor` y consultar las salidas
reales del backend. Sigue la referencia del proyecto: tema oscuro con violeta,
editor a la izquierda, resultados a la derecha y consola debajo. En ventanas
pequeñas los paneles se apilan y las tablas y el calendario desplazan su contenido.

## Encender y apagar

Con las dependencias instaladas, desde la raíz, en dos terminales:

```sh
cd backend
.venv/bin/python -m uvicorn schedule_compiler.main:app --reload --host 127.0.0.1 --port 8000
```

```sh
cd frontend
npm run dev
```

Abrir `http://127.0.0.1:5173`. Para detener cada servidor, pulsar **Ctrl+C** en su
terminal. Si activaste el entorno virtual, `deactivate` sale de él después de
parar el backend; activarlo no es obligatorio al usar `.venv/bin/python`.
La instalación inicial está en el [README principal](../README.md).

## Recorrido de prueba

1. Al abrir por primera vez aparece `oferta_compiladores.hor`, con el modo
   **Propuesta de clases** y la **Copia de trabajo**. Pulsar **Compilar**.
2. Explorar **Tokens**, **Árbol sintáctico**, **Tabla de símbolos**,
   **Errores y advertencias** y **Horario resultante**.
3. En el árbol, activar **Campos**, expandir nodos, acercar o desplazar. Pulsar un
   nodo para seleccionar su texto en el editor. **Enfoque** permite ver una sola
   declaración cuando el archivo contiene muchas materias.
4. Cargar el ejemplo **Horario completo de Carolina** y compilar: muestra 276
   tokens, 16 sesiones y 29 horas. **Semana** y **Lista** son dos vistas de las
   mismas sesiones normalizadas por el backend.
5. Cargar ejemplos de error léxico, sintáctico, aula ocupada o aula pendiente para
   comprobar los diagnósticos y los estados **Inválido** e **Incompleto**.
6. Escribir directamente o pulsar **Subir .hor** para cargar otro archivo. Revisar
   el modo: **Mi horario** requiere HORARIO; **Propuesta de clases** requiere OFERTA.
   Pulsar **Compilar** o **Ctrl/⌘+Enter**.

El botón de descarga del editor guarda el código `.hor`; el de resultados guarda
la respuesta JSON del último análisis vigente. **Limpiar** vacía texto, resultados
y consola. No modifica catálogos del servidor.

## Entradas, estado y errores

El archivo se decodifica estrictamente como UTF-8. Cancelar la selección, elegir
otra extensión o fallar la lectura conserva el código previo. Los saltos CRLF/CR
se convierten a LF para que editor, petición y rangos compartan el mismo texto.
La API recibe `source` y una etiqueta `source_name`, nunca una ruta del equipo.

Se guarda un borrador versionado en el almacenamiento local del navegador: texto,
nombre del archivo, modo y catálogo. Recargar restaura ese borrador; los resultados
se vuelven a calcular. Si el navegador no permite guardarlo, el editor sigue
funcionando y la consola lo indica. La descarga permite conservar una copia.

Cambiar el código o las opciones marca los resultados como anteriores y desactiva
su exportación y navegación al código hasta volver a compilar. Editar mientras
llega una respuesta tampoco confunde el resultado anterior con la entrada actual.
Cargar un ejemplo lentamente conserva cualquier edición realizada durante la espera.
Los fallos HTTP, de conexión o de contrato se muestran sin borrar el texto ni
anunciar una compilación exitosa.

La consola presenta estados de las fases devueltos por el motor y diagnósticos
reales, con filtros de errores y advertencias. La pestaña de diagnósticos distingue
**Entrada**, **Catálogo** y **Reglas**. Los conflictos históricos del Excel se
consultan como auditoría del catálogo. Las ubicaciones de texto seleccionan el
editor; las de Excel/JSON muestran su procedencia en un diálogo.

## Organización y decisiones

- `app/useCompiler.ts` coordina borrador, opciones, peticiones, cancelación y consola.
- `api/client.ts` consulta la API y valida las respuestas con JSON Schema mediante
  Ajv. Los cinco tipos TypeScript de `api/generated/` se generan desde `contracts/`.
- `features/editor/` usa CodeMirror para edición, resaltado y selección de rangos.
  Convierte offsets por punto de código de Python a unidades UTF-16 del navegador,
  incluyendo caracteres como emojis.
- `features/analysis/` presenta tablas, diagnósticos y un AST con React Flow y Dagre.
  El visor de árbol y el editor se cargan en módulos separados. Nodos, etiquetas,
  relaciones y rangos proceden del AST de la API; su disposición se calcula en React.
- `features/schedule/` dibuja las sesiones normalizadas. Distribuye visualmente los
  bloques superpuestos sin decidir si existe un error semántico.
- `components/` contiene estados vacíos, etiquetas, enlaces de origen y diálogos.

El resaltado del editor no es el analizador léxico del proyecto. La gramática,
referencias, duraciones y ocupación se validan exclusivamente en Python. No se
introducen reglas para nombres de docentes. Capacidad, laboratorio y límites
horarios siguen **sin configurar** en la política actual y aparecen en las reglas.
Un aula SIN_ASIGNAR sigue pendiente; dibujar una sesión no resuelve su asignación.

## Verificación reproducible

Desde la raíz, exportar y comprobar los contratos del backend:

```sh
backend/.venv/bin/python scripts/exportar_contratos.py --check
```

Desde `frontend`:

```sh
npm run check:types
npm run test:unit
npm run build
npx playwright install chromium
npm run test:e2e
```

Cuando cambie un contrato, ejecutar primero `scripts/exportar_contratos.py` sin
`--check` y después `npm run generate:types` en `frontend`. Revisar y versionar
los cambios generados; los componentes no mantienen copias manuales de esos tipos.

Verificación de esta etapa: 221 pruebas del backend, 7 pruebas de presentación,
17 pruebas en Chromium, contratos y tipos sincronizados, TypeScript y build.
Las pruebas de navegador usan la API real salvo los casos explícitos de fallo
HTTP o respuesta fuera de contrato. Cubren árbol con ramas y selección del código,
tokens, símbolos, horarios, errores, subida UTF-8, borrador, concurrencia, teclado,
descargas y pantalla de 390 px. Se inspeccionaron visualmente calendario, árbol
y vista pequeña. No se acredita compatibilidad con otros navegadores todavía.

Playwright inicia sus propios servidores en `127.0.0.1:18765` y `127.0.0.1:15173`,
los detiene al terminar y no reutiliza los servidores habituales de desarrollo.
Los puertos deben estar libres. Las capturas y trazas de fallos quedan en
`frontend/test-results/`, excluido de Git.

La etapa 7 de verificación final y preparación de la demostración queda pendiente.
La app no se ha publicado; el calendario no busca automáticamente nuevas aulas,
días u horas.
