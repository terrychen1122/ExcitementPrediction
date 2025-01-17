#!/usr/bin/env python
# coding:utf-8

"Extract features of projects' history statistics"

__author__ = "Xingyu Zhou"

import os
import sys
import pandas as pd 
import numpy as np
sys.path.append('..')
import import_data

def _cap(series, low_bound, high_bound):
    """
    Cap each elements of a series with low_bound and high_bound
    """
    s = series.copy()
    s[s < low_bound] = low_bound
    s[s > high_bound] = high_bound
    return s

def _quantify(df, list_of_columns):
    """
    Transform the categorical data to numeric data (f -> 0, t -> 1):
        Add new column x_cnt for each column x
    """
    list_of_new_cols = []
    for col in list_of_columns:
        new_col = col + '_cnt'
        df[new_col] = 0
        df.loc[df[col]=='t', new_col] = 1
        # add to new column list
        list_of_new_cols.append(new_col)
    return list_of_new_cols

def _acc_cnt(df, list_of_vars, list_of_cnts, has_gapdays=True):
    """
    Accumulative Count/Sum. There are several kinds of output:
        1. cumulative count/sum
        2. cumulative rate = cumulative count (1s) / total number (0s + 1s) so far
        3. cumulative cred rate (adjusted rate)
        4. cumulative cred capped rate (capped by low/upper bound)

    list_of_vars: list of variables (same value considerred accumulation on time)
    list_of_cnts: list of features to count/sum (for binary value 0/1, count; for continuous value, sum)
    has_gapdays: contains the gap days (the gap days between two projects for a var (e.g. a teacher creating project))
    
    The output is the combinations of list_of_vars * list_of_cnts and gapdays.
    """
    list_of_new_cols = []
    for var in list_of_vars:
        df_sorted = df.sort([var, 'date_posted'])
        df_sorted['date'] = pd.to_datetime(df_sorted['date_posted'], '%Y-%m-%d')
        df_sorted['one'] = 1
        df_grouped = df_sorted.groupby(var)

        # cumulative count for each var
        acc_cnt_col = var + '_cumcnt'
        df_sorted[acc_cnt_col] = df_grouped['one'].cumsum() - df_sorted['one']
        
        # add new column name to list
        list_of_new_cols.append(acc_cnt_col)
        # add new column to df
        df[acc_cnt_col] = df_sorted[acc_cnt_col].sort_index()

        means = {}
        for cnt_col in list_of_cnts:
            # column name
            cumsum_col = var + '_' + cnt_col.replace('cnt', 'cumcnt')
            rate_col = var + '_' + cnt_col.replace('cnt', 'cumrate')
            rate_cred_col = rate_col.replace('cumrate', 'cumcredrate')
            rate_cred_cap_col = rate_col.replace('cumrate', 'cumcredrate_cap')

            # cumulative sum/count
            df_prev_cumsum = df_grouped[cnt_col].cumsum() - df_sorted[cnt_col]
            # cumulative rate
            df_prev_rate = df_prev_cumsum / df_sorted[acc_cnt_col]
            # fix divide-by-0
            df_prev_rate[np.isinf(df_prev_rate)] = 0

            # dict stores the mean for every column (save time)
            if cnt_col not in means:
                means[cnt_col] = df_sorted[cnt_col].mean()
            # cumulative cred capped rate
            df_prev_cred_rate = (df_prev_cumsum + 10 * means[cnt_col]) / (df_sorted[acc_cnt_col] + 10)
            df_prev_cred_rate_cap = _cap(df_prev_cred_rate, 0, 0.25)
            
            # add new columns name to list
            list_of_new_cols.append(cumsum_col)
            list_of_new_cols.append(rate_col)
            list_of_new_cols.append(rate_cred_col)
            list_of_new_cols.append(rate_cred_cap_col)
            # add new columns to df
            df[cumsum_col] = df_prev_cumsum.sort_index()
            df[rate_col] = df_prev_rate.sort_index()
            df[rate_cred_col] = df_prev_cred_rate.sort_index()
            df[rate_cred_cap_col] = df_prev_cred_rate_cap.sort_index()

        # gapdays
        if has_gapdays:
            gapdays_col = var + '_gapdays'
            gapdays = df_grouped['date'].diff() / pd.offsets.Day(1)
            gapdays.fillna(9999, inplace=True)

            # add new columns name to list
            list_of_new_cols.append(gapdays_col)
            # add new column to df
            df[gapdays_col] = gapdays
            
    return list_of_new_cols

def _select(in_file, out_file, list_of_columns):
    print 'input from: ' + in_file + " ..."
    df = pd.read_csv(in_file)
    print 'output to: ' + out_file + " ..."
    return df.to_csv(out_file, columns=list_of_columns, index=False)

def _list_of_columns():
    list_of_columns = ['projectid', 'group', 'y', 'teacher_acctid_gapdays', 'schoolid_gapdays', 
    'teacher_acctid_cumcnt', 'schoolid_cumcnt', 'teacher_acctid_is_exciting_cumcredrate', 
    'schoolid_is_exciting_cumcredrate_cap', 'school_district_is_exciting_cumrate', 
    'school_county_is_exciting_cumrate', 'schoolid_at_least_1_teacher_referred_donor_cumrate',
    'teacher_acctid_at_least_1_teacher_referred_donor_cumrate', 'schoolid_fully_funded_cumrate', 
    'teacher_acctid_fully_funded_cumrate', 'school_district_fully_funded_cumrate', 
    'schoolid_at_least_1_green_donation_cumrate', 'schoolid_great_chat_cumrate', 
    'teacher_acctid_great_chat_cumrate', 'schoolid_is_teacher_acct_cumrate', 
    'teacher_acctid_is_teacher_acct_cumrate', 'schoolid_donation_total_cumcnt', 
    'teacher_acctid_donation_total_cumcnt']
    return list_of_columns

if __name__ == '__main__':
    # if path is not specified, default is 'Data'
    path = sys.argv[1] if len(sys.argv) > 1 else '../Data'
    # processing the whole file or refinement
    bnew = (sys.argv[2] == 'new') if len(sys.argv) > 2 else False
    
    whole_filepath = os.path.join('../Features_csv', 'history_stat.csv')
    refine_filepath = os.path.join('../Features_csv', 'refined_history_stat.csv')

    if not bnew and os.path.isfile(whole_filepath):
        print "reuse existing whole stat..."
        _select(whole_filepath, refine_filepath, _list_of_columns())
        sys.exit()

    # list_to_write: list of columns that will write to files
    list_to_write = ['projectid', 'group', 'y']

    projects_df = import_data.get_projects_df(path)
    # cut off the old data
    projects_df = projects_df[projects_df['group']!='none']

    outcomes_df = import_data.get_outcomes_df(path)
    # left join projects_df and outcomes_df
    df = pd.merge(projects_df, outcomes_df, how = 'left', on = 'projectid')
    list_of_categorical = ['is_exciting', 'at_least_1_teacher_referred_donor', 'fully_funded',
        'at_least_1_green_donation', 'great_chat', 'three_or_more_non_teacher_referred_donors',
        'one_non_teacher_referred_donor_giving_100_plus', 'donation_from_thoughtful_donor']
    # quantify categorical data
    list_of_cnts = _quantify(df, list_of_categorical)
    list_of_vars = ['teacher_acctid', 'schoolid', 'school_district', 'school_county']
    list_to_write += list_of_vars
    # counting for each vars
    list_of_new_cols = _acc_cnt(df, list_of_vars, list_of_cnts)
    # add new columns to write
    list_to_write += list_of_new_cols + list_of_vars

    # donations
    donations_df = import_data.get_donations_df(path)
    # projects + donations
    df2 = pd.merge(projects_df, donations_df, how='left', on='projectid')
    # quantify categorical data
    df2['is_teacher_acct_cnt'] = 0
    df2.loc[df2['is_teacher_acct']=='t', 'is_teacher_acct_cnt'] = 1
    # set 0 for null data
    df2['donation_total_cnt'] = df2["donation_total"]
    df2.loc[pd.isnull(df2['donation_total']), 'donation_total_cnt'] = 0

    # groupby + sum
    list_of_unicomb = ["projectid","date_posted","teacher_acctid","schoolid","school_district","school_city","school_zip"]
    list_of_cnts = ['is_teacher_acct_cnt', 'donation_total_cnt']
    df2 = df2.groupby(list_of_unicomb)[list_of_cnts].sum()
    df2.reset_index(inplace=True)
    
    list_of_vars = ['teacher_acctid', 'schoolid']
    # counting for each vars
    list_of_new_cols = _acc_cnt(df2, list_of_vars, list_of_cnts)
    list_to_write += list_of_new_cols

    # write to csv
    print 'write the whole to file: ' + whole_filepath + ' ...';
    # merge + eliminate null
    df = pd.merge(df, df2, how='left', on='projectid', suffixes=('', '_2')).fillna(0)
    df[list_to_write].to_csv(whole_filepath, index=False)

    # refinement
    print 'write the refined to file: ' + refine_filepath + ' ...';
    df[_list_of_columns()].to_csv(refine_filepath, index=False)
    



