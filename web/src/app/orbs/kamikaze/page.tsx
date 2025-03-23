import OrbLayout from "../components/orb-layout/orb-layout";

export default function KamikazePage() {
  return (
    <OrbLayout
      title="Kamikaze"
      description="Self destruction of your piece and all the surrounding pieces. Kamikaze only works if an enemy piece will be destroyed. This comes in useful when searching for invisible pieces, as you can repeatedly activate it if no visible enemy pieces are affected. Available in three variants: row, column, radial."
      strategy={
        <p>
          It is a strong power, but technically not as easy to use as its
          counterpart, Destroy. This power does not distinguish between any
          pieces, and <span style={{ fontStyle: "italic" }}>all</span> will
          succumb to its violent outburst. Best if used when you are set to lose
          as few as possible pieces, while maximizing the damage done to your
          opponent.
        </p>
      }
      multiDimensional={true}
    ></OrbLayout>
  );
}
