import { useMutation } from "@tanstack/react-query"
import { loginDriver, type LoginDriverDto, type LoginDriverResponseDto } from "@/api/auth"

export function useLogin() {
  return useMutation<LoginDriverResponseDto, Error, LoginDriverDto>({
    mutationFn: loginDriver,
  })
}
