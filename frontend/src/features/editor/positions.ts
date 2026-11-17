import type { SpanResponse } from '../../api/types'

export function utf16Offset(text: string, codepointOffset: number): number {
  let characters = 0
  let offset = 0
  for (const character of text) {
    if (characters >= codepointOffset) break
    offset += character.length
    characters += 1
  }
  return offset
}

export function editorRange(text: string, span: SpanResponse) {
  return {
    from: utf16Offset(text, span.start.offset),
    to: utf16Offset(text, span.end.offset),
  }
}

export function normalizeText(text: string): string {
  return text.replace(/\r\n?/g, '\n')
}
