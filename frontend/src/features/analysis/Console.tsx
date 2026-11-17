import { useEffect, useRef, useState } from 'react'
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Info,
  Terminal,
  Trash2,
  XCircle,
} from 'lucide-react'
import type { OriginResponse } from '../../api/types'
import { OriginLink } from '../../components/ui'

export interface ConsoleEntry {
  id: number
  time: string
  level: 'INFO' | 'ERROR' | 'ADVERTENCIA'
  message: string
  origin?: OriginResponse | null
}
export function Console({
  entries,
  onClear,
  onNavigate,
}: {
  entries: ConsoleEntry[]
  onClear: () => void
  onNavigate: (origin: OriginResponse) => void
}) {
  const [collapsed, setCollapsed] = useState(false)
  const [filter, setFilter] = useState('TODOS')
  const output = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (output.current) output.current.scrollTop = output.current.scrollHeight
  }, [entries, filter, collapsed])
  const count = (level: string) =>
    entries.filter((entry) => entry.level === level).length
  return (
    <section
      className={`console-panel ${collapsed ? 'is-collapsed' : ''}`}
      aria-label="Consola de compilación"
    >
      <header className="console-header">
        <Terminal size={16} />
        <strong>Consola</strong>
        <span className="console-subtitle">Proceso de compilación</span>
        <div className="header-actions">
          <button
            className="icon-button"
            title="Limpiar consola"
            aria-label="Limpiar consola"
            onClick={onClear}
          >
            <Trash2 size={14} />
          </button>
          <button
            className="icon-button"
            aria-label={collapsed ? 'Expandir consola' : 'Contraer consola'}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </header>
      {!collapsed && (
        <>
          <div className="console-filters">
            <button
              aria-pressed={filter === 'TODOS'}
              onClick={() => setFilter('TODOS')}
            >
              Mensajes
            </button>
            <button
              aria-pressed={filter === 'ERROR'}
              onClick={() => setFilter('ERROR')}
            >
              Errores <span>{count('ERROR')}</span>
            </button>
            <button
              aria-pressed={filter === 'ADVERTENCIA'}
              onClick={() => setFilter('ADVERTENCIA')}
            >
              Advertencias <span>{count('ADVERTENCIA')}</span>
            </button>
          </div>
          <div
            className="console-output"
            ref={output}
            role="log"
            aria-live="polite"
          >
            {entries
              .filter((entry) => filter === 'TODOS' || entry.level === filter)
              .map((entry) => (
                <div
                  className={`log-entry log-${entry.level.toLowerCase()}`}
                  key={entry.id}
                >
                  <time>{entry.time}</time>
                  {entry.level === 'ERROR' ? (
                    <XCircle size={14} />
                  ) : entry.level === 'ADVERTENCIA' ? (
                    <AlertTriangle size={14} />
                  ) : (
                    <Info size={14} />
                  )}
                  <span>{entry.message}</span>
                  {entry.origin && (
                    <OriginLink origin={entry.origin} onNavigate={onNavigate} />
                  )}
                </div>
              ))}
            {!entries.length && (
              <p className="muted small">La consola está vacía.</p>
            )}
          </div>
        </>
      )}
    </section>
  )
}
