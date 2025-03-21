import OrbLayout from "../components/orb-layout/orb-layout";

export default function ScramblePage() {
  return (
    <OrbLayout
      title="Scramble"
      description="Scrambles the positions of your piece and the surrounding pieces. Chaotic in nature, so should be used when your position could not be worsened."
      strategy={
        <p>
          All the pieces that fall within range of this power&apos;s effect are
          swept up. Then, they are randomly deposited back down onto any of
          tiles, again within range of the Scramble Power. If there are no
          pieces within range, this power can still be used to slightly change
          your position. This power really shines when there are many pieces,
          whether they are your own or your opponents, within range. When they
          all get planted back down, it is still your turn, so you can now
          initiate jumps or activate powers from the new tile locations. It can
          even be used to get to higher elevations, or unstuck other pieces.
          Since it is random, your strategy could fail, but it&apos;t hurt to
          try.
        </p>
      }
      multiDimensional={true}
    />
  );
}
