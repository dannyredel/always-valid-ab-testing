// Papers, books and software behind the methods on this page. Each entry says where it is used.
// Only works the notebooks or theory notes (docs/theory/) actually rely on.

export interface Reference {
  authors: string;
  year: number;
  title: string;
  venue: string;
  url: string;
  usedFor: string;
}

export interface ReferenceGroup {
  title: string;
  intro: string;
  items: Reference[];
}

export const REFERENCES: ReferenceGroup[] = [
  {
    title: 'Online experiments',
    intro: 'The practice of A/B testing at scale.',
    items: [
      {
        authors: 'Kohavi, R., Tang, D., & Xu, Y.', year: 2020,
        title: 'Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing',
        venue: 'Cambridge University Press', url: 'https://doi.org/10.1017/9781108653985',
        usedFor: 'The overall test design: one primary metric, a guardrail, the split check and pre-registered segments.',
      },
      {
        authors: 'Fabijan, A., Gupchup, J., Gupta, S., Omhover, J., Qin, W., Vermeer, L., & Dmitriev, P.', year: 2019,
        title: 'Diagnosing sample ratio mismatch in online controlled experiments: a taxonomy and rules of thumb for practitioners',
        venue: 'KDD 2019', url: 'https://doi.org/10.1145/3292500.3330722',
        usedFor: 'Why a broken 50 / 50 split is checked first.',
      },
    ],
  },
  {
    title: 'Peeking and always-valid inference',
    intro: 'Why checking a usual interval at every update goes wrong, and the intervals that stay valid however often you look.',
    items: [
      {
        authors: 'Armitage, P., McPherson, C. K., & Rowe, B. C.', year: 1969,
        title: 'Repeated significance tests on accumulating data',
        venue: 'Journal of the Royal Statistical Society, Series A, 132(2), 235–244', url: 'https://doi.org/10.2307/2343787',
        usedFor: 'The peeking problem: repeated looks inflate false alarms (notebook 02).',
      },
      {
        authors: 'Robbins, H.', year: 1970,
        title: 'Statistical methods related to the law of the iterated logarithm',
        venue: 'Annals of Mathematical Statistics, 41(5), 1397–1409', url: 'https://doi.org/10.1214/aoms/1177696786',
        usedFor: 'The normal-mixture boundary behind the always-valid interval.',
      },
      {
        authors: 'Johari, R., Koomen, P., Pekelis, L., & Walsh, D.', year: 2022,
        title: 'Always valid inference: continuous monitoring of A/B tests',
        venue: 'Operations Research, 70(3), 1806–1821', url: 'https://doi.org/10.1287/opre.2021.2135',
        usedFor: 'Always-valid p-values for A/B tests (the mixture SPRT used by Optimizely and Statsig).',
      },
      {
        authors: 'Howard, S. R., Ramdas, A., McAuliffe, J., & Sekhon, J.', year: 2021,
        title: 'Time-uniform, nonparametric, nonasymptotic confidence sequences',
        venue: 'Annals of Statistics, 49(2), 1055–1080', url: 'https://doi.org/10.1214/20-AOS1991',
        usedFor: 'Confidence sequences and tuning them to be tightest at a planned sample size.',
      },
      {
        authors: 'Waudby-Smith, I., Arbour, D., Sinha, R., Kennedy, E. H., & Ramdas, A.', year: 2023,
        title: 'Time-uniform central limit theory and asymptotic confidence sequences',
        venue: 'arXiv:2103.06476', url: 'https://arxiv.org/abs/2103.06476',
        usedFor: 'The interval on this page: an asymptotic confidence sequence from running totals (notebook 03).',
      },
      {
        authors: 'Maharaj, A. V., Sinha, R., Arbour, D., Waudby-Smith, I., Liu, S. Z., Sinha, M., Addanki, R., Ramdas, A., Garg, M., & Swaminathan, V.', year: 2023,
        title: 'Anytime-valid confidence sequences in an enterprise A/B testing platform',
        venue: 'WWW ’23 Companion', url: 'https://doi.org/10.1145/3543873.3584635',
        usedFor: 'The same method in production at Adobe, including sample-size planning.',
      },
      {
        authors: 'Ramdas, A., Grünwald, P., Vovk, V., & Shafer, G.', year: 2023,
        title: 'Game-theoretic statistics and safe anytime-valid inference',
        venue: 'Statistical Science, 38(4), 576–601', url: 'https://doi.org/10.1214/23-STS894',
        usedFor: 'Background: betting, e-values and Ville’s inequality.',
      },
      {
        authors: 'Lindon, M., & Malek, A.', year: 2022,
        title: 'Anytime-valid inference for multinomial count data',
        venue: 'NeurIPS 2022', url: 'https://arxiv.org/abs/2011.03567',
        usedFor: 'The always-valid split check (notebook 05).',
      },
    ],
  },
  {
    title: 'Variance reduction',
    intro: 'Using what is known before assignment to make the interval narrower without bias.',
    items: [
      {
        authors: 'Deng, A., Xu, Y., Kohavi, R., & Walker, T.', year: 2013,
        title: 'Improving the sensitivity of online controlled experiments by utilizing pre-experiment data',
        venue: 'WSDM 2013', url: 'https://doi.org/10.1145/2433396.2433413',
        usedFor: 'CUPED, the adjustment CUPAC builds on.',
      },
      {
        authors: 'Li, J.', year: 2020,
        title: 'Improving experimental power through control using predictions as covariate (CUPAC)',
        venue: 'DoorDash Engineering blog',
        url: 'https://careersatdoordash.com/blog/improving-experimental-power-through-control-using-predictions-as-covariate-cupac/',
        usedFor: 'CUPAC: a model’s prediction as the covariate (notebook 06).',
      },
      {
        authors: 'Lin, W.', year: 2013,
        title: 'Agnostic notes on regression adjustments to experimental data: reexamining Freedman’s critique',
        venue: 'Annals of Applied Statistics, 7(1), 295–318', url: 'https://doi.org/10.1214/12-AOAS583',
        usedFor: 'The regression cross-check of the adjusted estimate.',
      },
      {
        authors: 'Hosseini, R., & Najmi, A.', year: 2019,
        title: 'Unbiased variance reduction in randomized experiments',
        venue: 'arXiv:1904.03817', url: 'https://arxiv.org/abs/1904.03817',
        usedFor: 'Why a predictive model fitted outside the experiment keeps the estimate unbiased.',
      },
      {
        authors: 'Lindon, M., Ham, D. W., Tingley, M., & Bojinov, I.', year: 2022,
        title: 'Anytime-valid linear models and regression adjusted causal inference in randomized experiments',
        venue: 'arXiv:2210.08589', url: 'https://arxiv.org/abs/2210.08589',
        usedFor: 'Combining regression adjustment with always-valid inference.',
      },
    ],
  },
  {
    title: 'Heterogeneous effects and targeting',
    intro: 'Who benefits most, and who should get the bonus.',
    items: [
      {
        authors: 'Wager, S., & Athey, S.', year: 2018,
        title: 'Estimation and inference of heterogeneous treatment effects using random forests',
        venue: 'Journal of the American Statistical Association, 113(523), 1228–1242', url: 'https://doi.org/10.1080/01621459.2017.1319839',
        usedFor: 'Causal forests with honest trees (notebook 08).',
      },
      {
        authors: 'Athey, S., Tibshirani, J., & Wager, S.', year: 2019,
        title: 'Generalized random forests',
        venue: 'Annals of Statistics, 47(2), 1148–1178', url: 'https://doi.org/10.1214/18-AOS1709',
        usedFor: 'The forest estimator econml implements.',
      },
      {
        authors: 'Nie, X., & Wager, S.', year: 2021,
        title: 'Quasi-oracle estimation of heterogeneous treatment effects',
        venue: 'Biometrika, 108(2), 299–319', url: 'https://doi.org/10.1093/biomet/asaa076',
        usedFor: 'The R-learner objective the forest minimises.',
      },
      {
        authors: 'Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J.', year: 2018,
        title: 'Double/debiased machine learning for treatment and structural parameters',
        venue: 'The Econometrics Journal, 21(1), C1–C68', url: 'https://doi.org/10.1111/ectj.12097',
        usedFor: 'Cross-fitting and orthogonal scores (DoubleML group effects).',
      },
      {
        authors: 'Chernozhukov, V., Demirer, M., Duflo, E., & Fernández-Val, I.', year: 2018,
        title: 'Generic machine learning inference on heterogeneous treatment effects in randomized experiments, with an application to immunization in India',
        venue: 'NBER Working Paper 24678', url: 'https://doi.org/10.3386/w24678',
        usedFor: 'The calibration test: are the differences the forest found real?',
      },
      {
        authors: 'Yadlowsky, S., Fleming, S., Shah, N., Brunskill, E., & Wager, S.', year: 2025,
        title: 'Evaluating treatment prioritization rules via rank-weighted average treatment effects',
        venue: 'Journal of the American Statistical Association', url: 'https://arxiv.org/abs/2111.07966',
        usedFor: 'The targeting curve on the held-out half.',
      },
      {
        authors: 'Kitagawa, T., & Tetenov, A.', year: 2018,
        title: 'Who should be treated? Empirical welfare maximization methods for treatment choice',
        venue: 'Econometrica, 86(2), 591–616', url: 'https://doi.org/10.3982/ECTA13288',
        usedFor: 'Choosing who gets a treatment by the value it creates.',
      },
      {
        authors: 'Athey, S., & Wager, S.', year: 2021,
        title: 'Policy learning with observational data',
        venue: 'Econometrica, 89(1), 133–161', url: 'https://doi.org/10.3982/ECTA15732',
        usedFor: 'Scoring targeting rules with doubly robust estimates.',
      },
    ],
  },
  {
    title: 'Software',
    intro: 'The libraries the Python engine is checked against or built on.',
    items: [
      {
        authors: 'GrowthBook', year: 2024, title: 'gbstats: GrowthBook’s statistics engine',
        venue: 'Open-source software', url: 'https://github.com/growthbook/growthbook/tree/main/packages/stats',
        usedFor: 'Reference values the always-valid interval is tested against.',
      },
      {
        authors: 'Battocchi, K., Dillon, E., Hei, M., Lewis, G., Oka, P., Oprescu, M., & Syrgkanis, V.', year: 2019,
        title: 'EconML: a Python package for ML-based heterogeneous treatment effects estimation',
        venue: 'Open-source software', url: 'https://github.com/py-why/EconML',
        usedFor: 'Causal forest, calibration test and policy tree (notebook 08).',
      },
      {
        authors: 'Bach, P., Chernozhukov, V., Kurz, M. S., & Spindler, M.', year: 2022,
        title: 'DoubleML: an object-oriented implementation of double machine learning in Python',
        venue: 'Journal of Machine Learning Research, 23(53), 1–6', url: 'https://jmlr.org/papers/v23/21-0862.html',
        usedFor: 'Group effects for the subgroup baseline (notebook 08).',
      },
      {
        authors: 'Chen, H., Harinen, T., Lee, J.-Y., Yung, M., & Zhao, Z.', year: 2020,
        title: 'CausalML: Python package for causal machine learning',
        venue: 'arXiv:2002.11631', url: 'https://arxiv.org/abs/2002.11631',
        usedFor: 'The balance table (standardised differences).',
      },
      {
        authors: 'Seabold, S., & Perktold, J.', year: 2010,
        title: 'statsmodels: econometric and statistical modeling with Python',
        venue: 'Proceedings of the 9th Python in Science Conference', url: 'https://doi.org/10.25080/Majora-92bf1922-011',
        usedFor: 'Usual intervals, power, regressions and Wilson intervals throughout.',
      },
    ],
  },
];
