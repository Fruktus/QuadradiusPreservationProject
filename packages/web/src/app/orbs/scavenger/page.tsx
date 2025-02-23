import OrbLayout from "../components/orb-layout/orb-layout";

export default function ScavengerPage() {
  return (
    <OrbLayout
      title="Scavenger"
      description="When any piece is destroyed, this piece has a chance to acquire one of its powers. Works on both friendly and enemy pieces."
      strategy={
        <p className="text-gray-400">
          Position Scavenger pieces near combat zones to maximize chances of
          acquiring powers. Multiple Scavengers increase the odds of collecting
          powers from destroyed pieces.
        </p>
      }
    />
  );
}
