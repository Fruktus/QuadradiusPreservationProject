import OrbLayout from "../components/orb-layout/orb-layout";

export default function InvisiblePage() {
  return (
    <OrbLayout
      title="Invisible"
      description="Makes this piece invisible to your opponent. They can still hear the sound of movement and see the collected orbs disappear. If an invisible piece is attacked with spyware, it will still remain invisible, but the opponent will see any powers it acquires. Great for setting up surprise attacks or defenses."
      strategy={
        <p className="text-gray-400">
          Use this power to hide your pieces from opponent, making them wary of
          where you&apos;ll hit next.
        </p>
      }
    />
  );
}
