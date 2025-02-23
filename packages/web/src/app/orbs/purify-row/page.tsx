import { JSX } from "react";
import OrbFooter from "../components/orb-footer/orb-footer";

export default function PurifyRowPage(): JSX.Element {
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
            <h1 className="text-3xl font-bold m-0">Purify Row</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Removes all powers from enemy pieces in the same row as this
              piece. The width can be extended with Grow Quadradius.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Best used when enemy pieces are aligned horizontally. Position
              your piece at one end of the row to maximize the number of pieces
              affected.
            </p>
          </div>
        </div>
      </div>

      <OrbFooter />
    </div>
  );
}
