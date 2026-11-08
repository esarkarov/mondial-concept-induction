# Baselines

`python -m baselines.run_baselines` from the project root (after `src.labels`, `src.folds`, `src.features`).

Missing values stay NaN in `data/processed/features_<variant>.csv`. The baseline imputes them inside each training fold with `SimpleImputer(strategy="median")` (`keep_empty_features=True`), then applies the same medians to the test fold. Binary and share columns that are absent for a country with data in the source table are 0, not NaN.

Metrics are computed per test fold with the positive class (EU member) as target, averaged over the folds of a repeat, then mean and std (ddof=1) are taken over the repeats. Precision, recall and F1 are 0 when undefined.
