import OrbLayout from "../components/orb-layout/orb-layout";

export default function TripwirePage() {
  return (
    <OrbLayout
      title="Tripwire"
      multiDimensional
      description="Traps enemy pieces in place. If they move for any reason they will be destroyed. The width can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Use tripwire to limit the movement of dangerous pieces or to trap
          others behind them.
        </p>
      }
    />
  );
}
