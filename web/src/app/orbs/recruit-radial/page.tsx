import OrbLayout from "../components/orb-layout/orb-layout";

export default function RecruitRadialPage() {
  return (
    <OrbLayout
      title="Recruit Radial"
      description="Converts enemy pieces to your side in a radial pattern around this piece. The range can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Position your piece near clusters of enemy pieces to maximize the
          number of pieces you can recruit. Most effective when combined with
          Grow Quadradius to extend your recruitment range.
        </p>
      }
    />
  );
}
