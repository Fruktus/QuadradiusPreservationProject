import Callout from "@/components/callout";

export default function AdvancedTraining() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Advanced Training</h1>

      <div className="prose max-w-none prose-invert">
        <h2>Strategic Power Usage</h2>
        <p>
          TBD
        </p>

        <h2>Terrain Manipulation</h2>
        <p>
          TBD
        </p>

        <h2>Power Stacking</h2>
        <p>
          Multiple powers can be stacked on a single piece, but be cautious - a
          piece with 10 or more of the same power will overheat and be
          destroyed. Use this knowledge both defensively and offensively.
        </p>

        <Callout title="Pro Tip:" variant="info">
        <p className="text-gray-800">
            Don't get overzealous with powers. When an opponent's
            piece has multiple powers, using Pilfer on it will steal all their
            powers. This can be used to turn the tide of the battle.
          </p>
        </Callout>

        <h2>Advanced Tactics</h2>
        <ul className="list-disc ml-6">
          <li>
            Position pieces to threaten multiple opponent pieces simultaneously
          </li>
          <li>
            Create "powerful threats"; by stacking multiple different
            powers on key pieces
          </li>
          <li>
            Use terrain powers to create safe zones where opponents cannot
            easily attack
          </li>
        </ul>

        <Callout title="Warning:" variant="warning">
        <p className="text-gray-800">
            Be wary of opponents who seem to be "charging up"; pieces
            with multiple powers. They may be setting up for a complex
            combination attack. Consider these pieces a priority targets.
          </p>
        </Callout>
      </div>
    </div>
  );
}
