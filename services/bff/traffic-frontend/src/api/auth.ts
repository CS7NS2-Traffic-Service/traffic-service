export type VehicleType = "CAR" | "MOTORCYCLE" | "TRUCK" | "HGV"

export type RegisterDriverDto = {
  name: string
  email: string
  password: string
  license_number: string
  vehicle_type: VehicleType
  region: string
}

export type DriverProfile = {
  driver_id: string
  name: string
  email: string
  license_number: string
  vehicle_type: VehicleType | null
  region: string
  created_at: string
}

export type RegisterDriverResponseDto = {
  driver: DriverProfile
  access_token: string
}

export type LoginDriverDto = {
  email: string
  password: string
}

export type LoginDriverResponseDto = {
  driver: DriverProfile
  access_token: string
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
