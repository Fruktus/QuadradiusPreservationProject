import OrbLayout from "../components/orb-layout/orb-layout";

export default function HotspotPage() {
  return (
    <OrbLayout
      title="Hotspot"
      description="Changes an ordinary tile into a hotspot where any piece in your squadron can move to, regardless of how far away it is or its elevation."
      strategy={
        <p>
          Try to place Hotspots more in the center of the arena. That is the
          better location to plant these in, for it helps when fleeing or
          chasing. If you have the ability to plant two or more Hotspots, place
          them apart from one another. With two or more Hotspots, it makes it
          very hard for your opponent to chase you down when you can easily
          transport. Leaving the Hotspots unoccupied makes traveling to them at
          a moment&apos;s notice easier. However, sitting on them is a great way
          to protect your piece, for if someone tries to jump on it, you can
          move another piece into the Hotspot and jump them back.
        </p>
      }
    />
  );
}
