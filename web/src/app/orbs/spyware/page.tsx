import OrbLayout from "../components/orb-layout/orb-layout";

export default function SpywarePage() {
  return (
    <OrbLayout
      title="Spyware"
      description="Attaches a visible bugging device to any opponent's pieces. You can then view their power inventory. Available in three variants:"
      strategy={
        <p>
          While you can view any powers on your opponent&apos;s pieces that are
          bugged with Spyware, (or any powers they later receive) they are aware
          of the bugging device. This may cause them to not act rationally,
          knowing you are scrutinizing that piece with more detail. However, you
          can now decide if it is safe to be on the same row, column, or radial
          range of that piece. You can save yourself senseless losses of your
          pieces with that information.
        </p>
      }
      multiDimensional={true}
    >
      <ul>
        <li>Spyware Radial: Affects opponents surrounding you</li>
        <li>Spyware Row: Affects opponents in your row</li>
        <li>Spyware Column: Affects opponents in your column</li>
      </ul>
    </OrbLayout>
  );
}
