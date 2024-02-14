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
    correct = [float(i) for i in lines[idx + 1].split()[1:]]  # first row after index
    correct.extend([float(i) for i in lines[idx + 2].split()[1:]])  # second row after index (sometimes the animals
    # went through more than 5 reversals and since there are 5 blocks (~reversals) per row, we need two rows to be sure.

    idx = return_index('S:')
    incorrect = [float(i) for i in lines[idx + 1].split()[1:]]
    incorrect.extend([float(i) for i in lines[idx + 2].split()[1:]])

    # this adds the correct and incorrect trials and removes blocks the animal did not get to
    totals_ = [x + y for x, y in zip(correct, incorrect) if x + y != 0]

    # this creates a dictionary of blocks and their associated letters
    # presses_first_block = letter of the first block
    first_letter = meta.loc[animal]['presses_first_block']
    alphabet = string.ascii_uppercase
    idx = alphabet.index(first_letter)
    letters = alphabet[idx:idx+len(totals_)]

    # zip it all together into a lovely jubbly dictionary
    di = dict(zip(letters, totals_))
    print(f'Block totals: {di}')
    return di


def get_trials_from_block(letter):
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


def read_session_file(date_file):
    path = f'Data/Lever press data/20{date_file}_*{animal}*'
    with open(glob.glob(path)[0]) as f:
        lines_ = f.readlines()  # lines is a list containing each line as a string
    lines_ = lines_[25:]  # skip the head of file bc it screws up with index search later on
    return lines_


def get_list_of_trials(which_blocks, trials):
    if which_blocks == 'B2':
        li = get_trials_from_block(list(totals.keys())[1])
        trials.extend(li)
    elif which_blocks == 'ALL':
        if sum(totals.values()) == 100:
            for key in totals.keys():
                # part of the text file 'O:' does not store data, hence we're adding nans
                if key == 'O':
                    li = [np.nan]*int(totals['O'])
                else:
                    li = get_trials_from_block(key)
                trials.extend(li)


today = datetime.today().strftime('%y%m%d')
meta = pd.read_csv('Data/231213_analysed_summary.csv', index_col=0)
res = {}
for animal in list(meta.index):
    # animal = 'LSDB19'
    print(animal)

    reversals_from_lsd = []
    # TODO Trials to reversal
    files_toR = meta.loc[animal]['dates_toR']
    files_toR = files_toR.strip("']['").split("', '")
    trials_toR = []
    for file in files_toR:
        try:
            lines = read_session_file(date_file=file)
            totals = get_block_totals()
            reversals_from_lsd.append(len(totals.keys()))
            get_list_of_trials(which_blocks='B2', trials=trials_toR)
        except IndexError:
            print(f'oh oh no sign of file: {file}')

    # TODO Trials on day of reversal
    trials_onR = []
    lines = read_session_file(date_file=files_toR[-1])
    totals = get_block_totals()
    get_list_of_trials(which_blocks='B2', trials=trials_onR)

    # TODO Trials post reversal
    files_postR = meta.loc[animal]['dates_3DaysPostR']
    files_postR = files_postR.strip("']['").split("', '")
    trials_postR = []
    for file in files_postR:
        try:
            lines = read_session_file(date_file=file)
            totals = get_block_totals()
            reversals_from_lsd.append(len(totals.keys()))
            get_list_of_trials(which_blocks='ALL', trials=trials_postR)
        except IndexError:
            print(f'oh well no sign of file: {file}')

    res[animal] = {
        'n_reversals_long': reversals_from_lsd,
        'trials_toR': trials_toR, 'trials_onR': trials_onR, 'trials_postR': trials_postR,
        'n_trials_toR': len(trials_toR), 'n_trials_onR': len(trials_onR), 'n_trials_postR': len(trials_postR)
    }

res_df = pd.DataFrame.from_dict(res, orient='index')
res_w_meta = pd.merge(meta['Treatment'], res_df, left_index=True, right_index=True)
res_w_meta = res_w_meta.sort_values(by='Treatment', ascending=False)
res_w_meta.to_csv(f'Data/{today}_individual_trials.csv')

