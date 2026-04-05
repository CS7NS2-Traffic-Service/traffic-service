export function ensureUTCSuffix(iso: string): string {
  if (iso.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(iso)) return iso
  return iso + "Z"
}

export function formatUTCToLocal(iso: string): string {
  return new Date(ensureUTCSuffix(iso)).toLocaleString()
}

export function formatUTCToLocalTime(iso: string): string {
  return new Date(ensureUTCSuffix(iso)).toLocaleTimeString()
}
