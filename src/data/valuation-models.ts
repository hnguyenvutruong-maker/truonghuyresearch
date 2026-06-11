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
    conclusion: 'HPG now has an intentional valuation spread: DCF is the intrinsic discipline case below spot, while comparable analysis reflects a stronger normalized-cycle public-market case.',
    valuationNotes: [
      {
        method: 'DCF',
        price: 'VND 22.3k/share',
        assumptions: 'FCFF DCF, not FCFE or DDM; WACC 10.5%, exit EV/EBITDA 9.0x, sales growth tapering from 14.0% to 4.0%, COGS/sales normalizing to 80.0%, and capex/sales falling to 4.0%.',
        result: 'DCF sits below spot and below comparable value because it penalizes steel-cycle cash-flow volatility and terminal multiple risk.',
        groups: ['dcf'],
      },
      {
        method: 'Comparable Analysis',
        price: 'VND 25.5k-25.9k/share',
        assumptions: 'Selected steel peer P/E medians of 14.0x LTM, 11.4x 2026E, and 10.5x 2027E after trimming outlier peer multiples.',
        result: 'Comparable analysis lands above the DCF because the public market is giving more credit to normalized earnings than the intrinsic cash-flow case.',
        groups: ['comparable'],
      },
    ],
    report: {
      headline: 'HPG valuation deliberately separates intrinsic steel-cycle risk from public-market normalized earnings.',
      stance: 'Method spread: DCF at VND 22.3k/share versus comparable value at VND 25.5k-25.9k/share.',
      thesis: [
        'HPG is a cyclical industrial issuer, so a single valuation method can overstate confidence. The report uses a FCFF DCF to capture operating cash generation and a comparable-company analysis to cross-check the market multiple investors currently assign to steel and materials peers.',
        'The DCF is intentionally lower than the comparable output. That is the correct story for a steel company: intrinsic value should reflect spread volatility, working-capital swings, leverage, and capex timing, while comparable analysis reflects the multiple investors are willing to pay for normalized earnings today.',
        'The operating case is not a distressed case. It assumes recovery in revenue, gross margin, and capex intensity. The discount comes from requiring cash-flow conversion to prove itself rather than immediately capitalizing the full peer re-rating.',
        'The comparable model is the market check. It asks what HPG would be worth if investors applied selected steel/materials peer P/E medians to HPG earnings. Because public markets can look through the cycle faster than a DCF, this value is higher.',
      ],
      assumptions: [
        {
          label: 'DCF model',
          value: 'FCFF DCF',
          detail: 'Unlevered free cash flow to firm is discounted at WACC. This is not an FCFE model and not a DDM, because the core value driver is operating cash flow through the steel cycle rather than distributable dividends.',
        },
        {
          label: 'Discount rate / terminal value',
          value: 'WACC 10.5%; exit EV/EBITDA 9.0x',
          detail: 'The terminal value uses an exit multiple instead of a perpetual-growth terminal value. A 9.0x exit multiple keeps the intrinsic case below the peer check and prevents the model from assuming a full-cycle re-rating forever.',
        },
        {
          label: 'Operating case',
          value: 'Revenue growth 14.0% to 4.0%',
          detail: 'COGS/sales normalizes to 80.0% and capex/sales falls to 4.0% by the terminal year, reflecting a recovery case without assuming a boom-cycle margin.',
        },
        {
          label: 'Comparable set',
          value: 'Steel/materials peers',
          detail: 'The peer check uses selected normalized P/E medians of 14.0x LTM, 11.4x 2026E, and 10.5x 2027E after trimming outlier multiples. It is a market-implied anchor rather than a control-value estimate.',
        },
        {
          label: 'Why methods differ',
          value: 'DCF lower; comps higher',
          detail: 'The DCF discounts cash-flow risk directly. Comparable analysis capitalizes normalized earnings more quickly. The spread is therefore an analytical signal, not a model error.',
        },
      ],
      valuationResult: [
        {
          label: 'DCF output',
          value: 'VND 22.3k/share',
          detail: 'The intrinsic case is below spot because even a normalized recovery still carries steel-cycle risk, capex drag, and terminal multiple uncertainty.',
        },
        {
          label: 'Comparable output',
          value: 'VND 25.5k-25.9k/share',
          detail: 'Selected peer P/E medians imply upside versus the DCF because public investors are more willing to look through the cycle.',
        },
        {
          label: 'Valuation spread',
          value: 'Approx. 15%-16%',
          detail: 'The gap between DCF and comparable value is the core read: HPG needs better cash-flow evidence for the intrinsic case to catch up with the public-market multiple case.',
        },
      ],
      interpretation: [
        'HPG should not be presented as a single precise target price. The better read is a range bounded by DCF discipline on the low end and public peer multiples on the high end.',
        'If the investor believes spreads, utilization, and working capital will normalize quickly, the comparable range deserves more weight.',
        'If the investor wants cash-flow proof before paying for normalized earnings, the DCF value is the more conservative anchor.',
        'The report therefore says HPG is not obviously mispriced; it is a cyclicality debate. The market price sits between intrinsic caution and peer-based optimism.',
      ],
      risks: [
        'Steel spread compression or slower utilization would pressure the DCF fastest.',
        'Lower capex or stronger working-capital release would lift free cash flow and narrow the gap between DCF and comparable value.',
        'Comparable value can move quickly if the peer multiple set derates with China steel demand or Vietnam property sentiment.',
        'A higher terminal multiple would lift DCF value disproportionately because terminal value is a large share of enterprise value.',
        'A prolonged property or construction slowdown would make the comparable case less defensible even if peer multiples remain elevated.',
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
    conclusion: 'BID is a comparable-only bank valuation, so the key output is a deliberately wide P/E range around spot rather than a single precise target.',
    valuationNotes: [
      {
        method: 'Comparable Analysis',
        price: 'VND 39.7k-44.3k/share',
        assumptions: 'Vietnam bank selected P/E medians of 6.1x LTM, 9.4x 2026E, and 9.1x 2027E, benchmarked against listed banks.',
        result: 'The model creates a valuation band around spot: downside comes from the forward earnings base, while upside comes from normalized/LTM multiple support.',
        groups: ['comparable'],
      },
    ],
    report: {
      headline: 'BID valuation is a bank peer-multiple exercise with a visible downside/base/upside band.',
      stance: 'Comparable range: VND 39.7k-44.3k/share, centered around the current trading area but not forced to a single point.',
      thesis: [
        'BID is valued using comparable-company analysis rather than a corporate DCF. For banks, FCFF and FCFE are less clean because debt is operating funding, capital regulation matters, and value is usually framed through earnings, book value, ROE, and credit-cycle quality.',
        'The completed template uses P/E-style peer checks. Because BID is a bank, the useful output is not a false-precision DCF number; it is a band that shows how the valuation changes when the market uses LTM earnings versus forward earnings.',
        'The selected median row is intentionally not flat. A bank can look cheap or expensive depending on credit-cost normalization, provisioning cycle, and how quickly earnings recover. The model therefore allows the range to move from high-30k to mid-40k.',
        'The report should be read as a peer sanity check. It does not replace a full P/B-ROE bank valuation, but it is enough for a quick view of whether BID is trading far outside the listed-bank multiple framework.',
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
          value: 'P/E 6.1x LTM; 9.4x 2026E; 9.1x 2027E',
          detail: 'Selected medians are calibrated to a current-market bank valuation frame while preserving enough dispersion to show how sensitive BID is to the earnings base.',
        },
        {
          label: 'Bank-specific limitation',
          value: 'No FCFF / no DDM',
          detail: 'Debt is operating funding for a bank, so corporate free-cash-flow methods are less informative. A stronger bank model would add P/B, ROE, credit cost, capital adequacy, and asset-quality scenarios.',
        },
        {
          label: 'Why the range matters',
          value: 'Earnings base drives value',
          detail: 'LTM and forward earnings can imply different values when the bank is moving through a credit and provisioning cycle. The valuation range is therefore more useful than a single rounded target.',
        },
      ],
      valuationResult: [
        {
          label: 'Comparable output',
          value: 'VND 39.7k-44.3k/share',
          detail: 'The output brackets spot rather than matching it exactly. The lower end reflects a more cautious forward earnings read; the upper end reflects normalized/LTM support.',
        },
        {
          label: 'Method spread',
          value: 'Approx. 12%',
          detail: 'The spread is acceptable for a bank comparable model because credit costs, funding costs, and earnings normalization can shift the correct P/E base quickly.',
        },
      ],
      interpretation: [
        'BID screens broadly fair, but the method does not say the stock should equal spot. It says the current price is inside a reasonable bank peer-multiple band.',
        'A value near the lower end would be justified if credit costs rise, ROE normalization disappoints, or investors demand a lower multiple for state-linked balance-sheet risk.',
        'A value near the higher end would be justified if provisioning normalizes, earnings visibility improves, and the listed-bank peer set rerates.',
        'Because only one method is used, the report must explain the internal range clearly. For BID, the scenario spread inside comparable analysis is the valuation story.',
      ],
      risks: [
        'Credit-cost normalization can make forward earnings too optimistic or too conservative.',
        'State-linked bank valuation can be affected by policy lending, capital raising, and foreign ownership constraints.',
        'A pure P/E framework is less complete than a full P/B-ROE bank valuation, so the result should be used as a peer check.',
        'Funding-cost pressure or deposit competition would reduce the usefulness of simple P/E comparisons.',
        'A capital raise, regulatory change, or foreign ownership limit change could move the appropriate trading multiple quickly.',
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
    conclusion: 'FPT now shows the intended split: DCF is the growth-upside case, while comparable analysis is the tighter public-market multiple check.',
    valuationNotes: [
      {
        method: 'DCF',
        price: 'VND 83.2k/share',
        assumptions: 'FCFF DCF, not DDM; WACC 10.5%, exit EV/EBITDA 8.5x, and revenue growth tapering from 12.0% to 8.0%.',
        result: 'DCF sits above spot and above comparable analysis because it gives credit to FPT’s growth duration and cash-flow resilience.',
        groups: ['dcf'],
      },
      {
        method: 'Comparable Analysis',
        price: 'VND 76.2k-77.1k/share',
        assumptions: 'Selected tech and telecom peer P/E medians of 14.0x LTM, 12.9x 2026E, and 11.7x 2027E after trimming high-growth outliers.',
        result: 'Comparable analysis remains near the current public-market trading zone and acts as the conservative check below DCF.',
        groups: ['comparable'],
      },
    ],
    report: {
      headline: 'FPT valuation separates the long-duration growth case from the public-market multiple check.',
      stance: 'Growth spread: DCF at VND 83.2k/share versus comparable value at VND 76.2k-77.1k/share.',
      thesis: [
        'FPT is a higher-quality growth company than the cyclical industrial names, so a FCFF DCF is appropriate. The valuation captures sustained IT services demand, telecom cash flow, education growth, and a cleaner margin profile.',
        'The DCF is intentionally above the comparable output. That is the right direction for a quality growth company: a DCF can capture multi-year compounding, while public comparable analysis is constrained by today’s peer multiples.',
        'The DCF is still not the old aggressive case. The terminal exit multiple is 8.5x, not 14.0x, and the WACC remains 10.5%. The model therefore shows moderate upside rather than a stretched growth-stock valuation.',
        'Comparable analysis is used as the reality check. It trims high-growth peer outliers and asks where FPT should trade if investors apply selected public tech/telecom P/E medians today.',
      ],
      assumptions: [
        {
          label: 'DCF model',
          value: 'FCFF DCF',
          detail: 'Unlevered free cash flow is discounted at WACC. This is not a DDM because dividends are not the main value driver for the growth case.',
        },
        {
          label: 'Discount rate / terminal value',
          value: 'WACC 10.5%; exit EV/EBITDA 8.5x',
          detail: 'The terminal multiple is high enough to recognize FPT’s growth quality but low enough to avoid the old stretched valuation case. This is why DCF sits above comparable value without becoming unrealistic.',
        },
        {
          label: 'Operating case',
          value: 'Revenue growth 12.0% to 8.0%',
          detail: 'The model assumes growth moderates but remains structurally above more cyclical sectors.',
        },
        {
          label: 'Comparable set',
          value: 'Tech, IT services, telecom peers',
          detail: 'Selected peer medians of 14.0x LTM, 12.9x 2026E, and 11.7x 2027E provide the public-market sanity check after trimming high-growth outliers.',
        },
        {
          label: 'Why methods differ',
          value: 'DCF higher; comps lower',
          detail: 'DCF capitalizes FPT’s growth runway and cash-flow compounding. Comparable analysis reflects where listed peers trade today, so it should be lower and less optimistic.',
        },
      ],
      valuationResult: [
        {
          label: 'DCF output',
          value: 'VND 83.2k/share',
          detail: 'The DCF is the growth-upside case. It values FPT as a durable compounder with above-market growth and relatively clean cash conversion.',
        },
        {
          label: 'Comparable output',
          value: 'VND 76.2k-77.1k/share',
          detail: 'Selected peer multiples imply only modest upside because public markets apply a more conservative near-term multiple than the DCF terminal case.',
        },
        {
          label: 'Valuation spread',
          value: 'Approx. 8%-9%',
          detail: 'The spread is driven by duration. The more confidence one has in FPT’s long runway, the more weight the DCF deserves.',
        },
      ],
      interpretation: [
        'FPT is the case where a method spread is especially important. If the report only showed a single market-consistent price, it would hide the difference between near-term public multiples and long-duration intrinsic value.',
        'Investors who believe FPT can sustain growth in IT services, education, and telecom cash flow should pay more attention to the DCF output.',
        'Investors who want to anchor on what the market pays for comparable listed peers today should use the comparable range as the practical check.',
        'The final read is constructive but not extreme: the model supports upside, but most of that upside comes from believing in growth duration rather than from today’s peer multiples alone.',
      ],
      risks: [
        'A lower terminal multiple has a large impact because the company is valued as a duration growth asset.',
        'IT-services growth, wage pressure, FX, and overseas demand are the main operating sensitivities.',
        'Comparable valuation can compress if global technology multiples derate.',
        'If education or telecom cash flow underperforms, the DCF premium over comparable analysis would narrow.',
        'A higher WACC would reduce the value of later-year cash flows and pull DCF closer to the comparable range.',
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
    conclusion: 'BMP now shows a clear control-value spread: LBO is the financial-sponsor case at VND 142.0k/share, while precedent transactions imply a higher strategic/control value around VND 152.8k/share.',
    valuationNotes: [
      {
        method: 'Precedent Transactions',
        price: 'Approx. VND 152.8k/share',
        assumptions: 'Median selected precedent premium of 13.0%, with one-day and one-week premium checks below the headline control premium.',
        result: 'Precedent transactions land above the LBO because strategic/control buyers can justify a higher premium than a financial sponsor.',
        groups: ['transaction-lbo'],
      },
      {
        method: 'LBO',
        price: 'VND 142.0k/share',
        assumptions: 'Sponsor-return LBO; 5.0% control premium, entry EV/EBITDA around 7.4x, exit EV/EBITDA 7.5x, and 20.1% IRR in the template return case.',
        result: 'Sponsor case supports a modest premium but remains below precedent value because return hurdles constrain entry price.',
        groups: ['transaction-lbo'],
      },
    ],
    report: {
      headline: 'BMP valuation distinguishes financial-sponsor affordability from strategic control value.',
      stance: 'Control-value spread: LBO at VND 142.0k/share versus precedent value around VND 152.8k/share.',
      thesis: [
        'BMP is valued with precedent transactions and an LBO because the relevant question is control value. A sponsor or strategic buyer would underwrite entry price, leverage capacity, operating durability, and exit multiple rather than only current trading multiples.',
        'The two methods should not converge to the same number. The LBO is a financial-buyer affordability test. It asks what a sponsor can pay while still meeting a target IRR and cash-on-cash return. The precedent transaction check is a control-value test and can sit higher if strategic buyers pay for synergies, market access, or scarcity value.',
        'The model uses a modest 5.0% LBO premium to avoid overpaying in a sponsor case. The precedent check uses a higher 13.0% selected premium to reflect that control transactions typically clear above a financial buyer’s base case.',
        'That spread creates a useful negotiation frame: VND 142.0k/share is the sponsor-disciplined bid, while roughly VND 152.8k/share is the higher control-value indication.',
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
          value: '5.0% in LBO; 13.0% precedent median',
          detail: 'The LBO premium is deliberately modest because a sponsor must still clear return hurdles. The precedent premium is higher because control transactions can include strategic rationale.',
        },
        {
          label: 'Exit / return hurdle',
          value: '7.5x exit EV/EBITDA; 20.1% IRR',
          detail: 'The sponsor case is rebalanced at a VND 142.0k/share offer value with entry EV/EBITDA around 7.4x.',
        },
        {
          label: 'Why methods differ',
          value: 'Precedent above LBO',
          detail: 'A strategic/control buyer can pay for synergies or platform value. A financial sponsor is limited by leverage capacity, financing cost, exit multiple, and required IRR.',
        },
      ],
      valuationResult: [
        {
          label: 'Precedent output',
          value: 'Approx. VND 152.8k/share',
          detail: 'The selected 13.0% control premium produces the higher strategic/control-value indication.',
        },
        {
          label: 'LBO output',
          value: 'VND 142.0k/share',
          detail: 'The sponsor case supports a modest premium offer while maintaining the template 20.1% IRR and 2.50x cash return.',
        },
        {
          label: 'Valuation spread',
          value: 'Approx. VND 10.8k/share',
          detail: 'This spread is the control-value story: a strategic buyer can justify a higher price than a financial sponsor can underwrite.',
        },
      ],
      interpretation: [
        'BMP should be read as a transaction case, not a simple public-market multiple case. The question is what type of buyer is setting the price.',
        'If the buyer is a financial sponsor, the LBO value is the more relevant anchor because the sponsor must protect IRR, cash return, and debt capacity.',
        'If the buyer is strategic, the precedent transaction output deserves more weight because the buyer may pay for distribution, market position, procurement synergies, or scarcity.',
        'The final report should therefore show both numbers. Collapsing them into one value would hide the actual M&A negotiation dynamic.',
      ],
      risks: [
        'A lower exit multiple or weaker EBITDA path would compress the LBO offer quickly.',
        'Sponsor financing terms, interest costs, and leverage availability can change the clearing price.',
        'Precedent transaction samples can be stale or structurally different from BMP, so the premium output is a guide rather than a hard target.',
        'A strategic premium is only defensible if the acquirer can realize synergies or strategic benefits; otherwise the precedent value may overstate clearing price.',
        'PVC resin costs, construction demand, and margin stability are the operating variables that matter most for both transaction methods.',
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
    conclusion: 'PNJ now has a three-step valuation ladder: LBO is the sponsor floor, precedent is the middle control-value check, and comparable analysis is the higher public-growth case.',
    valuationNotes: [
      {
        method: 'LBO',
        price: 'VND 66.0k/share',
        assumptions: 'Sponsor-return LBO; 3.1% control premium, entry EV/EBITDA around 10.2x, exit EV/EBITDA 7.5x, and 20.1% IRR in the template return case.',
        result: 'Sponsor case is the lowest valuation anchor because leverage capacity, exit multiple discipline, and required returns cap what a financial buyer can pay.',
        groups: ['transaction-lbo'],
      },
      {
        method: 'Comparable / Precedent',
        price: 'Comparable VND 72.8k-74.3k; precedent approx. VND 69.8k',
        assumptions: 'Selected retail peer P/E medians of 13.2x LTM, 9.8x 2026E, and 10.2x 2027E after trimming high-growth outliers; precedent premium of 9.0%.',
        result: 'Comparable analysis is the highest case because public retail investors can pay for brand quality and growth; precedent sits between the public-growth case and LBO floor.',
        groups: ['comparable', 'transaction-lbo'],
      },
    ],
    report: {
      headline: 'PNJ valuation shows a clear ladder from sponsor floor to public-growth upside.',
      stance: 'Three-method spread: LBO VND 66.0k, precedent approx. VND 69.8k, comparable VND 72.8k-74.3k/share.',
      thesis: [
        'PNJ is valued with a sponsor LBO plus comparable and precedent transaction checks. That mix is appropriate because a consumer retail issuer can be framed either as a public growth compounder or as a control transaction with finite sponsor-return constraints.',
        'The main conclusion is the ladder between methods. A sponsor LBO should be lowest because a financial buyer must protect IRR and debt capacity. A precedent transaction should sit in the middle because a control buyer may pay a premium. A comparable-company analysis can be highest because public markets may pay for brand, store productivity, and growth optionality.',
        'This is the right scenario for PNJ. Jewelry retail is not just a balance-sheet asset; it has brand value, store economics, inventory exposure, and consumer-demand cyclicality. Different buyer types will value those drivers differently.',
        'The workbook now reflects that logic: LBO remains modest at VND 66.0k/share, precedent premium lifts value to about VND 69.8k/share, and selected retail peer multiples produce VND 72.8k-74.3k/share.',
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
          detail: 'The comparable analysis uses selected peer P/E medians of 13.2x LTM, 9.8x 2026E, and 10.2x 2027E to estimate what the public market might pay for similar earnings quality.',
        },
        {
          label: 'Precedent model',
          value: 'Control-premium transaction check',
          detail: 'The precedent analysis uses a selected 9.0% median premium to cross-check the LBO offer. It is intentionally above LBO and below comparable analysis.',
        },
        {
          label: 'Sponsor assumptions',
          value: '3.1% premium; 10.2x entry EV/EBITDA; 7.5x exit EV/EBITDA',
          detail: 'The sponsor case targets the template 20.1% IRR and 2.50x cash return at an offer value of VND 66.0k/share.',
        },
        {
          label: 'Why methods differ',
          value: 'LBO < precedent < comparable',
          detail: 'The LBO is constrained by sponsor returns. The precedent case adds a control premium. The comparable case reflects public-market willingness to pay for retail growth quality.',
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
          value: 'VND 72.8k-74.3k/share',
          detail: 'Selected retail peer multiples are the highest valuation case because they capitalize PNJ as a public consumer-growth name.',
        },
        {
          label: 'Precedent output',
          value: 'Approx. VND 69.8k/share',
          detail: 'The selected 9.0% control premium sits between the sponsor LBO and public comparable valuation.',
        },
        {
          label: 'Valuation spread',
          value: 'Approx. VND 8.3k/share',
          detail: 'The spread from LBO to comparable is the key analytical output. It shows how much value depends on whether PNJ is viewed as a sponsor deal, a control transaction, or a public growth retailer.',
        },
      ],
      interpretation: [
        'PNJ should not be summarized with one blended price. The method ladder is more informative because the company can plausibly be valued by different investor types.',
        'The LBO value is the floor for a disciplined financial buyer. If debt capacity, exit multiple, or cash conversion disappoints, even that floor could move lower.',
        'The precedent value is the middle case for control buyers. It requires a buyer willing to pay a premium, but not necessarily the full public-growth multiple.',
        'The comparable value is the upside public-market case. It assumes investors pay for PNJ’s brand quality, store base, and earnings growth more like regional consumer peers.',
        'A reader should therefore leave the report understanding the choice: sponsor discipline supports the high-60k area, while public-growth framing can justify the low-70k area.',
      ],
      risks: [
        'Comparable value can overstate upside if peer margins, growth, or market structures are not truly comparable.',
        'LBO value is sensitive to exit multiple, leverage capacity, and retail cash-flow resilience.',
        'Gold price volatility, consumer demand, inventory management, and store productivity are key operating risks.',
        'A weaker discretionary-spending cycle would hit the comparable case first because public multiples would compress.',
        'Inventory and working-capital pressure can reduce sponsor debt paydown and make the LBO floor less reliable.',
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
