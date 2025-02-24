import OrbLayout from "../components/orb-layout/orb-layout";

export default function PurifyRadialPage() {
  return (
    <OrbLayout
      title="Purify Radial"
      description="Removes all powers from enemy pieces in a radial pattern around this piece. The range can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Use to neutralize powerful enemy pieces that have accumulated many
          abilities. Most effective when multiple enemy pieces are clustered
          together.
        </p>
      }
    />
  );
}
