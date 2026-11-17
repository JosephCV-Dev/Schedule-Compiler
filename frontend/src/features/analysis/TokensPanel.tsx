import { useMemo, useState } from 'react'
import { Search } from 'lucide-react'
import type { AnalysisResponse, OriginResponse } from '../../api/types'

export function TokensPanel({
  result,
  onNavigate,
}: {
  result: AnalysisResponse
  onNavigate: (origin: OriginResponse) => void
}) {
  const [search, setSearch] = useState('')
  const patterns = useMemo(
    () => new Map(result.patterns.map((p) => [p.id, p])),
    [result.patterns],
  )
  const tokens = result.tokens.filter((t) =>
    `${t.kind} ${t.lexeme}`.toLowerCase().includes(search.toLowerCase()),
  )
  return (
    <div className="panel-content">
      <div className="panel-tools">
        <label className="search-box">
          <Search size={14} />
          <input
            aria-label="Buscar tokens"
            placeholder="Buscar token o lexema…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <span className="muted small">
          {tokens.length} de {result.tokens.length} tokens
        </span>
      </div>
      <div className="table-scroll">
        <table className="data-table token-table">
          <thead>
            <tr>
              <th>Token</th>
              <th>Lexema</th>
              <th>Patrón</th>
              <th>Línea</th>
              <th>Col.</th>
            </tr>
          </thead>
          <tbody>
            {tokens.map((token, i) => (
              <tr key={`${token.span.start.offset}-${i}`}>
                <td>
                  <span
                    className={`token-kind ${token.kind.startsWith('KW_') ? 'keyword' : token.kind.toLowerCase()}`}
                  >
                    {token.kind}
                  </span>
                </td>
                <td>
                  <button
                    className="code-link"
                    onClick={() =>
                      onNavigate({
                        kind: 'TEXTO',
                        source_id: result.metadata.source_name,
                        span: token.span,
                        sheet: null,
                        cells: [],
                        pointer: null,
                      })
                    }
                    title="Ubicar token en el editor"
                  >
                    {token.lexeme}
                  </button>
                </td>
                <td className="pattern-cell">
                  <code
                    title={`${patterns.get(token.pattern_id)?.expression ?? token.pattern_id}\n${patterns.get(token.pattern_id)?.description ?? ''}`}
                  >
                    {patterns.get(token.pattern_id)?.expression ??
                      token.pattern_id}
                  </code>
                </td>
                <td>{token.span.start.line}</td>
                <td>{token.span.start.column}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!tokens.length && (
          <p className="table-empty">
            No hay tokens que coincidan con la búsqueda.
          </p>
        )}
      </div>
    </div>
  )
}
