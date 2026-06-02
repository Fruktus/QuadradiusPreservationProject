import Callout from "@/components/callout";

export default function AdvancedTraining() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Advanced Training</h1>

      <div className="prose max-w-none">
        <h2>Strategic Power Usage</h2>
        <p>
          While collecting powers is important, strategic timing of their use is
          crucial. Consider saving defensive powers for when your opponent is in
          an aggressive position. Some powers can be combined for devastating
          effects - experiment with different combinations.
        </p>

        <h2>Terrain Manipulation</h2>
        <p>
          Advanced players use terrain-altering powers to control the
          battlefield. Creating high ground can protect your pieces while
          limiting enemy movement. Remember that pieces can only climb one level
          at a time, but can fall any distance.
        </p>

        <h2>Power Stacking</h2>
        <p>
          Multiple powers can be stacked on a single piece, but be cautious - a
          piece with 10 or more of the same power will overheat and be
          destroyed. Use this knowledge both defensively and offensively.
        </p>

        <Callout title="Pro Tip:" variant="info">
        <p className="text-gray-800">
            Don&apos;t get overzealous with powers. When an opponent&apos;s
            piece has multiple powers, using Pilfer on it will steal all their
            powers. This can be used to turn the tide of the battle.
          </p>
        </Callout>

        <h2>Advanced Tactics</h2>
        <ul className="list-disc ml-6">
          <li>
            Use Multiply on pieces with powerful abilities to create multiple
            threats
          </li>
          <li>
            Position pieces to threaten multiple opponent pieces simultaneously
          </li>
          <li>
            Create &quot;powerful threats&quot; by stacking multiple different
            powers on key pieces
          </li>
          <li>
            Use terrain powers to create safe zones where opponents cannot
            easily attack
          </li>
        </ul>

        <Callout title="Warning:" variant="warning">
        <p className="text-gray-800">
            Be wary of opponents who seem to be &quot;charging up&quot; pieces
            with multiple powers. They may be setting up for a complex
            combination attack. Consider these pieces a priority targets.
          </p>
        </Callout>
      </div>
    </div>
  );
}
