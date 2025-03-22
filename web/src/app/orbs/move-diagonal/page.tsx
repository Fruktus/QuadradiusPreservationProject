import OrbLayout from "../components/orb-layout/orb-layout";

export default function MoveDiagonalPage() {
  return (
    <OrbLayout
      title="Move Diagonal"
      description="This piece can now also move on a diagonal. Can be used as a way to move more quickly, slip between diagonal walls or over diagonal pits, or can be used to take an opponent by surprise and attack them."
      strategy={
        <p>
          It is very easy to chase down an opponent if you have Move Diagonal
          activated. Whenever they try to change direction, you can close in
          faster, since your movements cover more ground. In fact, most players
          are very accustomed to the up-down-left-right movement in the game
          that they fail to catch all possible choices when using or defending
          against a Move Diagonal piece. Be aware of this, and use it to your
          advantage.
        </p>
      }
    />
  );
}
