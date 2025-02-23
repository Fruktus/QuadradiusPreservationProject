import OrbLayout from "../components/orb-layout/orb-layout";

export default function CancelMultiplyPage() {
  return (
    <OrbLayout
      title="Cancel Multiply"
      description="Removes a multiplied piece from the board. This power only works on pieces that were created using the Multiply power. It cannot remove original pieces."
      strategy={
        <p className="text-gray-400">
          Use this to counter your opponent&apos;s Multiply strategy and clear
          the board of their multiplied pieces. This can help regain control of
          the board and open up movement paths.
        </p>
      }
    />
  );
}
