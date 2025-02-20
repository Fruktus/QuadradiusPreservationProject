import { notFound } from "next/navigation";

interface PowerDetails {
  name: string;
  description: string;
  strategy: string;
  memberOnly?: boolean;
}

const powerDetails: Record<string, PowerDetails> = {
  multiply: {
    name: "Multiply",
    description:
      "Generates a new piece in the arena. This new piece will have no powers of its own, but by adding pieces, you gain more coverage and control of the battle arena and limit your opponent&apos;s movement.",
    strategy:
      "Use it to confront an opponent and entice them to jump your newly formed piece. Then jump them back, and you come out of the confrontation ahead.",
  },
  "cancel-multiply": {
    name: "Cancel Multiply",
    description:
      "Removes a multiplied piece from the board. This power only works on pieces that were created using the Multiply power. It cannot remove original pieces.",
    strategy:
      "Use this to counter your opponent&apos;s Multiply strategy and clear the board of their multiplied pieces. This can help regain control of the board and open up movement paths.",
  },
  "orbic-rehash": {
    name: "Orbic Rehash",
    description: "Replaces all powers on the board with new random powers.",
    strategy:
      "Use this when your opponent has collected powerful orbs or when you're at a disadvantage with your current power distribution.",
  },
  "grow-quadradius": {
    name: "Grow Quadradius",
    description:
      "Increases the size of your piece, making it more imposing on the board.",
    strategy:
      "Use to intimidate opponents and create a stronger presence on the board. Larger pieces can be more effective in controlling territory.",
  },
  bombs: {
    name: "Bombs",
    description: "Places a bomb on the board that explodes when stepped on.",
    strategy:
      "Place bombs strategically to control movement paths and create hazards for your opponent.",
  },
  "network-bridge": {
    name: "Network Bridge",
    description:
      "Creates a connection between two pieces, allowing them to work together.",
    strategy:
      "Use to create strategic connections between your pieces and enhance their effectiveness.",
    memberOnly: true,
  },
  invisible: {
    name: "Invisible",
    description: "Makes your piece invisible to the opponent.",
    strategy:
      "Use this to create uncertainty and force your opponent to guess your piece's location.",
    memberOnly: true,
  },
  // Add all other powers following the same pattern
};

export default function PowerPage({ params }: { params: { power: string } }) {
  const power = powerDetails[params.power];

  if (!power) {
    notFound();
  }

  return <div className="prose max-w-none p-6"></div>;
}
