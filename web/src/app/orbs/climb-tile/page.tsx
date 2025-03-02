import OrbLayout from "../components/orb-layout/orb-layout";

export default function ClimbTilePage() {
  return (
    <OrbLayout
      title="Climb Tile"
      description="Able to move to a tile no matter how high it is. Great for scaling walls, reaching platforms, or getting out of pits. Eliminates the need for steps. Does not affect tile elevation and will leave others trapped."
      strategy={
        <p className="text-gray-400">
          Once this power is activated, consider the arena flat for this piece.
          No height is off limits. Not as effective in a flat, neutral arena,
          but once the landscape is disrupted, this piece can become quite
          valuable. You can use this to surprise attack unsuspecting opponent in 
          normally unreachable high ground.
        </p>
      }
    />
  );
}
