import OrbLayout from "../components/orb-layout/orb-layout";

export default function SnakeTunnelingPage() {
  return (
    <OrbLayout
      title="Snake Tunneling"
      description="Creates a winding random path which raises tiles to the maximum level, and destroys any enemy pieces residing on those tiles."
      strategy={
        <p className="text-gray-400">
          Use when enemy pieces are nearby, as the tunnel may hit them in its
          random path. The raised tiles can also create barriers or paths.
          Combine with Grow Quadradius to extend the tunnel&apos;s reach and
          coverage area.
        </p>
      }
    />
  );
}
