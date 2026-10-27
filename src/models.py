"""
Phase 5 (machine learning): predict next-year distress (Altman Z' < 1.23 in
year t+1) from the financial ratios of year t.

Design (all randomness uses config.RANDOM_SEED):
- Time-based split only: train, validation and test are blocks of feature years.
- Every preprocessing step is fitted on the training rows only and then
  applied unchanged to later years: winsorising at the 1st/99th percentile,
  median imputation of blank ratios (with "was missing" indicator columns),
  and scaling (logistic regression only). XGBoost handles blanks natively.
- Class imbalance: class weights (no resampling).
- Settings are chosen on validation (PR-AUC), the decision threshold on
  validation (best F1 for the distressed class); each model is then refitted
  on train + validation and evaluated on test once.
"""

from itertools import product

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score, precision_recall_curve,
                             precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from src.labels import FEATURE_COLUMNS
from src.ratios import RATIO_COLUMNS

TARGET = "distressed_t1"
# Model inputs: the 18 Phase 4 features without low_revenue (those rows are
# excluded from modelling, so the flag would be constant).
FLAG_FEATURES = [c for c in FEATURE_COLUMNS if c not in RATIO_COLUMNS and c != "low_revenue"]
RATIO_FEATURES = list(RATIO_COLUMNS)
FEATURES = RATIO_FEATURES + FLAG_FEATURES


# ---------------------------------------------------------------------------
# Data and split
# ---------------------------------------------------------------------------
def prepare(modelling_table, include_low_revenue=False):
    """Labelled rows ready for modelling; flags converted to 0/1 numbers."""
    df = modelling_table.copy()
    if not include_low_revenue:
        df = df[~df["low_revenue"].astype(bool)]
    df[FLAG_FEATURES] = df[FLAG_FEATURES].astype(float)
    return df.reset_index(drop=True)


def split(df, train_years, val_years, test_years):
    """Boolean masks for the three blocks of feature years (labelled rows only)."""
    y = df["label_year"]
    lab = df[TARGET].notna()
    return {
        "train": lab & y.between(*train_years),
        "val": lab & y.between(*val_years),
        "test": lab & y.between(*test_years),
    }


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------
class Winsorizer(BaseEstimator, TransformerMixin):
    """Cap each column at percentiles learned in fit (training rows only).

    Blanks are ignored when computing the cutoffs and stay blank.
    """

    def __init__(self, lower=0.01, upper=0.99):
        self.lower = lower
        self.upper = upper

    def fit(self, X, y=None):
        X = pd.DataFrame(X)
        self.columns_ = list(X.columns)
        self.low_ = X.quantile(self.lower)
        self.high_ = X.quantile(self.upper)
        return self

    def transform(self, X):
        X = pd.DataFrame(X, columns=self.columns_)
        return X.clip(lower=self.low_, upper=self.high_, axis=1)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.columns_, dtype=object)


def preprocessor(impute=True, scale=False):
    """Winsorise ratios (+ optional median imputation with indicators and scaling); flags pass through."""
    steps = [("winsorise", Winsorizer())]
    if impute:
        steps.append(("impute", SimpleImputer(strategy="median", add_indicator=True)))
    if scale:
        steps.append(("scale", StandardScaler()))
    ct = ColumnTransformer([("ratios", Pipeline(steps), RATIO_FEATURES),
                            ("flags", "passthrough", FLAG_FEATURES)],
                           verbose_feature_names_out=False)
    return ct.set_output(transform="pandas")


# ---------------------------------------------------------------------------
# Models and their small tuning grids
# ---------------------------------------------------------------------------
def model_specs(seed):
    """name -> (builder(params, y_train) -> Pipeline, parameter grid)."""
    def logreg(p, y):
        return Pipeline([("prep", preprocessor(scale=True)),
                         ("model", LogisticRegression(C=p["C"], class_weight="balanced", max_iter=5000))])

    def tree(p, y):
        return Pipeline([("prep", preprocessor()),
                         ("model", DecisionTreeClassifier(max_depth=p["max_depth"], min_samples_leaf=p["min_samples_leaf"],
                                                          class_weight="balanced", random_state=seed))])

    def forest(p, y):
        return Pipeline([("prep", preprocessor()),
                         ("model", RandomForestClassifier(n_estimators=500, max_depth=p["max_depth"],
                                                          min_samples_leaf=p["min_samples_leaf"], max_features="sqrt",
                                                          class_weight="balanced", random_state=seed, n_jobs=-1))])

    def xgb(p, y):
        # scale_pos_weight = healthy / distressed in the training rows: XGBoost's class weight
        spw = float((y == 0).sum() / max((y == 1).sum(), 1))
        return Pipeline([("prep", preprocessor(impute=False)),
                         ("model", XGBClassifier(n_estimators=p["n_estimators"], max_depth=p["max_depth"],
                                                 learning_rate=p["learning_rate"], subsample=0.8, colsample_bytree=0.8,
                                                 scale_pos_weight=spw, eval_metric="logloss", tree_method="hist",
                                                 random_state=seed, n_jobs=-1))])

    return {
        "Logistic regression": (logreg, {"C": [0.01, 0.1, 1, 10]}),
        "Decision tree": (tree, {"max_depth": [2, 3, 4, 5], "min_samples_leaf": [5, 10, 20]}),
        "Random forest": (forest, {"max_depth": [3, 5, 8, None], "min_samples_leaf": [1, 5, 10]}),
        "XGBoost": (xgb, {"n_estimators": [200, 500], "max_depth": [2, 3, 4], "learning_rate": [0.03, 0.1]}),
    }


def grid(param_grid):
    keys = list(param_grid)
    return [dict(zip(keys, vals)) for vals in product(*param_grid.values())]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def best_f1_threshold(y, prob):
    """Probability cutoff that maximises F1 for the distressed class."""
    prec, rec, thr = precision_recall_curve(y, prob)
    f1 = np.where(prec + rec > 0, 2 * prec * rec / (prec + rec), 0)[:-1]  # last point has no threshold
    return float(thr[np.argmax(f1)])


def evaluate(y, score, pred):
    """Metrics for the distressed class. `score` ranks rows (for ROC/PR-AUC); `pred` is 0/1."""
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0),
        "roc_auc": roc_auc_score(y, score),
        "pr_auc": average_precision_score(y, score),
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
        "rows": int(len(y)), "distressed": int(np.sum(y)),
    }


def tune(name, builder, param_grid, X_tr, y_tr, X_va, y_va):
    """Fit every setting on train, score PR-AUC on validation; return the table and the best setting."""
    rows = []
    for params in grid(param_grid):
        model = builder(params, y_tr).fit(X_tr, y_tr)
        prob = model.predict_proba(X_va)[:, 1]
        rows.append({"model": name, "params": params, "val_pr_auc": average_precision_score(y_va, prob),
                     "val_roc_auc": roc_auc_score(y_va, prob)})
    table = pd.DataFrame(rows).sort_values("val_pr_auc", ascending=False).reset_index(drop=True)
    return table, table.loc[0, "params"]


def walk_forward(df, builder, params, threshold, start_year, end_year, target=TARGET):
    """Out-of-sample probabilities by year: for each feature year t, train on
    labelled feature years <= t-1 (their labels are known by year t) and score
    every row of year t. Preprocessing is refitted inside each window.
    """
    out = []
    for t in range(start_year, end_year + 1):
        train = df[(df["label_year"] <= t - 1) & df[target].notna()]
        score_rows = df[df["label_year"] == t]
        if score_rows.empty:
            continue
        model = builder(params, train[target]).fit(train[FEATURES], train[target])
        prob = model.predict_proba(score_rows[FEATURES])[:, 1]
        out.append(score_rows[["cik", "name", "label_year", target]].assign(
            prob_distressed_t1=prob, pred_distressed_t1=(prob >= threshold).astype(int),
            train_rows=len(train), train_years=f"{int(train['label_year'].min())}-{t - 1}"))
    return pd.concat(out, ignore_index=True)
