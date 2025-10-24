import React, { useState } from 'react';
import Header from './components/Header';
import CompanyCard from './components/CompanyCard';
import ErrorDisplay from './components/ErrorDisplay';
import { fetchSingleCompanyEarningsDate } from './services/geminiService';
import type { CompanyEarningsProfile, CategorizedCompanies, Company } from './types';
import { CATEGORIZED_COMPANIES } from './constants';

const App: React.FC = () => {
  const [companies, setCompanies] = useState<CategorizedCompanies>(CATEGORIZED_COMPANIES);
  const [loadingTickers, setLoadingTickers] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleCardClick = async (clickedCompany: CompanyEarningsProfile) => {
    if (loadingTickers.length > 0) return;

    setLoadingTickers([clickedCompany.ticker]);
    setError(null);

    try {
      const earningsInfo = await fetchSingleCompanyEarningsDate(clickedCompany);
      // FIX: Replaced state update to use a more explicit loop. This helps TypeScript's inference engine
      // preserve the `CategorizedCompanies` type, which was being lost and causing `unknown` type errors.
      setCompanies(prevCategorizedCompanies => {
        const newCompanies: CategorizedCompanies = {};
        for (const category in prevCategorizedCompanies) {
          if (Object.prototype.hasOwnProperty.call(prevCategorizedCompanies, category)) {
            newCompanies[category] = prevCategorizedCompanies[category].map(company =>
              company.ticker === clickedCompany.ticker
                ? { ...company, ...earningsInfo }
                : company
            );
          }
        }
        return newCompanies;
      });
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("一个未知错误发生了。");
      }
    } finally {
      setLoadingTickers([]);
    }
  };

  const handleUpdateCategoryClick = async (category: string, companiesToUpdate: Company[]) => {
    if (loadingTickers.length > 0) return;

    const tickersToLoad = companiesToUpdate.map(c => c.ticker);
    setLoadingTickers(tickersToLoad);
    setError(null);

    const results = await Promise.allSettled(
      companiesToUpdate.map(company => fetchSingleCompanyEarningsDate(company))
    );

    const failedTickers: string[] = [];

    // FIX: Explicitly typing the new state object preserves the 'CategorizedCompanies' type.
    // Without this, TypeScript's inference can widen the type, leading to 'unknown' type errors.
    setCompanies(prevCompanies => {
      const newCompaniesInCategory = [...prevCompanies[category]];
      
      results.forEach((result, index) => {
        const company = companiesToUpdate[index];
        const targetIndex = newCompaniesInCategory.findIndex(c => c.ticker === company.ticker);
        
        if (targetIndex === -1) return;

        if (result.status === 'fulfilled') {
          newCompaniesInCategory[targetIndex] = { ...newCompaniesInCategory[targetIndex], ...result.value };
        } else {
          console.error(`Failed to fetch for ${company.ticker}:`, result.reason);
          failedTickers.push(company.ticker);
        }
      });
      const newCompanies: CategorizedCompanies = {
        ...prevCompanies,
        [category]: newCompaniesInCategory,
      };
      return newCompanies;
    });


    if (failedTickers.length > 0) {
      setError(`无法为以下公司获取数据: ${failedTickers.join(', ')}。`);
    }

    setLoadingTickers([]);
  };
  
  const categoryChineseToEnglish: Record<string, string> = {
    '科技': 'Technology',
    '消费': 'Consumer',
    '教育': 'Education'
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans">
      <div className="absolute inset-0 -z-10 h-full w-full bg-gray-900 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]">
        <div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-blue-500/20 opacity-20 blur-[100px]"></div>
      </div>
      <main className="container mx-auto px-4 py-8">
        <Header />
        
        {error && <div className="my-6"><ErrorDisplay message={error} /></div>}

        <div className="space-y-16">
          {Object.entries(companies).map(([category, companyList]) => {
             const isUpdatingCategory = companyList.every(c => loadingTickers.includes(c.ticker)) && loadingTickers.length > 0;

            return (
              <section key={category}>
                <div className="flex flex-col sm:flex-row justify-between items-center mb-8">
                    <h2 className="text-3xl font-bold text-white mb-4 sm:mb-0">
                        {category} <span className="text-gray-500 text-2xl font-light">• {categoryChineseToEnglish[category]}</span>
                    </h2>
                    <button
                        onClick={() => handleUpdateCategoryClick(category, companyList)}
                        disabled={loadingTickers.length > 0}
                        className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-lg transition-colors duration-300 shadow-lg hover:shadow-blue-500/50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-opacity-75 flex items-center justify-center"
                        aria-label={`一键更新${category}分类的业绩会议日期`}
                    >
                        {isUpdatingCategory ? (
                        <>
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>正在更新{category}类...</span>
                        </>
                        ) : (
                        <span>一键更新{category}类</span>
                        )}
                    </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {companyList.map((company) => (
                    <CompanyCard 
                      key={company.ticker} 
                      company={company} 
                      isLoading={loadingTickers.includes(company.ticker)}
                      onClick={() => handleCardClick(company)}
                    />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      </main>
    </div>
  );
};

export default App;
