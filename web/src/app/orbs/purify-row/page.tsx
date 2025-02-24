import OrbLayout from "../components/orb-layout/orb-layout";

export default function PurifyRowPage() {
  return (
    <OrbLayout
      title="Purify Row"
      description="Removes all powers from enemy pieces in the same row as this piece. The width can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Best used when enemy pieces are aligned horizontally. Position your
          piece at one end of the row to maximize the number of pieces affected.
        </p>
      }
    />
  );
}
