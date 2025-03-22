import OrbLayout from "../components/orb-layout/orb-layout";

export default function RecruitPage() {
  return (
    <OrbLayout
      title="Recruit"
      description="Activating this will recruit opponent's pieces to your side. Available in three variants: row, column, radial."
      strategy={
        <p>
          Recruit is a strategic power, best used to turn the tide of battle by
          converting a key piece of your opponent&apos;s into your own. Use it
          to strengthen your position or to disrupt your opponent&apos;s
          strategy.
        </p>
      }
      multiDimensional={true}
    >
      <ul>
        <li>Recruit Radial: Affects opponent&apos;s pieces surrounding you</li>
        <li>Recruit Row: Affects opponent&apos;s pieces in your row</li>
        <li>Recruit Column: Affects opponent&apos;s pieces in your column</li>
      </ul>
    </OrbLayout>
  );
}
