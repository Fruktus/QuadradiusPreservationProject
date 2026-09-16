import '@/styles/globals.css'

export default function DirectMatchLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={`antialiased min-h-screen flex items-center justify-center bg-base-500`}>
      {children}
    </div>
  )
}
