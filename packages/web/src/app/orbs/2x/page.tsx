import OrbLayout from "../components/orb-layout/orb-layout";

export default function TwoXPage() {
  return (
    <OrbLayout
      title="2x"
      description="Doubles the effectiveness of all powers on this piece. When used multiple times, powers can be quadrupled, octupled, etc."
      strategy={
        <p className="text-gray-400">
          Best used on pieces that have powerful offensive abilities like
          Destroy or Recruit. Multiple 2x powers can be stacked for exponential
          effects.
        </p>
      }
    />
  );
}
