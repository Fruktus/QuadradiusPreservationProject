const MultiDimention = () => {
  return (
    <div className="mt-3">
      <p className="inline-flex items-center">
        Multi-dimensional orb
        <span className=" ml-2 inline-flex items-center justify-center w-4 h-4 bg-white rounded-full text-black font-bold text-xs relative group cursor-pointer">
          ?
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            This power can be used in row, column or radial
          </div>
        </span>
      </p>
    </div>
  );
};

export default MultiDimention;
