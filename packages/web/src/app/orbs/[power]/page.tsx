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
    description:
      "Removes all the existing Power Orbs in the arena and replaces them with newly positioned ones. Useful when the current layout is benefiting your opponent, whereas a rehashed layout of orbs may benefit you more.",
    strategy:
      "Wait to use it when there are many Orbs in the arena, and your opponent is one move away from landing on an Orb. Let them waste their time positioning their pieces to gain Orbs, then hit them when they are about to cash in on their goal.",
  },
  "grow-quadradius": {
    name: "Grow Quadradius",
    description:
      "Extends the effective range of row, column, and radial type powers. Row and column powers are widened, while radial powers extend farther outward. Each time it's used, the Quadradius is extended even farther.",
    strategy:
      "A Grow Quadradius is only good if that piece has, or will have, range like powers. So if you don't have any range like powers (radial, row, column), make it your priority to acquire some with that piece. A normal radial power reaches 8 surrounding tiles, but when increased with a Grow Quadradius, it reaches 24 tiles! Same goes for row and column range powers.",
  },
  bombs: {
    name: "Bombs",
    description:
      "Unleashes a round of bombs into the entire arena. They not only devastate any piece they impact but they also compress tiles down deeper, eventually leaving a hole in the arena floor.",
    strategy:
      "Only use when you are losing and have less squadron pieces in the arena. The basic probability of Bombs is that it will even out the amount of pieces in the playing field. If there are more pieces in the arena from one player, they are more likely to be hit.",
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
  "smart-bombs": {
    name: "Smart Bombs",
    description:
      "Unleashes a round of smart bombs that will avoid your own squadron. They not only devastate any piece they impact but they also compress tiles down deeper, eventually leaving a hole in the arena floor.",
    strategy:
      "These are more intelligent than their weaker cousin, Bombs. While they will still appear to be randomly dropped on the arena, they will never strike your own squadron. This causes the Smart Bombs not only to be safely activated, but the probability of hitting your opponent is increased.",
  },
  "snake-tunneling": {
    name: "Snake Tunneling",
    description:
      "Energy tunnels below your piece, blindly seeking out opponents to destroy. This energy burrows thru the arena, randomly exploring, backtracking, and criss-crossing, forcing upwards any tile it encounters.",
    strategy:
      "This power has two main aspects: elevating tiles and destroying opponents. It's best used when opponents are nearby and when activated from the center of the arena to maximize coverage. The snaking range can be enhanced with Grow Quadradius.",
  },
  "raise-tile": {
    name: "Raise Tile",
    description:
      "Some tiles may be too high to step up to. By raising a tile high enough, you can climb out of holes or step onto higher platforms. You can also raise your tile high enough to help avoid an attacking opponent.",
    strategy:
      "A single raise will generally not protect you from approaching opponents, for a single step is easily climbed. However two used together can raise your tile high enough to avoid weak opponents.",
  },
  "lower-tile": {
    name: "Lower Tile",
    description:
      "You can lower a tile to form strategically placed stepping stones. If you have pieces trapped in a pit, a higher up piece can lower tiles to carve out steps. Other pieces can then move to higher platforms.",
    strategy:
      "Usually lowering a tile is not a good idea, so this power is harder to use properly. One good technique is to use it right before you use an Invert power. A lowered tile, when Inverted, will become an elevated tile.",
  },
  "climb-tile": {
    name: "Climb Tile",
    description:
      "Able to move to a tile no matter how high it is. Great for scaling walls, reaching platforms, or getting out of pits. Eliminates the need for steps. Does not affect tile elevation and will leave others trapped.",
    strategy:
      "Once this power is activated, consider the arena flat for this piece. No height is off limits. Not as effective in a flat, neutral arena, but once the landscape is disrupted, this piece can become quite valuable.",
  },
  "teach-radial": {
    name: "Teach Radial",
    description:
      "Teaches all powers from this piece to any friendly pieces in a radial pattern around it. The range of this power can be extended with Grow Quadradius.",
    strategy:
      "Use this to spread powerful combinations of powers to multiple pieces at once. Most effective when your pieces are positioned in a cluster and the teaching piece has valuable powers to share.",
  },
  "teach-row": {
    name: "Teach Row",
    description:
      "Teaches all powers from this piece to any friendly pieces in the same row. The width of this power can be extended with Grow Quadradius.",
    strategy:
      "Best used when your pieces are aligned horizontally. Position your teaching piece at one end of the row to maximize the number of pieces that can learn its powers.",
  },
  "teach-column": {
    name: "Teach Column",
    description:
      "Teaches all powers from this piece to any friendly pieces in the same column. The width of this power can be extended with Grow Quadradius.",
    strategy:
      "Best used when your pieces are aligned vertically. Position your teaching piece at the top or bottom of the column to maximize the number of pieces that can learn its powers.",
  },
  "2x": {
    name: "2x",
    description:
      "Doubles the effectiveness of all powers on this piece. When used multiple times, powers can be quadrupled, octupled, etc.",
    strategy:
      "Best used on pieces that have powerful offensive abilities like Destroy or Recruit. Multiple 2x powers can be stacked for exponential effects.",
  },
  beneficiary: {
    name: "Beneficiary",
    description:
      "When this piece is destroyed, all its powers are transferred to the piece that destroyed it. A clever way to pass powers between your own pieces.",
    strategy:
      "Load up a piece with useful powers and Beneficiary, then let it be captured by one of your other pieces to consolidate powers. Can also be used as a trap for opponents.",
  },
  scavenger: {
    name: "Scavenger",
    description:
      "When any piece is destroyed, this piece has a chance to acquire one of its powers. Works on both friendly and enemy pieces.",
    strategy:
      "Position Scavenger pieces near combat zones to maximize chances of acquiring powers. Multiple Scavengers increase the odds of collecting powers from destroyed pieces.",
    memberOnly: true,
  },
  "power-plant": {
    name: "Power Plant",
    description:
      "Generates a new random power for this piece at regular intervals. The power generated is chosen from all available powers in the game.",
    strategy:
      "Keep Power Plant pieces protected as they accumulate powers over time. Combine with teaching abilities to spread the generated powers to other pieces.",
    memberOnly: true,
  },
  "purify-radial": {
    name: "Purify Radial",
    description:
      "Removes all powers from enemy pieces in a radial pattern around this piece. The range can be extended with Grow Quadradius.",
    strategy:
      "Use to neutralize powerful enemy pieces that have accumulated many abilities. Most effective when multiple enemy pieces are clustered together.",
  },
  "purify-row": {
    name: "Purify Row",
    description:
      "Removes all powers from enemy pieces in the same row as this piece. The width can be extended with Grow Quadradius.",
    strategy:
      "Best used when enemy pieces are aligned horizontally. Position your piece at one end of the row to maximize the number of pieces affected.",
  },
  "purify-column": {
    name: "Purify Column",
    description:
      "Removes all powers from enemy pieces in the same column as this piece. The width can be extended with Grow Quadradius.",
    strategy:
      "Best used when enemy pieces are aligned vertically. Position your piece at the top or bottom of the column to maximize the number of pieces affected.",
  },
  "tripwire-radial": {
    name: "Tripwire Radial",
    description:
      "Creates invisible tripwires in a radial pattern that trigger when enemy pieces move through them. The range can be extended with Grow Quadradius.",
    strategy:
      "Place tripwires around key positions or choke points to control enemy movement. Multiple overlapping tripwires can create effective defensive zones.",
  },
  "tripwire-row": {
    name: "Tripwire Row",
    description:
      "Creates invisible tripwires along the row that trigger when enemy pieces move through them. The width can be extended with Grow Quadradius.",
    strategy:
      "Use to create horizontal barriers that enemies must cross. Can be combined with other row powers to create layered defenses.",
  },
  "tripwire-column": {
    name: "Tripwire Column",
    description:
      "Creates invisible tripwires along the column that trigger when enemy pieces move through them. The width can be extended with Grow Quadradius.",
    strategy:
      "Use to create vertical barriers that enemies must cross. Can be combined with other column powers to create layered defenses.",
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
