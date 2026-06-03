import OrbLayout from "../components/orb-layout/orb-layout";

export default function TwoXPage() {
  return (
    <OrbLayout
      title="2x"
      description="Doubles the amount of powers your piece currently possesses. Best strategy is to wait until you acquire as many powers as possible before using it. This way you can maximize your gain."
      strategy={
        <p className="text-gray-400">
          While you can acquire more than one 2x Power, you can not self-double
          a 2x Power (if you could, you could create an infinite amount of
          powers). Try to hold onto this power until you build up your
          piece&apos;s inventory. You&apos;ll gain much more. Also, great to use
          in conjunction with Learn or Teach Powers. If this is done correctly,
          your squadron can quickly become a super force that is near impossible
          to defeat.
        </p>
      }
    />
  );
}
