import { clsx } from "clsx"
import md5 from "js-md5"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function hashCredentials(username: string, password: string): string {
  return md5(`++${username.toUpperCase()}++${password}`)
}