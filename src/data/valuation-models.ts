export type ValuationGroupId = 'dcf' | 'comparable' | 'transaction-lbo';

export type ValuationGroup = {
  id: ValuationGroupId;
  title: string;
  eyebrow: string;
  description: string;
};

export type ValuationDownload = {
  label: string;
  href: string;
  format: 'XLSX' | 'XLS' | 'ZIP';
  sourceTemplate: string;
  sheets: string[];
  groups: ValuationGroupId[];
};

export type ValuationNote = {
  method: string;
  price: string;
  assumptions: string;
  result: string;
  groups: ValuationGroupId[];
};

export type ReportPoint = {
  label: string;
  value: string;
  detail: string;
};

export type ValuationReport = {
  headline: string;
  stance: string;
  thesis: string[];
  assumptions: ReportPoint[];
  valuationResult: ReportPoint[];
  interpretation: string[];
  risks: string[];
  disclaimer: string;
};

export type ValuationModel = {
  slug: string;
  ticker: string;
  company: string;
  sector: string;
  methods: string[];
  summary: string;
  conclusion: string;
  valuationNotes: ValuationNote[];
  report: ValuationReport;
  downloads: ValuationDownload[];
};

export const valuationGroups: ValuationGroup[] = [
  {
    id: 'dcf',
    title: 'DCF',
    eyebrow: 'Intrinsic Value',
    description: 'Forecast-driven valuation using free cash flow, discount rate, terminal value, and sensitivity checks.',
  },
  {
    id: 'comparable',
    title: 'Comparable Analysis',
    eyebrow: 'Public Market Multiples',
    description: 'Peer-based valuation using listed-company multiples to cross-check where the market prices similar earnings streams.',
  },
  {
    id: 'transaction-lbo',
    title: 'Precedent Transactions + LBO',
    eyebrow: 'Control Value / Sponsor Returns',
    description: 'Transaction and sponsor-return valuation for situations where control premiums, entry multiples, and exit returns matter.',
  },
];

export const valuationModels: ValuationModel[] = [
  {
    slug: 'hpg',
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
        assumptions: 'FCFF DCF, not FCFE or DDM; WACC 10.5%, exit EV/EBITDA 7.0x, and 2026-2030 sales growth tapering from 14.0% to 3.0%.',
        result: 'Intrinsic value is below spot, mainly from conservative free-cash-flow assumptions through the capacity cycle.',
        groups: ['dcf'],
      },
      {
        method: 'Comparable Analysis',
        price: 'VND 23.4k-26.1k/share',
        assumptions: 'Steel peer median P/E of 10.5x-13.0x and EV/EBITDA around 7.1x.',
        result: 'Public-market multiples are closer to the current share price and act as the valuation cross-check.',
        groups: ['comparable'],
      },
    ],
    report: {
      headline: 'HPG valuation points to a wide gap between conservative intrinsic value and market multiple support.',
      stance: 'Mixed: DCF conservative, comparable analysis closer to spot.',
      thesis: [
        'HPG is a cyclical industrial issuer, so a single valuation method can overstate confidence. The report uses a FCFF DCF to capture operating cash generation and a comparable-company analysis to cross-check the market multiple investors currently assign to steel and materials peers.',
        'The DCF is intentionally cautious because steel earnings are sensitive to volume, spread, working capital, and capex timing. The comparable analysis is more forgiving because it reflects where the market prices listed peer earnings today.',
      ],
      assumptions: [
        {
          label: 'DCF model',
          value: 'FCFF DCF',
          detail: 'Unlevered free cash flow to firm is discounted at WACC. This is not an FCFE model and not a DDM, because the core value driver is operating cash flow through the steel cycle rather than distributable dividends.',
        },
        {
          label: 'Discount rate / terminal value',
          value: 'WACC 10.5%; exit EV/EBITDA 7.0x',
          detail: 'The terminal value uses an exit multiple instead of a perpetual-growth terminal value to better reflect steel-cycle normalization.',
        },
        {
          label: 'Operating case',
          value: 'Revenue growth 14.0% to 3.0%',
          detail: 'The forecast tapers growth through 2026-2030 and keeps capex and working-capital pressure visible in free cash flow.',
        },
        {
          label: 'Comparable set',
          value: 'Steel/materials peers',
          detail: 'The peer check uses P/E and EV/EBITDA medians; it is a market-implied anchor rather than a control-value estimate.',
        },
      ],
      valuationResult: [
        {
          label: 'DCF output',
          value: 'VND 13.4k/share',
          detail: 'The intrinsic case sits below spot because cash-flow conversion is penalized by leverage and capex-cycle assumptions.',
        },
        {
          label: 'Comparable output',
          value: 'VND 23.4k-26.1k/share',
          detail: 'Peer P/E medians imply a mid-20k/share range, broadly closer to where the market already trades HPG.',
        },
      ],
      interpretation: [
        'The valuation spread is the message. A conservative DCF says the market should not ignore cyclicality, while comparable analysis says the public market is still willing to pay for normalized earnings.',
        'For decision-making, the DCF should be treated as a downside discipline case and the comparable analysis as the cleaner market anchor.',
      ],
      risks: [
        'Steel spread compression or slower utilization would pressure the DCF fastest.',
        'Lower capex or stronger working-capital release would lift free cash flow and narrow the gap between DCF and comparable value.',
        'Comparable value can move quickly if the peer multiple set derates with China steel demand or Vietnam property sentiment.',
      ],
      disclaimer: 'This report is an academic valuation exercise prepared from the completed workbook outputs and selected public market data. It is not investment advice, a recommendation, or a solicitation to buy or sell securities.',
    },
    downloads: [
      {
        label: 'DCF',
        href: '/research/valuation-models/hpg-dcf-analysis.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- DCF Analysis_Template.xlsx',
        sheets: ['DCF', 'NWC', 'WACC', 'A1', 'A2'],
        groups: ['dcf'],
      },
      {
        label: 'Comparable Analysis',
        href: '/research/valuation-models/hpg-comparable-analysis.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- Comparable Companies_Template.xlsx',
        sheets: ['List', 'Benchmarking 1', 'Benchmarking 2', 'Ouput', 'TargetCo', 'CompCo 1-15'],
        groups: ['comparable'],
      },
    ],
  },
  {
    slug: 'bid',
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
        groups: ['comparable'],
      },
    ],
    report: {
      headline: 'BID valuation is a peer-multiple exercise because bank cash flows are balance-sheet driven.',
      stance: 'Mixed: forward multiples are below spot, LTM multiple is above spot.',
      thesis: [
        'BID is valued using comparable-company analysis rather than a corporate DCF. For banks, FCFF and FCFE are less clean because debt is operating funding, capital regulation matters, and value is usually framed through earnings, book value, ROE, and credit-cycle quality.',
        'The completed template uses P/E-style peer checks. The output is intentionally shown as a range because the LTM and forward earnings bases tell different stories.',
      ],
      assumptions: [
        {
          label: 'Primary model',
          value: 'Comparable Analysis',
          detail: 'No FCFF DCF or DDM is used. The report relies on listed bank peer multiples and target-company earnings normalization.',
        },
        {
          label: 'Peer frame',
          value: 'Vietnam listed banks',
          detail: 'The benchmark set reflects banks with comparable deposit franchises, loan growth exposure, and market liquidity.',
        },
        {
          label: 'Multiple frame',
          value: 'P/E 7.0x-7.7x forward; 7.2x LTM',
          detail: 'Forward multiples are the cleaner normalized read; the LTM multiple is retained to show how sensitive the valuation is to earnings-base selection.',
        },
      ],
      valuationResult: [
        {
          label: 'Forward P/E output',
          value: 'Approx. VND 32.7k/share',
          detail: 'Forward earnings multiples imply value below the reference share price.',
        },
        {
          label: 'LTM P/E output',
          value: 'Approx. VND 52.2k/share',
          detail: 'The LTM earnings base produces a higher read, creating a wide range rather than a single target.',
        },
      ],
      interpretation: [
        'The most important output is dispersion. BID does not screen as a clean upside/downside call from this model alone.',
        'A stronger conclusion would require updated asset-quality assumptions, ROE normalization, credit-cost path, and capital adequacy context.',
      ],
      risks: [
        'Credit-cost normalization can make forward earnings too optimistic or too conservative.',
        'State-linked bank valuation can be affected by policy lending, capital raising, and foreign ownership constraints.',
        'A pure P/E framework is less complete than a full P/B-ROE bank valuation, so the result should be used as a peer check.',
      ],
      disclaimer: 'This report is an academic valuation exercise prepared from the completed workbook outputs and selected public market data. It is not investment advice, a recommendation, or a solicitation to buy or sell securities.',
    },
    downloads: [
      {
        label: 'Comparable Analysis',
        href: '/research/valuation-models/bid-comparable-analysis.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- Comparable Companies_Template.xlsx',
        sheets: ['List', 'Benchmarking 1', 'Benchmarking 2', 'Ouput', 'TargetCo', 'CompCo 1-15'],
        groups: ['comparable'],
      },
    ],
  },
  {
    slug: 'fpt',
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
        assumptions: 'FCFF DCF, not DDM; WACC 9.5%, exit EV/EBITDA 14.0x, and revenue growth tapering from 12.0% to 8.0%.',
        result: 'Cash-flow valuation is materially above spot under the base growth and margin assumptions.',
        groups: ['dcf'],
      },
      {
        method: 'Comparable Analysis',
        price: 'VND 90.0k-92.8k/share',
        assumptions: 'Tech and telecom peer median P/E of 14.0x-16.9x and EV/EBITDA of 7.4x-9.4x.',
        result: 'Comparable analysis supports upside, but it is less aggressive than the DCF case.',
        groups: ['comparable'],
      },
    ],
    report: {
      headline: 'FPT valuation is supported by both intrinsic growth cash flow and public peer multiples.',
      stance: 'Constructive: DCF upside is stronger than comparable-analysis upside.',
      thesis: [
        'FPT is a higher-quality growth company than the cyclical industrial names, so a FCFF DCF is appropriate. The valuation captures sustained IT services demand, telecom cash flow, education growth, and a cleaner margin profile.',
        'Comparable analysis is used as a reality check. It asks whether listed tech and telecom peers support the valuation before relying on a long-duration DCF.',
      ],
      assumptions: [
        {
          label: 'DCF model',
          value: 'FCFF DCF',
          detail: 'Unlevered free cash flow is discounted at WACC. This is not a DDM because dividends are not the main value driver for the growth case.',
        },
        {
          label: 'Discount rate / terminal value',
          value: 'WACC 9.5%; exit EV/EBITDA 14.0x',
          detail: 'The terminal multiple reflects a higher-quality technology-services business with durable growth and margin visibility.',
        },
        {
          label: 'Operating case',
          value: 'Revenue growth 12.0% to 8.0%',
          detail: 'The model assumes growth moderates but remains structurally above more cyclical sectors.',
        },
        {
          label: 'Comparable set',
          value: 'Tech, IT services, telecom peers',
          detail: 'Peer medians provide the public-market sanity check for the DCF output.',
        },
      ],
      valuationResult: [
        {
          label: 'DCF output',
          value: 'VND 132.5k/share',
          detail: 'The DCF is materially above spot because sustained growth and terminal quality are the main value drivers.',
        },
        {
          label: 'Comparable output',
          value: 'VND 90.0k-92.8k/share',
          detail: 'Peer multiples support upside, but the range is below the DCF because public markets apply a lower normalized multiple than the terminal DCF case.',
        },
      ],
      interpretation: [
        'FPT is the cleanest case where both methods point in the same direction.',
        'The difference between DCF and comparable value should be read as the price of long-term growth confidence. If investors believe growth and margins persist, DCF carries more weight; if they want a market anchor, the comparable range is more conservative.',
      ],
      risks: [
        'A lower terminal multiple has a large impact because the company is valued as a duration growth asset.',
        'IT-services growth, wage pressure, FX, and overseas demand are the main operating sensitivities.',
        'Comparable valuation can compress if global technology multiples derate.',
      ],
      disclaimer: 'This report is an academic valuation exercise prepared from the completed workbook outputs and selected public market data. It is not investment advice, a recommendation, or a solicitation to buy or sell securities.',
    },
    downloads: [
      {
        label: 'DCF',
        href: '/research/valuation-models/fpt-dcf-analysis.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- DCF Analysis_Template.xlsx',
        sheets: ['DCF', 'NWC', 'WACC', 'A1', 'A2'],
        groups: ['dcf'],
      },
      {
        label: 'Comparable Analysis',
        href: '/research/valuation-models/fpt-comparable-analysis.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- Comparable Companies_Template.xlsx',
        sheets: ['List', 'Benchmarking 1', 'Benchmarking 2', 'Ouput', 'TargetCo', 'CompCo 1-15'],
        groups: ['comparable'],
      },
    ],
  },
  {
    slug: 'bmp',
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
        groups: ['transaction-lbo'],
      },
      {
        method: 'LBO',
        price: 'VND 162.2k/share',
        assumptions: 'Sponsor-return LBO; 20.0% control premium, entry EV/EBITDA around 8.5x, exit EV/EBITDA 7.5x, and 20.1% IRR.',
        result: 'Sponsor case clears the return hurdle near the precedent transaction check.',
        groups: ['transaction-lbo'],
      },
    ],
    report: {
      headline: 'BMP is best read through control-value methods rather than a public-market trading multiple alone.',
      stance: 'Constructive transaction case: precedent and LBO values cluster tightly.',
      thesis: [
        'BMP is valued with precedent transactions and an LBO because the relevant question is control value. A sponsor or strategic buyer would underwrite entry price, leverage capacity, operating durability, and exit multiple rather than only current trading multiples.',
        'The precedent transaction check and LBO offer value are close, which gives the model a cleaner triangulation than a single standalone method.',
      ],
      assumptions: [
        {
          label: 'Precedent model',
          value: 'Control-premium transaction analysis',
          detail: 'The precedent set uses transaction EV/Sales, EV/EBITDA, P/E, and premium paid. This is not a DCF or DDM.',
        },
        {
          label: 'LBO model',
          value: 'Sponsor-return model',
          detail: 'The LBO uses acquisition offer price, entry multiple, leverage, debt paydown, exit multiple, IRR, and cash-on-cash return.',
        },
        {
          label: 'Control premium',
          value: '20.0% in LBO; 23.5% precedent median',
          detail: 'The premium frame is the bridge between the current trading price and a control-buyer valuation.',
        },
        {
          label: 'Exit / return hurdle',
          value: '7.5x exit EV/EBITDA; 20.1% IRR',
          detail: 'The sponsor case clears the target return at a VND 162.2k/share offer value.',
        },
      ],
      valuationResult: [
        {
          label: 'Precedent output',
          value: 'Approx. VND 167.0k/share',
          detail: 'Median precedent premium and transaction multiples imply a value slightly above the LBO offer.',
        },
        {
          label: 'LBO output',
          value: 'VND 162.2k/share',
          detail: 'The sponsor case supports a premium offer while maintaining a 20.1% IRR and 2.50x cash return.',
        },
      ],
      interpretation: [
        'BMP has a coherent control-value range. The valuation does not rely on a broad public multiple; it asks whether an acquirer can pay a premium and still clear return hurdles.',
        'The result is strongest if margin stability and cash conversion hold, because those variables drive sponsor deleveraging and exit flexibility.',
      ],
      risks: [
        'A lower exit multiple or weaker EBITDA path would compress the LBO offer quickly.',
        'Sponsor financing terms, interest costs, and leverage availability can change the clearing price.',
        'Precedent transaction samples can be stale or structurally different from BMP, so the premium output is a guide rather than a hard target.',
      ],
      disclaimer: 'This report is an academic valuation exercise prepared from the completed workbook outputs and selected public market data. It is not investment advice, a recommendation, or a solicitation to buy or sell securities.',
    },
    downloads: [
      {
        label: 'Precedent Transactions',
        href: '/research/valuation-models/bmp-precedent-transactions.xlsx',
        format: 'XLSX',
        sourceTemplate: 'SV- Precedent Transactions_Template.xlsx',
        sheets: ['List', 'Output', 'ACQR;TRGT 1-10'],
        groups: ['transaction-lbo'],
      },
      {
        label: 'LBO',
        href: '/research/valuation-models/bmp-lbo-analysis.xls',
        format: 'XLS',
        sourceTemplate: 'LBO Analysis_Completed.xls',
        sheets: ['Cover', 'TS', 'IS', 'BS', 'CF', 'DS', 'RA', 'A1', 'A2', 'A3'],
        groups: ['transaction-lbo'],
      },
    ],
  },
  {
    slug: 'pnj',
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
        assumptions: 'Sponsor-return LBO; 25.0% control premium, entry EV/EBITDA around 12.2x, exit EV/EBITDA 7.5x, and 20.1% IRR.',
        result: 'Sponsor case supports a premium to spot and aligns with the precedent premium check.',
        groups: ['transaction-lbo'],
      },
      {
        method: 'Comparable / Precedent',
        price: 'Comparable VND 112.9k-140.2k; precedent approx. VND 81.6k',
        assumptions: 'Retail peer P/E of 17.0x-20.4x and EV/EBITDA of 9.5x-11.7x; precedent premium of 27.5%.',
        result: 'Public peers screen well above spot, while transaction premium evidence is closer to the LBO output.',
        groups: ['comparable', 'transaction-lbo'],
      },
    ],
    report: {
      headline: 'PNJ shows the widest method spread: public retail multiples are high, control-value methods are closer to 80k/share.',
      stance: 'Wide range: LBO/precedent near 80k, public comparable value much higher.',
      thesis: [
        'PNJ is valued with a sponsor LBO plus comparable and precedent transaction checks. That mix is appropriate because a consumer retail issuer can be framed either as a public growth compounder or as a control transaction with finite sponsor-return constraints.',
        'The main conclusion is not a single point estimate. It is the spread between what public retail peers imply and what a sponsor/control buyer can support.',
      ],
      assumptions: [
        {
          label: 'LBO model',
          value: 'Sponsor-return model',
          detail: 'The LBO uses acquisition premium, entry EV/EBITDA, leverage, exit multiple, IRR, and cash return. It is not a DDM.',
        },
        {
          label: 'Comparable model',
          value: 'Public retail peer multiples',
          detail: 'The comparable analysis uses peer P/E and EV/EBITDA medians to estimate what the public market might pay for similar earnings quality.',
        },
        {
          label: 'Precedent model',
          value: 'Control-premium transaction check',
          detail: 'The precedent analysis uses median premium and transaction multiples to cross-check the LBO offer.',
        },
        {
          label: 'Sponsor assumptions',
          value: '25.0% premium; 12.2x entry EV/EBITDA; 7.5x exit EV/EBITDA',
          detail: 'The sponsor case targets a 20.1% IRR and 2.50x cash return at an offer value of VND 80.0k/share.',
        },
      ],
      valuationResult: [
        {
          label: 'LBO output',
          value: 'VND 80.0k/share',
          detail: 'The sponsor-return model supports a premium to spot but does not reach the public comparable range.',
        },
        {
          label: 'Comparable output',
          value: 'VND 112.9k-140.2k/share',
          detail: 'Retail peer multiples screen well above spot and well above the LBO output.',
        },
        {
          label: 'Precedent output',
          value: 'Approx. VND 81.6k/share',
          detail: 'The precedent premium check sits close to the LBO value, which reinforces the control-value read.',
        },
      ],
      interpretation: [
        'PNJ is a valuation-method selection problem. If treated as a public growth retailer, comparable multiples imply a much higher range. If treated as a control transaction, the LBO and precedent checks cluster near 80k/share.',
        'The report therefore separates trading value from control value instead of forcing a single blended target.',
      ],
      risks: [
        'Comparable value can overstate upside if peer margins, growth, or market structures are not truly comparable.',
        'LBO value is sensitive to exit multiple, leverage capacity, and retail cash-flow resilience.',
        'Gold price volatility, consumer demand, inventory management, and store productivity are key operating risks.',
      ],
      disclaimer: 'This report is an academic valuation exercise prepared from the completed workbook outputs and selected public market data. It is not investment advice, a recommendation, or a solicitation to buy or sell securities.',
    },
    downloads: [
      {
        label: 'LBO',
        href: '/research/valuation-models/pnj-lbo-analysis.xls',
        format: 'XLS',
        sourceTemplate: 'LBO Analysis_Completed.xls',
        sheets: ['Cover', 'TS', 'IS', 'BS', 'CF', 'DS', 'RA', 'A1', 'A2', 'A3'],
        groups: ['transaction-lbo'],
      },
      {
        label: 'Comparable / Precedent',
        href: '/research/valuation-models/pnj-comparable-precedent-analysis.zip',
        format: 'ZIP',
        sourceTemplate: 'SV- Comparable Companies_Template.xlsx + SV- Precedent Transactions_Template.xlsx',
        sheets: ['Comparable: List, Benchmarking, Ouput, CompCo 1-15', 'Precedent: List, Output, ACQR;TRGT 1-10'],
        groups: ['comparable', 'transaction-lbo'],
      },
    ],
  },
];
