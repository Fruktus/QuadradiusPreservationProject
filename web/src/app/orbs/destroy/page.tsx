import OrbLayout from "../components/orb-layout/orb-layout";

export default function DestroyPage() {
  return (
    <OrbLayout
      title="Destroy"
      description="Annihilate any piece in your path. This power allows you to remove a single piece from the board, regardless of its position."
      strategy={
        <p>
          Destroy is a precise and powerful tool, best used to eliminate key
          pieces of your opponent&apos;s strategy. Use it to break through
          defenses or to remove a threatening piece that could turn the tide
          against you.
        </p>
      }
    />
  );
}
