import { lazy, Suspense, useRef } from 'react'
import {
  CalendarDays,
  Database,
  Download,
  GitBranch,
  Layers,
  TriangleAlert,
} from 'lucide-react'
import type { AnalysisResponse, OriginResponse } from '../../api/types'
import { Badge, EmptyState } from '../../components/ui'
import { TokensPanel } from './TokensPanel'
import { SymbolsPanel } from './SymbolsPanel'
import { DiagnosticsPanel } from './DiagnosticsPanel'
import { SchedulePanel } from '../schedule/SchedulePanel'

const AstTree = lazy(() => import('./AstTree'))
export type ResultTab =
  'tokens' | 'tree' | 'symbols' | 'diagnostics' | 'schedule'
const tabs = [
  { id: 'tokens', label: 'Tokens', icon: Layers },
  { id: 'tree', label: 'Árbol sintáctico', icon: GitBranch },
  { id: 'symbols', label: 'Tabla de símbolos', icon: Database },
  { id: 'diagnostics', label: 'Errores y advertencias', icon: TriangleAlert },
  { id: 'schedule', label: 'Horario resultante', icon: CalendarDays },
] as const
export function ResultsPanel({
  result,
  tab,
  onTab,
  onNavigate,
  busy,
  stale,
  onExport,
}: {
  result: AnalysisResponse | null
  tab: ResultTab
  onTab: (tab: ResultTab) => void
  onNavigate: (origin: OriginResponse) => void
  busy: boolean
  stale: boolean
  onExport: () => void
}) {
  const buttons = useRef<(HTMLButtonElement | null)[]>([])
  const navigation = { result: result!, onNavigate }
  return (
    <section
      className="results-panel panel"
      aria-label="Resultados del compilador"
    >
      <div
        className="result-tabs"
        role="tablist"
        aria-label="Salidas del compilador"
      >
        {tabs.map((item, index) => (
          <button
            key={item.id}
            ref={(node) => {
              buttons.current[index] = node
            }}
            role="tab"
            id={`tab-${item.id}`}
            aria-selected={tab === item.id}
            aria-controls={`panel-${item.id}`}
            tabIndex={tab === item.id ? 0 : -1}
            onClick={() => onTab(item.id)}
            onKeyDown={(event) => {
              const next =
                event.key === 'ArrowRight'
                  ? (index + 1) % tabs.length
                  : event.key === 'ArrowLeft'
                    ? (index + tabs.length - 1) % tabs.length
                    : event.key === 'Home'
                      ? 0
                      : event.key === 'End'
                        ? tabs.length - 1
                        : -1
              if (next >= 0) {
                event.preventDefault()
                onTab(tabs[next].id)
                buttons.current[next]?.focus()
              }
            }}
          >
            <item.icon size={16} />
            <span>{item.label}</span>
            {item.id === 'diagnostics' && !!result?.diagnostics.length && (
              <b>{result.diagnostics.length}</b>
            )}
          </button>
        ))}
      </div>
      <div className="result-meta">
        <span>
          {busy
            ? 'Analizando entrada…'
            : result
              ? 'Resultado del análisis'
              : 'Esperando compilación'}
          {stale && <span className="stale-label"> · versión anterior</span>}
        </span>
        <div className="result-meta-actions">
          {result && (
            <>
              <Badge value={result.status} />
              <button
                className="icon-button"
                disabled={stale || busy}
                title={
                  stale
                    ? 'Vuelve a compilar antes de exportar'
                    : 'Descargar resultado JSON'
                }
                aria-label="Descargar resultado JSON"
                onClick={onExport}
              >
                <Download size={14} />
              </button>
            </>
          )}
        </div>
      </div>
      {stale && (
        <div className="stale-banner" role="status">
          La entrada o las opciones cambiaron. Vuelve a compilar para actualizar
          los resultados.
        </div>
      )}
      <div
        className="result-view"
        role="tabpanel"
        id={`panel-${tab}`}
        aria-labelledby={`tab-${tab}`}
        aria-busy={busy}
      >
        {!result ? (
          <EmptyState
            title={
              busy ? 'Analizando tu horario' : 'Todo empieza con tu código'
            }
            detail={
              busy
                ? 'Esperando el resultado de las tres fases…'
                : 'Escribe un horario o carga un ejemplo. Pulsa Compilar para ver los resultados reales.'
            }
          />
        ) : tab === 'tokens' ? (
          <TokensPanel {...navigation} />
        ) : tab === 'symbols' ? (
          <SymbolsPanel {...navigation} />
        ) : tab === 'diagnostics' ? (
          <DiagnosticsPanel {...navigation} />
        ) : tab === 'schedule' ? (
          result.schedules.length ? (
            <SchedulePanel {...navigation} />
          ) : (
            <EmptyState
              title="No hay horario resultante"
              detail="Corrige los errores del análisis o selecciona ofertas en un bloque HORARIO."
            />
          )
        ) : result.ast ? (
          <Suspense
            fallback={
              <EmptyState
                title="Preparando árbol"
                detail="Cargando el visor de nodos y ramas…"
              />
            }
          >
            <AstTree
              root={result.ast}
              onNavigate={(span) =>
                onNavigate({
                  kind: 'TEXTO',
                  source_id: result.metadata.source_name,
                  span,
                  cells: [],
                  sheet: null,
                  pointer: null,
                })
              }
            />
          </Suspense>
        ) : (
          <EmptyState
            icon={<GitBranch size={28} />}
            title="No se pudo construir el árbol"
            detail="Corrige los errores léxicos o sintácticos y vuelve a compilar."
          />
        )}
      </div>
    </section>
  )
}
