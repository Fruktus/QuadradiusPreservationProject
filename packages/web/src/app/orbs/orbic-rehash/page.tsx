export default function OrbicRehashPage() {
  return (
    <div className="prose max-w-none p-6">
      <div className="flex items-start gap-8">
        <div className="w-1/3">
          <div className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center">
            {/* Placeholder for GIF */}
            <span className="text-gray-400">Animation Coming Soon</span>
          </div>
        </div>

        <div className="w-2/3">
          <div className="flex items-center gap-4 mb-6">
            <h1 className="text-3xl font-bold m-0">Orbic Rehash</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Replaces all powers on the board with new random powers.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Use this when your opponent has collected powerful orbs or when
              you&apos;re at a disadvantage with your current power
              distribution.
            </p>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <a
          href="/quadradius/orbs"
          className="text-blue-600 hover:text-blue-800"
        >
          ← Back to Powers List
        </a>
      </div>
    </div>
  );
}
