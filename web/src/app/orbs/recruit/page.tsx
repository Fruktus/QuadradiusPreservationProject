import OrbLayout from "../components/orb-layout/orb-layout";

export default function RecruitPage() {
  return (
    <OrbLayout
      title="Recruit"
      multiDimensional
      description="Converts enemy pieces to your side in a radial/row/column pattern. The range can be extended with Grow Quadradius."
      strategy={
        <p className="text-gray-400">
          Plan your recruitment to maximize the number of pieces you can
          recruit. Most effective when combined with Grow Quadradius to extend
          your recruitment range.
        </p>
      }
    />
  );
}
