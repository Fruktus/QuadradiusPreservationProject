import OrbLayout from "../components/orb-layout/orb-layout";

export function generateStaticParams() {
  return [{ power: "nothing" }];
}

export default function PowerPage() {
  return (
    <OrbLayout
      title="Unsupported Power"
      description="This power page has not been created yet."
      strategy={
        <p className="text-gray-400">
          Please check back later for information about this power.
        </p>
      }
    />
  );
}
