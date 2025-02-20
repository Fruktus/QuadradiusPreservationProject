import Link from "next/link";

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
              Removes all the existing Power Orbs in the arena and replaces them
              with newly positioned ones. Useful when the current layout is
              benefiting your opponent, whereas a rehashed layout of orbs may
              benefit you more.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Wait to use it when there are many Orbs in the arena, and your
              opponent is one move away from landing on an Orb. Let them waste
              their time positioning their pieces to gain Orbs, then hit them
              when they are about to cash in on their goal. Also good if there
              are Orbs out of reach, such as too high, landlocked, or behind
              your opponents defenses.
            </p>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <Link href="/orbs" className="text-blue-600 hover:text-blue-800">
          ← Back to Powers List
        </Link>
      </div>
    </div>
  );
}
