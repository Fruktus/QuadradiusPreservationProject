import OrbLayout from "../components/orb-layout/orb-layout";

export default function PurifyPage() {
  return (
    <OrbLayout
      title="Purify"
      multiDimensional
      description="Removes all positive modifications from enemy pieces and negative from your own in the same row/column/radial as this piece. The size of this power can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Position your piece best to affect the most pieces.
        </p>
      }
    />
  );
}
