import OrbLayout from "../components/orb-layout/orb-layout";

export default function OrbicRehashPage() {
  return (
    <OrbLayout
      title="Orbic Rehash"
      description="Removes all the existing Power Orbs in the arena and replaces them with newly positioned ones. Useful when the current layout is benefiting your opponent, whereas a rehashed layout of orbs may benefit you more."
      strategy={
        <p className="text-gray-400">
          Wait to use it when there are many Orbs in the arena, and your
          opponent is one move away from landing on an Orb. Let them waste their
          time positioning their pieces to gain Orbs, then hit them when they
          are about to cash in on their goal. Also good if there are Orbs out of
          reach, such as too high, landlocked, or behind your opponents
          defenses.
        </p>
      }
    />
  );
}
