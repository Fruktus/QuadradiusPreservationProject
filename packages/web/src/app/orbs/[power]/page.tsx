export function generateStaticParams() {
  return [{ power: "nothing" }];
}

export default function PowerPage() {
  return (
    <div className="prose max-w-none p-6">
      <h1>Unsupported Power</h1>
    </div>
  );
}
