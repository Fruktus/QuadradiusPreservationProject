import OrbLayout from "../components/orb-layout/orb-layout";

export default function OrbSpyPage() {
  return (
    <OrbLayout
      title="Orb Spy"
      description="Attaches a visible bugging device to all the tiles in your range. You can view the power of any Orb that spawns there. Available in three variants:"
      strategy={
        <p>
          Can be used to predict your opponents moves, even before they know
          what they will do, based on the power they are about to acquire. If
          you have activated Spy Orb tiles, stay off of them, hoping new Orbs
          may appear there. If your opponent has activated Spy Orbs, try to
          cyber squat on those tiles, cutting down the chance of new Orbs
          appearing there.
        </p>
      }
      multiDimensional={true}
    >
      <ul>
        <li>Orb Spy Radial: Affects tiles surrounding you</li>
        <li>Orb Spy Row: Affects tiles in your row</li>
        <li>Orb Spy Column: Affects tiles in your column</li>
      </ul>
    </OrbLayout>
  );
}
