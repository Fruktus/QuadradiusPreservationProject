import OrbLayout from "../components/orb-layout/orb-layout";

export default function SwapPage() {
  return (
    <OrbLayout
      title="Swap"
      description="Your piece and all the surrounding pieces swap ownership. Can be used to swap positions, plan attacks, gain more pieces, or even gain more powers."
      strategy={
        <p>
          Keep in mind that a Swap always gives the piece you are using to your
          opponent, so don&apos;t use it if you have many powers on that piece.
          In fact, they will get all of your pieces within range, and likewise,
          you will gain all of their pieces. Three things to consider when you
          are about to use this power; Will you profit from the amount of pieces
          received, will you profit from the powers received, and do you stand
          to have a better position in the arena after the swap? Swap can also
          be used to gain ownership of their pieces deep inside a well protected
          area. As with any powers, it is still your turn after the Swap, so you
          will have the first movement after you changed pieces. Now is the time
          to eradicate any piece that you felt was your strongest before you
          swapped. Try to remember what powers you had on the pieces before the
          Swap. It helps to predict how your opponent might use their next turn.
        </p>
      }
      multiDimensional={true}
    />
  );
}
