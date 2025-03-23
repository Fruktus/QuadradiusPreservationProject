import OrbLayout from "../components/orb-layout/orb-layout";

export default function DestroyPage() {
  return (
    <OrbLayout
      title="Destroy"
      description="Activating this will destroy all enemy pieces in your path. Available in three variants: row, column, radial."
      strategy={
        <p>
          Destroy is a precise and powerful tool, best used to eliminate key
          pieces of your opponent&apos;s strategy. Use it to break through
          defenses or to remove a threatening piece that could turn the tide
          against you.
        </p>
      }
      multiDimensional={true}
    ></OrbLayout>
  );
}
