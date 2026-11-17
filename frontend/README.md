# Frontend

React + TypeScript + Vite. Node >=22.12 y npm. Desde la carpeta `frontend`:

```sh
npm ci
npm run dev
```

Abrir `http://127.0.0.1:5173`. Ejecutar también el backend para comprobar la
conexión; si está apagado, la página indica que la API no está disponible.

Vite envía las solicitudes `/api` al backend local en el puerto 8000. Para cambiar
el destino, copiar `.env.example` a `.env` y editar API_TARGET; reiniciar Vite.
La variable configura el servidor de desarrollo, no se expone como secreto en el
navegador. No se requiere CORS para este flujo con proxy.

```sh
npm run typecheck
npm run build
```

`build` comprueba TypeScript y genera `dist/`. `npm run preview` sirve esa salida
estática para inspección; no conecta el proxy de desarrollo de la API. El
despliegue posterior deberá enrutar `/api` al backend correspondiente.

Organización: `app` para composición y estilos; `api` para el cliente HTTP;
`features/editor`, `features/analysis` y `features/schedule` para las futuras
funciones; `components` para componentes compartidos cuando sean necesarios.

En esta etapa solo hay una página de arranque, sin editor ni compilación.
