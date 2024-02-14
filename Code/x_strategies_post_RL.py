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
    correct, incorrect = [], []
    for i in range(1, 3):
        li_corr = [float(i) for i in lines[return_index('R:') + i].split()[1:]]
        li_incorr = [float(i) for i in lines[return_index('S:') + i].split()[1:]]
        correct.extend(li_corr)
        incorrect.extend(li_incorr)

    totals_ = [x + y for x, y in zip(correct, incorrect) if x + y != 0]

    alphabet = string.ascii_uppercase
    idx = alphabet.index(letter)
    letters = alphabet[idx:idx+len(totals_)]

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
    for n, c in groupby(trials):
        num, count = n, sum(1 for i in c)
        li.append((num, count))
    streak = max([y for x, y in li if x == 1.0])
    streak0 = li[0][1]
    streak0_perc = li[0][1] / len(trials)

    pairs_li = []
    for i in range(len(trials)):
        pair = tuple(trials[i:i + 2])
        pairs_li.append(pair)

    lose_stay = pairs_li.count((0.0, 0.0)) / len(trials)
    lose_shift = pairs_li.count((0.0, 1.0)) / len(trials)
    win_shift = pairs_li.count((1.0, 0.0)) / len(trials)
    win_stay = pairs_li.count((1.0, 1.0)) / len(trials)

    names_ = ['streak', 'streak0', 'streak0_perc', 'lose_stay', 'lose_shift', 'win_shift', 'win_stay', 'trials']
    vars_ = [streak, streak0, streak0_perc, lose_stay, lose_shift, win_shift, win_stay, trials]

    for i in range(len(vars_)):
        res[animal][names_[i]] = vars_[i]


def run_utest(df, y):
    a = df[df['Treatment'] == 'Saline'][y].values
    b = df[df['Treatment'] == 'LSD'][y].values
    utest = mannwhitneyu(a, b)
    return utest


today = datetime.today().strftime('%y%m%d')
meta = pd.read_csv('Data/231129_meta_with_metrics.csv', index_col=0)
res = {}
li_animals = list(meta.index)
for animal in li_animals:
    # animal = 'LSDB04'
    print(animal)
    file_li = meta.loc[animal]['dates_3postRL']
    file_li = file_li.strip("']['").split("', '")

    date_file = file_li[0]
    path = f'Data/files/20{date_file}_*_Subject {animal}.txt'
    try:
        with open(glob.glob(path)[0]) as file:
            lines = file.readlines()  # lines is a list containing each line as a string
            lines = lines[19:]  # skip the head of file bc it screws up with index search later on

        first_b_letter = meta.loc[animal]['presses_first_block']
        totals = make_block_totals_di(letter=first_b_letter)

        trials = []
        if sum(totals.values()) == 100:
            for key in totals.keys():
                li = get_presses_from_block(key)
                trials.extend(li)

        res[animal] = {}
        get_strategy_metrics()

    except IndexError:
        print(f'oh well no sign of file: {path}')

res_df = pd.DataFrame.from_dict(res, orient='index')
res_w_strategy = pd.merge(meta['Treatment'], res_df, left_index=True, right_index=True)
res_w_strategy = res_w_strategy.sort_values(by='Treatment', ascending=False)
res_w_strategy.to_csv(f'Data/{today}_meta_w_strategies.csv')

run_utest(df=res_w_strategy, y='streak')


test = res_w_strategy[res_w_strategy['Treatment'] == 'Saline']
test = pd.DataFrame(test['b2_trials'].to_list(), columns=[str(i) for i in range(100)])
accuracies_saline = test.sum(axis=0)/8

test = res_w_strategy[res_w_strategy['Treatment'] == 'LSD']
test = pd.DataFrame(test['b2_trials'].to_list(), columns=[str(i) for i in range(100)])
accuracies_lsd = test.sum(axis=0)/8

plt.scatter(x=range(100), y=accuracies_saline, c='green')
plt.scatter(x=range(100), y=accuracies_lsd)
plt.ylim(-0.05, 1.05)


