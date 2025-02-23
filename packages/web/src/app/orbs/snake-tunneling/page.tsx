import OrbLayout from "../components/orb-layout/orb-layout";

export default function SnakeTunnelingPage() {
  return (
    <OrbLayout
      title="Snake Tunneling"
      description="Energy tunnels below your piece, blindly seeking out opponents to destroy. This energy burrows thru the arena, randomly exploring, backtracking, and criss-crossing, forcing upwards any tile it encounters."
      strategy={
        <>
          <p className="text-gray-400">
            This power has two main aspects to it. First, it is a great way to
            elevate tiles. It can be used to build you out of a hole, or form
            snake like, elevated walk ways. Second, this power will destroy any
            opponent it comes in contact with.
          </p>
          <p className="text-gray-400">
            Since this power will snake out from the piece that activated it,
            it's best if used when your opponent is nearby. Sometimes, the power
            will back track over tiles it already contacted. This is
            unfortunate. The power has a slightly higher chance of covering new
            ground when it does not run into the edges of the arena. So it is
            best if used when towards the center of the arena.
          </p>
          <p className="text-gray-400">
            Also, the snaking range of this power can be doubled, tripled, etc,
            when combined with Grow Quadradius.
          </p>
        </>
      }
    />
  );
}
