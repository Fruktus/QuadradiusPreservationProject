import OrbLayout from "../components/orb-layout/orb-layout";

export default function KamikazePage() {
  return (
    <OrbLayout
      title="Kamikaze"
      description="Self destruction of your piece and all the surrounding pieces. Helpful if you have infiltrated a cluster of your opponents pieces or if you find yourself about to fall victim to an opponents attack. Available in three variants:"
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
    >
      <ul>
        <li>Kamikaze Radial: Affects pieces surrounding you</li>
        <li>Kamikaze Row: Affects pieces in your row</li>
        <li>Kamikaze Column: Affects pieces in your column</li>
      </ul>
    </OrbLayout>
  );
}
