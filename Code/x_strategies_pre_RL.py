from scipy.stats import mannwhitneyu
import matplotlib.pyplot as plt
from itertools import groupby
from datetime import datetime
import seaborn as sns
import pandas as pd
import math
import glob
import string


def return_index(substring):
    """
    Finds the row index of matching substring.
    :param substring: Key from experiment file (R:, S:, K: etc.) Needs to contain double colon.
    :return: index
    """
    for i, s in enumerate(lines):
        if substring in s:
            return i


def make_block_totals_di(letter):
    """
    How many correct and incorrect trials does the rat go through?
    :return: Takes numbers from R and S block, returns their sums per block.
    """
    # how many trials per block 1/2/3 --> get numbers from R and S then sum
    idx = return_index('R:')
    correct = [float(i) for i in lines[idx + 1].split()[1:]]
    idx = return_index('S:')
    incorrect = [float(i) for i in lines[idx + 1].split()[1:]]
    totals_ = [x + y for x, y in zip(correct, incorrect)]

    alphabet = string.ascii_uppercase
    idx = alphabet.index(letter)
    letters = alphabet[idx:idx+5]

    di = dict(zip(letters, totals_))
    return di


def get_presses_from_block(letter):
    """
    Find index for a specific block. Using the totals, calculates the number of rows
    of 0s and 1s it needs. Those rows are strings that are merged to a list,
    leaving out first element (0s and 1s begin at position 1 not 0).
    :param letter: Which block do you want to extract the presses from?
    :return: presses per block
    """
    idx_ = return_index(f"{letter}:")
    n_data_rows = math.ceil((totals[letter] + 1) / 5)

    presses_ = []
    for i in range(1, n_data_rows + 1):
        data_row = [float(i) for i in lines[idx_ + i].split()[1:]]
        presses_ += data_row
    presses_ = presses_[1:int(totals[letter] + 1)]

    return presses_


def get_strategy_metrics():
    li = []
    for n, c in groupby(b2_trials):
        num, count = n, sum(1 for i in c)
        li.append((num, count))
    streak = max([y for x, y in li if x == 1.0])
    persistent0s = li[0][1]
    persistent0s_perc = li[0][1] / len(b2_trials)

    pairs_li = []
    for i in range(len(b2_trials)):
        pair = tuple(b2_trials[i:i + 2])
        pairs_li.append(pair)

    lose_stay = pairs_li.count((0.0, 0.0)) / len(b2_trials)
    lose_shift = pairs_li.count((0.0, 1.0)) / len(b2_trials)
    win_shift = pairs_li.count((1.0, 0.0)) / len(b2_trials)
    win_stay = pairs_li.count((1.0, 1.0)) / len(b2_trials)

    names_ = ['streak', 'persistent0s', 'persistent0s_perc', 'lose_stay', 'lose_shift', 'win_shift', 'win_stay', 'b2_trials']
    vars_ = [streak, persistent0s, persistent0s_perc, lose_stay, lose_shift, win_shift, win_stay, b2_trials]

    for i in range(len(vars_)):
        res[animal][names_[i]] = vars_[i]


def run_utest(df, y):
    a = df[df['treatment'] == 'Saline'][y].values
    b = df[df['treatment'] == 'LSD'][y].values
    utest = mannwhitneyu(a, b)
    return utest


today = datetime.today().strftime('%y%m%d')
meta = pd.read_csv('Data/231129_meta_with_metrics.csv', index_col=0)
res = {}
li_animals = list(meta.index)
for animal in li_animals:
    # animal = 'LSDB19'
    file_li = meta.loc[animal]['dates_to_RL']
    file_li = file_li.strip("']['").split("', '")

    b2_trials = []
    for date_file in file_li:
        # date_file = file_li[-1]
        path = f'Data/Level press data/20{date_file}_*_Subject {animal}.txt'
        with open(glob.glob(path)[0]) as file:
            lines = file.readlines()  # lines is a list containing each line as a string

        first_b_letter = meta.loc[animal]['presses_first_block']
        totals = make_block_totals_di(letter=first_b_letter)

        b2_letter = list(totals.keys())[1]
        presses = get_presses_from_block(b2_letter)
        b2_trials.extend(presses)

    res[animal] = {}
    get_strategy_metrics()


res_df = pd.DataFrame.from_dict(res, orient='index')
res_w_strategy = pd.merge(meta, res_df, left_index=True, right_index=True)
res_w_strategy = res_w_strategy.sort_values(by='Treatment', ascending=False)
res_w_strategy.to_csv(f'Data/{today}_meta_w_strategies.csv')


# ..............
run_utest(df=res_w_strategy, y='persistent0s')

strategies = res_w_strategy.drop(columns=['trials', 'accuracy', 'date_files', 'persistent0s', 'streak'])
strategies = strategies.melt(id_vars=['cohort', 'treatment'])

kws = {'data': strategies, 'y': 'value', 'x': 'variable', 'hue': 'treatment'}
plt.figure(figsize=(4.5, 5))
g = sns.boxplot(**kws, fliersize=0, saturation=1)
sns.stripplot(**kws, edgecolor='white', linewidth=0.7, s=6, dodge=True)
plt.title('Proportion of strategies')
plt.tight_layout()
