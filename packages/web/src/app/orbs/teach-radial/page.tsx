import { JSX } from "react";
import Link from "next/link";

export default function TeachRadialPage(): JSX.Element {
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
            <h1 className="text-3xl font-bold m-0">Teach Radial</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Teaches all powers from this piece to any friendly pieces in a
              radial pattern around it. The range of this power can be extended
              with Grow Quadradius.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Use this to spread powerful combinations of powers to multiple
              pieces at once. Most effective when your pieces are positioned in
              a cluster and the teaching piece has valuable powers to share.
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
