export function ensureUTCSuffix(iso: string): string {
  if (iso.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(iso)) return iso
  return iso + "Z"
}

export function parseLocalDateTime(iso: string): Date {
  const [datePart, timePart = "00:00"] = iso.split("T")
  const [year, month, day] = datePart.split("-").map(Number)
  const [hours, minutes] = timePart.split(":").map(Number)
  return new Date(year, (month || 1) - 1, day || 1, hours || 0, minutes || 0)
}

export function formatUTCToLocal(iso: string): string {
  return new Date(ensureUTCSuffix(iso)).toLocaleString()
}

export function formatUTCToLocalTime(iso: string): string {
  return new Date(ensureUTCSuffix(iso)).toLocaleTimeString()
}

export function shortId(uuid: string): string {
  return `#${uuid.replace(/-/g, "").slice(0, 4).toUpperCase()}`
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.round((seconds % 3600) / 60)
  if (h === 0) return `${m} min`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}
