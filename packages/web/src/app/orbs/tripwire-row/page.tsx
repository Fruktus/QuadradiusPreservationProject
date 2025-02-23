import OrbLayout from "../components/orb-layout/orb-layout";

export default function TripwireRowPage() {
  return (
    <OrbLayout
      title="Tripwire Row"
      description="Sets invisible traps along the same row as this piece. Enemy pieces that move into these spaces are immediately destroyed. The width can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Use to control horizontal movement paths and protect your pieces from
          side attacks. Position the tripwires to force enemies into
          disadvantageous positions or to protect valuable pieces from flanking
          maneuvers.
        </p>
      }
    />
  );
}
