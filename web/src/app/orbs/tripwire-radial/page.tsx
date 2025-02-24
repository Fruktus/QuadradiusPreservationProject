import OrbLayout from "../components/orb-layout/orb-layout";

export default function TripwireRadialPage() {
  return (
    <OrbLayout
      title="Tripwire Radial"
      description="Sets invisible traps in a radial pattern around this piece. Enemy pieces that move into these spaces are immediately destroyed. The range can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Place tripwires around key strategic positions or choke points to
          control enemy movement. Most effective when enemies have limited path
          options. The traps remain active until triggered or the piece is
          destroyed.
        </p>
      }
    />
  );
}
