import OrbLayout from "../components/orb-layout/orb-layout";

export default function SnakeTunnelingPage() {
  return (
    <OrbLayout
      title="Snake Tunneling"
      description="Creates a winding tunnel that can destroy enemy pieces and raise tiles in its path. The tunnel's path is semi-random but tends to seek out nearby enemies."
      strategy={
        <p className="text-gray-400">
          Use when enemy pieces are nearby, as the tunnel tends to seek them
          out. The raised tiles can also create barriers or paths. Combine with
          Grow Quadradius to extend the tunnel&apos;s reach and coverage area.
        </p>
      }
    />
  );
}
