import { useForm } from "react-hook-form"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

type RegisterFormValues = {
  username: string
  password: string
}

function RegisterForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>()

  function onSubmit(data: RegisterFormValues) {
    console.log("Register:", data)
  }

  return (
    <CardContent>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          Register
        </Button>
      </form>
    </CardContent>
  )
}

function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Create an account</CardTitle>
        </CardHeader>
        <RegisterForm />
      </Card>
    </div>
  )
}

export default RegisterPage
