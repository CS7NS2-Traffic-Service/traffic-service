import { useForm } from "react-hook-form"
import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useRegister } from "@/hooks/useRegister"
import type { RegisterDriverDto } from "@/api/auth"
import { useDriverStore } from "@/stores/driverStore"

const VEHICLE_TYPES = ["CAR", "MOTORCYCLE", "TRUCK", "HGV"] as const

function RegisterForm() {
  const navigate = useNavigate()
  const login = useDriverStore((state) => state.login)
  const { mutate: registerDriver, isPending, error } = useRegister()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterDriverDto>()

  function onSubmit(data: RegisterDriverDto) {
    registerDriver(data, {
      onSuccess: (response) => {
        login(response.driver, response.access_token)
        navigate("/")
      },
    })
  }

  return (
    <CardContent>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {error && (
          <p className="text-sm text-red-500">{error.message}</p>
        )}
        <div className="space-y-1">
          <Input
            placeholder="Full name"
            {...register("name", { required: "Name is required" })}
          />
          {errors.name && (
            <p className="text-sm text-red-500">{errors.name.message}</p>
          )}
        </div>
        <div className="space-y-1">
          <Input
            type="email"
            placeholder="Email"
            {...register("email", { required: "Email is required" })}
          />
          {errors.email && (
            <p className="text-sm text-red-500">{errors.email.message}</p>
          )}
        </div>
        <div className="space-y-1">
          <Input
            type="password"
            placeholder="Password"
            {...register("password", {
              required: "Password is required",
              minLength: { value: 8, message: "Password must be at least 8 characters" },
            })}
          />
          {errors.password && (
            <p className="text-sm text-red-500">{errors.password.message}</p>
          )}
        </div>
        <div className="space-y-1">
          <Input
            placeholder="License number"
            {...register("license_number", { required: "License number is required" })}
          />
          {errors.license_number && (
            <p className="text-sm text-red-500">{errors.license_number.message}</p>
          )}
        </div>
        <div className="space-y-1">
          <select
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-xs transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm"
            defaultValue=""
            {...register("vehicle_type", { required: "Vehicle type is required" })}
          >
            <option value="" disabled>
              Vehicle type
            </option>
            {VEHICLE_TYPES.map((type) => (
              <option key={type} value={type}>
                {type.charAt(0) + type.slice(1).toLowerCase()}
              </option>
            ))}
          </select>
          {errors.vehicle_type && (
            <p className="text-sm text-red-500">{errors.vehicle_type.message}</p>
          )}
        </div>
        <div className="space-y-1">
          <Input
            placeholder="Region"
            {...register("region", { required: "Region is required" })}
          />
          {errors.region && (
            <p className="text-sm text-red-500">{errors.region.message}</p>
          )}
        </div>
        <Button type="submit" className="w-full" disabled={isPending}>
          {isPending ? "Registering..." : "Register"}
        </Button>
      </form>
    </CardContent>
  )
}

function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create an account</CardTitle>
        </CardHeader>
        <RegisterForm />
      </Card>
    </div>
  )
}

export default RegisterPage
