from sklearn.linear_model import LogisticRegression
from itertools import groupby
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)


def get_strategy_metrics(trials_, session):
    """
    Example list of trials:[0, 0, 1, 0, 1, 1, 1]
    1. calculate accuracy
    2. groups_li: get groups & their counts e.g., [(0, 2), (1, 1), (0, 1), (1, 3)].
    - streak = the highest number of successive successful trials
    - persistent0s = number of zeros before first successful trial --> take the count of the first group
    - persistent0s_perc = persistent0s / total trials

    3. pairs_li: trials as pairs e.g., (0, 0), (0, 1), (1, 0), (0, 1), (1, 1), (1, 1). Count different strategies:
    (0, 0) = lose stay; (0, 1) = lose-shift; (1, 0) = win-shift; (1, 1) = win-stay

    :return: save the above metrics in a dictionary where the key is the animal ID
    """

    accuracy = sum(trials)/len(trials)

    groups_li = []
    for n, c in groupby(trials_):
        num, count = n, sum(1 for i in c)
        groups_li.append((num, count))
    streak = max([y for x, y in groups_li if x == 1.0])
    persistent0s = groups_li[0][1]
    persistent0s_perc = groups_li[0][1] / len(trials_)

    pairs_li = []
    for i in range(len(trials_)):
        pair = tuple(trials_[i:i + 2])
        pairs_li.append(pair)

    lose_stay = pairs_li.count((0.0, 0.0)) / len(trials_)
    lose_shift = pairs_li.count((0.0, 1.0)) / len(trials_)
    win_shift = pairs_li.count((1.0, 0.0)) / len(trials_)
    win_stay = pairs_li.count((1.0, 1.0)) / len(trials_)

    names_ = ['accuracy', 'streak', 'P0s', 'P0s_perc', 'LStay', 'Lshift', 'Wshift', 'Wstay']
    names_ = [f'{session}__' + i for i in names_]
    vars_ = [accuracy, streak, persistent0s, persistent0s_perc, lose_stay, lose_shift, win_shift, win_stay]

    for i in range(len(vars_)):
        res[animal][names_[i]] = vars_[i]


def get_column_in_list(which_col):
    col = df_lats_regs[df_lats_regs['Rat_ID'] == animal][which_col].values[0]
    col = [float(i) for i in col.strip('][').split(',')]
    return col


# TODO 1: Get strategy features for individual trials
df = pd.read_csv('Data/231213_individual_trials.csv')
res = {}
for animal in df['Rat_ID']:
    print(animal)
    res[animal] = {}

    for which_session in ['trials_toR', 'trials_onR', 'trials_postR']:
        # which_session = 'trials_postR'
        trials = df[df['Rat_ID'] == animal][which_session].values[0]
        trials = [float(i) for i in trials.strip('][').split(',')]
        # because of the 'O:' block, there were some Nan values in the individual trials
        # to calculate the different strategy metrics, next line removes them
        trials = [x for x in trials if str(x) != 'nan']
        get_strategy_metrics(trials, which_session)


# TODO 2: Get associations of latencies and trial accuracy
lats = pd.read_csv('Data/231213_extracted_latencies.csv')
df_lats_regs = pd.merge(df, lats, on='Rat_ID')
df_lats_regs = df_lats_regs.sort_values(by='Rat_ID').reset_index(drop=True)

for animal in df_lats_regs['Rat_ID']:
    for which_session in ['toR1', 'onR1', 'toR2', 'onR2', 'postR1', 'postR2']:
        x = get_column_in_list(f'lats_{which_session}')
        y = get_column_in_list(f'trials_{which_session[0:-1]}')

        xy = pd.DataFrame({'latencies': x, 'trials': y})
        xy = xy.dropna()

        x = np.array(xy['latencies']).reshape(-1, 1)
        y = np.array(xy['trials'])

        model = LogisticRegression(solver='liblinear', C=10.0, random_state=0)
        model.fit(x, y)
        coef = model.coef_[0][0]
        print('Model classes, Intercept, Score, Coef')
        print(model.classes_, model.intercept_, model.score(x, y), coef)
        res[animal][f'coef_{which_session}'] = coef

# convert dictionary with all the features to a df
res_df = pd.DataFrame.from_dict(res, orient='index')
# merge with other features
cols = ['Rat_ID', 'Treatment', 'n_reversals_long', 'n_trials_toR', 'n_trials_onR']
res_final = pd.merge(df[cols], res_df, left_on='Rat_ID', right_index=True)
# merge with latency medians
res_final = pd.merge(
    res_final,
    lats.set_index('Rat_ID').filter(like='med'),
    left_on='Rat_ID', right_index=True, how='outer')

res_final.to_csv('Data/231213_RES_all_strategies.csv', index=False)


# ________________________________
reversals = res_final[['Rat_ID', 'Treatment', 'n_reversals_long']].copy()
li = []
for i in reversals.n_reversals_long:
    i = [float(i) for i in i.strip('][').split(',')]
    li.append(i)
reversals['n_reversals'] = li
reversals = reversals.explode('n_reversals').reset_index(drop=True)
reversals.index.name = 'idx'
reversals = reversals.sort_values(by=['Rat_ID', 'idx'])
reversals['n_reversals'] = [int(i) for i in reversals['n_reversals']]

indices = []
for i in reversals.groupby('Rat_ID').size():
    li = list(range(i))
    indices.extend(li)
reversals['Days post LSD'] = indices

reversals = reversals[reversals['Days post LSD'] < 5]  # do not have data for all animal 5-7 days post LSD
reversals = reversals.drop(columns='n_reversals_long')
reversals = reversals.pivot(index=['Rat_ID', 'Treatment'], columns='Days post LSD', values='n_reversals')
reversals.columns = [f'{i} days post LSD' for i in reversals.columns]
reversals.to_csv('Data/231213_RES_longitudinal_n_reversals.csv')

# sns.boxplot(data=test, x="Days post LSD", y="n_reversals", hue="Treatment")
