import { JSX } from "react";
import Link from "next/link";

export default function SmartBombsPage(): JSX.Element {
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
            <h1 className="text-3xl font-bold m-0">Smart Bombs</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Unleashes a round of smart bombs that will avoid your own
              squadron. They not only devastate any piece they impact but they
              also compress tiles down deeper, eventually leaving a hole in the
              arena floor.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              These are more intelligent than their weaker cousin, Bombs. While
              they will still appear to be randomly dropped on the arena, they
              will never strike your own squadron. This causes the Smart Bombs
              not only to be safely activated, but the probability of hitting
              your opponent is increased.
            </p>
            <p className="text-gray-400">
              These Smart Bombs will also lower a tile on impact. If the tile
              can not go any lower, the stress of the impact will cause the tile
              to be penetrated, and a hole will be left in its wake. The arena
              landscape will drastically change when Smart Bombs are dropped.
            </p>
            <p className="text-gray-400">
              The amount of Smart Bombs dropped can be estimated by watching a
              gauge that appears next to the power window. The amount of Smart
              Bombs dropped is determined by what size arena you are playing in.
              Also, keep in mind that the amount of Bombs can be doubled,
              tripled, etc, when combined with Grow Quadradius.
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
