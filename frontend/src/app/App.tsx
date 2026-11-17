import { useEffect, useState } from 'react'
import { getHealth } from '../api/health'

type Connection = 'checking' | 'connected' | 'unavailable'

export function App() {
  const [connection, setConnection] = useState<Connection>('checking')

  useEffect(() => {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => {
      controller.abort()
      setConnection('unavailable')
    }, 5000)

    void getHealth(controller.signal)
      .then(() => {
        if (!controller.signal.aborted) setConnection('connected')
      })
      .catch(() => {
        if (!controller.signal.aborted) setConnection('unavailable')
      })
      .finally(() => window.clearTimeout(timeout))

    return () => {
      controller.abort()
      window.clearTimeout(timeout)
    }
  }, [])

  const connectionText = {
    checking: 'Comprobando conexión con la API…',
    connected: 'API conectada',
    unavailable: 'API sin conexión. Inicia el backend y recarga esta página.',
  }[connection]

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="brand-icon" aria-hidden="true">{'</>'}</span>
        <span>Generador y Validador de Horarios Universitarios</span>
        <span className="version">.hor v0.2</span>
      </header>
      <main>
        <section className="foundation" aria-labelledby="foundation-title">
          <p className="eyebrow">Etapa 4 · Sintaxis y AST</p>
          <h1 id="foundation-title">El analizador sintáctico está listo.</h1>
          <p>
            Los tokens y el árbol ya se pueden inspeccionar desde la terminal. Aquí se
            incorporarán el editor y las vistas de resultados en la etapa de interfaz.
          </p>
          <div className={`connection connection--${connection}`} role="status">
            <span className="status-dot" aria-hidden="true" />
            {connectionText}
          </div>
          <p className="next-step">Siguiente etapa: semántica y API de análisis.</p>
        </section>
      </main>
      <footer>Proyecto académico de Compiladores · Desarrollo por etapas</footer>
    </div>
  )
}
