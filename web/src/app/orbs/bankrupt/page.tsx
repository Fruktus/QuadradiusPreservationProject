import OrbLayout from "../components/orb-layout/orb-layout";

export default function BankruptPage() {
  return (
    <OrbLayout
      title="Bankrupt"
      description="All of the vacant tiles in your range will be programmed to deplete all powers and remove any positive modifications from any opponent's torus that finds itself coming in contact with one of these tiles. Available in three variants:"
      strategy={
        <p>
          This power can be used to keep a strengthened or heavily modified
          piece at bay. Such things as Jump Proofs and Move Diagonals cannot
          chase you down without sacrificing their advantage over you. These
          charged tiles do not affect weak, powerless pieces for they have
          nothing to lose. They can now be thought of as your attacking piece.
          You can more safely step right up next to the most dangerous of foes,
          being sure to stay on your own Bankrupt tile, forcing their most
          powerful piece to retreat. The elephant scared of the mouse tactic.
          You can still get Power Orbs that spawn on any opposing Bankrupt tile,
          for you acquire it after you lose all your current powers and
          modifications. If you had Move Again activated, you will lose your
          turn if you step onto an opponent&apos;s Bankrupt tile.
        </p>
      }
      multiDimensional={true}
    >
      <ul>
        <li>Bankrupt Radial: Affects tiles surrounding you</li>
        <li>Bankrupt Row: Affects tiles in your row</li>
        <li>Bankrupt Column: Affects tiles in your column</li>
      </ul>
    </OrbLayout>
  );
}
