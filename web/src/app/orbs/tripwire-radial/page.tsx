import OrbLayout from "../components/orb-layout/orb-layout";

export default function TripwireRadialPage() {
  return (
    <OrbLayout
      title="Tripwire Radial"
      description="Traps enemy pieces in place. If these pieces move for any reason, they will be destroyed. The range can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Use tripwire to limit the movement of dangerous pieces or to
          trap others behind them.
        </p>
      }
    />
  );
}
