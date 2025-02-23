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
    <div className="w-full border-b border-gray-700">
      <nav className="flex space-x-4">
        {tabs.map((tab) => {
          const isActive =
            pathname === tab.href || (pathname === "/" && tab.href === "/orbs");
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`px-3 py-2 text-sm font-medium rounded-t-lg ${
                isActive
                  ? "bg-neutral text-blue-400 border-b-2 border-blue-400"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
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
