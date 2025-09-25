import config from "../../../configurations/config.json";

interface MemberInfo {
  rank: string;
  benefits: string[];
  requirements?: string[];
}

const membershipLevels: MemberInfo[] = [
  {
    rank: "Free Player",
    benefits: [
      "Access to basic game features",
      "Play against other players",
      "Basic orbs and powers",
    ],
  },
  {
    rank: "Premium Member",
    benefits: [
      "Custom username without GUEST suffix",
      "Owned account - no imposters",
      "Ranked matches against members",
      "Access to Advanced settings (including board and squadron size, colors, round time)",
      "Access to all orbs and powers",
    ],
    requirements: ["Monthly subscription"],
  },
];

export default function MembersPage() {
  return (
    <div className="prose max-w-none">
      <h2 className="text-2xl font-bold mb-6 mt-4">Membership Levels</h2>
      <div className="grid gap-8 md:grid-cols-2">
        {membershipLevels.map((level) => (
          <div
            key={level.rank}
            className="bg-white p-6 rounded-lg shadow-md border border-gray-200"
          >
            <h3 className="text-xl font-semibold text-blue-600 mb-4">
              {level.rank}
            </h3>

            <div className="mb-4">
              <h4 className="text-lg font-medium mb-2 text-gray-800">
                Benefits:
              </h4>
              <ul className="list-disc pl-5 space-y-1">
                {level.benefits.map((benefit, index) => (
                  <li key={index} className="text-gray-600">
                    {benefit}
                  </li>
                ))}
              </ul>
            </div>

            {level.requirements && (
              <div>
                <h4 className="text-lg font-medium mb-2 text-gray-800">
                  Requirements:
                </h4>
                <ul className="list-disc pl-5 space-y-1">
                  <li className="text-gray-600">
                    Free registration via{" "}
                    <a
                      href={config.discordRegistration}
                      target="_blank"
                      className="text-blue-600 hover:text-blue-800"
                    >
                      Discord
                    </a>
                  </li>
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
