import OrbLayout from "../components/orb-layout/orb-layout";

export default function PowerPlantPage() {
  return (
    <OrbLayout
      title="Power Plant"
      description="Generates a new random power for this piece at regular intervals. The power generated is chosen from all available powers in the game."
      strategy={
        <p className="text-gray-400">
          Keep Power Plant pieces protected as they accumulate powers over time.
          Combine with teaching abilities to spread the generated powers to
          other pieces.
        </p>
      }
    />
  );
}
