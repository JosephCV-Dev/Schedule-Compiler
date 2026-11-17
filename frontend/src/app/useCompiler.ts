import { useCallback, useEffect, useRef, useState } from 'react'
import {
  analyzeSource,
  getCatalogs,
  getExample,
  getExamples,
} from '../api/client'
import type {
  AnalysisRequest,
  AnalysisResponse,
  CatalogList,
  ExampleList,
  OriginResponse,
} from '../api/types'
import type { ConsoleEntry } from '../features/analysis/Console'
import type { ResultTab } from '../features/analysis/ResultsPanel'
import { normalizeText } from '../features/editor/positions'
import initialSource from '../../../examples/oferta_compiladores.hor?raw'

export type Scope = NonNullable<AnalysisRequest['scope']>
export type CatalogId = NonNullable<AnalysisRequest['catalog_id']>
interface Draft {
  source: string
  sourceName: string
  scope: Scope
  catalogId: CatalogId
}
interface Snapshot {
  result: AnalysisResponse
  draft: Draft
  id: number
}
const storageKey = 'schedule-compiler:draft:v1'
const time = () =>
  new Intl.DateTimeFormat('es-MX', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: 'America/Mexico_City',
  }).format(new Date())
function restoreDraft(): Draft {
  try {
    const draft = JSON.parse(localStorage.getItem(storageKey) ?? 'null')
    if (
      draft?.version === 1 &&
      typeof draft.source === 'string' &&
      typeof draft.sourceName === 'string' &&
      draft.sourceName.length &&
      ['PERSONAL', 'PROPUESTA'].includes(draft.scope) &&
      ['isc-26-1-trabajo', 'isc-26-1-original'].includes(draft.catalogId)
    )
      return {
        source: normalizeText(draft.source),
        sourceName: draft.sourceName,
        scope: draft.scope,
        catalogId: draft.catalogId,
      }
  } catch {
    /* El editor también funciona sin almacenamiento local. */
  }
  return {
    source: normalizeText(initialSource.replace(/^#.*\n/gm, '').trimStart()),
    sourceName: 'oferta_compiladores.hor',
    scope: 'PROPUESTA',
    catalogId: 'isc-26-1-trabajo',
  }
}
function errorText(error: unknown) {
  return error instanceof Error ? error.message : 'Ocurrió un error inesperado.'
}

export function useCompiler() {
  const [draft, setDraft] = useState<Draft>(restoreDraft)
  const draftRef = useRef(draft)
  draftRef.current = draft
  const revision = useRef(0)
  const [saved, setSaved] = useState(true)
  const [connection, setConnection] = useState<
    'checking' | 'connected' | 'unavailable'
  >('checking')
  const [catalogs, setCatalogs] = useState<CatalogList>([])
  const [examples, setExamples] = useState<ExampleList>([])
  const [example, setExample] = useState('carolina')
  const [loadingExample, setLoadingExample] = useState(false)
  const [busy, setBusy] = useState(false)
  const busyRef = useRef(false)
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null)
  const [tab, setTab] = useState<ResultTab>('tokens')
  const [notice, setNotice] = useState<string | null>(null)
  const [logs, setLogs] = useState<ConsoleEntry[]>([
    {
      id: 0,
      time: time(),
      level: 'INFO',
      message:
        'Editor listo. Escribe, carga un .hor o elige un ejemplo para comenzar.',
    },
  ])
  const nextLog = useRef(1)
  const resourcesAbort = useRef<AbortController | null>(null)
  const compileAbort = useRef<AbortController | null>(null)
  const loadAbort = useRef<AbortController | null>(null)
  const requestSequence = useRef(0)
  const loadSequence = useRef(0)
  const storageWarning = useRef(false)
  const addLog = useCallback(
    (
      level: ConsoleEntry['level'],
      message: string,
      origin?: OriginResponse | null,
    ) => {
      const entry = {
        id: nextLog.current++,
        time: time(),
        level,
        message,
        origin,
      }
      setLogs((previous) => [...previous.slice(-299), entry])
    },
    [],
  )
  const updateDraft = useCallback((patch: Partial<Draft>) => {
    const next = { ...draftRef.current, ...patch }
    draftRef.current = next
    revision.current += 1
    setDraft(next)
  }, [])
  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify({ version: 1, ...draft }))
      setSaved(true)
    } catch {
      setSaved(false)
      if (!storageWarning.current) {
        storageWarning.current = true
        addLog(
          'ADVERTENCIA',
          'No se pudo guardar el borrador local. Puedes descargar el archivo .hor.',
        )
      }
    }
  }, [draft, addLog])
  const refreshResources = useCallback(async () => {
    resourcesAbort.current?.abort()
    const controller = new AbortController()
    resourcesAbort.current = controller
    let timeout = false
    const timer = window.setTimeout(() => {
      timeout = true
      controller.abort()
    }, 8000)
    setConnection('checking')
    try {
      const [catalogList, exampleList] = await Promise.all([
        getCatalogs(controller.signal),
        getExamples(controller.signal),
      ])
      if (controller.signal.aborted) return
      setCatalogs(catalogList)
      setExamples(exampleList)
      setConnection('connected')
    } catch (error) {
      if (controller.signal.aborted && !timeout) return
      setConnection('unavailable')
      addLog(
        'ADVERTENCIA',
        timeout
          ? 'La API no respondió a tiempo. Puedes reintentar la conexión.'
          : `No se pudo conectar con la API. ${errorText(error)}`,
      )
    } finally {
      window.clearTimeout(timer)
    }
  }, [addLog])
  useEffect(() => {
    void refreshResources()
    return () => {
      resourcesAbort.current?.abort()
      compileAbort.current?.abort()
      loadAbort.current?.abort()
    }
  }, [refreshResources])
  const cancelCompilation = useCallback(() => {
    requestSequence.current += 1
    compileAbort.current?.abort()
    busyRef.current = false
    setBusy(false)
  }, [])
  const compile = useCallback(async () => {
    if (busyRef.current) return
    const input = { ...draftRef.current }
    const sequence = ++requestSequence.current
    const controller = new AbortController()
    compileAbort.current?.abort()
    compileAbort.current = controller
    let timeout = false
    const timer = window.setTimeout(() => {
      timeout = true
      controller.abort()
    }, 15000)
    busyRef.current = true
    setBusy(true)
    setSnapshot(null)
    setNotice(null)
    addLog(
      'INFO',
      `Analizando ${input.sourceName} · ${input.scope === 'PERSONAL' ? 'Horario personal' : 'Propuesta de clases'}…`,
    )
    try {
      const result = await analyzeSource(
        {
          source: input.source,
          source_name: input.sourceName,
          scope: input.scope,
          catalog_id: input.catalogId,
          language_version: '0.2',
          policy_id: 'proyecto-v0.2',
        },
        controller.signal,
      )
      if (sequence !== requestSequence.current || controller.signal.aborted)
        return
      setSnapshot({ result, draft: input, id: sequence })
      setConnection('connected')
      const stages = {
        LEXICO: 'Análisis léxico',
        SINTACTICO: 'Análisis sintáctico',
        SEMANTICO: 'Análisis semántico',
      }
      const states = {
        COMPLETADA: 'completado',
        CON_ERRORES: 'con errores',
        NO_EJECUTADA: 'no ejecutado',
      }
      result.phases.forEach((phase) =>
        addLog('INFO', `${stages[phase.stage]} ${states[phase.state]}.`),
      )
      result.diagnostics.forEach((diagnostic) =>
        addLog(diagnostic.severity, diagnostic.message, diagnostic.origin),
      )
      addLog(
        'INFO',
        `Análisis finalizado: ${result.status === 'VALIDO' ? 'válido' : result.status === 'INVALIDO' ? 'inválido' : 'incompleto'} según catálogo y política actuales.`,
      )
      if (result.diagnostics.length) setTab('diagnostics')
    } catch (error) {
      if (
        sequence !== requestSequence.current ||
        (controller.signal.aborted && !timeout)
      )
        return
      const message = timeout
        ? 'El análisis superó el tiempo de espera. El código sigue en el editor; vuelve a intentarlo.'
        : `No se pudo completar el análisis. ${errorText(error)}`
      setNotice(message)
      addLog('ERROR', message)
    } finally {
      window.clearTimeout(timer)
      if (sequence === requestSequence.current) {
        busyRef.current = false
        setBusy(false)
      }
    }
  }, [addLog])
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if (
        (event.ctrlKey || event.metaKey) &&
        event.key === 'Enter' &&
        !event.defaultPrevented
      ) {
        event.preventDefault()
        void compile()
      }
    }
    window.addEventListener('keydown', shortcut)
    return () => window.removeEventListener('keydown', shortcut)
  }, [compile])
  async function loadExample() {
    const sequence = ++loadSequence.current
    const before = revision.current
    loadAbort.current?.abort()
    const controller = new AbortController()
    loadAbort.current = controller
    const timer = window.setTimeout(() => controller.abort(), 10000)
    setLoadingExample(true)
    setNotice(null)
    try {
      const data = await getExample(example, controller.signal)
      if (sequence !== loadSequence.current) return
      if (before !== revision.current) {
        addLog(
          'ADVERTENCIA',
          'El texto cambió mientras se cargaba el ejemplo; se conservó tu edición.',
        )
        return
      }
      cancelCompilation()
      updateDraft({
        source: normalizeText(data.source),
        sourceName: data.source_name,
        scope: data.scope,
      })
      setSnapshot(null)
      setTab('tokens')
      addLog('INFO', `Ejemplo cargado: ${data.title}. Listo para compilar.`)
    } catch (error) {
      if (sequence === loadSequence.current) {
        const message = controller.signal.aborted
          ? 'No se pudo cargar el ejemplo a tiempo.'
          : errorText(error)
        setNotice(message)
        addLog('ERROR', message)
      }
    } finally {
      window.clearTimeout(timer)
      if (sequence === loadSequence.current) setLoadingExample(false)
    }
  }
  async function loadFile(file?: File) {
    if (!file) return
    const sequence = ++loadSequence.current
    const before = revision.current
    loadAbort.current?.abort()
    setLoadingExample(false)
    if (!file.name.toLowerCase().endsWith('.hor')) {
      setNotice(
        'Selecciona un archivo con extensión .hor. El código actual se conserva.',
      )
      return
    }
    try {
      const source = normalizeText(
        new TextDecoder('utf-8', { fatal: true }).decode(
          await file.arrayBuffer(),
        ),
      )
      if (sequence !== loadSequence.current) return
      if (before !== revision.current) {
        addLog(
          'ADVERTENCIA',
          'El texto cambió durante la lectura del archivo; se conservó tu edición.',
        )
        return
      }
      cancelCompilation()
      updateDraft({ source, sourceName: file.name })
      setSnapshot(null)
      setNotice(null)
      setTab('tokens')
      addLog(
        'INFO',
        `Archivo cargado: ${file.name}. Revisa el modo y pulsa Compilar.`,
      )
    } catch {
      if (sequence !== loadSequence.current) return
      const message =
        'No se pudo leer el archivo como UTF-8. El código actual se conserva.'
      setNotice(message)
      addLog('ERROR', message)
    }
  }
  function clear() {
    cancelCompilation()
    loadSequence.current += 1
    loadAbort.current?.abort()
    setLoadingExample(false)
    updateDraft({ source: '', sourceName: 'nuevo.hor' })
    setSnapshot(null)
    setNotice(null)
    setTab('tokens')
    setLogs([])
    addLog('INFO', 'Editor y resultados limpiados.')
  }
  const stale =
    !!snapshot &&
    (snapshot.draft.source !== draft.source ||
      snapshot.draft.sourceName !== draft.sourceName ||
      snapshot.draft.scope !== draft.scope ||
      snapshot.draft.catalogId !== draft.catalogId)
  return {
    draft,
    saved,
    connection,
    catalogs,
    examples,
    example,
    setExample,
    loadingExample,
    busy,
    snapshot,
    tab,
    setTab,
    notice,
    setNotice,
    logs,
    setLogs,
    addLog,
    updateDraft,
    refreshResources,
    compile,
    loadExample,
    loadFile,
    clear,
    stale,
  }
}
