import OrbLayout from "../components/orb-layout/orb-layout";

export default function RaiseTilePage() {
  return (
    <OrbLayout
      title="Raise Tile"
      description="Some tiles may be too high to step up to. By raising a tile high enough, you can climb out of holes or step onto higher platforms. You can also raise your tile high enough to help avoid an attacking opponent."
      strategy={
        <>
          <p className="text-gray-400">
            A single raise will generally not protect you from approaching
            opponents, for a single step is easily climbed. However two used
            together can raise your tile high enough to avoid weak opponents.
          </p>
          <p className="text-gray-400">
            Of course, if the arena landscape is already in disarray, a Raise
            can be quite beneficial. They can be used to form steps leading up
            to elevated tiles.
          </p>
        </>
      }
    />
  );
}
