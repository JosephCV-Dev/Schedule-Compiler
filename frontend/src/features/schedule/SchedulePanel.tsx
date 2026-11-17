import { useMemo, useState } from 'react'
import { CalendarDays, List, Info, Clock3 } from 'lucide-react'
import type {
  AnalysisResponse,
  AstNodeResponse,
  OriginResponse,
  SessionResponse,
} from '../../api/types'
import { fieldText } from '../../components/ui'
import { placeSessions } from './layout'

const weekdays = [
  'LUNES',
  'MARTES',
  'MIERCOLES',
  'JUEVES',
  'VIERNES',
  'SABADO',
  'DOMINGO',
]
const dayLabels: Record<string, string> = {
  LUNES: 'Lunes',
  MARTES: 'Martes',
  MIERCOLES: 'Miércoles',
  JUEVES: 'Jueves',
  VIERNES: 'Viernes',
  SABADO: 'Sábado',
  DOMINGO: 'Domingo',
}
export function time(minutes: number) {
  return `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`
}

function enrollmentOrigin(
  node: AstNodeResponse | null,
  id: string,
  source: string,
): OriginResponse | null {
  if (!node) return null
  if (
    node.kind === 'EnrollmentDeclaration' &&
    node.children?.some((child) => child.value === id)
  )
    return {
      kind: 'TEXTO',
      source_id: source,
      span: node.span,
      sheet: null,
      cells: [],
      pointer: null,
    }
  for (const child of node.children ?? []) {
    const origin = enrollmentOrigin(child, id, source)
    if (origin) return origin
  }
  return null
}

export function SchedulePanel({
  result,
  onNavigate,
}: {
  result: AnalysisResponse
  onNavigate: (origin: OriginResponse) => void
}) {
  const [selected, setSelected] = useState(0)
  const [mode, setMode] = useState<'week' | 'list'>('week')
  const schedule = result.schedules[selected] ?? result.schedules[0]
  const names = useMemo(
    () =>
      new Map(
        result.symbols
          .filter((s) => s.kind === 'OFERTA')
          .map((s) => [
            s.attributes.find((a) => a.name === 'identificador')?.value.value,
            s.label,
          ]),
      ),
    [result.symbols],
  )
  const sessions = schedule?.sessions ?? []
  const ids = Array.from(new Set(sessions.map((s) => s.offer_id)))
  const days = sessions.some((s) => s.day === 'SABADO' || s.day === 'DOMINGO')
    ? weekdays
    : weekdays.slice(0, 5)
  const firstHour = sessions.length
    ? Math.max(
        0,
        Math.floor(
          Math.min(...sessions.map((s) => s.interval.start_minute)) / 60,
        ) - 1,
      )
    : 8
  const lastHour = sessions.length
    ? Math.min(
        24,
        Math.ceil(
          Math.max(...sessions.map((s) => s.interval.end_minute)) / 60,
        ) + 1,
      )
    : 18
  const hours = Array.from(
    { length: lastHour - firstHour + 1 },
    (_, i) => firstHour + i,
  )
  function locate(session: SessionResponse) {
    const origin =
      session.origins.find((o) => o.kind === 'TEXTO') ??
      enrollmentOrigin(
        result.ast,
        session.offer_id,
        result.metadata.source_name,
      ) ??
      session.origins[0]
    if (origin) onNavigate(origin)
  }
  const duration =
    sessions.reduce(
      (sum, s) => sum + s.interval.end_minute - s.interval.start_minute,
      0,
    ) / 60
  return (
    <div className="panel-content schedule-panel">
      <div className="panel-tools">
        <label className="compact-label">
          Horario
          <select
            aria-label="Seleccionar horario"
            value={selected}
            onChange={(e) => setSelected(Number(e.target.value))}
          >
            {result.schedules.map((s, i) => (
              <option key={i} value={i}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <div className="segmented">
          <button
            aria-label="Vista semanal"
            aria-pressed={mode === 'week'}
            onClick={() => setMode('week')}
          >
            <CalendarDays size={14} />
            Semana
          </button>
          <button
            aria-label="Vista de lista"
            aria-pressed={mode === 'list'}
            onClick={() => setMode('list')}
          >
            <List size={14} />
            Lista
          </button>
        </div>
      </div>
      {result.status !== 'VALIDO' && (
        <p className="inline-note">
          <Info size={15} />
          Horario parcial: consulta los diagnósticos y las asignaciones
          pendientes.
        </p>
      )}
      {mode === 'week' ? (
        <div className="calendar-scroll">
          <div
            className="calendar"
            style={{ minWidth: days.length * 112 + 50 }}
          >
            <div
              className="calendar-head"
              style={{
                gridTemplateColumns: `50px repeat(${days.length}, 1fr)`,
              }}
            >
              <span className="clock-label">
                <Clock3 size={13} />
              </span>
              {days.map((day) => (
                <strong key={day}>{dayLabels[day]}</strong>
              ))}
            </div>
            <div
              className="calendar-body"
              style={{
                gridTemplateColumns: `50px repeat(${days.length}, 1fr)`,
                height: (lastHour - firstHour) * 56,
              }}
            >
              <div className="time-track">
                {hours.map((hour) => (
                  <span key={hour} style={{ top: (hour - firstHour) * 56 }}>
                    {time(hour * 60)}
                  </span>
                ))}
              </div>
              {days.map((day) => (
                <div className="day-track" key={day}>
                  {placeSessions(sessions.filter((s) => s.day === day)).map(
                    ({ session, lane, lanes }) => (
                      <button
                        className={`class-block course-${ids.indexOf(session.offer_id) % 6} ${session.interval.end_minute - session.interval.start_minute <= 60 ? 'is-short' : ''} ${session.room.value === null ? 'is-pending' : ''}`}
                        key={session.id}
                        onClick={() => locate(session)}
                        title={`${names.get(session.offer_id) || session.offer_id} · ${time(session.interval.start_minute)}–${time(session.interval.end_minute)} · ${fieldText(session.room)}`}
                        style={{
                          top:
                            ((session.interval.start_minute - firstHour * 60) /
                              60) *
                              56 +
                            3,
                          height:
                            ((session.interval.end_minute -
                              session.interval.start_minute) /
                              60) *
                              56 -
                            6,
                          left: `calc(${(lane * 100) / lanes}% + 3px)`,
                          width: `calc(${100 / lanes}% - 6px)`,
                        }}
                      >
                        <small>
                          {time(session.interval.start_minute)}–
                          {time(session.interval.end_minute)}
                        </small>
                        <strong>
                          {names.get(session.offer_id) || session.offer_id}
                        </strong>
                        <span>{fieldText(session.room)}</span>
                      </button>
                    ),
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Día</th>
                <th>Hora</th>
                <th>Materia</th>
                <th>Aula</th>
              </tr>
            </thead>
            <tbody>
              {[...sessions]
                .sort(
                  (a, b) =>
                    weekdays.indexOf(a.day) - weekdays.indexOf(b.day) ||
                    a.interval.start_minute - b.interval.start_minute,
                )
                .map((s) => (
                  <tr key={s.id}>
                    <td>{dayLabels[s.day]}</td>
                    <td className="nowrap">
                      {time(s.interval.start_minute)}–
                      {time(s.interval.end_minute)}
                    </td>
                    <td>
                      <button className="code-link" onClick={() => locate(s)}>
                        {names.get(s.offer_id) || s.offer_id}
                      </button>
                    </td>
                    <td>{fieldText(s.room)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="schedule-summary">
        <span>
          {ids.length} materias · {sessions.length} sesiones
        </span>
        <strong>{duration} horas semanales</strong>
        <span>Según catálogo y política actuales</span>
      </div>
    </div>
  )
}
