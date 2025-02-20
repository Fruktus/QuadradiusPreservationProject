import Link from "next/link";

export default function BombsPage() {
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
            <h1 className="text-3xl font-bold m-0">Bombs</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Unleashes a round of bombs into the entire arena. They not only
              devastate any piece they impact but they also compress tiles down
              deeper, eventually leaving a hole in the arena floor.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Only use when you are losing and have less squadron pieces in the
              arena. The basic probability of Bombs is that it will even out the
              amount of pieces in the playing field. If there are more pieces in
              the arena from one player, they are more likely to be hit.
            </p>
            <p className="text-gray-400">
              These Bombs will also lower a tile on impact. If the tile can not
              go any lower, the stress of the impact will cause the tile to be
              penetrated, and a hole will be left in its wake. The arena
              landscape will drastically change when Bombs are dropped.
            </p>
            <p className="text-gray-400">
              The amount of Bombs dropped can be estimated by watching a gauge
              that appears next to the power window. The amount of Bombs dropped
              is determined by what size arena you are playing in. Also, keep in
              mind that the amount of Bombs can be doubled, tripled, etc, when
              used in combination with Grow Quadradius.
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
