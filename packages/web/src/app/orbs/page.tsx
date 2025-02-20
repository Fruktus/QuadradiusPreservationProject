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
      <h1 className="text-3xl font-bold mb-8 text-white">Powers List</h1>

      {Object.entries(groupedPowers).map(([category, categoryPowers]) => (
        <div key={category} className="mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-gray-100">
            {category}
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {categoryPowers.map((power) => (
              <a
                key={power.name}
                href={`/orbs/${power.slug}`}
                className="block p-4 rounded-lg border border-gray-700 bg-gray-800 hover:border-blue-500 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-blue-400">
                    {power.name}
                  </h3>
                  {power.memberOnly && (
                    <span className="text-xs bg-yellow-900 text-yellow-100 px-2 py-1 rounded">
                      Member Only
                    </span>
                  )}
                </div>
              </a>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
