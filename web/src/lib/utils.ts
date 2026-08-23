import { ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

// Combines CSS class names into one string.
// 
// `clsx` handles conditional classes, e.g.:
//   cn("button", isActive && "active")
//   // → "button active"   (if isActive is true)
//   // → "button"          (if isActive is false)
// 
// `twMerge` additionally removes conflicting Tailwind classes (the later one wins):
//   cn("text-red-500", "text-blue-500")
//   // → "text-blue-500"
// 
// This keeps component `className` values easy to compose without
// manually concatenating strings or worrying about Tailwind conflicts.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
