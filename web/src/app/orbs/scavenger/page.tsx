import OrbLayout from "../components/orb-layout/orb-layout";

export default function ScavengerPage() {
  return (
    <OrbLayout
      title="Scavenger"
      description="When this piece destroys an enemy piece it will capture its powers."
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
