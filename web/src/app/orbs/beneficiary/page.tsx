import OrbLayout from "../components/orb-layout/orb-layout";

export default function BeneficiaryPage() {
  return (
    <OrbLayout
      title="Beneficiary"
      description="When this piece is destroyed, all its powers are transferred to the piece that destroyed it. A clever way to pass powers between your own pieces."
      strategy={
        <p className="text-gray-400">
          Load up a piece with useful powers and Beneficiary, then let it be
          captured by one of your other pieces to consolidate powers. Can also
          be used as a trap for opponents.
        </p>
      }
    />
  );
}
