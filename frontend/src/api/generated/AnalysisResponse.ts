/* Generado desde contracts/. No editar a mano. */

export type SchemaVersion = '1'
export type LanguageVersion = string
export type CatalogId = string
export type CatalogSha256 = string
export type PolicyId = string
export type PolicyVersion = string
export type Scope = 'PERSONAL' | 'PROPUESTA'
export type SourceName = string
export type AnalysisStatus = 'VALIDO' | 'INVALIDO' | 'INCOMPLETO'
export type Stage = 'LEXICO' | 'SINTACTICO' | 'SEMANTICO'
export type PhaseState = 'COMPLETADA' | 'CON_ERRORES' | 'NO_EJECUTADA'
export type Phases = PhaseResponse[]
export type Id = string
export type Description = string
export type Expression = string
export type Patterns = PatternResponse[]
export type Kind = string
export type Lexeme = string
export type PatternId = string
export type Offset = number
export type Line = number
export type Column = number
export type Tokens = TokenResponse[]
export type Id1 = string
export type Kind1 = string
export type Label = string
export type Value = string | number | null
export type ValueState = 'CONOCIDO' | 'DESCONOCIDO' | 'SIN_ASIGNAR'
export type Children = AstNodeResponse[]
export type Id2 = string
export type Kind2 = string
export type Label1 = string
export type Name = string
export type Value1 = string | null
export type Attributes = SymbolAttributeResponse[]
export type Kind3 = 'TEXTO' | 'EXCEL' | 'JSON'
export type SourceId = string
export type Sheet = string | null
export type Cells = string[]
export type Pointer = string | null
export type Origins = OriginResponse[]
export type Symbols = SymbolResponse[]
export type Code = string
export type Stage1 = string
export type Severity = 'ERROR' | 'ADVERTENCIA' | 'INFO'
export type Message = string
export type Related = OriginResponse[]
export type Diagnostics = DiagnosticResponse[]
export type CatalogDiagnostics = DiagnosticResponse[]
export type Code1 = string
export type CheckState = 'CUMPLE' | 'INCUMPLE' | 'NO_EVALUABLE' | 'NO_APLICA' | 'DESACTIVADA'
export type Required = boolean
export type Message1 = string
export type Origins1 = OriginResponse[]
export type Checks = CheckResponse[]
export type Name1 = string
export type Id3 = string
export type OfferId = string
export type Weekday = 'LUNES' | 'MARTES' | 'MIERCOLES' | 'JUEVES' | 'VIERNES' | 'SABADO' | 'DOMINGO'
export type StartMinute = number
export type EndMinute = number
export type Origins2 = OriginResponse[]
export type Sessions = SessionResponse[]
export type Schedules = ScheduleResponse[]

export interface AnalysisResponse {
  schema_version?: SchemaVersion
  metadata: MetadataResponse
  status: AnalysisStatus
  phases: Phases
  patterns: Patterns
  tokens: Tokens
  ast: AstNodeResponse | null
  symbols: Symbols
  diagnostics: Diagnostics
  catalog_diagnostics: CatalogDiagnostics
  checks: Checks
  schedules: Schedules
}
export interface MetadataResponse {
  language_version: LanguageVersion
  catalog_id: CatalogId
  catalog_sha256: CatalogSha256
  policy_id: PolicyId
  policy_version: PolicyVersion
  scope: Scope
  source_name: SourceName
}
export interface PhaseResponse {
  stage: Stage
  state: PhaseState
}
export interface PatternResponse {
  id: Id
  description: Description
  expression: Expression
}
export interface TokenResponse {
  kind: Kind
  lexeme: Lexeme
  pattern_id: PatternId
  span: SpanResponse
}
export interface SpanResponse {
  start: PositionResponse
  end: PositionResponse
}
export interface PositionResponse {
  offset: Offset
  line: Line
  column: Column
}
export interface AstNodeResponse {
  id: Id1
  kind: Kind1
  label: Label
  value?: Value
  value_state?: ValueState | null
  span: SpanResponse
  children?: Children
}
export interface SymbolResponse {
  id: Id2
  kind: Kind2
  label: Label1
  attributes: Attributes
  origins: Origins
}
export interface SymbolAttributeResponse {
  name: Name
  value: FieldValueResponse
}
export interface FieldValueResponse {
  state: ValueState
  value: Value1
}
export interface OriginResponse {
  kind: Kind3
  source_id: SourceId
  span: SpanResponse | null
  sheet: Sheet
  cells: Cells
  pointer: Pointer
}
export interface DiagnosticResponse {
  code: Code
  stage: Stage1
  severity: Severity
  message: Message
  origin: OriginResponse | null
  related: Related
}
export interface CheckResponse {
  code: Code1
  state: CheckState
  required: Required
  message: Message1
  origins: Origins1
}
export interface ScheduleResponse {
  name: Name1
  sessions: Sessions
}
export interface SessionResponse {
  id: Id3
  offer_id: OfferId
  day: Weekday
  interval: IntervalResponse
  room: FieldValueResponse
  origins: Origins2
}
export interface IntervalResponse {
  start_minute: StartMinute
  end_minute: EndMinute
}
