"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface TabProps {
  tabs: {
    label: string;
    href: string;
  }[];
}

export default function Tabs({ tabs }: TabProps) {
  const pathname = usePathname();

  return (
    <div className="w-full border-b border-[var(--foreground)]">
      <nav className="flex space-x-4">
        {tabs.map((tab) => {
          const isActive =
            pathname === tab.href || (pathname === "/" && tab.href === "/orbs");
          return (
            <Link
              key={tab.href}
              href={tab.href}
              style={{
                lineHeight: "1.2",
              }}
              className={`px-3 py-1 text-md font-medium rounded-t-lg pixel-text w-32 text-center ${
                isActive
                  ? "bg-[var(--red-dark)] text-[var(--red-light)] border-b-2 border-[var(--primary)]"
                  : "text-[var(--text-primary)] hover:text-[var(--button-text)] hover:bg-[var(--red-medium)]"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
