import OrbLayout from "../components/orb-layout/orb-layout";

export default function BombsPage() {
  return (
    <OrbLayout
      title="Bombs"
      description="Unleashes a round of bombs into the entire arena, attacking both friendly and enemy pieces. They not only devastate any piece they impact but they also compress tiles down deeper, eventually leaving a hole in the arena floor."
      strategy={
        <>
          <p className="text-gray-400">
            Only use when you are losing and have less squadron pieces in the
            arena. The basic probability of Bombs is that it will even out the
            amount of pieces in the playing field. If there are more pieces in
            the arena from one player, they are more likely to be hit.
          </p>
          <p className="text-gray-400">
            These Bombs will also lower a tile on impact. If the tile can not go
            any lower, the stress of the impact will cause the tile to be
            penetrated, and a hole will be left in its wake. The arena landscape
            will drastically change when Bombs are dropped.
          </p>
          <p className="text-gray-400">
            The amount of Bombs dropped can be estimated by watching a gauge
            that appears next to the power window. The amount of Bombs dropped
            is determined by what size arena you are playing in. Also, keep in
            mind that the amount of Bombs can be doubled, tripled, etc, when
            used in combination with Grow Quadradius.
          </p>
        </>
      }
    />
  );
}
