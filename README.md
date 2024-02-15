**Terms**:
Session = the 1h long experiment while rat is in the box
Trial = the two presses, there are 100 trials per session (unless the session is time-constrained, rather than trial n-constrained)
Each session has multiple blocks, each block has multiple trials.

**Project** is organised into /Code /Data and /Graphs folders. All raw data as well as data outputs are saved in /Data.

The **/Code directory** contains following scripts:
1. _**summary_file_analysis.py**_ : input is the summary file with each animal as an excel sheet.
   Calculates accuracy up to/on/after reversal. Also extracts dates for files up to/on/after reversal.
   The output is saved as {date}_analysed_summary.csv

2. _**get_individual_trials.py**_ : takes in {date}_analysed_summary.csv data and based on the columns containing dates for raw experiments up to/on/post reversal.
   {date}_analysed_summary.csv must contain a column "presses_first_block" with the 'letter' which encodes first block of the experiment (in our data, this was different
   for the two cohorts).
   Output is saved as {date}_individual_trials.csv with the outcome of all trials as 0s and 1s.

3. _**latencies.py**_ : similarly takes in {date}_analysed_summary.csv and instead of extracting the inidividual 0s and 1s, extracts latencies per trial as well as median latencies.
   Output is saved as {date}_extracted_latencies.csv

4. _**get_trials_from_trials_latencies.py**_ : takes in the {date}_individual_trials.csv and {date}_extracted_latencies.csv and outputs analysed strategies.
   Saves as {date}_RES_all_strategies.csv. At the end, you can also choose to output the {date}_RES_longitudinal_n_reversals.csv which is a pivoted df of
   n_reversals per day post LSD

5. _**final_feature_selection.py**_ : elastic net logistic regression ft selection model which can be used on the {date}_RES_all_strategies.csv to understand features most
   predictive of treatment group assignment.
   
