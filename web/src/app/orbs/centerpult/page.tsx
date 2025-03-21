import OrbLayout from "../components/orb-layout/orb-layout";

export default function CenterpultPage() {
  return (
    <OrbLayout
      title="Centerpult"
      description="Your piece can catapult itself into the vacant center of any four, symmetric pieces, as long as occupying the empty, center tile will complete either a plus sign or an 'x' shaped pattern."
      strategy={
        <p>
          Once this piece has an activated Centerpult, it could move into the
          middle of four other tori anywhere in the arena, as long as the tile
          is empty, and either the four corners surrounding the tile are
          occupied, or the four adjacent tiles surrounding the tile are
          occupied. The surrounding tori can consist of your own squadron, your
          opponent&apos;s squadron, or a mixture of the two. Elevation is not a
          restriction with this power, and you can move to a center of any
          height, from any height. You can not use this power to move to the
          edge of an arena, or a corner, even if the empty tile is surrounded on
          all sides by two or three tori since the combined force of four is
          required to physically pull in your torus from across the Arena.
        </p>
      }
    />
  );
}
