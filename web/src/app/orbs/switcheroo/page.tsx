import OrbLayout from "../components/orb-layout/orb-layout";

export default function SwitcherooPage() {
  return (
    <OrbLayout
      title="Switcheroo"
      description="This piece will be able to switch positions with any other piece in your squadron, regardless of distance or height."
      strategy={
        <p>
          The downside is, your turn is over after switching the two pieces. So
          you are technically not covering any ground using this movement
          technique. However, you can focus your efforts on a piece that has
          Switcheroo, and move it onto a better position for orb absorption,
          beefing up its inventory and abilities. Also, don&apos;t always think
          of your Switcheroo piece as the one to build up. Sometimes it is best
          used to reposition an already stronger piece next to an orb. If you
          are strategic enough to activate Switcheroo twice on a single piece,
          you can now switch with an opponent&apos;s piece also. This technique
          can be used to pull their piece into danger or entrapment, or to
          reposition yourself into your opponent&apos;s area.
        </p>
      }
    />
  );
}
