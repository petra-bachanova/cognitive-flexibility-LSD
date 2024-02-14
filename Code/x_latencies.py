from scipy.stats import mannwhitneyu
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from itertools import groupby
from datetime import datetime
import seaborn as sns
import numpy as np
import ast
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


def get_block_totals():
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

    return totals_


def get_latencies(letter):
    """
    Find index for a specific part of the text file. There are 100 trials => 100 latencies. To get these as a list,
    take rows with those numbers (6 elements per row, 100/6 => 21 rows), split each row to its elements,
    extend the list (lat_li).
    Lastly, because we only care about block 2 latencies, we take a subset of the 100 latencies =>
    lat_li[b1 total: b1+b2 totals].
    :param letter: Which part of the text file do you want to extract the latencies from?
    :return: latencies in block 2
    """
    # idx_ = return_index(f"{letter}:")
    idx_ = return_index(letter)
    latency_rows = math.ceil((100 + 1) / 5)
    lat_li = []
    # j==0 is the letter denoting block, j==1 is the first latency row and j==21 is the last, hence range(1, 22).
    for j in range(1, latency_rows):
        data_row = [float(i_) for i_ in lines[idx_ + j].split()[1:]]
        lat_li += data_row

    b1_total = int(totals[0])
    b1_b2_sum = int(totals[0] + totals[1])
    lat_li = lat_li[b1_total: b1_b2_sum]

    return lat_li


def plot_lmplot():
    sns.lmplot(data=test_scl, x='Trial_n', y='value', hue='variable', palette=['#E55604', '#47A992'],
               legend=False, height=5, aspect=1.5)
    sns.lineplot(data=test_scl, x='Trial_n', y='Roll_accuracy')
    lgd = plt.legend(frameon=False, bbox_to_anchor=(1.3, 0.5))
    plt.title(f'{animal} Latencies vs rolling accuracy (FW=5)')
    plt.tight_layout()
    plt.savefig(f'Graphs/Accuracy vs Latencies/{animal}.png', bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=300)
    plt.close()


today = datetime.today().strftime('%y%m%d')
meta = pd.read_csv('Data/231129_meta_with_metrics.csv', index_col=0)
df = pd.read_csv('Data/231129_meta_w_strategies.csv', index_col=0)
raw_df = pd.DataFrame()
corr_di = {}
li_animals = list(meta.index)
for animal in li_animals[8:]:
    # animal = 'LSDB12'
    file_li = meta.loc[animal]['dates_to_RL']
    file_li = file_li.strip("']['").split("', '")

    laten1 = []
    laten2 = []
    for date_file in file_li:
        # date_file = file_li[0]
        path = f'Data/Level press data/20{date_file}_*_Subject {animal}.txt'
        with open(glob.glob(path)[0]) as file:
            lines = file.readlines()  # lines is a list containing each line as a string

        totals = get_block_totals()
        laten1.extend(get_latencies('V:'))
        laten2.extend(get_latencies('W:'))

    # Calculate rolling accuracy based on a floating window of 5 trials.
    li = df.loc[animal]['b2_trials']
    li = ast.literal_eval(li)
    accuracies = []
    for i in range(len(li)):
        sum_ = np.array(li[i:i+5]).sum()
        length = len(li[i:i+5])
        accuracies.append(sum_ / length)

    # Last 4 values can be removed (bc floating window would include 4, 3, 2, and 1 trials for the last 4 calculations)
    accuracies = accuracies[0:len(accuracies) - 4]
    laten1 = laten1[0:len(laten1) - 4]
    laten2 = laten2[0:len(laten2) - 4]

    per = pd.DataFrame(
        {'Rat_ID': animal, 'Trial_n': range(len(accuracies)), 'Roll_accuracy': accuracies, 'Lat1': laten1, 'Lat2': laten2})
    raw_df = pd.concat([raw_df, per])

    test = per[(per['Lat1'] < 200) & (per['Lat2'] < 200)]
    test = test.set_index(['Rat_ID', 'Trial_n'])
    scaler = MinMaxScaler()
    test_scl = scaler.fit_transform(test)
    test_scl = pd.DataFrame(test_scl, columns=test.columns, index=test.index).reset_index()
    test_scl = test_scl.melt(id_vars=['Rat_ID', 'Trial_n', 'Roll_accuracy'])

    plot_lmplot()

    cor1 = np.corrcoef(per['Roll_accuracy'], per['Lat1'])[0][1]
    cor2 = np.corrcoef(per['Roll_accuracy'], per['Lat2'])[0][1]
    cor3 = np.corrcoef(per['Trial_n'], per['Lat1'])[0][1]
    cor4 = np.corrcoef(per['Trial_n'], per['Lat2'])[0][1]
    cor5 = np.corrcoef(per['Lat1'], per['Lat2'])[0][1]

    corr_di[animal] = {
        'RollAcc_Lat1': cor1, 'RollAcc_Lat2': cor2, 'Trialn_Lat1': cor3, 'Trialn_Lat2': cor4, 'Lat1_Lat2': cor5}

corr_df = pd.DataFrame.from_dict(corr_di, orient='index')
cols = ['Treatment', 'trials', 'accuracy', 'accuracy_5postRL', 'accuracy_10postRL', 'accuracy_20postRL']
corr_df = pd.merge(meta[cols], corr_df, left_index=True, right_index=True)

sns.heatmap(corr_df.corr(), annot=True)
plt.tight_layout()
