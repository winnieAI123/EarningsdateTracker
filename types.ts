export interface Company {
  name: string;
  ticker: string;
  domain: string;
  chineseName: string;
}

export interface EarningsData {
  company_name: string;
  ticker: string;
  earnings_date: string;
  notes?: string;
}

export interface CompanyEarningsProfile extends Company {
  earnings_date?: string;
  notes?: string;
}

export type CategorizedCompanies = Record<string, CompanyEarningsProfile[]>;
