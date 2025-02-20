import Link from "next/link";

export default function GrowQuadradiusPage() {
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
            <h1 className="text-3xl font-bold m-0">Grow Quadradius</h1>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">
              Extends the effective range of row, column, and radial type
              powers. Row and column powers are widened, while radial powers
              extend farther outward. Each time it's used, the Quadradius is
              extended even farther.
            </p>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            <p className="text-gray-400">
              A Grow Quadradius is only good if that piece has, or will have,
              range like powers. If you don't have any range like powers
              (radial, row, column), make it your priority to acquire some with
              that piece. A normal radial power reaches 8 surrounding tiles, but
              when increased with a Grow Quadradius, it reaches 24 tiles! That's
              triple the amount.
            </p>
            <p className="text-gray-400">
              If used a second time on the same piece, you can reach 48
              surrounding tiles - almost 6 times stronger with just two Grow
              Quadradius powers activated. You can Grow Quadradius up to 3 times
              per piece. While extremely rare and difficult, a single piece can
              activate enough Grow Quadradiuses to reach almost the entire
              arena!
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Enhanced Powers</h2>
            <p className="text-gray-400">
              Powers enhanced by Grow Quadradius: Plateau, Moat, Trenches,
              Walls, Inverts, Teaches, Learns, Pilfers, Parasites, Scrambles,
              Swaps, Spywares, Orb Spys, Purifys, Tripwires, Inhibits,
              Kamikazes, Destroys, Acidics, Recruits, Bombs, Smart Bombs, and
              Snake Tunneling.
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
