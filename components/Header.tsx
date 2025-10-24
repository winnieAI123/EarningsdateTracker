import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="text-center py-8 md:py-12">
      <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-300 mb-2">
        上市公司业绩会议追踪器
      </h1>
      <p className="text-lg text-gray-400">
        由 Gemini API 驱动，实时追踪您关注的公司的下一次业绩发布会
      </p>
    </header>
  );
};

export default Header;
