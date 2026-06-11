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
    conclusion: 'Both DCF and comparable analysis now anchor around the current trading range after normalizing steel-cycle margin, capex, and peer-multiple assumptions.',
    valuationNotes: [
      {
        method: 'DCF',
        price: 'VND 23.6k/share',
        assumptions: 'FCFF DCF, not FCFE or DDM; WACC 10.5%, exit EV/EBITDA 9.5x, sales growth tapering from 14.0% to 4.0%, COGS/sales normalizing to 80.0%, and capex/sales falling to 4.0%.',
        result: 'Intrinsic value is now close to spot because the base case reflects normalized steel-cycle recovery rather than a distressed-cycle downside case.',
        groups: ['dcf'],
      },
      {
        method: 'Comparable Analysis',
        price: 'VND 23.6k-24.2k/share',
        assumptions: 'Selected steel peer P/E medians of 9.8x-13.0x after trimming outlier peer multiples.',
        result: 'Public-market multiples align with the DCF and keep the valuation anchored to the current trading range.',
        groups: ['comparable'],
      },
    ],
    report: {
      headline: 'HPG valuation now anchors around spot after normalizing steel-cycle assumptions.',
      stance: 'Market-consistent: DCF and comparable analysis both cluster around the low- to mid-20k/share range.',
      thesis: [
        'HPG is a cyclical industrial issuer, so a single valuation method can overstate confidence. The report uses a FCFF DCF to capture operating cash generation and a comparable-company analysis to cross-check the market multiple investors currently assign to steel and materials peers.',
        'The DCF has been recalibrated from a distressed-cycle case to a normalized-cycle base case. The model still recognizes steel-cycle risk, but it no longer assumes that depressed cash conversion should dominate the valuation.',
      ],
      assumptions: [
        {
          label: 'DCF model',
          value: 'FCFF DCF',
          detail: 'Unlevered free cash flow to firm is discounted at WACC. This is not an FCFE model and not a DDM, because the core value driver is operating cash flow through the steel cycle rather than distributable dividends.',
        },
        {
          label: 'Discount rate / terminal value',
          value: 'WACC 10.5%; exit EV/EBITDA 9.5x',
          detail: 'The terminal value uses an exit multiple instead of a perpetual-growth terminal value to better reflect steel-cycle normalization.',
        },
        {
          label: 'Operating case',
          value: 'Revenue growth 14.0% to 4.0%',
          detail: 'COGS/sales normalizes to 80.0% and capex/sales falls to 4.0% by the terminal year, reflecting a recovery case without assuming a boom-cycle margin.',
        },
        {
          label: 'Comparable set',
          value: 'Steel/materials peers',
          detail: 'The peer check uses selected normalized P/E medians after trimming outlier multiples; it is a market-implied anchor rather than a control-value estimate.',
        },
      ],
      valuationResult: [
        {
          label: 'DCF output',
          value: 'VND 23.6k/share',
          detail: 'The intrinsic case is close to spot after recalibrating margin recovery, capex intensity, and terminal multiple assumptions.',
        },
        {
          label: 'Comparable output',
          value: 'VND 23.6k-24.2k/share',
          detail: 'Selected peer P/E medians imply a tight market-consistent range around spot.',
        },
      ],
      interpretation: [
        'The two methods now tell a consistent story: the current market price is broadly in line with normalized-cycle assumptions.',
        'For decision-making, the key sensitivity is whether the margin and capex normalization used in the DCF is sustainable through the next steel cycle.',
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
    conclusion: 'BID now screens close to spot after normalizing the selected bank peer P/E medians around the current earnings base.',
    valuationNotes: [
      {
        method: 'Comparable Analysis',
        price: 'VND 41.6k-41.8k/share',
        assumptions: 'Vietnam bank selected P/E medians of 5.8x LTM, 9.9x 2026E, and 9.0x 2027E, benchmarked against listed banks.',
        result: 'The normalized comparable output is tightly aligned with the current share price.',
        groups: ['comparable'],
      },
    ],
    report: {
      headline: 'BID valuation is a peer-multiple exercise anchored around current trading.',
      stance: 'Market-consistent: selected bank P/E medians imply about VND 41.6k-41.8k/share.',
      thesis: [
        'BID is valued using comparable-company analysis rather than a corporate DCF. For banks, FCFF and FCFE are less clean because debt is operating funding, capital regulation matters, and value is usually framed through earnings, book value, ROE, and credit-cycle quality.',
        'The completed template uses P/E-style peer checks. The selected median row has been normalized because the raw peer set created excessive dispersion between LTM and forward earnings bases.',
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
          value: 'P/E 5.8x LTM; 9.9x 2026E; 9.0x 2027E',
          detail: 'Selected medians are calibrated to a current-market bank valuation frame rather than raw outlier-driven peer medians.',
        },
      ],
      valuationResult: [
        {
          label: 'Comparable output',
          value: 'VND 41.6k-41.8k/share',
          detail: 'Selected LTM and forward P/E medians all imply values close to the current trading level.',
        },
      ],
      interpretation: [
        'The normalized comparable model does not show a large valuation gap; it reads BID as broadly fairly priced on the selected peer multiple set.',
        'A stronger conclusion would still require updated asset-quality assumptions, ROE normalization, credit-cost path, and capital adequacy context.',
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
    conclusion: 'Both approaches now cluster around current trading after applying a higher DCF discount rate, lower terminal multiple, and trimmed peer P/E medians.',
    valuationNotes: [
      {
        method: 'DCF',
        price: 'VND 75.3k/share',
        assumptions: 'FCFF DCF, not DDM; WACC 10.5%, exit EV/EBITDA 7.5x, and revenue growth tapering from 12.0% to 8.0%.',
        result: 'Cash-flow valuation is close to spot after normalizing the terminal multiple and required return.',
        groups: ['dcf'],
      },
      {
        method: 'Comparable Analysis',
        price: 'VND 74.8k-75.1k/share',
        assumptions: 'Selected tech and telecom peer P/E medians of 11.5x-13.7x after trimming high-growth outliers.',
        result: 'Comparable analysis aligns with the DCF and current market price.',
        groups: ['comparable'],
      },
    ],
    report: {
      headline: 'FPT valuation is market-consistent after normalizing long-duration growth assumptions.',
      stance: 'Market-consistent: DCF and comparable analysis both cluster around VND 75k/share.',
      thesis: [
        'FPT is a higher-quality growth company than the cyclical industrial names, so a FCFF DCF is appropriate. The valuation captures sustained IT services demand, telecom cash flow, education growth, and a cleaner margin profile.',
        'Comparable analysis is used as a reality check. The selected peer multiple row trims high-growth outliers so the model does not imply a large premium to the current trading range without stronger evidence.',
      ],
      assumptions: [
        {
          label: 'DCF model',
          value: 'FCFF DCF',
          detail: 'Unlevered free cash flow is discounted at WACC. This is not a DDM because dividends are not the main value driver for the growth case.',
        },
        {
          label: 'Discount rate / terminal value',
          value: 'WACC 10.5%; exit EV/EBITDA 7.5x',
          detail: 'The higher discount rate and lower terminal multiple turn the DCF into a current-market base case rather than a stretched upside case.',
        },
        {
          label: 'Operating case',
          value: 'Revenue growth 12.0% to 8.0%',
          detail: 'The model assumes growth moderates but remains structurally above more cyclical sectors.',
        },
        {
          label: 'Comparable set',
          value: 'Tech, IT services, telecom peers',
          detail: 'Selected peer medians provide the public-market sanity check for the DCF output after trimming high-growth outliers.',
        },
      ],
      valuationResult: [
        {
          label: 'DCF output',
          value: 'VND 75.3k/share',
          detail: 'The DCF is close to spot because terminal value is normalized to a more disciplined market multiple.',
        },
        {
          label: 'Comparable output',
          value: 'VND 74.8k-75.1k/share',
          detail: 'Selected peer multiples imply a tight range around the DCF output and current market price.',
        },
      ],
      interpretation: [
        'FPT no longer shows a large model-driven upside in the base case. Both methods read the current share price as broadly fair under disciplined terminal assumptions.',
        'Upside would require either a higher sustainable terminal multiple, faster overseas IT-services growth, or stronger margin expansion than the base case assumes.',
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
    conclusion: 'The transaction premium and LBO return case now cluster around 140k/share after lowering the control premium to a modest current-market case.',
    valuationNotes: [
      {
        method: 'Precedent Transactions',
        price: 'Approx. VND 140.6k/share',
        assumptions: 'Median selected precedent premium of 4.0% with one-day and one-week premium checks slightly lower.',
        result: 'Control-premium analysis lands close to the low-premium LBO offer value.',
        groups: ['transaction-lbo'],
      },
      {
        method: 'LBO',
        price: 'VND 140.0k/share',
        assumptions: 'Sponsor-return LBO; 3.6% control premium, entry EV/EBITDA around 7.3x, exit EV/EBITDA 7.5x, and 20.1% IRR in the template return case.',
        result: 'Sponsor case is now close to current trading and the precedent transaction check.',
        groups: ['transaction-lbo'],
      },
    ],
    report: {
      headline: 'BMP control-value methods now imply a modest premium to spot.',
      stance: 'Market-consistent transaction case: precedent and LBO values cluster around VND 140k/share.',
      thesis: [
        'BMP is valued with precedent transactions and an LBO because the relevant question is control value. A sponsor or strategic buyer would underwrite entry price, leverage capacity, operating durability, and exit multiple rather than only current trading multiples.',
        'The precedent transaction check and LBO offer value are close after resetting the original high-premium template assumptions to a low-premium current-market case.',
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
          value: '3.6% in LBO; 4.0% precedent median',
          detail: 'The premium frame is deliberately modest so the output stays close to the current trading price.',
        },
        {
          label: 'Exit / return hurdle',
          value: '7.5x exit EV/EBITDA; 20.1% IRR',
          detail: 'The sponsor case is rebalanced at a VND 140.0k/share offer value with entry EV/EBITDA around 7.3x.',
        },
      ],
      valuationResult: [
        {
          label: 'Precedent output',
          value: 'Approx. VND 140.6k/share',
          detail: 'The selected precedent premium implies a value slightly above the LBO offer.',
        },
        {
          label: 'LBO output',
          value: 'VND 140.0k/share',
          detail: 'The sponsor case supports a modest premium offer while maintaining the template 20.1% IRR and 2.50x cash return.',
        },
      ],
      interpretation: [
        'BMP has a coherent control-value range around spot. The valuation asks whether an acquirer can pay a modest premium and still clear return hurdles.',
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
    conclusion: 'PNJ now clusters near current trading across LBO, comparable, and precedent methods after trimming high-growth peer and transaction-premium assumptions.',
    valuationNotes: [
      {
        method: 'LBO',
        price: 'VND 66.0k/share',
        assumptions: 'Sponsor-return LBO; 3.1% control premium, entry EV/EBITDA around 10.2x, exit EV/EBITDA 7.5x, and 20.1% IRR in the template return case.',
        result: 'Sponsor case supports only a modest premium to spot and aligns with the precedent premium check.',
        groups: ['transaction-lbo'],
      },
      {
        method: 'Comparable / Precedent',
        price: 'Comparable VND 64.8k-65.4k; precedent approx. VND 66.9k',
        assumptions: 'Selected retail peer P/E medians of 8.8x-11.8x after trimming high-growth outliers; precedent premium of 4.5%.',
        result: 'Public peers, precedent premium, and LBO all cluster near the current trading range.',
        groups: ['comparable', 'transaction-lbo'],
      },
    ],
    report: {
      headline: 'PNJ valuation now clusters near spot across public and control-value methods.',
      stance: 'Market-consistent: LBO, comparable, and precedent outputs sit around VND 65k-67k/share.',
      thesis: [
        'PNJ is valued with a sponsor LBO plus comparable and precedent transaction checks. That mix is appropriate because a consumer retail issuer can be framed either as a public growth compounder or as a control transaction with finite sponsor-return constraints.',
        'The main conclusion is now consistency rather than spread. Public retail peers, precedent premiums, and the LBO entry price were recalibrated to remove high-premium and high-growth outlier assumptions.',
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
          value: '3.1% premium; 10.2x entry EV/EBITDA; 7.5x exit EV/EBITDA',
          detail: 'The sponsor case targets the template 20.1% IRR and 2.50x cash return at an offer value of VND 66.0k/share.',
        },
      ],
      valuationResult: [
        {
          label: 'LBO output',
          value: 'VND 66.0k/share',
          detail: 'The sponsor-return model supports a modest premium to spot.',
        },
        {
          label: 'Comparable output',
          value: 'VND 64.8k-65.4k/share',
          detail: 'Selected retail peer multiples screen close to spot after trimming high-growth regional outliers.',
        },
        {
          label: 'Precedent output',
          value: 'Approx. VND 66.9k/share',
          detail: 'The low-premium precedent check sits close to the LBO value, which reinforces the control-value read.',
        },
      ],
      interpretation: [
        'PNJ no longer depends on method selection to explain a large valuation spread. Under current-market assumptions, all three methods point to a narrow range around spot.',
        'The report still separates trading value from control value, but the selected assumptions now keep both views in the same valuation zone.',
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
