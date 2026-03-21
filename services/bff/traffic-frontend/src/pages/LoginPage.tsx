import { useForm } from "react-hook-form"
import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useLogin } from "@/hooks/useLogin"
import type { LoginDriverDto } from "@/api/auth"
import { useDriverStore } from "@/stores/driverStore"

function LoginForm() {
  const navigate = useNavigate()
  const login = useDriverStore((state) => state.login)
  const { mutate: loginDriver, isPending, error } = useLogin()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginDriverDto>()

  function onSubmit(data: LoginDriverDto) {
    loginDriver(data, {
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
              minLength: { value: 2, message: "Password must be at least 2 characters" },
            })}
          />
          {errors.password && (
            <p className="text-sm text-red-500">{errors.password.message}</p>
          )}
        </div>
        <Button type="submit" className="w-full" disabled={isPending}>
          {isPending ? "Signing in..." : "Login"}
        </Button>
      </form>
    </CardContent>
  )
}

function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
        </CardHeader>
        <LoginForm />
      </Card>
    </div>
  )
}

export default LoginPage
