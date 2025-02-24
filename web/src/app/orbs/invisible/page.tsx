import OrbLayout from "../components/orb-layout/orb-layout";

export default function InvisiblePage() {
  return (
    <OrbLayout
      title="Invisible"
      description="Makes this piece invisible to your opponent. They can still see where the piece is located, but they cannot see what powers it has. Great for setting up surprise attacks or defenses."
      strategy={
        <p className="text-gray-400">
          Use this power to hide your piece&apos;s capabilities from your
          opponent. They won&apos;t know what powers your piece has until you
          use them, allowing you to set up unexpected combinations and traps.
        </p>
      }
    />
  );
}
