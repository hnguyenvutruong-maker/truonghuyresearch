export type ValuationDownload = {
  label: string;
  href: string;
  format: 'XLSX' | 'XLS' | 'ZIP';
  sourceTemplate: string;
  sheets: string[];
};

export type ValuationModel = {
  ticker: string;
  company: string;
  sector: string;
  methods: string[];
  summary: string;
  downloads: ValuationDownload[];
};

export const valuationModels: ValuationModel[] = [
  {
    ticker: 'HPG',
    company: 'Hoa Phat Group',
    sector: 'Steel & Industrial Materials',
    methods: ['DCF', 'Comparable Analysis'],
    summary: 'Industrial cyclicality model pack with intrinsic value and public-market multiple cross-checks.',
    downloads: [
      {
        label: 'DCF',
        href: '/research/valuation-models/hpg-dcf-analysis.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- DCF Analysis_Template.xlsx',
        sheets: ['DCF', 'NWC', 'WACC', 'A1', 'A2'],
      },
      {
        label: 'Comparable Analysis',
        href: '/research/valuation-models/hpg-comparable-analysis.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- Comparable Companies_Template.xlsx',
        sheets: ['List', 'Benchmarking 1', 'Benchmarking 2', 'Ouput', 'TargetCo', 'CompCo 1-15'],
      },
    ],
  },
  {
    ticker: 'BID',
    company: 'BIDV',
    sector: 'Banking',
    methods: ['Comparable Analysis'],
    summary: 'Bank valuation workflow centered on peer multiples, benchmarking pages, and target-company inputs.',
    downloads: [
      {
        label: 'Comparable Analysis',
        href: '/research/valuation-models/bid-comparable-analysis.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- Comparable Companies_Template.xlsx',
        sheets: ['List', 'Benchmarking 1', 'Benchmarking 2', 'Ouput', 'TargetCo', 'CompCo 1-15'],
      },
    ],
  },
  {
    ticker: 'FPT',
    company: 'FPT Corporation',
    sector: 'Technology & IT Services',
    methods: ['DCF', 'Comparable Analysis'],
    summary: 'Growth-company model pack combining forecast-driven DCF and public peer valuation checks.',
    downloads: [
      {
        label: 'DCF',
        href: '/research/valuation-models/fpt-dcf-analysis.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- DCF Analysis_Template.xlsx',
        sheets: ['DCF', 'NWC', 'WACC', 'A1', 'A2'],
      },
      {
        label: 'Comparable Analysis',
        href: '/research/valuation-models/fpt-comparable-analysis.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- Comparable Companies_Template.xlsx',
        sheets: ['List', 'Benchmarking 1', 'Benchmarking 2', 'Ouput', 'TargetCo', 'CompCo 1-15'],
      },
    ],
  },
  {
    ticker: 'BMP',
    company: 'Binh Minh Plastics',
    sector: 'Building Materials',
    methods: ['Precedent Transactions', 'LBO'],
    summary: 'Transaction-led valuation set pairing acquisition multiples with sponsor-return analysis.',
    downloads: [
      {
        label: 'Precedent Transactions',
        href: '/research/valuation-models/bmp-precedent-transactions.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- Precedent Transactions_Template.xlsx',
        sheets: ['List', 'Output', 'ACQR;TRGT 1-10'],
      },
      {
        label: 'LBO',
        href: '/research/valuation-models/bmp-lbo-analysis.xls',
        format: 'XLS',
        sourceTemplate: 'LBO Analysis_Completed.xls',
        sheets: ['Cover', 'TS', 'IS', 'BS', 'CF', 'DS', 'RA', 'A1', 'A2', 'A3'],
      },
    ],
  },
  {
    ticker: 'PNJ',
    company: 'Phu Nhuan Jewelry',
    sector: 'Consumer Retail',
    methods: ['LBO', 'Comparable / Precedent'],
    summary: 'Retail valuation set with sponsor-return analysis and a combined public/transaction multiple pack.',
    downloads: [
      {
        label: 'LBO',
        href: '/research/valuation-models/pnj-lbo-analysis.xls',
        format: 'XLS',
        sourceTemplate: 'LBO Analysis_Completed.xls',
        sheets: ['Cover', 'TS', 'IS', 'BS', 'CF', 'DS', 'RA', 'A1', 'A2', 'A3'],
      },
      {
        label: 'Comparable / Precedent',
        href: '/research/valuation-models/pnj-comparable-precedent-analysis.zip',
        format: 'ZIP',
        sourceTemplate: 'SV- Comparable Companies_Template.xlsx + SV- Precedent Transactions_Template.xlsx',
        sheets: ['Comparable: List, Benchmarking, Ouput, CompCo 1-15', 'Precedent: List, Output, ACQR;TRGT 1-10'],
      },
    ],
  },
];
