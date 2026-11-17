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
          <p className="eyebrow">Etapa 1 · Estructura inicial</p>
          <h1 id="foundation-title">La base del proyecto está lista.</h1>
          <p>
            Este espacio se convertirá en el editor de horarios. El análisis
            léxico, sintáctico y semántico se construirá en las siguientes etapas.
          </p>
          <div className={`connection connection--${connection}`} role="status">
            <span className="status-dot" aria-hidden="true" />
            {connectionText}
          </div>
          <p className="next-step">Siguiente etapa: modelos y contrato del análisis.</p>
        </section>
      </main>
      <footer>Proyecto académico de Compiladores · Desarrollo por etapas</footer>
    </div>
  )
}
