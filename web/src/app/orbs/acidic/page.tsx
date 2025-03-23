import OrbLayout from "../components/orb-layout/orb-layout";

export default function AcidicPage() {
  return (
    <OrbLayout
      title="Acidic"
      description="Activating this will dissolve all enemy pieces in your path, and make the tile unusable. Available in three variants: row, column, radial."
      strategy={
        <p>
          Acidic is a precise and powerful tool, best used to eliminate key
          pieces of your opponent&apos;s strategy. Use it to break through
          defenses or to remove a threatening piece that could turn the tide
          against you.
        </p>
      }
      multiDimensional={true}
    ></OrbLayout>
  );
}
