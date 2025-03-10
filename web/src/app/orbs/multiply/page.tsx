import OrbLayout from "../components/orb-layout/orb-layout";

export default function MultiplyPage() {
  return (
    <OrbLayout
      title="Multiply"
      description="Generates a new piece in the arena. This new piece will have no powers of its own, but by adding pieces, you gain more coverage and control of the battle arena and limit your opponent's movement."
      strategy={
        <p className="text-gray-400">
          Use it to confront an opponent and entice them to jump your newly
          formed piece. Then jump them back, and you come out of the
          confrontation ahead.
        </p>
      }
    />
  );
}
