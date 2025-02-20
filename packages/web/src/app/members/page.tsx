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
      "Access to all orbs and powers",
      "Create private matches",
      "Custom player profile",
      "Ad-free experience",
      "Priority server access",
    ],
    requirements: ["Monthly subscription", "Valid email verification"],
  },
];

export default function MembersPage() {
  return (
    <div className="prose max-w-none">
      <h2 className="text-2xl font-bold mb-6">Membership Levels</h2>
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
              <h4 className="text-lg font-medium mb-2">Benefits:</h4>
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
                <h4 className="text-lg font-medium mb-2">Requirements:</h4>
                <ul className="list-disc pl-5 space-y-1">
                  {level.requirements.map((req, index) => (
                    <li key={index} className="text-gray-600">
                      {req}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
