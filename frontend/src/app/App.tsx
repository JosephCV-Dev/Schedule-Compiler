import { lazy, Suspense, useRef, useState } from 'react'
import {
  BookOpen,
  CheckCircle2,
  Code2,
  Download,
  FileCode2,
  GraduationCap,
  LayoutPanelLeft,
  LoaderCircle,
  Play,
  RefreshCw,
  Trash2,
  Upload,
  X,
} from 'lucide-react'
import type { OriginResponse } from '../api/types'
import { Modal } from '../components/Modal'
import { originText } from '../components/ui'
import { Console } from '../features/analysis/Console'
import { ResultsPanel } from '../features/analysis/ResultsPanel'
import type { EditorHandle } from '../features/editor/SourceEditor'
import { useCompiler } from './useCompiler'
import type { CatalogId, Scope } from './useCompiler'

const SourceEditor = lazy(() =>
  import('../features/editor/SourceEditor').then((module) => ({
    default: module.SourceEditor,
  })),
)

const catalogName = (id: string) =>
  id === 'isc-26-1-original' ? 'Catálogo original' : 'Copia de trabajo'
function download(content: string, name: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = name
  anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function App() {
  const c = useCompiler()
  const editor = useRef<EditorHandle>(null)
  const upload = useRef<HTMLInputElement>(null)
  const resultPanel = useRef<HTMLDivElement>(null)
  const [origin, setOrigin] = useState<OriginResponse | null>(null)
  const [guide, setGuide] = useState(false)
  const [cursor, setCursor] = useState({ line: 1, column: 1 })
  function navigate(location: OriginResponse) {
    if (c.stale) {
      c.setNotice(
        'Los resultados pertenecen a una entrada anterior. Vuelve a compilar para navegar al código.',
      )
      return
    }
    if (
      location.kind === 'TEXTO' &&
      location.span &&
      location.source_id === c.draft.sourceName
    )
      editor.current?.reveal(location.span)
    else setOrigin(location)
  }
  const currentCatalog = c.catalogs.find(
    (catalog) => catalog.id === c.draft.catalogId,
  )
  const catalogs = c.catalogs.length
    ? c.catalogs
    : [{ id: 'isc-26-1-trabajo' }, { id: 'isc-26-1-original' }]
  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="brand-icon">
          <Code2 size={20} />
        </span>
        <div>
          <h1>Generador y Validador de Horarios Universitarios</h1>
          <p>
            Laboratorio de Compiladores <span>·</span> Ingeniería en Sistemas
            Computacionales
          </p>
        </div>
        <span className="language-badge">
          .hor <b>v0.2</b>
        </span>
      </header>
      <aside className="sidebar" aria-label="Navegación principal">
        <button
          className="nav-button is-active"
          onClick={() => editor.current?.focus()}
        >
          <Code2 size={23} />
          <span>Editor</span>
        </button>
        <button
          className="nav-button"
          onClick={() => {
            c.setTab('schedule')
            resultPanel.current?.scrollIntoView({
              block: 'nearest',
              behavior: 'smooth',
            })
          }}
        >
          <LayoutPanelLeft size={21} />
          <span>Resultados</span>
        </button>
        <button
          className="nav-button guide-button"
          onClick={() => setGuide(true)}
        >
          <BookOpen size={20} />
          <span>Guía</span>
        </button>
        <div className="university-mark">
          <GraduationCap size={26} />
          <strong>UACAM</strong>
          <span>Compiladores</span>
        </div>
      </aside>
      <main className="main-workspace">
        <section className="toolbar" aria-label="Acciones de compilación">
          <div className="toolbar-primary">
            <button
              className="button button-primary"
              onClick={() => void c.compile()}
              disabled={c.busy || c.loadingExample}
              title="Compilar (Ctrl/⌘ + Enter)"
            >
              {c.busy ? (
                <LoaderCircle size={16} className="spin" />
              ) : (
                <Play size={16} fill="currentColor" />
              )}
              {c.busy ? 'Compilando…' : 'Compilar'}
            </button>
            <button
              className="button button-secondary"
              onClick={() => upload.current?.click()}
            >
              <Upload size={15} />
              Subir .hor
            </button>
            <input
              ref={upload}
              className="visually-hidden"
              type="file"
              accept=".hor"
              aria-label="Seleccionar archivo .hor"
              onChange={(event) => {
                void c.loadFile(event.target.files?.[0])
                event.target.value = ''
              }}
            />
            <button
              className="button button-quiet"
              onClick={() => {
                c.clear()
                setCursor({ line: 1, column: 1 })
                editor.current?.focus()
              }}
            >
              <Trash2 size={15} />
              Limpiar
            </button>
          </div>
          <div className="toolbar-options">
            <label>
              Modo
              <select
                aria-label="Modo de análisis"
                value={c.draft.scope}
                onChange={(e) =>
                  c.updateDraft({ scope: e.target.value as Scope })
                }
              >
                <option value="PERSONAL">Mi horario</option>
                <option value="PROPUESTA">Propuesta de clases</option>
              </select>
            </label>
            <label>
              Catálogo
              <select
                aria-label="Catálogo"
                value={c.draft.catalogId}
                onChange={(e) =>
                  c.updateDraft({ catalogId: e.target.value as CatalogId })
                }
              >
                {catalogs.map((catalog) => (
                  <option key={catalog.id} value={catalog.id}>
                    {catalogName(catalog.id)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="example-loader">
            <label className="visually-hidden" htmlFor="example-picker">
              Elegir ejemplo
            </label>
            <select
              id="example-picker"
              value={c.example}
              onChange={(e) => c.setExample(e.target.value)}
              disabled={!c.examples.length}
            >
              {!c.examples.length ? (
                <option>Ejemplos no disponibles</option>
              ) : (
                c.examples.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                  </option>
                ))
              )}
            </select>
            <button
              className="button button-secondary"
              disabled={!c.examples.length || c.loadingExample}
              onClick={() => void c.loadExample()}
            >
              {c.loadingExample ? (
                <LoaderCircle size={14} className="spin" />
              ) : (
                <FileCode2 size={14} />
              )}
              Cargar ejemplo
            </button>
          </div>
        </section>
        {c.notice && (
          <div className="app-notice" role="alert">
            <span>{c.notice}</span>
            <button
              className="icon-button"
              aria-label="Cerrar aviso"
              onClick={() => c.setNotice(null)}
            >
              <X size={15} />
            </button>
          </div>
        )}
        <div className="workbench">
          <section
            className="editor-panel panel"
            aria-label="Editor de horarios"
          >
            <header className="panel-header">
              <FileCode2 size={16} />
              <strong>Código fuente</strong>
              <span className="file-name" title={c.draft.sourceName}>
                {c.draft.sourceName}
              </span>
              <button
                className="icon-button"
                title="Descargar código .hor"
                aria-label="Descargar código .hor"
                disabled={!c.draft.source}
                onClick={() =>
                  download(
                    c.draft.source,
                    c.draft.sourceName.split(/[\\/]/).pop() || 'horario.hor',
                    'text/plain;charset=utf-8',
                  )
                }
              >
                <Download size={15} />
              </button>
            </header>
            <Suspense
              fallback={
                <div className="source-editor muted">Preparando editor…</div>
              }
            >
              <SourceEditor
                ref={editor}
                value={c.draft.source}
                onChange={(source) => {
                  if (source !== c.draft.source) c.updateDraft({ source })
                }}
                onCompile={() => {
                  void c.compile()
                }}
                onCursor={(line, column) => setCursor({ line, column })}
              />
            </Suspense>
            <div className="editor-footer">
              <span>{c.draft.source.split('\n').length} líneas · UTF-8</span>
              <span>
                {c.saved ? (
                  <>
                    <CheckCircle2 size={11} />
                    Borrador guardado
                  </>
                ) : (
                  'Sin guardado local'
                )}
              </span>
            </div>
          </section>
          <div className="results-container" ref={resultPanel}>
            <ResultsPanel
              key={c.snapshot?.id ?? 'empty'}
              result={c.snapshot?.result ?? null}
              tab={c.tab}
              onTab={c.setTab}
              onNavigate={navigate}
              busy={c.busy}
              stale={c.stale}
              onExport={() => {
                if (c.snapshot)
                  download(
                    JSON.stringify(c.snapshot.result, null, 2),
                    'analisis-horario.json',
                    'application/json;charset=utf-8',
                  )
              }}
            />
          </div>
        </div>
        <Console
          entries={c.logs}
          onClear={() => c.setLogs([])}
          onNavigate={navigate}
        />
      </main>
      <footer className="statusbar">
        <div>
          <span className={`connection-dot connection-${c.connection}`} />
          <span role="status">
            {c.connection === 'connected'
              ? 'API conectada'
              : c.connection === 'checking'
                ? 'Conectando…'
                : 'API sin conexión'}
          </span>
          <button
            className="status-retry"
            title="Reintentar conexión"
            aria-label="Reintentar conexión"
            onClick={() => void c.refreshResources()}
          >
            <RefreshCw size={12} />
          </button>
          <span className="status-catalog">
            {currentCatalog
              ? `${currentCatalog.offers} ofertas · ${currentCatalog.sessions} sesiones`
              : 'Catálogo pendiente'}
          </span>
        </div>
        <div>
          <span>
            Línea {cursor.line}, Columna {cursor.column}
          </span>
          <span>UTF-8</span>
          <span>.hor v0.2</span>
        </div>
      </footer>
      <Modal
        open={!!origin}
        title="Ubicación de origen"
        onClose={() => setOrigin(null)}
      >
        {origin && (
          <div className="modal-content">
            <p>Este dato procede del catálogo, no del texto del editor.</p>
            <dl className="origin-details">
              <dt>Fuente</dt>
              <dd>{origin.source_id}</dd>
              <dt>Ubicación</dt>
              <dd>{originText(origin)}</dd>
            </dl>
            <p className="muted">
              El archivo original se conserva. Puedes consultar sus celdas o su
              ubicación en el catálogo del proyecto.
            </p>
          </div>
        )}
      </Modal>
      <Modal
        open={guide}
        title="Cómo analizar tu horario"
        onClose={() => setGuide(false)}
      >
        <div className="modal-content">
          <ol>
            <li>
              Escribe o pega tu código, carga un <strong>.hor</strong> o elige
              un ejemplo.
            </li>
            <li>
              Usa <strong>Mi horario</strong> para selecciones HORARIO o{' '}
              <strong>Propuesta de clases</strong> para definir OFERTA.
            </li>
            <li>
              Pulsa <strong>Compilar</strong> o Ctrl/⌘ + Enter y explora las
              pestañas.
            </li>
          </ol>
          <p>
            La duración se expresa en horas enteras. Las palabras reservadas van
            en mayúsculas y sin puntos y coma.
          </p>
          <pre>
            {'HORARIO "Mi horario" {\n    INSCRIBIR "ISC_7B_COMPILADORES"\n}'}
          </pre>
          <p>
            Los docentes son texto libre. Las aulas se comparan con las
            ocupaciones cargadas. <strong>SIN_ASIGNAR</strong> deja la
            asignación pendiente.
          </p>
          <p className="muted">
            Capacidad, laboratorio y límites horarios no están configurados en
            la política actual; se muestran en las comprobaciones del análisis.
          </p>
        </div>
      </Modal>
    </div>
  )
}
