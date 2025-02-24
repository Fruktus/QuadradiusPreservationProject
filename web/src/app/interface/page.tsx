export default function Interface() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Game Interface</h1>

      <div className="prose max-w-none">
        <h2>Cursor Indicators</h2>
        <ul>
          <li>Arrow - Your turn</li>
          <li>Bright arrow - Can select or drag</li>
          <li>Octagon - Not your turn</li>
          <li>Dotted octagon - Wait for effect</li>
          <li>X - Cannot interact</li>
          <li>Exploded asterisk - Turn begins</li>
        </ul>

        <h2>Power Descriptions</h2>
        <p>
          When you get a Power Orb, you can read the name of the power on your
          cursor. A brief description appears in the Power Menu to the right.
          This description will scroll away after a few seconds, so position
          your cursor over it to hold it open.
        </p>

        <h2>Visual Cues</h2>
        <ul>
          <li>Analog dial counters - Show remaining pieces for each player</li>
          <li>Flashing colored light - Indicates current player&apos;s turn</li>
          <li>7 red LEDs - Countdown to new Power Orbs</li>
          <li>5 red LEDs - Number of upcoming Power Orbs</li>
          <li>Timer countdown - Displayed under chat window</li>
        </ul>

        <h2>Chat System</h2>
        <p>
          You can type anywhere in the game while you are playing and send a
          message to your opponent. Just type and hit ENTER.
        </p>
      </div>
    </div>
  );
}
