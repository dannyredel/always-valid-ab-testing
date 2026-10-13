# Variance reduction: CUPED, CUPAC, MLRATE, and always-valid inference

> Written for Live A/B Lab on 2026-10-12. Basis for notebook 06 and a blog article.

## Why it matters here

Every interval on the page has the form *estimate ± multiplier × standard error*. The always-valid method raises the multiplier (3.04 instead of 1.96 at the planned sample size), which is the price of being allowed to look at any time. Variance reduction attacks the other factor: it shrinks the standard error, and the always-valid interval narrows by exactly the same proportion. The two are complementary: one makes peeking safe, the other makes each look sharper.

If a covariate $X$ measured **before** assignment explains a share $R^2$ of the outcome's variance, then:

- variance falls by a factor $1 - R^2$;
- the interval narrows by a factor $\sqrt{1 - R^2}$;
- the sample needed for the same power falls by a factor $1 - R^2$.

## CUPED (Deng, Xu, Kohavi & Walker, 2013)

**Controlled-experiment Using Pre-Experiment Data.** Replace the outcome $Y$ with

$$
\tilde Y = Y - \theta\,(X - \bar X), \qquad \theta = \frac{\operatorname{Cov}(Y, X)}{\operatorname{Var}(X)},
$$

where $X$ is usually the same metric measured before the experiment. Because $X$ is independent of assignment, $\tilde Y$ has the same expected difference between arms but smaller variance.

- Equivalent to a regression of $Y$ on treatment and $X$.
- **Lin (2013)** showed that adding treatment × covariate interactions (centred covariates) makes the adjustment never worse than no adjustment, even with a misspecified model. That is the version we will use.

## CUPAC (DoorDash, 2020)

**Control Using Predictions As Covariates.** Instead of one raw pre-period metric, use a **machine-learning prediction** of the outcome, built only from pre-treatment features, as the covariate $X$ in CUPED. A model can combine many weak signals into one strong one.

- Not a peer-reviewed paper: an engineering blog post by Jeff Li at DoorDash (8 June 2020). DoorDash reported roughly 10–20% smaller required samples.
- Etsy later described its own implementation ("predicted control variates").
- The rule that makes it valid: the model must be trained on data that the experiment cannot influence (earlier cohorts, or cross-fitting), and use only features fixed before assignment.

## MLRATE (Guo et al., NeurIPS 2021)

**Machine Learning Regression-Adjusted Treatment Effect estimator**, from Meta. The academic treatment of the CUPAC idea:

- Uses cross-fitting, so the ML predictions are never made on the data they were trained on, which avoids overfitting bias.
- Proves consistency and asymptotic normality; if the predictions are useless, it is asymptotically no worse than the plain difference in means.
- On 48 metrics at Facebook: over 70% lower variance than difference in means, about 19% lower than single-covariate CUPED.

## Combining with always-valid intervals

Two routes, both usable here:

1. **Asymptotic confidence sequences** (Waudby-Smith, Arbour, Sinha, Kennedy & Ramdas, 2023), the method in notebook 03. It only needs an estimator that behaves like an average, with a consistent standard error. Regression-adjusted and AIPW estimators qualify, so we plug the adjusted standard error into the same multiplier. The adjustment coefficient is re-estimated as data arrives; that is fine asymptotically and gets checked by simulation in notebook 06. GrowthBook's `gbstats` supports this (`RegressionAdjustedStatistic` feeding its sequential test), so it remains our reference.
2. **Anytime-valid linear models** (Lindon, Ham, Tingley & Bojinov). Sequential F-tests and confidence sequences for regression, plus model-free confidence sequences for treatment effects in randomised experiments. Implemented in `avlm` (R) and `savvi` (Python). A second, independent check.

## The new-player problem (our case)

CUPED's gains come from a strong pre-treatment predictor. **New players have no history**, so classic CUPED (same metric, pre-period) is unavailable. With only what is known at sign-up (country tier, device, channel, time of day), our simulated world allows at most:

| Covariates | Best possible $R^2$ | Interval width | Sample needed |
|---|---|---|---|
| Sign-up attributes only (notebook 01 model) | 2.4% | × 0.988 | × 0.98 |
| A real pre-sign-up signal explaining 10% | 10% | × 0.949 | × 0.90 |
| A real pre-sign-up signal explaining 30% | 30% | × 0.837 | × 0.70 |

Is this a flaw of the simulation or how mobile gaming works? Both, partly:

- **True of the industry.** In new-user tests (onboarding, first-session rewards), there is no pre-period behaviour, and coarse attributes predict a yes/no outcome poorly. CUPED pays off most in tests on *existing* players (live ops, pricing, store offers), where past spend and sessions are strong predictors.
- **Simplified in our world.** Real user-acquisition pipelines do carry richer signals known at install: campaign and creative, ad network, device model and price tier, click-to-install time, re-install flags, and often a **predicted LTV or engagement score** from the acquisition partner. A CUPAC model built on these, trained on earlier cohorts, is what a gaming data team would actually use.

**Plan (Daniel, 2026-10-12): do both.** Notebook 06 first shows regression adjustment on the sign-up attributes (correct, honest, tiny gain, and why), then adds one realistic pre-sign-up signal to the simulator and a CUPAC model trained on an earlier cohort, and shows the payoff in interval width and sample size.

## References

- Deng, A., Xu, Y., Kohavi, R., & Walker, T. (2013). Improving the sensitivity of online controlled experiments by utilizing pre-experiment data. *WSDM '13*. (Extracted text in Vega's paper library: `Vega/paper-library/md/`.)
- Lin, W. (2013). Agnostic notes on regression adjustments to experimental data: Reexamining Freedman's critique. *Annals of Applied Statistics*, 7(1).
- Li, J. (2020). Improving experimental power through Control Using Predictions as Covariate (CUPAC). DoorDash Engineering blog, 8 June 2020. Repost: https://opendatascience.com/tag/control-using-predictions-as-covariates/
- Etsy Code as Craft. Reducing experiment duration with predicted control variates. https://www.etsy.com/codeascraft/reducing-experiment-duration-with-predicted-control-variates
- Guo, Y., Coey, D., Konutgan, M., Li, W., Schoener, C., & Goldman, M. (2021). Machine learning for variance reduction in online experiments. *NeurIPS 34*. https://arxiv.org/abs/2106.07263
- Waudby-Smith, I., Arbour, D., Sinha, R., Kennedy, E. H., & Ramdas, A. (2023). Time-uniform central limit theory and asymptotic confidence sequences. https://arxiv.org/abs/2103.06476
- Lindon, M., Ham, D. W., Tingley, M., & Bojinov, I. Anytime-valid linear models and regression adjusted causal inference in randomized experiments. https://arxiv.org/abs/2210.08589 (R package `avlm`).
