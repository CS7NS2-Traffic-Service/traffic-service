import { useMutation } from "@tanstack/react-query"
import { registerDriver, type RegisterDriverDto, type RegisterDriverResponseDto } from "@/api/auth"

export function useRegister() {
  return useMutation<RegisterDriverResponseDto, Error, RegisterDriverDto>({
    mutationFn: registerDriver,
  })
}
