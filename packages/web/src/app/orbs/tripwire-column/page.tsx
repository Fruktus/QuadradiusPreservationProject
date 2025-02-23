import { JSX } from "react";
import OrbFooter from "../components/orb-footer/orb-footer";

export default function TripwireColumnPage(): JSX.Element {
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
            <h1 className="text-3xl font-bold m-0">Tripwire Column</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Creates invisible tripwires along the column that trigger when
              enemy pieces move through them. The width can be extended with
              Grow Quadradius.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Use to create vertical barriers that enemies must cross. Can be
              combined with other column powers to create layered defenses.
            </p>
          </div>
        </div>
      </div>

      <OrbFooter />
    </div>
  );
}
