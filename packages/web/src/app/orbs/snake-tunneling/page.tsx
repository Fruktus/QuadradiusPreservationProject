import { JSX } from "react";
import Link from "next/link";

export default function SnakeTunnelingPage(): JSX.Element {
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
            <h1 className="text-3xl font-bold m-0">Snake Tunneling</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Energy tunnels below your piece, blindly seeking out opponents to
              destroy. This energy burrows thru the arena, randomly exploring,
              backtracking, and criss-crossing, forcing upwards any tile it
              encounters.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              This power has two main aspects to it. First, it is a great way to
              elevate tiles. It can be used to build you out of a hole, or form
              snake like, elevated walk ways. Second, this power will destroy
              any opponent it comes in contact with.
            </p>
            <p className="text-gray-400">
              Since this power will snake out from the piece that activated it,
              it&apos;s best if used when your opponent is nearby. Sometimes,
              the power will back track over tiles it already contacted. This is
              unfortunate. The power has a slightly higher chance of covering
              new ground when it does not run into the edges of the arena. So it
              is best if used when towards the center of the arena.
            </p>
            <p className="text-gray-400">
              Also, the snaking range of this power can be doubled, tripled,
              etc, when combined with Grow Quadradius.
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
