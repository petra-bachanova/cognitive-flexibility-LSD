from datetime import datetime
import pandas as pd
import numpy as np
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

    totals_ = [x + y for x, y in zip(correct, incorrect) if x + y != 0]

    first_letter = meta.loc[animal]['presses_first_block']
    alphabet = string.ascii_uppercase
    idx = alphabet.index(first_letter)
    letters = alphabet[idx:idx+len(totals_)]

    di = dict(zip(letters, totals_))
    print(f'Block totals: {di}')
    return di


def read_session_file(date_file):
    path = f'Data/Lever press data/20{date_file}_*{animal}*'
    with open(glob.glob(path)[0]) as f:
        lines_ = f.readlines()  # lines is a list containing each line as a string
    lines_ = lines_[25:]  # skip the head of file bc it screws up with index search later on
    return lines_


def get_latencies_from_session(letter):
    """
    Find index for a specific part of the text file. There are 100 trials => 100 latencies. To get these as a list,
    take rows with those numbers (6 elements per row, 100/6 => 21 rows), split each row to its elements,
    extend the list (lat_li).
    Lastly, because we only care about block 2 latencies, we take a subset of the 100 latencies =>
    lat_li[b1 total: b1+b2 totals].
    :param letter: Which part of the text file do you want to extract the latencies from?
    :return: latencies in block 2
    """
    idx_ = return_index(letter)
    latency_rows = math.ceil((100 + 1) / 5)  # 5 latencies per line, 100 latencies in total
    latencies_ = []
    # j==0 is the letter denoting block, j==1 is the first latency row and j==21 (100 is the last, hence range(1, 22).
    for j in range(1, latency_rows):
        data_row = [float(i_) for i_ in lines[idx_ + j].split()[1:]]
        latencies_ += data_row

    return latencies_


def get_list_of_trials(which_blocks, lats_all, letter):
    if which_blocks == 'B2':
        lats = get_latencies_from_session(letter=letter)
        # only latencies from B2
        b1 = list(totals.values())[0]
        b1_b2_sum = b1 + list(totals.values())[1]
        lats = lats[int(b1): int(b1_b2_sum)]
    elif which_blocks == 'ALL':
        lats = get_latencies_from_session(letter=letter)
    else:
        lats = []
        print('huh?')
    lats_all.extend(lats)


today = datetime.today().strftime('%y%m%d')
meta = pd.read_csv('Data/231212_analysed_summary.csv', index_col=0)
res = {}
for animal in list(meta.index)[8:]:
    # animal = 'LSDB19'
    print(animal)

    # TODO Trials to reversal
    files_toR = meta.loc[animal]['dates_toR']
    files_toR = files_toR.strip("']['").split("', '")
    lats_toR1 = []
    lats_toR2 = []
    for file in files_toR:
        # file = files_toR[0]
        lines = read_session_file(date_file=file)
        totals = get_block_totals()
        get_list_of_trials(which_blocks='B2', lats_all=lats_toR1, letter='V')
        get_list_of_trials(which_blocks='B2', lats_all=lats_toR2, letter='W')

    # TODO Trials on day of reversal
    lats_onR1 = []
    lats_onR2 = []
    lines = read_session_file(date_file=files_toR[-1])
    totals = get_block_totals()
    get_list_of_trials(which_blocks='B2', lats_all=lats_onR1, letter='V')
    get_list_of_trials(which_blocks='B2', lats_all=lats_onR2, letter='W')

    # TODO Trials post reversal
    files_postR = meta.loc[animal]['dates_3DaysPostR']
    files_postR = files_postR.strip("']['").split("', '")
    lats_postR1 = []
    lats_postR2 = []
    for file in files_postR:
        try:
            lines = read_session_file(date_file=file)
            totals = get_block_totals()
            get_list_of_trials(which_blocks='ALL', lats_all=lats_postR1, letter='V')
            get_list_of_trials(which_blocks='ALL', lats_all=lats_postR2, letter='W')
        except IndexError:
            print(f'oh well no sign of file: {file}')

    res[animal] = {
        'lats_toR1': lats_toR1, 'lats_toR2': lats_toR2,
        'lats_onR1': lats_onR1, 'lats_onR2': lats_onR2,
        'lats_postR1': lats_postR1, 'lats_postR2': lats_postR2,
        'lats_toR1_med': np.median(lats_toR1), 'lats_toR2_med': np.median(lats_toR2),
        'lats_onR1_med': np.median(lats_onR1), 'lats_onR2_med': np.median(lats_onR2),
        'lats_postR1_med': np.median(lats_postR1), 'lats_postR2_med': np.median(lats_postR2),

        'n_lats_toR1': len(lats_toR1), 'n_lats_toR2': len(lats_toR2),
        'n_lats_onR1': len(lats_onR1), 'n_lats_onR2': len(lats_onR2),
        'n_lats_postR1': len(lats_postR1), 'n_lats_postR2': len(lats_postR2)
    }

res_df = pd.DataFrame.from_dict(res, orient='index')
cols = ['n_lats_toR1', 'n_lats_toR2', 'n_lats_onR1', 'n_lats_onR2', 'n_lats_postR1', 'n_lats_postR2']
res_df = pd.merge(meta['Treatment'], res_df.drop(columns=cols), left_index=True, right_index=True)
res_df = res_df.sort_values(by='Treatment', ascending=False)
res_df = res_df.reset_index()
res_df = res_df.rename(columns={'index': 'Rat_ID'})
res_df.to_csv(f'Data/{today}_extracted_latencies.csv', index=False)

