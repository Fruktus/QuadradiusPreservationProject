import { JSX } from "react";
import Link from "next/link";

export default function LowerTilePage(): JSX.Element {
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
            <h1 className="text-3xl font-bold m-0">Lower Tile</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              You can lower a tile to form strategically placed stepping stones.
              If you have pieces trapped in a pit, a higher up piece can lower
              tiles to carve out steps. Other pieces can then move to higher
              platforms.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Usually lowering a tile is not a good idea, so this power is
              harder to use properly. One good technique is to use it right
              before you use an Invert power. A lowered tile, when Inverted,
              will become an elevated tile.
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
