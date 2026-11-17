import type { ReactNode } from 'react'
import { ArrowUpRight, Braces } from 'lucide-react'
import type { FieldValueResponse, OriginResponse } from '../api/types'

export function EmptyState({
  title,
  detail,
  icon = <Braces size={28} />,
}: {
  title: string
  detail: string
  icon?: ReactNode
}) {
  return (
    <div className="empty-state">
      <span className="empty-icon">{icon}</span>
      <h2>{title}</h2>
      <p>{detail}</p>
    </div>
  )
}

const labels: Record<string, string> = {
  VALIDO: 'Válido',
  INVALIDO: 'Inválido',
  INCOMPLETO: 'Incompleto',
  CUMPLE: 'Cumple',
  INCUMPLE: 'Incumple',
  NO_EVALUABLE: 'No evaluable',
  NO_APLICA: 'No aplica',
  DESACTIVADA: 'Desactivada',
  ERROR: 'Error',
  ADVERTENCIA: 'Advertencia',
  INFO: 'Información',
  CONOCIDO: 'Conocido',
  DESCONOCIDO: 'Desconocido',
  SIN_ASIGNAR: 'Sin asignar',
}
export function label(value: string): string {
  return labels[value] ?? value
}
export function Badge({ value }: { value: string }) {
  return (
    <span className={`badge badge--${value.toLowerCase()}`}>
      {label(value)}
    </span>
  )
}
export function fieldText(field: FieldValueResponse): string {
  return field.value ?? label(field.state)
}
export function originText(origin: OriginResponse): string {
  if (origin.kind === 'TEXTO' && origin.span)
    return `L${origin.span.start.line}:C${origin.span.start.column}`
  if (origin.kind === 'EXCEL')
    return `${origin.sheet} · ${origin.cells.join(', ')}`
  return `${origin.source_id}${origin.pointer ?? ''}`
}
export function OriginLink({
  origin,
  onNavigate,
}: {
  origin: OriginResponse | null
  onNavigate: (origin: OriginResponse) => void
}) {
  if (!origin) return <span className="muted">—</span>
  return (
    <button
      className="origin-link"
      title={`${origin.source_id} · ${originText(origin)}`}
      onClick={() => onNavigate(origin)}
    >
      {originText(origin)}
      <ArrowUpRight size={12} />
    </button>
  )
}
