import type { SessionResponse } from '../../api/types'

export interface PlacedSession {
  session: SessionResponse
  lane: number
  lanes: number
}
// Distribución visual de intervalos; los diagnósticos provienen exclusivamente de la API.
export function placeSessions(sessions: SessionResponse[]): PlacedSession[] {
  const ordered = [...sessions].sort(
    (a, b) =>
      a.interval.start_minute - b.interval.start_minute ||
      a.interval.end_minute - b.interval.end_minute,
  )
  const result: PlacedSession[] = []
  let cluster: PlacedSession[] = []
  let ends: number[] = []
  let clusterEnd = -1
  function finish() {
    for (const placed of cluster) placed.lanes = ends.length
    result.push(...cluster)
    cluster = []
    ends = []
  }
  for (const session of ordered) {
    if (session.interval.start_minute >= clusterEnd && cluster.length) finish()
    let lane = ends.findIndex((end) => end <= session.interval.start_minute)
    if (lane < 0) lane = ends.length
    ends[lane] = session.interval.end_minute
    cluster.push({ session, lane, lanes: 1 })
    clusterEnd = Math.max(
      cluster.length === 1 ? -1 : clusterEnd,
      session.interval.end_minute,
    )
  }
  finish()
  return result
}
