import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)


def run_model(x_, y_, l1_min, l1_max):
    log_en = LogisticRegression(penalty="elasticnet", max_iter=10000, warm_start=True, solver="saga")
    param_grid = [{"C": np.linspace(0.1, 10, num=100), 'l1_ratio': np.linspace(l1_min, l1_max, num=21)}]
    clf = GridSearchCV(log_en, param_grid, cv=3, scoring="balanced_accuracy", n_jobs=-1, verbose=False)
    clf.fit(x_, y_)
    return clf


def print_stats(clf):
    best_estimator = clf.best_estimator_
    classes = " vs ".join(best_estimator.classes_)
    best_model_score = clf.best_score_
    coef_ = best_estimator.coef_[0]
    feature_num = len(np.nonzero(coef_)[0])
    print(f'Classes: {classes}\nBest estimator: {best_estimator}\n'
          f'Best model score: {best_model_score}\nFt number: {feature_num}')

    return coef_


data = pd.read_csv('Data/231213_RES_all_strategies.csv')

# Prep data for TEST
x = data.drop(columns=['Rat_ID', 'Treatment', 'n_reversals_long']).dropna(axis=0)
cols = list(x.filter(like='lats').columns)
cols.extend(list(x.filter(like='coef').columns))
x = x[cols]

features = x.columns
scaler = MinMaxScaler()
x = scaler.fit_transform(x)
y = data.dropna(axis=0)['Treatment'].reset_index(drop=True)
# Run model
model = run_model(x, y, l1_min=0.2, l1_max=1)
coef = print_stats(model)
coef_df = pd.DataFrame([features[np.nonzero(coef)[0]], coef[np.nonzero(coef)[0]]]).transpose()
fts = list(coef_df[0].values)

# Data for VALIDATION
x = data[fts].dropna(axis=1)
features = x.columns
scaler = MinMaxScaler()
x = scaler.fit_transform(x)
y = data['Treatment']
# Run model
run_model(x, y, l1_max=0.1)
coef = print_stats(model)

# feature output
coef_df = pd.DataFrame([features[np.nonzero(coef)[0]], coef[np.nonzero(coef)[0]]]).transpose()
coef_df.columns = ["Feature", "Coef"]
coef_df.Coef = coef_df.Coef.astype(float)
coef_df = coef_df.sort_values(by="Coef", ascending=False).reset_index(drop=True)

coef_df['Coef'] *= -1
