import OrbLayout from "../components/orb-layout/orb-layout";

export default function RecruitPage() {
  return (
    <OrbLayout
      title="Recruit"
      description="Convert an opponent's piece to your side. This power allows you to take control of a single piece from the board, turning it into one of your own."
      strategy={
        <p>
          Recruit is a strategic power, best used to turn the tide of battle by
          converting a key piece of your opponent&apos;s into your own. Use it
          to strengthen your position or to disrupt your opponent&apos;s
          strategy.
        </p>
      }
    />
  );
}
