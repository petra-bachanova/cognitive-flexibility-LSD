from datetime import datetime
import pandas as pd
import warnings
import re

warnings.filterwarnings("ignore", category=FutureWarning)


def format_animal_id():
    if len(str(i)) == 1:
        animal_id = f'LSDB{str(i).zfill(2)}'
    else:
        animal_id = f'LSDB{i}'
    return animal_id


def get_dates_and_metrics_toR(data, idx_rl, ratid):
    # subset rows up to reversal & sums trials across Correct and Incorrect Blocks on different days
    df_up_to_reversal = data.iloc[0:idx_rl+1, :]
    sums = df_up_to_reversal.sum()

    trials_toR = sums['B2Correct'] + sums['B2Incorrect']
    accuracy = round(sums['B2Correct'] / trials_toR, 3)
    dates_toR = list(df_up_to_reversal['Date'].dt.strftime('%y-%m-%d'))

    df_3DaysPostR = data.iloc[idx_rl+1: idx_rl+4, :]
    dates_postR = list(df_3DaysPostR['Date'].dt.strftime('%y-%m-%d'))
    di[ratid] = {'dates_toR': dates_toR, 'dates_3DaysPostR': dates_postR,
                 'trials_toR': trials_toR, 'accuracy_toR': accuracy}


def get_metrics_post_R(data, idx_rl, ratid, n_days):
    # Melt dataframe from (and including) reversal date so that the columns are: date, block ID and trial value
    data = data.iloc[idx_rl:, :]
    melt = data.melt(id_vars='Date').copy()
    # Sort by date and block ID
    melt = melt.sort_values(by=['Date', 'variable']).reset_index(drop=True)

    # We want to exclude 'unused' blocks = blocks that the rat did not progress into in a day
    # Sum incorrect & correct trials per day per block If this == 0 --> unused block.
    melt['block_date'] = [re.sub('^(.[0-9]).*?$', '\\1', j) for j in melt['variable']]
    melt['block_date'] = melt['block_date'] + [f' {str(k.strftime("%m%d"))}' for k in melt['Date']]
    unused_blocks = melt.groupby('block_date').sum()
    unused_blocks = unused_blocks[unused_blocks['value'] == 0].index
    # remove such blocks from the melted dataframe
    # now we can just take n blocks post reversal to do stats on
    # e.g., 5 blocks post reversal --> 10 rows after reversal row (5 correct & 5 incorrect)
    melt = melt[~melt['block_date'].isin(unused_blocks)]

    # get date of the day after reversal
    if n_days == 0:
        dates = melt['Date'].unique()[0:1]
    else:
        dates = melt['Date'].unique()[1:1+n_days]
    melt = melt.loc[melt['Date'].isin(dates)]
    melt['variable'] = [re.sub('^.{2}', '', k) for k in melt['variable']]
    accuracy_postR = melt.groupby('variable')['value'].sum()
    di[ratid][f'accuracy_{n_days}DaysPostR'] = accuracy_postR['Correct'] / accuracy_postR.sum()


def make_metrics_dict(path_, ratid):
    # path_ = 'Data/LSDB 01-08'
    # ratid = 'LSDB04'
    df = pd.read_excel(f'{path_}.xlsx', sheet_name=ratid)
    df = df.dropna(subset='ProgramC7').reset_index(drop=True)
    cols = ['ProgramC7', 'B1Total', 'B2Total', 'B3Total', 'B4Total', 'B5Total', 'B6Total ', 'B7Total', 'B8Total',
            'ReversalCount', 'BlockAvg', 'BlockAvgDev', 'DayAvgDev', 'Notes', 'SumCorrect', 'SumIncorrect']
    df = df.drop(columns=cols)
    try:
        # get row (date) when the animal reversed
        idx_reversal = df[df['B3Incorrect'] > 0].index[0]
        # get metrics pre and post reversal
        get_dates_and_metrics_toR(data=df, idx_rl=idx_reversal, ratid=ratid)
        # get_metrics_post_R(data=df, idx_rl=idx_reversal, ratid=ratid, n_days=0)
        get_metrics_post_R(data=df, idx_rl=idx_reversal, ratid=ratid, n_days=3)

    except IndexError:
        print(f'Animal {ratid} has not reversed yet!')
        di[ratid] = {'trials': 'animal not reversed', 'accuracy': '', 'date_files': ''}


today = datetime.today().strftime('%y%m%d')
di = {}
for i in range(1, 21):
    animal = format_animal_id()
    if i < 9:
        file = 'Data/LSDB 01-08'
    else:
        file = 'Data/LSDB 09-20'
    make_metrics_dict(path_=file, ratid=animal)

res = pd.DataFrame.from_dict(di, orient='index')
metadata = pd.read_csv('Data/rat_metadata.csv')
res = pd.merge(metadata, res, left_on='Rat_ID', right_index=True)
res.to_csv(f'Data/{today}_analysed_summary.csv', index=False)

