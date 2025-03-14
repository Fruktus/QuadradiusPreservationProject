export default function BasicTraining() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Basic Training</h1>

      <div className="prose max-w-none">
        <p>
          When it is your turn, your piece can initially move one space in any
          direction (except diagonal).
        </p>

        <h2>Power Orbs</h2>
        <p>
          Power orbs are what make each game of Quadradius interesting. Jump on
          spaces with power orbs to obtain one of many different powers. You can
          use these powers at any time to beat your opponent.
        </p>

        <h3>Using Powers</h3>
        <p>
          To use a power, click the piece with the power. Then click on the
          power you wish to use.
        </p>

        <h3>Learning About Powers</h3>
        <p>
          To find out what the power you picked does you can read the instructions
          on the right side. You can also press the small question mark on the right
          side of the powerup. Finally, if you don&apos;t know what opponent&apos;s powerup did,
          you can click on it on the Recent Powerups list to learn about it.
        </p>

        <div className="bg-gray-50 p-4 rounded mt-6">
          <h3 className="font-semibold text-gray-800">Quick Tips:</h3>
          <ul className="text-gray-800">
            <li>Move one space at a time in non-diagonal directions</li>
            <li>Collect power orbs by landing on them</li>
            <li>Use powers strategically to gain advantage</li>
            <li>Eliminate opponents by jumping on them</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
