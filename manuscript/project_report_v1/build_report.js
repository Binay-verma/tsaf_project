// Full project report (Word). Tables come from tables.json (extracted from audited manuscript v6).
// Run from repo root: node manuscript/project_report_v1/build_report.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType,
  ShadingType, AlignmentType, Footer, PageNumber, LevelFormat, BorderStyle, PageBreak, ImageRun,
} = require("docx");

const DIR = __dirname;
const ROOT = path.resolve(DIR, "../..");
const T = JSON.parse(fs.readFileSync(path.join(DIR, "tables.json"), "utf8"));
const TC = JSON.parse(fs.readFileSync(path.join(ROOT, "review/journal_seven_tasks_20261031_v1/tie_correction_v2.json"), "utf8"));
const W = 9638; // A4 content width (DXA) with 2 cm margins

const P = (text, opts = {}) => new Paragraph({ spacing: { after: 120, line: 288 }, ...opts,
  children: (Array.isArray(text) ? text : [text]).map(t => typeof t === "string" ? new TextRun(t) : new TextRun(t)) });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const B = (text) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 80, line: 276 },
  children: (Array.isArray(text) ? text : [text]).map(t => new TextRun(t)) });
const bold = t => ({ text: t, bold: true });
const NOTE = t => new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })] });

function table(key, firstWidth, fixed) {
  const t = T[key];
  const n = t.header.length;
  const fw = firstWidth || Math.round(W / n);
  const rest = Math.floor((W - fw) / (n - 1));
  const widths = fixed ? fixed.slice() : [fw, ...Array(n - 1).fill(rest)];
  widths[n - 1] += W - widths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 4, color: "BFC7D1" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (txt, i, head, last) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, borders,
    shading: head ? { type: ShadingType.CLEAR, color: "auto", fill: "1F3B57" } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: [new Paragraph({ keepNext: !last, alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT,
      children: [new TextRun({ text: txt, size: 18, bold: head, color: head ? "FFFFFF" : "1A1A1A" })] })],
  });
  return [
    new Paragraph({ spacing: { before: 160, after: 80 }, keepNext: true,
      children: [new TextRun({ text: `${key}. `, bold: true, size: 20 }), new TextRun({ text: t.caption, size: 20 })] }),
    new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths,
      rows: [new TableRow({ tableHeader: true, cantSplit: true, children: t.header.map((h, i) => cell(h, i, true, false)) }),
             ...t.rows.map((r, k) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, i, false, k === t.rows.length - 1)) }))] }),
    new Paragraph({ spacing: { after: 120 }, children: [] }),
  ];
}

function figure(file, w, h, caption) {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: "png", data: fs.readFileSync(file),
      transformation: { width: w, height: h }, altText: { title: caption, description: caption, name: path.basename(file) } })] }),
    NOTE(caption),
  ];
}

const yo = TC.B_years.opposite_sign, yt = TC.B_years.exact_tie_in_either_year, lf = TC.B_lofo.cells_with_sign_flip;
const so = TC.A_typed_minus_pooled.opposite_sign, ss = TC.A_typed_minus_pooled.same_sign, st = TC.A_typed_minus_pooled.exact_tie_in_either;
const to = TC.A_typed_minus_pooled.timesfm_opposite;

const body = [
  // ---------- title ----------
  new Paragraph({ spacing: { before: 2400, after: 240 }, children: [new TextRun({ text: "Festival covariates in foundation and local forecasting models for Indian electricity", bold: true, size: 44, font: "Cambria", color: "1F3B57" })] }),
  new Paragraph({ spacing: { after: 480 }, children: [new TextRun({ text: "Full project report: question, data, methods, results, corrections, status and next steps", size: 26, color: "36606F" })] }),
  P([bold("Author: "), "Binay Verma"]),
  P([bold("Date: "), "1 November 2026"]),
  P([bold("Status: "), "Research in progress. Internal report for supervisor and viva use; not a journal submission and not independently reviewed."]),
  P([bold("Repository: "), "github.com/Binay-verma/tsaf_project (branch journal-seven-tasks-20261031-claude, commit c41d4fa)"]),
  P([bold("Sources of every number: "), "the audited manuscript v6 (manuscript/integrated_review_v6), the registered re-analysis and its tie correction (review/journal_seven_tasks_20261031_v1), and the project status files. Tables are extracted from v6 by script, not retyped."]),
  new Paragraph({ children: [new PageBreak()] }),

  // ---------- 1 ----------
  H1("1. Summary"),
  P("This project asks how festival information should be given to forecasting models for daily electricity supplied in three Indian states (Delhi, Karnataka, Maharashtra). Two pretrained time-series foundation models (Chronos-2 and TimesFM-3) and four local models (Ridge, SARIMAX, a stable LightGBM and a leaf-2 tree variant) receive the same cases under eight matched input designs: calendar only, five zero channels, typed (one flag per festival) and pooled (one shared flag) day or ±3-day window flags, and fake-date placebos."),
  B("Festival day flags usually reduce next-day error compared with calendar-only inputs (Table 1). The two lowest errors use different encodings: TimesFM-3 with pooled flags (0.42459) and SARIMAX with typed flags (0.42533)."),
  B(`The preferred encoding is not stable. Within India the typed-minus-pooled sign is opposite between 2024 and 2025 in ${yo} of 36 model/representation/lead cells (plus ${yt} exact tie); leaving out one festival flips it in ${lf} of 36; India and NYC agree in ${ss}, are opposite in ${so} and tie in ${st}; all ${to} TimesFM-3 cells reverse between India and NYC.`),
  B("Checking which festival a government notice actually names corrected one date (Karnataka 2025 Vijayadashami: 1 October, not 2 October)."),
  B("Native 80% prediction intervals of both foundation models under-cover festival periods: coverage is below 0.80 in 85 of 100 lead-1 festival-year/arm cells."),
  B("Genuinely future confirmation is set up (frozen forecasts, a registered weekly study, a drafted Singapore replication) but no future result exists yet."),
  P("The contribution is a careful empirical evaluation with controls and retained negative results. It is not a new architecture, a causal holiday effect, or a demonstration that one encoding is generally best."),

  // ---------- 2 ----------
  H1("2. Question and scope"),
  P("Main question: when festival information is sparse, is it better to give each festival family its own input (typed) or one shared input (pooled), and does the answer hold across models, years, festival sets and data sources?"),
  P("Typed design: five binary channels, one per family (Holi, Dussehra, Ganesh Chaturthi, Ugadi/Gudi Padwa, Diwali). Pooled design: one channel that is on for any family, padded with four zero channels so both designs use five channels. Equal channel counts do not mean equal information, and zero padding is itself tested."),
  P("Out of scope: unconstrained demand or hourly peak load, causal effects of festivals, new model architectures, and claims of contamination-free evaluation."),

  // ---------- 3 ----------
  H1("3. Data"),
  H2("3.1 Indian electricity"),
  P("Target: daily energy met/supplied in GWh for Delhi, Karnataka and Maharashtra, from Robbie Andrew's compilation of GRID-INDIA (formerly POSOCO) daily reports, snapshot retrieved 29 October 2026 (data through 28 October 2026). An earlier corrected state dataset (Hunt and Bloomfield, Zenodo 14983362, CC BY 4.0) is kept separate and never spliced. Historical revisions exist: archived values differ from later snapshots by up to 61.5 GWh in the reviewed cases, and two tested issue-date snapshots lag by 2–3 days. Scored labels are never imputed."),
  P("Event cases: 528 forecast cases = 176 state/target-date combinations × leads 1, 7 and 14, covering 75 distinct target dates, 24 family/state/year groups and 10 family-year clusters in 2024–2025. Ordinary cases: 216 seasonal non-festival cases. Nearby days, states and leads are correlated; the 10 family-year clusters are the effective event units."),
  H2("3.2 Festival calendars"),
  P("Dates come from state annual holiday notifications (named-family ledger). An all-58 anchor review found 54 declared-family matches, two explicit shared-national-main exceptions, one Karnataka 2025 mismatch and one Maharashtra 2022 Gudi Padwa evidence gap. The Karnataka 2025 notice names Vijayadashami on 1 October and Gandhi Jayanti on 2 October; the original ledger had used 2 October. A registered correction fixed this from the document, not from forecast errors, and recentred the affected window. The Maharashtra 2022 gap means the retained document does not corroborate the date; it is not proof the date is wrong. No amendment chains or human sign-off are certified."),
  H2("3.3 Separate-source checks"),
  B("NYC (MTA subway and bus ridership, dataset sayj-mze2): 84 event cases around Yom Kippur (21 Sept) and Columbus Day (12 Oct) 2026, 42 ordinary cases; a fixed 7-day observation buffer maps decision leads 1/7/14 to model steps 8/14/21. The protocol was committed before the data were acquired; the public push time of that commit is not independently verified. Two occurrences in one city."),
  B("England/Wales (NESO transmission demand): 16 ordinary September 2026 days under ideal availability and a 21-day delay. No holidays; it tests a different electricity source and delay, not festival transfer."),

  // ---------- 4 ----------
  H1("4. Models and evaluation"),
  B("Foundation models: Chronos-2 and TimesFM-3 with pinned code and weights (hashes checked), 730-day context, fixed seeds, no fine-tuning. TimesFM-3 weights carry academic noncommercial terms."),
  B("Local models: rich Ridge, SARIMAX, stable float32 LightGBM and a separately reported leaf-2 tree, with parameters chosen on earlier data only, purged future labels and monthly refits. Local and foundation adaptation and history budgets differ, so rankings are not architecture-only comparisons."),
  B("Metric: MASE with a fixed pre-year 730-day weekly scale; averages taken within state/year/family, then states, years and families equally. Native intervals: 80% coverage, scaled width, pinball loss and WIS, with crossings and invalid intervals retained."),
  B("Inference policy: no daily-row significance tests or bootstraps over two event years; complete registered contrast ranges and cluster splits are reported instead."),

  // ---------- 5 ----------
  H1("5. Results"),
  H2("5.1 Indian festival windows"),
  ...table("Table 1", 2400),
  P("The full typed-minus-pooled range over all registered contrasts is −0.03971 to 0.05564 (positive favours pooling). Same-case feature changes from the calendar correction at lead 1 range from −0.00119 to 0.00836; changes from replacing the three recentred cases under original features range from −0.00251 to 0.00171. These are different quantities."),
  ...figure(path.join(ROOT, "presentation/viva_update_v2/lead1_mase.png"), 600, 210, "Figure 1. Lead-1 MASE for calendar-only, typed-day and pooled-day inputs (data of Table 1)."),
  ...table("Table 2", 2400),
  P("On ordinary days, festival inputs change errors little; Chronos-2 is slightly worse with festival flags than with calendar only on this sample."),
  H2("5.2 Stability across years, festivals and sources"),
  P(`Across the 36 cells (6 models × day/window × 3 leads), the 2024 and 2025 contrasts have opposite signs in ${yo} cells, with ${yt} exact tie (LightGBM day flags at lead 1 in 2024 give identical forecasts). Leaving out one family flips the balanced sign in ${lf} cells. India and NYC agree in ${ss} cells, are opposite in ${so} and tie in ${st} (LightGBM day flags give identical NYC forecasts). A few orderings persist: SARIMAX day flags at lead 1 favour typed identities in both years, under every leave-one-family-out subset and in NYC; TimesFM-3 day flags at lead 1 favour pooling in 9 of 10 Indian clusters but typed identities in NYC.`),
  ...figure(path.join(ROOT, "presentation/viva_update_v2/year_split_day_lead1.png"), 600, 210, "Figure 2. Typed-minus-pooled MASE by event year, day flags, lead 1 (positive favours pooling)."),
  ...table("Table A4", 0, [1900, 1000, 1100, 1100, 1100, 1150, 2288]),
  P("This split was registered before it was computed, but it uses forecasts that had already been inspected; the persistent orderings are expectations for future confirmation, not established effects. A first version of these counts treated exact ties as disagreements (reporting 20 and 14); the corrected values are used here and the original outputs are preserved."),
  H2("5.3 Closest calendar encodings"),
  ...table("Table 3", 2400),
  P("These are daily adaptations of the encodings studied by Kreusel et al. (2026), not an exact replication of their hourly experiment; channel counts differ, so the table does not isolate a coding effect."),
  H2("5.4 NYC and NESO"),
  ...table("Table 4", 2400),
  ...table("Table A1", 2400),
  ...table("Table 5", 2400),
  P("Delay does not necessarily worsen realised error in this small sample, because the forecast step and fitted features also change."),
  H2("5.5 Native uncertainty"),
  ...table("Table 6", 1700),
  ...table("Table A5", 1900),
  P("No common-grid crossings or invalid endpoints occur in this cohort. An earlier past-only calibration study (CQR, 4,590 historical interval rows) raised TimesFM history next-day coverage from 0.7111 to 0.8444 (frozen) or 0.8222 (expanding) but widened intervals; at longer leads WIS sometimes worsened. That study is a different cohort and is not a fix for festival intervals."),
  H2("5.6 Comparators and diagnostics"),
  ...table("Table A2", 2400),
  P("These fixed response-profile comparators are simpler daily adaptations, not the impact-driven learned event embeddings of Alipour et al., which could not be reproduced (no runnable code, incomplete settings, no account-level data)."),
  ...table("Table A3", 2000),
  P("Associations between past support/response heterogeneity and the typed-pooled contrast are weak and mixed; the 24 cells are not independent and composition can confound them. A controlled simulation (16 scenarios × 32 seeds = 512 datasets, 2,560 method cells) illustrates the familiar pooling trade-off under its own generator only."),
  H2("5.7 Earlier studies (different cohorts, kept for the record)"),
  B("Original four-year Chronos seven-channel Diwali input worsened mean day-1 festival MAE: a preserved negative result."),
  B("Mechanism controls (150 cases per arm): regional versus generic dates with equal seven channels changed mean MAE by about +1.4 to +1.6% for Chronos and +3.3 to +6.4% for TimesFM; seven zero channels alone changed some forecasts by 6–7 GWh."),
  B("Post-weight daily panel (396 cases per configuration, targets 15 Sept–28 Oct 2026): TimesFM history MASE 0.54620 / 1.16303 / 1.30856 at leads 1/7/14 versus Chronos history 0.58548 / 1.31670 / 1.59292. Previously inspected targets; not an untouched test."),
  B("Pooled-versus-typed (6,912 rows) and family-label exclusion (3,888 forecasts) studies: pooled flags help some models, Ridge and SARIMAX often prefer separate flags, and Ridge reverses at leads 7 and 14."),
  B("Refitting: monthly refits improve several aggregate local-model errors but can worsen individual festival-year results."),

  // ---------- 6 ----------
  H1("6. Failures, corrections and negative results retained"),
  B("An earlier float64 tree reproduction failed; a float32 version was introduced. In a stricter review, 15 of 45 Delhi lead-1 near-zero feature entries differ after float32 conversion while forecasts agree within 7.6e-12 GWh."),
  B("Integration failures (an encoder dispatch omission and a foreign schema field) were repaired with versioned adapters without changing cases, features, settings, metrics or tolerances; closed forecasts were kept byte-for-byte."),
  B("The Karnataka 2025 date correction and the Maharashtra 2022 evidence gap (section 3.2)."),
  B("The exact-tie counting error in the stability summary (section 5.2)."),
  B("Mixed and negative results: no universal pooling benefit, Chronos-2 slightly worse with festival flags on ordinary days, under-covering intervals."),

  // ---------- 7 ----------
  H1("7. Confirmation on future data"),
  B("Original freeze (30 October 2026): TimesFM history/calendar, Ridge, the original tree and naive forecasts; 216 eligible rows for 31 October–11 November. No festival-feature arms."),
  B("Interval annex (30 October, 20:42 IST): native/frozen/expanding intervals for the original TimesFM points; 216 rows."),
  B("Chronos-2 competitor (completed 31 October 05:14 IST): 84 stored, 66 eligible forecasts; same source and episode."),
  B("Scoring: not before 12 November 2026 05:30 IST and only with the first complete actual data vintage; no retuning. The target period includes Diwali 2026. One episode cannot confirm the typed-versus-pooled pattern."),
  B("Weekly rolling study: 52 Monday windows from 16 November 2026 (14:30–15:29 IST) to 8 November 2027; six models, eight arms, three states, decision leads 1/7/14. Not activated. A registered timing rule (v2, public before the first window) requires calendars only for the years each issuance touches; activation still needs reviewed source-rights and observation-day evidence and human-verified 2026 calendars. Missed windows are recorded, never back-filled."),
  B("Singapore replication: drafted, not registered. Energy Market Authority half-hourly demand and Ministry of Manpower public holidays (Chinese New Year, Hari Raya Puasa, Vesak Day, Hari Raya Haji, Deepavali). The code layer is ready; no data have been acquired."),

  // ---------- 8 ----------
  H1("8. Data rights and calendar status"),
  B("Indian compilation: no licence found; the author emailed the curator on 30 October 2026; no reply yet. The snapshot is in the public repository with a rights notice (data/external/RIGHTS_NOTICE.md) and will be removed on request. Public access is not a permission grant."),
  B("Hunt and Bloomfield and SASEA data: CC BY 4.0. MTA: the dataset overview states no data-use limitations. NESO: custom terms; raw archives are kept outside Git."),
  B("2026 state notifications were located only as copies on secondary hosts (Maharashtra gazette of 8 December 2025, Karnataka list, Delhi GNCTD order of 4 December 2025) and are not yet verified by a person. If confirmed, Dussehra is on 20 October in Delhi and Maharashtra but Vijayadashami on 21 October in Karnataka. A builder (src/calendar_package_builder_v1.py) and a blank form (review/calendar_entry_2026_v1) turn a human reading into the files the weekly study needs."),

  // ---------- 9 ----------
  H1("9. Reproducibility"),
  B("All code, protocols, forecasts, failures and audit files are in the repository; model weights and local environments are not."),
  B("121 automated tests pass in a fresh Python 3.12 environment with pinned packages; the continuation checksum verifier passes on Linux. On Windows, line-ending conversion makes the verifier report changes that are not real."),
  B("Clean internal reruns reproduce all 4,032 NYC local forecasts byte-for-byte and all 72 validation MAEs. These are internal software checks on the same software, not independent human reproduction. A reviewer packet (review/journal_seven_tasks_20261031_v1/REVIEWER_PACKET_v6.md) lists reproduction tiers and expected outputs."),

  // ---------- 10 ----------
  H1("10. Closest prior work"),
  B("Ziel (2018) compared one shared holiday dummy, grouped dummies and a separate dummy per holiday for German load; separate dummies did not generally improve on a single dummy, and univariate results were mixed by holiday type. The typed-versus-pooled choice is therefore not new; this project tests it through foundation-model covariate channels with zero and placebo controls."),
  B("Kreusel et al. (2026) study calendar encodings in covariate-informed foundation models including Chronos-2 and TimesFM-3 on hourly data."),
  B("Alipour et al. propose impact-driven learned event covariates; not reproducible here."),
  B("Sanyal et al. (2017) use moving-holiday regressors for Indian series; Arora and Taylor (2018) model special days with rule-based seasonal ARMA."),

  // ---------- 11 ----------
  H1("11. Limitations"),
  B("Two event years and three related states; NYC adds two occurrences in one city; NESO adds no holidays."),
  B("Historical outcomes were inspected, so all historical results are exploratory."),
  B("Weather, supply constraints, coincident observances, source revisions and calendar amendments are alternative explanations."),
  B("Model pretraining exposure to historical or proxy data cannot be ruled out."),
  B("Data reuse permission, calendar amendment certification and independent human review are outstanding."),

  // ---------- 12 ----------
  H1("12. Status of the seven journal tasks and next steps"),
  B([bold("Distinct contribution: "), "manuscript v6 done internally; distinctiveness is the supervisor's and reviewers' judgement."]),
  B([bold("Generalisation: "), "Singapore drafted with code ready; needs the EMA history and terms check, then a registration push."]),
  B([bold("Untouched confirmation: "), "guards intact; score frozen forecasts from 12 November; weekly study awaits rights evidence and verified calendars."]),
  B([bold("Closest methods: "), "mapped; only Ziel's holiday-as-Sunday variant is missing (optional)."]),
  B([bold("Source and calendar credibility: "), "rights notice added; 2026 calendars need a human reading of the PDFs; curator reply pending."]),
  B([bold("Independent review: "), "packet ready; needs a real external researcher."]),
  B([bold("Dependence and uncertainty: "), "cluster-level reporting done."]),
  P("Immediate actions, in order: verify the three 2026 calendar PDFs and build the calendar package; check the Singapore source page; obtain source-rights and reporting-day evidence; score the frozen episodes on or after 12 November 2026; ask the supervisor to review manuscript v6."),

  // ---------- refs ----------
  H1("References"),
  ...[
    "Ziel, F. (2018). Modeling public holidays in load forecasting: a German case study. Journal of Modern Power Systems and Clean Energy 6(2), 191–207. doi:10.1007/s40565-018-0385-5",
    "Arora, S. and Taylor, J.W. (2018). Rule-based autoregressive moving average models for forecasting load on special days: a case study for France. European Journal of Operational Research 266(1), 259–268. doi:10.1016/j.ejor.2017.08.056",
    "Kreusel, A. et al. (2026). On the encoding of calendar features in covariate-informed time series foundation models. arXiv:2610.13676.",
    "Alipour, E. et al. Impact-driven event covariates for time-series foundation models (venue metadata unresolved).",
    "Sanyal, Mitra, McElroy and Roy (2017). Holiday effects in Indian manufacturing series. US Census Bureau RRS2017-04.",
    "Kaljevic, Arzola and Zhang (2026). Benchmarking time series foundation models for load forecasting under covariate uncertainty. arXiv:2610.07232.",
    "Meyer et al. Rethinking evaluation in the era of time series foundation models: (un)known information leakage challenges. arXiv:2510.13654.",
    "Ansari et al. (2025). Chronos-2: from univariate to universal forecasting. arXiv:2510.15821.",
    "Romano, Patterson and Candès (2019). Conformalized quantile regression. arXiv:1905.03222.",
    "Andrew, R. Indian Energy and Emissions Data, robbieandrew.github.io/india (compiled from GRID-INDIA/POSOCO daily reports).",
    "Hunt and Bloomfield. Indian state daily electricity dataset, Zenodo 14983362 (CC BY 4.0).",
  ].map(r => new Paragraph({ spacing: { after: 100 }, indent: { left: 360, hanging: 360 }, children: [new TextRun({ text: r, size: 20 })] })),
];

const doc = new Document({
  creator: "Binay Verma", title: "Festival covariates and electricity forecasting: full project report",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Cambria", size: 32, bold: true, color: "1F3B57" }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Cambria", size: 26, bold: true, color: "36606F" }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1, keepNext: true } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Binay Verma — project report, 1 November 2026 — page ", size: 16, color: "777777" }),
                 new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: body,
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(DIR, "Project_Report_Binay_Verma.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out);
});
