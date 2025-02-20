import OrbLayout from "../components/orb-layout/orb-layout";

export default function TripwireColumnPage() {
  return (
    <OrbLayout
      title="Tripwire Column"
      description="Sets invisible traps along the same column as this piece. Enemy pieces that move into these spaces are immediately destroyed. The width can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Use to control vertical movement paths and create defensive lines.
          Position the tripwires to protect key positions or to force enemies to
          take longer routes around your defenses.
        </p>
      }
    />
  );
}
