import OrbLayout from "../components/orb-layout/orb-layout";

export default function BeneficiaryPage() {
  return (
    <OrbLayout
      title="Beneficiary"
      description="When this powerup is used all of your powerups are transfered to it."
      strategy={
        <p className="text-gray-400">
          Create a devastating combo attack or a powerful piece.
          Be wary of the overheat.
        </p>
      }
    />
  );
}
