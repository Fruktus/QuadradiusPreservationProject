import OrbLayout from "../components/orb-layout/orb-layout";

export default function FlatToSpherePage() {
  return (
    <OrbLayout
      title="Flat To Sphere"
      description="This piece can now move from one side of the arena to the other. It treats the playing field as if the flat arena is now a sphere with no physical edges. Can cover ground quickly and prevents being walled in."
      strategy={
        <>
          <p>
            This power is like sailing around the globe. The arena is no longer
            a bounding square to this piece, but rather a sphere. Keep in mind
            that you still cannot move to tiles that are too high, so if you try
            to move to the other side of the board, the new tile you are
            attempting to move to needs to be within the elevation of what this
            piece is capable of climbing.
          </p>
          <p>
            The Flat To Sphere Power has great potential when combined with Move
            Diagonal. You can move to the other side of the board, and choose to
            land on one of the adjacent tiles. Also, if you have Move Diagonal
            and Flat To Sphere activated on a single piece, and you are in the
            corner of the arena, you can move to any of the four corners with
            ease.
          </p>
        </>
      }
    />
  );
}
