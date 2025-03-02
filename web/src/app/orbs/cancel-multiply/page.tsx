import OrbLayout from "../components/orb-layout/orb-layout";

export default function CancelMultiplyPage() {
  return (
    <OrbLayout
      title="Cancel Multiply"
      description="Cancels the in-progress Multiply. Can only be used before placing the Multiplied piece"
      strategy={
        <p className="text-gray-400">
          Use this if you change your mind about using Multiply.
        </p>
      }
    />
  );
}
