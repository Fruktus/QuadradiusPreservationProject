import OrbLayout from "../components/orb-layout/orb-layout";

export default function TeachnPage() {
  return (
    <OrbLayout
      title="Teach"
      multiDimensional
      description="Teaches all powers from this piece to any friendly pieces in the same row/column/radial. The size of this power can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Position your teaching piece best to maximize the number of pieces
          that can learn its powers.
        </p>
      }
    />
  );
}
