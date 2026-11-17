/* Generado desde contracts/. No editar a mano. */

export type Id = string
export type File = string
export type Sha256 = string
export type Sheet = string
export type SnapshotSha256 = string
export type Offers = number
export type Sessions = number
export type CatalogList = CatalogSummaryResponse[]

export interface CatalogSummaryResponse {
  id: Id
  source: CatalogSourceResponse
  snapshot_sha256: SnapshotSha256
  offers: Offers
  sessions: Sessions
}
export interface CatalogSourceResponse {
  file: File
  sha256: Sha256
  sheet: Sheet
}
