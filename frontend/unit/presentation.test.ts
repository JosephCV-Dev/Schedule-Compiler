import assert from 'node:assert/strict'
import test from 'node:test'
import {
  editorRange,
  normalizeText,
  utf16Offset,
} from '../src/features/editor/positions.ts'
import { placeSessions } from '../src/features/schedule/layout.ts'
import type { SessionResponse } from '../src/api/types.ts'

function session(id: string, start: number, end: number): SessionResponse {
  return {
    id,
    offer_id: id,
    day: 'LUNES',
    interval: { start_minute: start, end_minute: end },
    room: { state: 'CONOCIDO', value: 'A' },
    origins: [],
  }
}
test('posiciones Unicode del backend se convierten a unidades UTF-16 del editor', () => {
  const text = 'A😀B\nC'
  assert.equal(utf16Offset(text, 2), 3)
  const range = editorRange(text, {
    start: { offset: 2, line: 1, column: 3 },
    end: { offset: 3, line: 1, column: 4 },
  })
  assert.equal(text.slice(range.from, range.to), 'B')
})
test('rango vacío de fin de archivo se ubica después de emojis', () => {
  const text = '😀\nX'
  const range = editorRange(text, {
    start: { offset: 4, line: 2, column: 2 },
    end: { offset: 4, line: 2, column: 2 },
  })
  assert.deepEqual(range, { from: text.length, to: text.length })
})
test('carga web normaliza saltos antes de enviarlos al backend', () => {
  assert.equal(normalizeText('A\r\nB\rC\n😀'), 'A\nB\nC\n😀')
})
test('sesiones contiguas usan todo el ancho y no cambian los datos originales', () => {
  const input = [session('B', 720, 780), session('A', 600, 720)]
  const before = JSON.stringify(input)
  const placed = placeSessions(input)
  assert.deepEqual(
    placed.map((p) => [p.session.id, p.lane, p.lanes]),
    [
      ['A', 0, 1],
      ['B', 0, 1],
    ],
  )
  assert.equal(JSON.stringify(input), before)
})
test('sesiones superpuestas se colocan en carriles sin esconder una detrás de otra', () => {
  const placed = placeSessions([
    session('A', 600, 780),
    session('B', 660, 720),
    session('C', 720, 840),
    session('D', 840, 900),
  ])
  assert.deepEqual(
    placed.map((p) => [p.session.id, p.lane, p.lanes]),
    [
      ['A', 0, 2],
      ['B', 1, 2],
      ['C', 1, 2],
      ['D', 0, 1],
    ],
  )
})
test('tres sesiones simultáneas tienen tres carriles', () => {
  const placed = placeSessions([
    session('A', 600, 720),
    session('B', 600, 720),
    session('C', 600, 720),
  ])
  assert.equal(new Set(placed.map((p) => p.lane)).size, 3)
  assert.ok(placed.every((p) => p.lanes === 3))
})
test('calendario vacío conserva una salida vacía', () => {
  assert.deepEqual(placeSessions([]), [])
})
