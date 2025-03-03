export default function Gameplay() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Gameplay</h1>

      <div className="prose max-w-none">
        <h2>Basic Rules</h2>
        <p>
          You and your opponent both start off with an equal amount of pieces in
          your squadron. You can move your piece in any of four directions to
          advance or retreat. Those directions are up, down, left, and right.
        </p>

        <h2>Movement</h2>
        <p>
          You begin by picking up any piece of yours, and move it in any of
          those directions, one tile space at a time. Your goal is to approach
          and jump on the pieces of your opponent&apos;s squadron to eliminate
          them.
        </p>

        <h2>Power Orbs</h2>
        <p>
          There are random Orbs that appear in the arena. These are Power Orbs,
          and considered a commodity by Quadradius players. When you land on
          these, you absorb 1 of over 70 powers. This power is now in the
          inventory of that piece and you can use it at any time.
        </p>

        <h2>Terrain Changes</h2>
        <p>
          At some point later in the game, certain powers will cause the arena
          landscape to begin to change. Tiles will be raised or lowered. You can
          easily jump down to a lower tile, or walk up a step that is slightly
          higher than your piece, but you can not climb up tiles that are higher
          than a single step.
        </p>

        <div className="bg-yellow-50 p-4 rounded mt-6">
          <h3 className="font-semibold text-yellow-800">Warning:</h3>
          <p className="text-gray-800">
            Don&apos;t get overzealous with the powers. If you get 10 or more of
            any single power on any single piece, you can overheat. The
            mechanized torus was not built to withstand this type of power
            storage and the core will melt down.
          </p>
        </div>
      </div>
    </div>
  );
}
