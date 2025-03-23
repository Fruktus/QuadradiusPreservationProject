import OrbLayout from "../components/orb-layout/orb-layout";

export default function JumpProofPage() {
  return (
    <OrbLayout
      title="Jump Proof"
      description="Your piece is shielded from jump attacks. You can easily and safely chase down an opponent. Can also be used as a road block."
      strategy={
        <p>
          After using this power, opponents with powerless pieces will flee from
          your armored piece if you approach. Try to chase down pieces in a
          group, so you will be able to jump some when they try to run. Stay
          within that group, devouring as many pieces as you can. Remember, this
          piece can still be killed with many types of powers, and even taking
          over with a Swap or Recruit Power. Stay focused and don&apos;t waste
          all your moves chasing pieces on the run, for they may be gathering
          powers, or setting you up for a trap as they flee.
        </p>
      }
    />
  );
}
