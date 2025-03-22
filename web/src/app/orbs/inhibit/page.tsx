import OrbLayout from "../components/orb-layout/orb-layout";

export default function InhibitPage() {
  return (
    <OrbLayout
      title="Inhibit"
      description="Disables the power absorbing mechanism of your opponent's pieces. While they can still swap powers, this inhibits their ability to acquire new powers by docking with the Power Orb. Available in three variants: row, column, radial."
      strategy={
        <p>
          Putting this annoyance on your opponent&apos;s piece will render them
          unable to absorb and collect any Power Orbs with that piece. They can
          still land on an Orb, but it will remain intact and when they move off
          it, it still remains. If you happen to jump on a piece that is on an
          unabsorbed Orb, you will kill the piece, and absorb the power in the
          same move. If they happen to have Jump Proof armor on, they can sit on
          an Orb to block it from being absorbed by anyone. A piece that has an
          Inhibitor attached to it will most likely not be able to get any
          stronger, and is essentially a much more useless piece. Try to tag as
          many pieces of your opponent&apos;s squadron with these as possible.
        </p>
      }
      multiDimensional={true}
    >
      <ul>
        <li>Inhibit Radial: Affects opponents surrounding you</li>
        <li>Inhibit Row: Affects opponents in your row</li>
        <li>Inhibit Column: Affects opponents in your column</li>
      </ul>
    </OrbLayout>
  );
}
