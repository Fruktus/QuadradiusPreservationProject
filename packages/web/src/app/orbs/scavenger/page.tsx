import { JSX } from "react";
import OrbFooter from "../components/orb-footer/orb-footer";

export default function ScavengerPage(): JSX.Element {
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
            <h1 className="text-3xl font-bold m-0">Scavenger</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              When any piece is destroyed, this piece has a chance to acquire
              one of its powers. Works on both friendly and enemy pieces.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Position Scavenger pieces near combat zones to maximize chances of
              acquiring powers. Multiple Scavengers increase the odds of
              collecting powers from destroyed pieces.
            </p>
          </div>
        </div>
      </div>

      <OrbFooter />
    </div>
  );
}
