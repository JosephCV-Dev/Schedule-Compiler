import { useState } from 'react'
import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react'
import type { AnalysisResponse, OriginResponse } from '../../api/types'
import { Badge, OriginLink } from '../../components/ui'

export function DiagnosticsPanel({
  result,
  onNavigate,
}: {
  result: AnalysisResponse
  onNavigate: (origin: OriginResponse) => void
}) {
  const [view, setView] = useState<'input' | 'catalog' | 'checks'>('input')
  const [severity, setSeverity] = useState('TODAS')
  const diagnostics = (
    view === 'catalog' ? result.catalog_diagnostics : result.diagnostics
  ).filter((d) => severity === 'TODAS' || d.severity === severity)
  return (
    <div className="panel-content diagnostics-panel">
      <div className="panel-tools">
        <div className="segmented" aria-label="Vista de diagnósticos">
          <button
            aria-pressed={view === 'input'}
            onClick={() => setView('input')}
          >
            Entrada <span>{result.diagnostics.length}</span>
          </button>
          <button
            aria-pressed={view === 'catalog'}
            onClick={() => setView('catalog')}
          >
            Catálogo <span>{result.catalog_diagnostics.length}</span>
          </button>
          <button
            aria-pressed={view === 'checks'}
            onClick={() => setView('checks')}
          >
            Reglas <span>{result.checks.length}</span>
          </button>
        </div>
        {view !== 'checks' && (
          <select
            aria-label="Filtrar diagnósticos"
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
          >
            <option value="TODAS">Todas las severidades</option>
            <option value="ERROR">Errores</option>
            <option value="ADVERTENCIA">Advertencias</option>
            <option value="INFO">Información</option>
          </select>
        )}
      </div>
      {view === 'checks' ? (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Regla</th>
                <th>Estado</th>
                <th>Alcance</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              {result.checks.map((check, i) => (
                <tr key={`${check.code}-${i}`}>
                  <td>
                    <code>{check.code}</code>
                  </td>
                  <td>
                    <Badge value={check.state} />
                  </td>
                  <td className="muted">
                    {check.required ? 'Requerida' : 'Informativa'}
                  </td>
                  <td>{check.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="diagnostic-list">
          {view === 'catalog' && (
            <p className="inline-note">
              <Info size={15} />
              Estos hallazgos pertenecen al catálogo. Se muestran separados del
              resultado de tu horario.
            </p>
          )}
          {!diagnostics.length && (
            <div className="diagnostic-clear">
              <CheckCircle2 size={28} />
              <h3>Sin diagnósticos en esta vista</h3>
              <p>
                {result.status === 'VALIDO'
                  ? 'Las reglas requeridas del alcance actual se cumplen.'
                  : 'Consulta las otras vistas y las comprobaciones del análisis.'}
              </p>
            </div>
          )}
          {diagnostics.map((d, i) => (
            <article
              className={`diagnostic-card severity-${d.severity.toLowerCase()}`}
              key={`${d.code}-${i}`}
            >
              <div className="diagnostic-title">
                {d.severity === 'ERROR' ? (
                  <XCircle size={17} />
                ) : d.severity === 'ADVERTENCIA' ? (
                  <AlertTriangle size={17} />
                ) : (
                  <Info size={17} />
                )}
                <strong>{d.code}</strong>
                <span className="diagnostic-stage">{d.stage}</span>
              </div>
              <p>{d.message}</p>
              <div className="diagnostic-origin">
                <OriginLink origin={d.origin} onNavigate={onNavigate} />
                <span className="muted small">{d.origin?.source_id}</span>
              </div>
              {!!d.related.length && (
                <details>
                  <summary>
                    Ubicaciones relacionadas ({d.related.length})
                  </summary>
                  <div className="related-origins">
                    {d.related.map((o, index) => (
                      <div key={index}>
                        <OriginLink origin={o} onNavigate={onNavigate} />
                        <span className="muted small">{o.source_id}</span>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
