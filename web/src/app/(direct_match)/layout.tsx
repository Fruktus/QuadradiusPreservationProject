import { Doto } from "next/font/google"
import '@/styles/globals.css'

const doto = Doto({ weight: "600", variable: "--font-doto", subsets: ["latin"] })

export default function DirectMatchLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={`${doto.variable} antialiased min-h-screen flex items-center justify-center bg-base-500`}>
      {children}
    </div>
  )
}