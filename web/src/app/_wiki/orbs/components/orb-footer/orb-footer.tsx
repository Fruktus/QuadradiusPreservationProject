import Link from "next/link";
import React from "react";

const OrbFooter = () => {
  return (
    <div className="mt-10">
      <Link href="/orbs" className="text-blue-600 hover:text-blue-800">
        ← Back to Powers List
      </Link>
    </div>
  );
};

export default OrbFooter;
