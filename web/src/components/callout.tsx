type CalloutProps = {
    title: string
    variant?: "neutral" | "warning" | "success" | "info"
    children: React.ReactNode
}

export default function Callout({
    title,
    variant = "neutral",
    children,
}: CalloutProps) {
    const styles = {
        neutral: "bg-gray-50 text-gray-800",
        warning: "bg-yellow-50 text-yellow-800",
        success: "bg-green-50 text-green-800",
        info:    "bg-blue-50 text-blue-800"
    }

    return (
        <div className={`p-4 rounded mt-6 ${styles[variant]}`}>
            <h3 className="font-semibold">{title}</h3>
            <div className="mt-2">{children}</div>
        </div>
    )
}