import OrbLayout from "../components/orb-layout/orb-layout";

export default function TeachRadialPage() {
  return (
    <OrbLayout
      title="Teach Radial"
      description="Teaches all powers from this piece to any friendly pieces in a radial pattern around it. The range of this power can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Use this to spread powerful combinations of powers to multiple pieces
          at once. Most effective when your pieces are positioned in a cluster
          and the teaching piece has valuable powers to share.
        </p>
      }
    />
  );
}
