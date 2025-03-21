import Link from "next/link";

interface PowerInfo {
  name: string;
  category: string;
  memberOnly?: boolean;
  slug: string;
}

const powers: PowerInfo[] = [
  {
    name: "Multiply",
    category: "Basic",
    slug: "multiply",
  },
  {
    name: "Cancel Multiply",
    category: "Basic",
    slug: "cancel-multiply",
  },
  {
    name: "Orbic Rehash",
    category: "Basic",
    slug: "orbic-rehash",
  },
  {
    name: "Grow Quadradius",
    category: "Enhancement",
    slug: "grow-quadradius",
  },
  {
    name: "Bombs",
    category: "Combat",
    slug: "bombs",
  },
  {
    name: "Smart Bombs",
    category: "Combat",
    slug: "smart-bombs",
  },
  {
    name: "Invisible",
    category: "Movement",
    memberOnly: true,
    slug: "invisible",
  },
  {
    name: "Recruit Radial",
    category: "Combat",
    slug: "recruit-radial",
  },
  {
    name: "Network Bridge",
    category: "Enhancement",
    memberOnly: true,
    slug: "network-bridge",
  },
  {
    name: "Snake Tunneling",
    category: "Combat",
    slug: "snake-tunneling",
  },
  {
    name: "Raise Tile",
    category: "Movement",
    slug: "raise-tile",
  },
  {
    name: "Lower Tile",
    category: "Movement",
    slug: "lower-tile",
  },
  {
    name: "Climb Tile",
    category: "Movement",
    slug: "climb-tile",
  },
  {
    name: "Teach Radial",
    category: "Power Manipulation",
    slug: "teach-radial",
  },
  {
    name: "Teach Row",
    category: "Power Manipulation",
    slug: "teach-row",
  },
  {
    name: "Teach Column",
    category: "Power Manipulation",
    slug: "teach-column",
  },
  {
    name: "2x",
    category: "Enhancement",
    slug: "2x",
  },
  {
    name: "Beneficiary",
    category: "Enhancement",
    slug: "beneficiary",
  },
  {
    name: "Scavenger",
    category: "Enhancement",
    memberOnly: true,
    slug: "scavenger",
  },
  {
    name: "Power Plant",
    category: "Enhancement",
    memberOnly: true,
    slug: "power-plant",
  },
  {
    name: "Purify Radial",
    category: "Power Manipulation",
    slug: "purify-radial",
  },
  {
    name: "Purify Row",
    category: "Power Manipulation",
    slug: "purify-row",
  },
  {
    name: "Purify Column",
    category: "Power Manipulation",
    slug: "purify-column",
  },
  {
    name: "Tripwire Radial",
    category: "Combat",
    slug: "tripwire-radial",
  },
  {
    name: "Tripwire Row",
    category: "Combat",
    slug: "tripwire-row",
  },
  {
    name: "Tripwire Column",
    category: "Combat",
    slug: "tripwire-column",
  },
];

export default function OrbsPage() {
  // Group powers by category
  const groupedPowers = powers.reduce((acc, power) => {
    if (!acc[power.category]) {
      acc[power.category] = [];
    }
    acc[power.category].push(power);
    return acc;
  }, {} as Record<string, PowerInfo[]>);

  return (
    <div className="prose prose-invert max-w-none p-6">
      <h1 className="text-2xl font-bold mb-2 text-white">Powers List</h1>
      <h2 className="text-xl font-semibold mb-8 text-gray-100 ">
        (List is partial. We are still working on it.)
      </h2>

      {Object.entries(groupedPowers).map(([category, categoryPowers]) => (
        <div key={category} className="mb-4">
          <h2 className="text-xl font-semibold mb-2 text-gray-100">
            {category}
          </h2>
          <div className="grid gap-2 grid-cols-2 sm:grid-cols-3 md:grid-cols-4">
            {categoryPowers.map((power) => (
              <Link
                key={power.name}
                href={`/orbs/${power.slug}`}
                className="block p-2 rounded-lg border border-gray-900 bg-[var(--base-300)] hover:bg-[var(--base-200)] transition-colors"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-200">
                    {power.name}
                  </h3>
                  {power.memberOnly && (
                    <span className="member-badge ml-1">Member</span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
