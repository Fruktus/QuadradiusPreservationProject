import OrbLayout from "../components/orb-layout/orb-layout";

export default function ParasitePage() {
  return (
    <OrbLayout
      title="Parasite"
      description="Leeches onto the power absorbing mechanism of opponents. Any forthcoming powers they acquire, so do you. Also shares leeched powers with your whole network of parasitic pieces. Available in three variants:"
      strategy={
        <p>
          A good player will try to avoid getting Power Orbs when they are
          infected with Parasite, but sometimes they have little choice. Even if
          you infect your opponent with different pieces from your squadron,
          they are all in the same parasitic sharing network. So even if an
          opponent is infected, infect them again with another one of your
          pieces. Or infect another opponent&apos;s piece with another one of
          yours. Whenever any one infected piece lands on an Orb and acquires
          the power, all of your pieces that have unleashed a parasite will
          absorb this single power.
        </p>
      }
      multiDimensional={true}
    >
      <ul>
        <li>Parasite Radial: Affects opponents surrounding you</li>
        <li>Parasite Row: Affects opponents in your row</li>
        <li>Parasite Column: Affects opponents in your column</li>
      </ul>
    </OrbLayout>
  );
}
