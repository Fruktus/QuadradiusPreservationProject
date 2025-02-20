import { JSX } from "react";
import Link from "next/link";

export default function ClimbTilePage(): JSX.Element {
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
            <h1 className="text-3xl font-bold m-0">Climb Tile</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Able to move to a tile no matter how high it is. Great for scaling
              walls, reaching platforms, or getting out of pits. Eliminates the
              need for steps. Does not affect tile elevation and will leave
              others trapped.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Once this power is activated, consider the arena flat for this
              piece. No height is off limits. Not as effective in a flat,
              neutral arena, but once the landscape is disrupted, this piece can
              become quite valuable.
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
