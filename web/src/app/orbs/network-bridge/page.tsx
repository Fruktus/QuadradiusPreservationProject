import OrbLayout from "../components/orb-layout/orb-layout";

export default function NetworkBridgePage() {
  return (
    <OrbLayout
      title="Network Bridge"
      description="Creates a connection between two pieces, allowing them to share and synchronize their powers. When one piece gains or loses a power, the connected piece is similarly affected."
      strategy={
        <p className="text-gray-400">
          Connect pieces that complement each other&apos;s abilities. When one
          piece acquires new powers through Scavenger or Power Plant, both
          pieces will benefit. Be careful though - if one piece is purified,
          both will lose their powers.
        </p>
      }
    />
  );
}
