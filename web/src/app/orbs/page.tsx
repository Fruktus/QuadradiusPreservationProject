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
    name: "Recruit",
    category: "Combat",
    slug: "recruit",
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
    name: "Teach",
    category: "Power Manipulation",
    slug: "teach",
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
    name: "Purify",
    category: "Power Manipulation",
    slug: "purify",
  },
  {
    name: "Tripwire",
    category: "Combat",
    slug: "tripwire",
  },
  {
    name: "Pilfer",
    category: "Power Manipulation",
    slug: "pilfer",
  },
  {
    name: "Parasite",
    category: "Power Manipulation",
    slug: "parasite",
  },
  {
    name: "Move Diagonal",
    category: "Movement",
    slug: "move-diagonal",
  },
  {
    name: "Flat To Sphere",
    category: "Movement",
    slug: "flat-to-sphere",
  },
  {
    name: "Relocate",
    category: "Movement",
    slug: "relocate",
  },
  {
    name: "Hotspot",
    category: "Movement",
    slug: "hotspot",
  },
  {
    name: "Switcheroo",
    category: "Movement",
    memberOnly: true,
    slug: "switcheroo",
  },
  {
    name: "Centerpult",
    category: "Movement",
    memberOnly: true,
    slug: "centerpult",
  },
  {
    name: "Jump Proof",
    category: "Defense",
    slug: "jump-proof",
  },
  {
    name: "Scramble",
    category: "Power Manipulation",
    slug: "scramble",
  },
  {
    name: "Swap",
    category: "Power Manipulation",
    slug: "swap",
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
