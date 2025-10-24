import React from 'react';
import type { CompanyEarningsProfile } from '../types';

interface CompanyCardProps {
  company: CompanyEarningsProfile;
  isLoading: boolean;
  onClick: () => void;
}

const CalendarIcon: React.FC = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
);

const CardSpinner: React.FC = () => (
  <div className="flex items-center justify-center h-full">
    <svg className="animate-spin h-6 w-6 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
    <span className="ml-3 text-gray-400">查询中...</span>
  </div>
);

const CompanyCard: React.FC<CompanyCardProps> = ({ company, isLoading, onClick }) => {
  const logoUrl = `https://logo.clearbit.com/${company.domain}`;

  return (
    <div 
        className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6 transform transition-all duration-300 hover:scale-105 hover:border-blue-400 shadow-lg hover:shadow-blue-500/20"
        role="button"
        tabIndex={0}
        onClick={!isLoading ? onClick : undefined}
        onKeyDown={(e) => { if (e.key === 'Enter' && !isLoading) onClick() }}
        aria-label={`查询 ${company.chineseName} 的业绩会议日期`}
        style={{ cursor: isLoading ? 'wait' : 'pointer' }}
    >
      <div className="flex items-center mb-4">
        <img src={logoUrl} alt={`${company.name} logo`} className="h-10 w-10 rounded-full mr-4 bg-white p-1 object-contain" />
        <div>
          <h2 className="text-xl font-bold text-white">{company.chineseName}</h2>
          <p className="text-sm text-gray-400">{company.ticker}</p>
        </div>
      </div>
      <div className="mt-6">
        <p className="text-sm text-gray-300 mb-2">下次业绩会议日期</p>
        <div className="flex items-center bg-gray-900 rounded-md p-3 h-[60px]">
           {isLoading ? (
            <CardSpinner />
          ) : company.earnings_date ? (
            <>
              <CalendarIcon />
              <p className="text-2xl font-semibold text-teal-300">{company.earnings_date}</p>
            </>
          ) : (
            <span className="text-blue-400 font-semibold w-full text-center">点击查询最新日期</span>
          )}
        </div>
      </div>
      {company.notes && !isLoading && (
        <div className="mt-4 text-xs text-gray-500 italic">
          <p>* {company.notes}</p>
        </div>
      )}
    </div>
  );
};

export default CompanyCard;
