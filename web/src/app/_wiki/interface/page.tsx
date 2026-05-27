export default function Interface() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Game Interface</h1>

      <div className="prose max-w-none prose-invert">
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
          When you get a Power Orb, you can read the name of the power on your cursor.
          Also, a brief description appears in the Power Menu to the right.
          This description will scroll away after a few seconds, so position your cursor over it to hold it open.
          If you want to re-read a description, click on the question mark listed next to powers, either in the cursor pop up menu, big Power Menu, or by clicking on a recently used power in the chat window.
          The Power Descriptions can be turned off in the Arena Menu.
        </p>

        <h2>Using a Power</h2>
        <p>
          Quickly click on a piece that has a power to bring up and lock onto the pop up power menu, and then click on the power name.
          You can also view a master list of all your powers in the big Power Menu to the right.
          If you click on a power listed there, you can view what pieces possess that power.
          You can then click on the highlight to activate that power.
        </p>

        <h2>Using a Power</h2>
        <p>
          You can type anywhere in the game while you are playing and send a message to your opponent.
          Just type and hit ENTER.
          This is where you do all your smack talk.
        </p>

        <h2>Visual Cues</h2>
        <ul>
          <li>Analog dial counters - Show remaining pieces for each player</li>
          <li>Flashing colored light - Indicates current player&apos;s turn</li>
          <li>7 red LEDs - Countdown to new Power Orbs</li>
          <li>5 red LEDs - Number of upcoming Power Orbs</li>
          <li>Timer countdown - Displayed under chat window</li>
        </ul>

      </div>
    </div>
  );
}
