import OrbLayout from "../components/orb-layout/orb-layout";

export default function TeachColumnPage() {
  return (
    <OrbLayout
      title="Teach Column"
      description="Teaches all powers from this piece to any friendly pieces in the same column. The width of this power can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Best used when your pieces are aligned vertically. Position your
          teaching piece at the top or bottom of the column to maximize the
          number of pieces that can learn its powers.
        </p>
      }
    />
  );
}
