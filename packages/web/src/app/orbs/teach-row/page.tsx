import OrbLayout from "../components/orb-layout/orb-layout";

export default function TeachRowPage() {
  return (
    <OrbLayout
      title="Teach Row"
      description="Teaches all powers from this piece to any friendly pieces in the same row. The width of this power can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Best used when your pieces are aligned horizontally. Position your
          teaching piece at one end of the row to maximize the number of pieces
          that can learn its powers.
        </p>
      }
    />
  );
}
