import { JSX } from "react";
import Link from "next/link";
import { OrbFooter } from "@/components/OrbFooter";

export default function RaiseTilePage(): JSX.Element {
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
            <h1 className="text-3xl font-bold m-0">Raise Tile</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Some tiles may be too high to step up to. By raising a tile high
              enough, you can climb out of holes or step onto higher platforms.
              You can also raise your tile high enough to help avoid an
              attacking opponent.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              A single raise will generally not protect you from approaching
              opponents, for a single step is easily climbed. However two used
              together can raise your tile high enough to avoid weak opponents.
            </p>
            <p className="text-gray-400">
              Of course, if the arena landscape is already in disarray, a Raise
              can be quite beneficial. They can be used to form steps leading up
              to elevated tiles.
            </p>
          </div>
        </div>
      </div>

      <OrbFooter />
    </div>
  );
}
