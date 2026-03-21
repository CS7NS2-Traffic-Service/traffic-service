import { useDriverStore } from "@/stores/driverStore"

export function authHeaders(): Record<string, string> {
  const token = useDriverStore.getState().token
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export async function handleResponse<T>(response: Response, fallbackMessage: string): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: fallbackMessage }))
    throw new Error(error.detail ?? fallbackMessage)
  }
  return response.json()
}
