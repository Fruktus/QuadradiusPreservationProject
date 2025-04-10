import { ReactNode } from "react";
import OrbFooter from "../orb-footer/orb-footer";
import MultiDimention from "../multidimention/multidimention";

interface OrbLayoutProps {
  title: string;
  description: string;
  strategy: ReactNode;
  children?: ReactNode;
  multiDimensional?: boolean;
}

export default function OrbLayout({
  title,
  description,
  strategy,
  children,
  multiDimensional,
}: OrbLayoutProps) {
  return (
    <div className="prose max-w-none p-6">
      <div className="flex items-start gap-8">
        <div className="w-1/3">
          <div className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center">
            {/* Placeholder for GIF */}
            <span className="text-gray-400">Animation Coming Soon</span>
          </div>
        </div>

        <div className="w-2/3">
          <div className="flex items-center gap-4 mb-2 justify flex-row">
            <h1 className="text-3xl font-bold inline">{title} </h1>
            {multiDimensional && <MultiDimention />}
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Description</h2>
            <p className="text-gray-400">{description}</p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2">Strategy</h2>
            {strategy}
          </div>

          {children}
        </div>
      </div>

      <OrbFooter />
    </div>
  );
}
