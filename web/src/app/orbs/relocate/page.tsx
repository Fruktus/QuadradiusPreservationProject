import OrbLayout from "../components/orb-layout/orb-layout";

export default function RelocatePage() {
  return (
    <OrbLayout
      title="Relocate"
      description="This piece will be randomly moved to a new, unoccupied area in the arena. Useful when your position could not be worsened, such as being backed against the wall, or having no Power Orbs close to this piece."
      strategy={
        <>
          <p>
            This is great to use on a piece that is still back with originating
            ally lines, and you wish to quickly move it into the battle zone. Do
            not use it if you are in the center of the board and feel you
            already have a good position. It is best if used when along the
            edges. After all, the odds of getting a better position are greater.
          </p>
          <p>
            A Relocated piece will never land you on your own piece, an
            opponent&apos;s piece, a Power Orb, or a tile with a hole in it.
            Keep these factors in mind when deciding to activate the power. Also
            keep in mind that after you use the power, it is still your turn. So
            if it places you next to your opponent, you can safely jump on them
            with little to no chance of retaliation.
          </p>
        </>
      }
    />
  );
}
