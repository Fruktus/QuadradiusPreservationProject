import OrbLayout from "../components/orb-layout/orb-layout";

export default function PilferPage() {
  return (
    <OrbLayout
      title="Pilfer"
      description="A piece will steal all the powers from your opponents that are in range. Available in three variants: row, column, radial."
      strategy={
        <p>
          Similar to Learn, except it is a way to learn powers from your
          opponent while simultaneously removing their powers. If you have a
          Teach Power on the same piece with a Pilfer, always try to Pilfer
          first to get their powers, then Teach, so you have more powers to
          share with your squadron.
        </p>
      }
      multiDimensional={true}
    />
  );
}
