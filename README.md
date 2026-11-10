# Financial Peer Groups in Thai Finance

Groups 27 Thai financial companies by what their statements look like, rather than by business type, and flags the companies least like the others. Built with pandas, NumPy, scikit-learn, Matplotlib and Seaborn.

## Outputs

| File | What it shows |
|---|---|
| [output/dashboard.html](output/dashboard.html) | One-page dashboard: summary, cluster cards, charts and the company table. Download and open it in a browser |
| [output/01_company_map.png](output/01_company_map.png) | Companies placed by financial profile; closer means more similar |
| [output/02_profile_heatmap.png](output/02_profile_heatmap.png) | Each company's six measures against the typical company |
| [output/03_unusual_companies.png](output/03_unusual_companies.png) | Isolation Forest score; orange marks the flagged companies |
| [output/04_cluster_check.png](output/04_cluster_check.png) | Silhouette and bootstrap stability for 2 to 5 clusters |
| [output/companies.csv](output/companies.csv) | Measures, cluster and score for each company |
| [Financial_Peer_Groups_Explained.docx](docs/Financial_Peer_Groups_Explained.docx) | Explanation in Thai: purpose, objectives, method, tools, results and limits |

![Company map](output/01_company_map.png)

## Results

| Cluster | Compared with all companies | Members |
|---|---|---|
| A (16) | Lower equity to assets, steadier ROA | All 9 banks, ASK, ASP, BLA, BUI, KGI, MTI, THANI |
| B (7) | More volatile ROA, lower ROE | AIRA, AYUD, GBX, NKI, THRE, THREL, TNITY |
| C (4) | Faster asset growth, higher credit cost | AEONTS, KTC, MTC, SAWAD |

- Clusters match business type only weakly (adjusted Rand index 0.16, where 1 is identical).
- Isolation Forest flags TNITY, SAWAD and KTC as least like the others. Unusual means different, not better or worse.

## Method

1. Summarize each company's 2021-2025 data as six measures: median ROE, ROA, equity to assets and credit cost to assets, asset growth (CAGR) and ROA volatility.
2. Fill gaps with the median, cap values at the 5th and 95th percentiles, and scale with `RobustScaler`.
3. Score 2 to 5 clusters with `KMeans` on silhouette and bootstrap stability, and keep 3.
4. Project to two axes with `PCA` for the map, and score unusualness with `IsolationForest`.

## Run it

```bash
pip install -r requirements.txt
python peer_analysis.py --open
```

The script reads `company_panel.csv` and overwrites the files in `output/`. `company_panel.csv` was built from the workbooks in `data/workbooks` by the separate [thai-financials-pipeline](https://github.com/KorawitJung/thai-financials-pipeline) project.

## Data sources

The workbooks in [data/workbooks](data/workbooks) are annual statement exports for 2021-2025. Amounts are in thousand baht. 26 use the SET statement export layout; the SCB file uses a separate bilingual layout and holds Siam Commercial Bank's statements, not those of its listed parent SCBX. Each company also has its own page on the Stock Exchange of Thailand (SET) and its filings on the Thai SEC.

| Company | Group | Workbook | SET page | SEC filings |
|---|---|---|---|---|
| BAY | Bank | [FinancialStatement BAY 2021-2025.xlsx](data/workbooks/FinancialStatement%20BAY%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/BAY/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=BAY) |
| BBL | Bank | [FinancialStatement BBL 2021-2025.xlsx](data/workbooks/FinancialStatement%20BBL%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/BBL/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=BBL) |
| KBANK | Bank | [FinancialStatement Kbank 2021-2025.xlsx](data/workbooks/FinancialStatement%20Kbank%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/KBANK/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=KBANK) |
| KKP | Bank | [FinancialStatement KKP 2021-2025.xlsx](data/workbooks/FinancialStatement%20KKP%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/KKP/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=KKP) |
| KTB | Bank | [FinancialStatement KTB 2021-2025.xlsx](data/workbooks/FinancialStatement%20KTB%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/KTB/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=KTB) |
| LHFG | Bank | [FinancialStatement LHFG 2021-2025.xlsx](data/workbooks/FinancialStatement%20LHFG%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/LHFG/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=LHFG) |
| SCB | Bank | [FinancialStatement SCB 2021-2025.xlsx](data/workbooks/FinancialStatement%20SCB%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/SCB/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=SCB) |
| TISCO | Bank | [FinancialStatement TISCO 2021-2025.xlsx](data/workbooks/FinancialStatement%20TISCO%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/TISCO/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=TISCO) |
| TTB | Bank | [FinancialStatement TTB 2021-2025.xlsx](data/workbooks/FinancialStatement%20TTB%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/TTB/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=TTB) |
| AEONTS | Other financials | [FinancialStatement AEONTS 2021-2025.xlsx](data/workbooks/FinancialStatement%20AEONTS%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/AEONTS/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=AEONTS) |
| AIRA | Other financials | [FinancialStatement AIRA 2021-2025.xlsx](data/workbooks/FinancialStatement%20AIRA%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/AIRA/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=AIRA) |
| ASK | Other financials | [FinancialStatement ASK 2021-2025.xlsx](data/workbooks/FinancialStatement%20ASK%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/ASK/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=ASK) |
| ASP | Other financials | [FinancialStatement ASP 2021-2025.xlsx](data/workbooks/FinancialStatement%20ASP%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/ASP/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=ASP) |
| GBX | Other financials | [FinancialStatement GBX 2021-2025.xlsx](data/workbooks/FinancialStatement%20GBX%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/GBX/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=GBX) |
| KGI | Other financials | [FinancialStatement KGI 2021-2025.xlsx](data/workbooks/FinancialStatement%20KGI%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/KGI/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=KGI) |
| KTC | Other financials | [FinancialStatement KTC 2021-2025.xlsx](data/workbooks/FinancialStatement%20KTC%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/KTC/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=KTC) |
| MTC | Other financials | [FinancialStatement MTC 2021-2025.xlsx](data/workbooks/FinancialStatement%20MTC%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/MTC/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=MTC) |
| SAWAD | Other financials | [FinancialStatement SAWAD 2021-2025.xlsx](data/workbooks/FinancialStatement%20SAWAD%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/SAWAD/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=SAWAD) |
| THANI | Other financials | [FinancialStatement THANI 2021-2025.xlsx](data/workbooks/FinancialStatement%20THANI%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/THANI/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=THANI) |
| TNITY | Other financials | [FinancialStatement TNITY 2021-2025.xlsx](data/workbooks/FinancialStatement%20TNITY%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/TNITY/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=TNITY) |
| AYUD | Insurance | [FinancialStatement AYUD 2021-2025.xlsx](data/workbooks/FinancialStatement%20AYUD%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/AYUD/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=AYUD) |
| BLA | Insurance | [FinancialStatement BLA 2021-2025.xlsx](data/workbooks/FinancialStatement%20BLA%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/BLA/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=BLA) |
| BUI | Insurance | [FinancialStatement BUI 2021-2025.xlsx](data/workbooks/FinancialStatement%20BUI%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/BUI/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=BUI) |
| MTI | Insurance | [FinancialStatement MTI 2021-2025.xlsx](data/workbooks/FinancialStatement%20MTI%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/MTI/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=MTI) |
| NKI | Insurance | [FinancialStatement NKI 2021-2025.xlsx](data/workbooks/FinancialStatement%20NKI%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/NKI/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=NKI) |
| THRE | Insurance | [FinancialStatement THRE 2021-2025.xlsx](data/workbooks/FinancialStatement%20THRE%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/THRE/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=THRE) |
| THREL | Insurance | [FinancialStatement THREL 2021-2025.xlsx](data/workbooks/FinancialStatement%20THREL%202021-2025.xlsx) | [SET](https://www.set.or.th/en/market/product/stock/quote/THREL/financial-statement/company-highlights) | [SEC filings](https://market.sec.or.th/public/idisc/en/viewmore/fs-full?searchSymbol=THREL) |

Filings used to check specific figures:
- [Kasikornbank audited statements, 2025](https://www.kasikornbank.com/en/IR/FinanInfoReports/financialReports/4Q25_audited-en.pdf): restated 2024 totals
- [Allianz Ayudhya Capital 56-1 One Report, 2025](https://ayud.azay.co.th/content/dam/onemarketing/azay/ayud-azay-co-th/investor-relations-information/annual-registration-statement-56-1/2568/2025-56-1-One-report-EN.pdf): reclassification of 2024 cash
- [Bank of Ayudhya reviewed statements, Q1 2025](https://www.krungsri.com/getmedia/541fcbaa-4a6e-459c-9813-1a7578a577e8/ir-financial-statement-mar2025-reviewed-en): 2024 cash figures

## Limitations

- Separation is moderate (silhouette 0.37, stability 0.71), so companies near a boundary could fall in another cluster.
- Five clusters score higher on silhouette (0.42) but leave two clusters of two companies, and five colors cannot be told apart reliably by color-blind readers, so the model stops at three.
- The 27 companies are a selection, not the whole market.
- Some insurers report on the equity method, and some 2024 figures were later restated, which affects comparison.
- Data redistribution terms have not been checked. Keep this repository private until they are.

This is a portfolio project, not investment advice.
