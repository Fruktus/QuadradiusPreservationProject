import OrbLayout from "../components/orb-layout/orb-layout";

export default function PurifyColumnPage() {
  return (
    <OrbLayout
      title="Purify Column"
      description="Removes all positive modifications from enemy pieces and negative from your own in the same column as this piece. The width can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Best used when enemy pieces are aligned vertically. Position your
          piece at the top or bottom of the column to maximize the number of
          pieces affected.
        </p>
      }
    />
  );
}
