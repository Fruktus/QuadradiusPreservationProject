import OrbLayout from "../components/orb-layout/orb-layout";

export default function LowerTilePage() {
  return (
    <OrbLayout
      title="Lower Tile"
      description="You can lower a tile to form strategically placed stepping stones. If you have pieces trapped in a pit, a higher up piece can lower tiles to carve out steps. Other pieces can then move to higher platforms."
      strategy={
        <p className="text-gray-400">
          Usually lowering a tile is not a good idea, so this power is harder to
          use properly. One good technique is to use it right before you use an
          Invert power. A lowered tile, when Inverted, will become an elevated
          tile.
        </p>
      }
    />
  );
}
