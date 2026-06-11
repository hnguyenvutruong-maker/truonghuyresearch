export type ValuationDownload = {
  label: string;
  href: string;
  format: 'XLSX' | 'XLS' | 'ZIP';
  sourceTemplate: string;
  sheets: string[];
};

export type ValuationNote = {
  method: string;
  price: string;
  assumptions: string;
  result: string;
};

export type ValuationModel = {
  ticker: string;
  company: string;
  sector: string;
  methods: string[];
  summary: string;
  conclusion: string;
  valuationNotes: ValuationNote[];
  downloads: ValuationDownload[];
};

export const valuationModels: ValuationModel[] = [
  {
    ticker: 'HPG',
    company: 'Hoa Phat Group',
    sector: 'Steel & Industrial Materials',
    methods: ['DCF', 'Comparable Analysis'],
    summary: 'Industrial cyclicality model pack with intrinsic value and public-market multiple cross-checks.',
    conclusion: 'DCF is deliberately conservative because of leverage and capex-cycle pressure; the market multiple cross-check supports a mid-20k/share valuation range.',
    valuationNotes: [
      {
        method: 'DCF',
        price: 'VND 13.4k/share',
        assumptions: 'WACC 10.5%, exit EV/EBITDA 7.0x, and 2026-2030 sales growth tapering from 14.0% to 3.0%.',
        result: 'Intrinsic value is below spot, mainly from conservative free-cash-flow assumptions through the capacity cycle.',
      },
      {
        method: 'Comparable Analysis',
        price: 'VND 23.4k-26.1k/share',
        assumptions: 'Steel peer median P/E of 10.5x-13.0x and EV/EBITDA around 7.1x.',
        result: 'Public-market multiples are closer to the current share price and act as the valuation cross-check.',
      },
    ],
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
    conclusion: 'BID screens mixed: forward P/E implies downside while LTM P/E is higher because normalized bank earnings are still moving through the base.',
    valuationNotes: [
      {
        method: 'Comparable Analysis',
        price: 'VND 32.7k-52.2k/share',
        assumptions: 'Vietnam bank peer median P/E of 7.0x-7.7x forward and 7.2x LTM, benchmarked against listed banks.',
        result: 'Forward multiples point below spot; the LTM read is higher, so the model flags dispersion rather than a single clean target.',
      },
    ],
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
    conclusion: 'Both approaches support upside, with DCF producing the higher value because it capitalizes sustained IT-services growth and margin durability.',
    valuationNotes: [
      {
        method: 'DCF',
        price: 'VND 132.5k/share',
        assumptions: 'WACC 9.5%, exit EV/EBITDA 14.0x, and revenue growth tapering from 12.0% to 8.0%.',
        result: 'Cash-flow valuation is materially above spot under the base growth and margin assumptions.',
      },
      {
        method: 'Comparable Analysis',
        price: 'VND 90.0k-92.8k/share',
        assumptions: 'Tech and telecom peer median P/E of 14.0x-16.9x and EV/EBITDA of 7.4x-9.4x.',
        result: 'Comparable analysis supports upside, but it is less aggressive than the DCF case.',
      },
    ],
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
    conclusion: 'The transaction premium and LBO return case cluster tightly around the low- to mid-160k/share range.',
    valuationNotes: [
      {
        method: 'Precedent Transactions',
        price: 'Approx. VND 167.0k/share',
        assumptions: 'Median precedent premium of 23.5%, EV/Sales 1.0x, EV/EBITDA 4.7x, and P/E 6.4x.',
        result: 'Control-premium analysis lands slightly above the LBO offer value.',
      },
      {
        method: 'LBO',
        price: 'VND 162.2k/share',
        assumptions: '20.0% control premium, entry EV/EBITDA around 8.5x, exit EV/EBITDA 7.5x, and 20.1% IRR.',
        result: 'Sponsor case clears the return hurdle near the precedent transaction check.',
      },
    ],
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
    conclusion: 'PNJ has a broad valuation spread: LBO and precedent premium cluster near 80k/share, while public retail peers imply a much higher trading-multiple range.',
    valuationNotes: [
      {
        method: 'LBO',
        price: 'VND 80.0k/share',
        assumptions: '25.0% control premium, entry EV/EBITDA around 12.2x, exit EV/EBITDA 7.5x, and 20.1% IRR.',
        result: 'Sponsor case supports a premium to spot and aligns with the precedent premium check.',
      },
      {
        method: 'Comparable / Precedent',
        price: 'Comparable VND 112.9k-140.2k; precedent approx. VND 81.6k',
        assumptions: 'Retail peer P/E of 17.0x-20.4x and EV/EBITDA of 9.5x-11.7x; precedent premium of 27.5%.',
        result: 'Public peers screen well above spot, while transaction premium evidence is closer to the LBO output.',
      },
    ],
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
