export default function MultiplyPage() {
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
            <h1 className="text-3xl font-bold m-0">Multiply</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Generates a new piece in the arena. This new piece will have no
              powers of its own, but by adding pieces, you gain more coverage
              and control of the battle arena and limit your opponent&apos;s
              movement.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Use it to confront an opponent and entice them to jump your newly
              formed piece. Then jump them back, and you come out of the
              confrontation ahead.
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
