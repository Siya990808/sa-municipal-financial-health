# South African Municipal Financial Health

**Which municipalities are financially distressed — and what separates them from the healthy ones?**

Built entirely from the **National Treasury's Municipal Money API**. Public, free, no API key, no scraping.

> Postgraduate Diploma in Data Analytics · IIE Varsity College · Siyabonga Mfusi

---

## Headline findings

**One in three municipalities cannot cover a month of operating costs.** Treasury treats a one-month cash buffer as the floor. In FY2024, **72 of 235** municipalities sat below it — and **54 ended the year with negative cash**, meaning they spent money they did not have.

**Debtor collection has broken down sector-wide.** The median municipality carries **80% of its debtor book past 90 days**. This is not a handful of badly run councils; it is the normal condition. Revenue booked on the statement of financial performance is substantially not cash anyone will ever collect.

**R61.9 billion** of unauthorised, irregular, fruitless and wasteful expenditure was reported in a single year.

**Only 41 of 257 municipalities earned a clean audit** — 16.0%.

## The core result: the audit opinion tracks the money

The Auditor-General's opinion is about whether the *books* are reliable, not directly about solvency. If the two were unrelated, the grade would tell a resident nothing about their municipality's finances.

They are not unrelated. Median values, FY2024:

| Audit outcome | Cash (months) | Debt >90 days | Operating margin | UIFW / spend | n |
|---|---:|---:|---:|---:|---:|
| **Clean** | 6.7 | 61.6% | **+0.9%** | **0.8%** | 41 |
| Unqualified (emphasis of matter) | 3.4 | 80.3% | −8.9% | 11.8% | 98 |
| Qualified | 3.0 | 84.2% | −18.1% | 19.9% | 84 |
| Adverse | 2.7 | 87.7% | −28.4% | 31.3% | 5 |
| Disclaimer | 2.6 | 82.6% | −35.1% | 27.8% | 10 |

**Monotonic on every ratio.** Clean-audit municipalities hold roughly twice the cash, collect materially better, and are the only group that breaks even.

Spearman rank correlation against audit severity:

| Ratio | ρ |
|---|---:|
| UIFW as share of expenditure | **+0.516** |
| Operating margin | −0.389 |
| Debt over 90 days | +0.323 |
| Cash coverage | −0.184 |

**UIFW is the sharpest dividing line.** A clean-audit municipality reports irregular and wasteful spending near zero (0.8%); the very next grade down reports 11.8%. That is a step change, not a slope — and it is the strongest single correlate of a worse opinion.

## The metros

Eight metropolitan municipalities serve roughly 40% of the population. A district municipality in trouble is a local problem; a metro in trouble is a national one.

| Metro | Months of cash |
|---|---:|
| Ekurhuleni | **−1.5** |
| Johannesburg | **0.6** |
| eThekwini | 2.1 |
| Nelson Mandela Bay | 2.5 |
| Cape Town | 2.6 |
| Buffalo City | 3.3 |
| Mangaung | 8.4 |
| Tshwane | 21.2 |

Two of the eight sit below Treasury's one-month floor, Ekurhuleni on a negative cash position. Only three clear the preferred three-month buffer.

## By province

| Province | Median health score | Median cash (months) | Median UIFW |
|---|---:|---:|---:|
| Western Cape | **75.2** | 5.6 | **3.7%** |
| Gauteng | 54.4 | 0.8 | 8.7% |
| Limpopo | 53.4 | 4.0 | 9.4% |
| KwaZulu-Natal | 53.2 | 4.8 | 12.9% |
| Eastern Cape | 51.0 | 2.8 | 10.7% |
| Mpumalanga | 41.5 | 2.2 | 15.4% |
| Northern Cape | 41.0 | 2.2 | 18.9% |
| North West | 38.7 | 6.5 | **27.7%** |
| Free State | **37.7** | 2.0 | 17.1% |

Western Cape municipalities score roughly twice the Free State median. Gauteng is the interesting case — a mid-table health score sitting on the thinnest cash in the country, because its metros run large budgets on small buffers.

## Method

**Seven API extracts**, joined on Treasury's `demarcation.code`: municipality reference data, statement of financial performance, cash flow, debtor ageing, UIFW, audit opinions, and capital expenditure.

**Four ratios**, each a standard credit-analysis measure:

| Ratio | Definition |
|---|---|
| Cash coverage | Year-end cash ÷ (operating expenditure ÷ 12) |
| Debt over 90 days | Debtor buckets from 91 days outward ÷ total debtor book |
| Operating margin | Surplus ÷ revenue |
| UIFW | (Unauthorised + irregular + fruitless) ÷ expenditure |

**Data quality is treated as part of the analysis, not plumbing.** Municipal returns are filed by hundreds of separate finance departments of wildly varying capacity, and some of what comes back is not credible. Each ratio is audited against the range it can physically occupy:

| Ratio | Reported | Implausible | Action |
|---|---:|---:|---|
| Cash coverage | 245 | 10 | voided |
| Debt over 90 days | 218 | 3 | voided |
| Operating margin | 245 | 1 | voided |
| UIFW | 246 | 0 | — |
| Capital execution | 243 | **25** | excluded from the composite |

Implausible values are set to missing rather than clipped. A municipality reporting more than 100% of its debtor book as over-90-days has a filing inconsistency; inventing a value of exactly 100% for it would be fabrication.

`capex_exec` is kept in the exported data but excluded from the composite score — one in ten filings reports capital spend wildly out of proportion to the adjusted budget, which is an artefact rather than an event.

**The composite score** converts each ratio to a **percentile rank** rather than a z-score. With outliers this extreme a z-score composite would be dominated by a few bad filings; percentile ranks are bounded and robust. A municipality is only scored if at least three of the four ratios are usable.

## Figures

| | |
|---|---|
| `figure_1_national_distributions.png` | All four ratios against their thresholds |
| `figure_2_audit_outcomes.png` | Audit outcomes 2015–2024, ordinal scale |
| `figure_3_health_by_audit.png` | Median ratios by audit outcome — the central result |
| `figure_4_distress_ranking.png` | The 20 most distressed municipalities |
| `figure_5_metros.png` | Cash coverage across the eight metros |

## Outputs

`outputs/municipal_scorecard.csv` — every municipality with all ratios, audit outcome and composite score. `outputs/health_by_audit_outcome.csv` — the summary table above.

## Reproducing

```bash
pip install -r requirements.txt
python src/fetch_data.py     # optional — data/ is committed
jupyter notebook notebooks/municipal_financial_health.ipynb
```

The extracts are small enough to commit, so the notebook runs offline with no API call. Re-running `fetch_data.py` refreshes them.

> One API quirk worth knowing if you build on this: multiple aggregates must be separated by `|`, not `,`. A comma-separated list is accepted silently and every measure after the first is dropped.

## Limitations

This is **reported** data. A municipality whose financial controls have collapsed is also the one least able to file accurate figures, so the worst cases are likely understated — the bias runs toward optimism exactly where scepticism is most warranted. Municipalities that failed to submit at all are absent from the ratios entirely, so the sector-wide picture here is, if anything, flattering.

The composite weights its four ratios equally. That is a defensible default, not a derived truth; a credit analyst would weight cash coverage more heavily and the ranking would move.

Ratios are single-year snapshots. A municipality can look solvent on the strength of a grant that landed just before year end.

## Data

[National Treasury Municipal Money API](https://municipaldata.treasury.gov.za/) — audited actuals for FY2024, audit opinions 2015–2024, across 257 municipalities. Public domain, no key required.

## Tech

Python · pandas · NumPy · Matplotlib · Jupyter
