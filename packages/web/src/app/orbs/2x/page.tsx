import { JSX } from "react";
import Link from "next/link";

export default function TwoXPage(): JSX.Element {
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
            <h1 className="text-3xl font-bold m-0">2x</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Doubles the effectiveness of all powers on this piece. When used
              multiple times, powers can be quadrupled, octupled, etc.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              Best used on pieces that have powerful offensive abilities like
              Destroy or Recruit. Multiple 2x powers can be stacked for
              exponential effects.
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
