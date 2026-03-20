export type RegisterDriverDto = {
  username: string
  password: string
}

export type RegisterDriverResponseDto = {
  driver_id: string
  username: string
}

export type LoginDriverDto = {
  username: string
  password: string
}

export type LoginDriverResponseDto = {
  access_token: string
  username: string
}

export async function loginDriver(data: LoginDriverDto): Promise<LoginDriverResponseDto> {
  const response = await fetch("/api/driver/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Login failed" }))
    throw new Error(error.detail ?? "Login failed")
  }

  return response.json()
}

export async function registerDriver(data: RegisterDriverDto): Promise<RegisterDriverResponseDto> {
  const response = await fetch("/api/driver/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Registration failed" }))
    throw new Error(error.detail ?? "Registration failed")
  }

  return response.json()
}
