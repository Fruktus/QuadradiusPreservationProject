import OrbLayout from "../components/orb-layout/orb-layout";

export default function GrowQuadradiusPage() {
  return (
    <OrbLayout
      title="Grow Quadradius"
      description="Extends the effective range of row, column, and radial type powers. Row and column powers are widened, while radial powers extend farther outward. Each time it's used, the Quadradius is extended even farther."
      strategy={
        <>
          <p className="text-gray-400">
            A Grow Quadradius is only good if that piece has, or will have,
            range-like powers. If you don&apos;t have any range-like powers
            (radial, row, column), make it your priority to acquire some with
            that piece. A normal radial power reaches 8 surrounding tiles, but
            when increased with a Grow Quadradius, it reaches 24 tiles!
            That&apos;s triple the amount.
          </p>
          <p className="text-gray-400">
            If used a second time on the same piece, you can reach 48
            surrounding tiles - almost 6 times stronger with just two Grow
            Quadradius powers activated. You can Grow Quadradius up to 3 times
            per piece. While extremely rare and difficult, a single piece can
            activate enough Grow Quadradiuses to reach almost the entire arena!
          </p>
          <h2 className="text-xl font-semibold mb-2">Enhanced Powers</h2>
          <p className="text-gray-400">
            Powers enhanced by Grow Quadradius: Plateau, Moat, Trenches, Walls,
            Inverts, Teaches, Learns, Pilfers, Parasites, Scrambles, Swaps,
            Spywares, Orb Spys, Purifys, Tripwires, Inhibits, Kamikazes,
            Destroys, Acidics, Recruits, Bombs, Smart Bombs, and Snake
            Tunneling.
          </p>
        </>
      }
    />
  );
}
