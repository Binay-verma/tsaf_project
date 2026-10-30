# Past-only native interval calibration — completed 30 October 2026

This phase tests uncertainty adjustment, not a new point-forecast model. Native points, medians and quantiles are unchanged. The standard expansion-only conformalized quantile regression method is cited to Romano, Patterson and Candès (2019); temporal dependence means no automatic coverage guarantee.

Three rules were fixed before new comparison outcomes: unchanged native intervals, calibration using 16 labels from15–30September, and calibration using all labels strictly before each forecast **origin**. No future target label, method/window search or outcome-selected winner. Historical evaluation uses the same15target dates14–28October perstate/lead; these data were already inspected and remain exploratory.

The next-day table reports empirical coverage of nominal80%intervals. Each configuration has45related state/date cases. WIS is a proper interval/median score; lower is better. Coverage must be read with width costs in the full report.

| Configuration | Native coverage | Frozen Sept coverage | Expanding coverage | Native WIS | Frozen WIS | Expanding WIS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Chronos history |0.7333|0.8222|0.8222|0.3977|0.3936|0.3956|
| Chronos calendar |0.7111|0.8444|0.7778|0.4092|0.4041|0.4061|
| TimesFM history |0.7111|0.8444|0.8222|0.3649|0.3594|0.3599|
| TimesFM calendar |0.7778|0.8444|0.8444|0.3769|0.3770|0.3802|

Some next-day results improve, but intervals widen. At lead7, expansion generally increases already near-nominal coverage and **worsens WIS**. Lead14can still under-cover. The experiment does not solve the earlier differently scoped festival-feature uncertainty problem or improve unchanged point accuracy. All methods/negative outcomes remain reported.

The common primary comparison contains1,620intervalrows at leads1/7/14for four configurations. Additional TimesFM coverage spans all14leads:3,780rows including810overlap. Unique historical rows total4,590, not5,400independent observations. New342TimesFMcontext tasks reproduce792earlier point/quantile rows; independent input/date/rank/source/scale/score audits pass. All1,039protectedpriorartifacts remain unchanged.53tests pass in working and separate clean environments.

A **separate prospective interval annex** was issued30October2026at20:42:14IST and public commit29bdd984770904a032cebe9efcd2a12a8d5ffc17 was remote-verified before eligible target dates. It copies original frozen TimesFM points/quantiles and retains native/fixed/expanding arms before new historical coverage outcomes were reviewed. It contains216eligibleintervalrows=72originalTimesFMcases×3arms, covering31October–11November. This is the same episode/source, not independent confirmation. The original252forecast/protocol/freeze files remain unchanged. No future actuals or scores exist, and automation stays paused.

Read the [full report](results/native_calibration_v1/REPORT.md), [prospective annex](results/prospective_interval_20261030_v1/README.md), and [review supplement](manuscript/calibration_update_v1/CALIBRATION_UPDATE.md). The forecast preview shows pending predictions, never fabricated future observations. Source rights, amendments, human review, adequate independent/untouched evidence and verified Q1 venue rank remain open.
