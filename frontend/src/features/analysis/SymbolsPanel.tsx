import { useState } from 'react'
import { Search } from 'lucide-react'
import type { AnalysisResponse, OriginResponse } from '../../api/types'
import { fieldText, OriginLink } from '../../components/ui'

export function SymbolsPanel({
  result,
  onNavigate,
}: {
  result: AnalysisResponse
  onNavigate: (origin: OriginResponse) => void
}) {
  const [search, setSearch] = useState('')
  const [kind, setKind] = useState('TODOS')
  const symbols = result.symbols.filter(
    (s) =>
      (kind === 'TODOS' || kind === s.kind) &&
      `${s.id} ${s.label}`.toLowerCase().includes(search.toLowerCase()),
  )
  return (
    <div className="panel-content">
      <div className="panel-tools">
        <label className="search-box">
          <Search size={14} />
          <input
            aria-label="Buscar símbolos"
            placeholder="Buscar símbolo…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <select
          aria-label="Tipo de símbolo"
          value={kind}
          onChange={(e) => setKind(e.target.value)}
        >
          <option value="TODOS">Todos los tipos</option>
          {Array.from(new Set(result.symbols.map((s) => s.kind))).map((k) => (
            <option key={k}>{k}</option>
          ))}
        </select>
      </div>
      <div className="table-scroll">
        <table className="data-table symbol-table">
          <thead>
            <tr>
              <th>Símbolo</th>
              <th>Tipo</th>
              <th>Atributos</th>
              <th>Origen</th>
            </tr>
          </thead>
          <tbody>
            {symbols.map((symbol) => (
              <tr key={symbol.id}>
                <td>
                  <strong>{symbol.label}</strong>
                  <code className="secondary-code">{symbol.id}</code>
                </td>
                <td>
                  <span className="type-pill">{symbol.kind}</span>
                </td>
                <td>
                  <dl className="attributes">
                    {symbol.attributes.map((a) => (
                      <div key={a.name}>
                        <dt>{a.name.replaceAll('_', ' ')}</dt>
                        <dd className={a.value.value === null ? 'muted' : ''}>
                          {fieldText(a.value)}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </td>
                <td>
                  <OriginLink
                    origin={symbol.origins[0] ?? null}
                    onNavigate={onNavigate}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!symbols.length && (
          <p className="table-empty">
            No hay símbolos disponibles para este filtro.
          </p>
        )}
      </div>
    </div>
  )
}
