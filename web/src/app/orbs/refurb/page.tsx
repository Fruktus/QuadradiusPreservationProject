import OrbLayout from "../components/orb-layout/orb-layout";

export default function RefurbPage() {
  return (
    <OrbLayout
      title="Refurb"
      description="All of the tiles in your range that have either been damaged or modified in some way will be replaced with newly installed ones. Available in three variants: row, column, radial."
      strategy={
        <p>
          Can be used to remove Power Orbs, holes from either bombs or acid,
          Hotspots, Orb Spys, Bankrupts, and even trigger tripwires by severing
          the fuse mechanism. Keep in mind that all modifications are
          refurbished, not just your opponents. However, it will not place the
          tile height back to neutral elevation. Great way to tread past
          obstacles and reach an opponent where they felt safe. Also, after
          heavy carnage from both Bombs and Smart Bombs, this is a great way to
          gain more usable ground back. Any enemy pieces on tripwired tiles
          within your range will be destroyed when the tiles are replaced.
        </p>
      }
      multiDimensional={true}
    ></OrbLayout>
  );
}
