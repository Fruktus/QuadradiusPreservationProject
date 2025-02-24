import OrbLayout from "../components/orb-layout/orb-layout";

export default function SmartBombsPage() {
  return (
    <OrbLayout
      title="Smart Bombs"
      description="Unleashes a round of smart bombs that will avoid your own squadron. They not only devastate any piece they impact but they also compress tiles down deeper, eventually leaving a hole in the arena floor."
      strategy={
        <>
          <p className="text-gray-400">
            These are more intelligent than their weaker cousin, Bombs. While
            they will still appear to be randomly dropped on the arena, they
            will never strike your own squadron. This causes the Smart Bombs not
            only to be safely activated, but the probability of hitting your
            opponent is increased.
          </p>
          <p className="text-gray-400">
            These Smart Bombs will also lower a tile on impact. If the tile can
            not go any lower, the stress of the impact will cause the tile to be
            penetrated, and a hole will be left in its wake. The arena landscape
            will drastically change when Smart Bombs are dropped.
          </p>
          <p className="text-gray-400">
            The amount of Smart Bombs dropped can be estimated by watching a
            gauge that appears next to the power window. The amount of Smart
            Bombs dropped is determined by what size arena you are playing in.
            Also, keep in mind that the amount of Bombs can be doubled, tripled,
            etc, when combined with Grow Quadradius.
          </p>
        </>
      }
    />
  );
}
