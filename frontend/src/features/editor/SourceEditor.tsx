import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'
import { basicSetup } from 'codemirror'
import { EditorState, Prec } from '@codemirror/state'
import { EditorView, keymap } from '@codemirror/view'
import { indentWithTab } from '@codemirror/commands'
import {
  HighlightStyle,
  StreamLanguage,
  syntaxHighlighting,
} from '@codemirror/language'
import { tags } from '@lezer/highlight'
import type { SpanResponse } from '../../api/types'
import { editorRange } from './positions'

const words = new Set(
  'OFERTA MATERIA GRUPO DOCENTE SESION AULA DIA HORA DURACION HORARIO INSCRIBIR DESCONOCIDO SIN_ASIGNAR LUNES MARTES MIERCOLES JUEVES VIERNES SABADO DOMINGO'.split(
    ' ',
  ),
)
// Solo coloreado visual. La API conserva toda la validación del lenguaje.
const language = StreamLanguage.define({
  token(stream) {
    if (stream.eatSpace()) return null
    if (stream.match(/#.*/)) return 'comment'
    if (stream.match(/"(?:[^"\\]|\\.)*"?/)) return 'string'
    if (stream.match(/[0-9]{2}:[0-9]{2}|[0-9]+/)) return 'number'
    if (stream.match(/[{}]/)) return 'bracket'
    const word = stream.match(/\w+/)
    if (word)
      return Array.isArray(word) && words.has(word[0])
        ? 'keyword'
        : 'variableName'
    stream.next()
    return null
  },
})
const theme = EditorView.theme(
  {
    '&': {
      height: '100%',
      fontSize: '13px',
      backgroundColor: '#191b24',
      color: '#d9deef',
    },
    '.cm-scroller': {
      fontFamily: '"JetBrains Mono", "Cascadia Code", Consolas, monospace',
      lineHeight: '1.85',
    },
    '.cm-content': { padding: '18px 0', caretColor: '#c5adff' },
    '.cm-line': { padding: '0 20px 0 12px' },
    '.cm-gutters': {
      background: '#191b24',
      color: '#69728d',
      borderRight: '1px solid #292d3b',
      minWidth: '44px',
    },
    '.cm-activeLineGutter': { backgroundColor: '#242536', color: '#c6b2ff' },
    '.cm-activeLine': { backgroundColor: '#23233470' },
    '&.cm-focused .cm-selectionBackground, .cm-selectionBackground': {
      backgroundColor: '#6d4cc85c !important',
    },
    '&.cm-focused': { outline: 'none' },
  },
  { dark: true },
)
const highlights = HighlightStyle.define([
  { tag: tags.keyword, color: '#7abaf5' },
  { tag: tags.string, color: '#e8c47c' },
  { tag: tags.number, color: '#a5d8a6' },
  { tag: tags.comment, color: '#6f7d94', fontStyle: 'italic' },
  { tag: tags.brace, color: '#c5b6f0' },
])

export interface EditorHandle {
  reveal: (span: SpanResponse) => void
  focus: () => void
}
interface Props {
  value: string
  onChange: (value: string) => void
  onCompile: () => void
  onCursor: (line: number, column: number) => void
}

export const SourceEditor = forwardRef<EditorHandle, Props>(
  function SourceEditor({ value, onChange, onCompile, onCursor }, ref) {
    const container = useRef<HTMLDivElement>(null)
    const view = useRef<EditorView | null>(null)
    const handlers = useRef({ onChange, onCompile, onCursor })
    handlers.current = { onChange, onCompile, onCursor }
    useImperativeHandle(
      ref,
      () => ({
        reveal(span) {
          const editor = view.current
          if (!editor) return
          const range = editorRange(editor.state.doc.toString(), span)
          editor.dispatch({
            selection: { anchor: range.from, head: range.to },
            effects: EditorView.scrollIntoView(range.from, { y: 'center' }),
          })
          editor.focus()
        },
        focus() {
          view.current?.focus()
        },
      }),
      [],
    )
    useEffect(() => {
      if (!container.current) return
      const editor = new EditorView({
        parent: container.current,
        state: EditorState.create({
          doc: value,
          extensions: [
            basicSetup,
            theme,
            syntaxHighlighting(highlights),
            language,
            EditorState.tabSize.of(4),
            EditorView.contentAttributes.of({
              'aria-label': 'Código fuente .hor',
              spellcheck: 'false',
            }),
            Prec.highest(
              keymap.of([
                {
                  key: 'Mod-Enter',
                  run: () => {
                    handlers.current.onCompile()
                    return true
                  },
                },
                indentWithTab,
              ]),
            ),
            EditorView.updateListener.of((update) => {
              if (update.docChanged)
                handlers.current.onChange(update.state.doc.toString())
              if (update.selectionSet || update.docChanged) {
                const position = update.state.selection.main.head
                const line = update.state.doc.lineAt(position)
                handlers.current.onCursor(
                  line.number,
                  Array.from(update.state.sliceDoc(line.from, position))
                    .length + 1,
                )
              }
            }),
          ],
        }),
      })
      view.current = editor
      return () => {
        view.current = null
        editor.destroy()
      }
      // El editor mantiene su selección; los cambios externos se aplican en el efecto siguiente.
    }, [])
    useEffect(() => {
      const editor = view.current
      if (editor && editor.state.doc.toString() !== value)
        editor.dispatch({
          changes: { from: 0, to: editor.state.doc.length, insert: value },
        })
    }, [value])
    return <div className="source-editor" ref={container} />
  },
)
