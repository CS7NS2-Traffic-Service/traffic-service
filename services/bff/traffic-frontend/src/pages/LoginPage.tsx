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
  const setToken = useDriverStore((state) => state.setToken)
  const setUsername = useDriverStore((state) => state.setUsername)
  const { mutate: loginDriver, isPending, error } = useLogin()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginDriverDto>()

  function onSubmit(data: LoginDriverDto) {
    loginDriver(data, {
      onSuccess: (response) => {
        setToken(response.access_token)
        setUsername(response.username)
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
            placeholder="Username"
            {...register("username", { required: "Username is required" })}
          />
          {errors.username && (
            <p className="text-sm text-red-500">{errors.username.message}</p>
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
