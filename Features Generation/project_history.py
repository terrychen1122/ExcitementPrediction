#!/usr/bin/env python
# coding:utf-8

"Extract features of projects' history statistics"

__author__ = "Xingyu Zhou (xingyuhit@gmail.com)"

import os
import sys
import pandas as pd 
import numpy as np
sys.path.append('..')
import import_data

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
    list_of_new_cols = []
    for var in list_of_vars:
        df_sorted = df.sort([var, 'date_posted'])
        df_sorted['date'] = pd.to_datetime(df_sorted['date_posted'], '%Y-%m-%d')
        df_sorted['one'] = 1
        df_grouped = df_sorted.groupby(var)

        # cumulative count for each var
        acc_cnt_col = var + '_cumcnt'
        df_sorted[acc_cnt_col] = df_grouped['one'].cumsum() - df_sorted['one']
        
        # add new column
        list_of_new_cols.append(acc_cnt_col)
        df[acc_cnt_col] = df_sorted[acc_cnt_col].sort_index()

        for cnt_col in list_of_cnts:
            cumsum_col = var + '_' + cnt_col.replace('cnt', 'cumcnt')
            rate_col = var + '_' + cnt_col.replace('cnt', 'cumrate')
            df_prev_cumsum = df_grouped[cnt_col].cumsum() - df_sorted[cnt_col]
            df_prev_rate = df_prev_cumsum / df_sorted[acc_cnt_col]
            df_prev_rate[np.isinf(df_prev_rate)] = 0
            
            # add new columns
            list_of_new_cols.append(cumsum_col)
            list_of_new_cols.append(rate_col)
            df[cumsum_col] = df_prev_cumsum.sort_index()
            df[rate_col] = df_prev_rate.sort_index()

        if has_gapdays:
            gapdays_col = var + '_gapdays'
            gapdays = df_grouped['date'].diff()/ pd.offsets.Day(1)
            gapdays.fillna(9999, inplace=True)

            # add new column
            list_of_new_cols.append(gapdays_col)
            df[gapdays_col] = gapdays
            
    return list_of_new_cols

if __name__ == '__main__':
    # if path is not specified, default is 'Data'
    path = sys.argv[1] if len(sys.argv) > 1 else '../Data'

    list_to_write = ['projectid', 'group', 'y']
    projects_df = import_data.get_projects_df(path)
    # outcomes
    outcomes_df = import_data.get_outcomes_df(path)
    list_of_categorical = ['is_exciting', 'at_least_1_teacher_referred_donor', 'fully_funded',
        'at_least_1_green_donation', 'great_chat', 'three_or_more_non_teacher_referred_donors',
        'one_non_teacher_referred_donor_giving_100_plus', 'donation_from_thoughtful_donor']
    # quantify categorical data
    list_of_cnts = _quantify(outcomes_df, list_of_categorical)

    # outcomes + projects
    df = pd.merge(projects_df, outcomes_df, how = 'left', on = 'projectid')
    list_of_vars = ['teacher_acctid', 'schoolid', 'school_district', 'school_county']
    # counting for each vars
    list_of_new_cols = _acc_cnt(df, list_of_vars, list_of_cnts)
    list_to_write += list_of_new_cols

    # donations
    donations_df = import_data.get_donations_df(path)
    # quantify categorical data
    donations_df['is_teacher_acct_cnt'] = 0
    donations_df.loc[donations_df['is_teacher_acct']=='t', 'is_teacher_acct_cnt'] = 1
    # set 0 for null data
    donations_df['donation_total_cnt'] = donations_df["donation_total"]
    donations_df.loc[pd.isnull(donations_df['donation_total']), 'donation_total_cnt'] = 0

    # projects + donations
    df2 = pd.merge(projects_df, donations_df, how='left', on='projectid')

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
    df = pd.merge(df, df2)
    df[list_to_write].to_csv(os.path.join('Features_csv', 'project_history.csv'), index=False)






