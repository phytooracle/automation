#!/usr/bin/env python3
"""
Author : Emmanuel Gonzalez
Date   : 2020-08-23
**Notes: This code was developed by collaborators at the USDA
        (see references). It was modified to allow for it's
        integration in a scalable data processing pipeline.**
References: Jacob Long, Matthew Herritt, Alison Thompson
Purpose: PS2 fluorescence aggregation
"""

import argparse
import os
import sys
import glob
import json
import pandas as pd


# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='PS2 fluorescence aggregation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('csv',
                        metavar='csv',
                        type=str,
                        help='A positional argument')

    parser.add_argument('-od',
                        '--outdir',
                        help='Output dir',
                        metavar='outdir',
                        type=str,
                        default='fluorescence_aggregation_out')

    parser.add_argument('-of',
                        '--outfile',
                        help='Output file name',
                        metavar='outfile',
                        type=str,
                        default='fluorescence_aggregation')

    parser.add_argument('-m',
                        '--multithresh',
                        help='Multithreshold json file',
                        metavar='multithresh',
                        type=str,
                        required=True,
                        default=None)

    return parser.parse_args()


# --------------------------------------------------


def create_multithresh(df):
    start_pattern = [0,0,0,0,0,0,0.9,1,1,1,0,0,0.1,0.8]
    print('starting build')

    pattern = [1,0,0,0.1,0.8]
    while len(start_pattern) != len(df):
        for i in pattern:
            if len(start_pattern) == len(df):
                break
            
            start_pattern.append(i)
           

    print('finish_build')
    return start_pattern



def generate_aggregate(csv_list, thresh_path):
    to_concat = []

    for csv in csv_list:

        with open(thresh_path) as f:
            multithresh_list = json.loads(f.read())

        df = pd.read_csv(csv).drop('Unnamed: 0', axis=1)
        sorted_df = df.sort_values(['Label', 'Max'])

        multithresh_list = create_multithresh(sorted_df)

        print('thrsh:', len(multithresh_list), 'df:', len(df))

        try:
            #sorted_df = df[['folder_name', 'Label', 'x', 'y', 'Area', 'Mean', 'Min', 'Max']]
            sorted_df['MultiThr'] = multithresh_list

        except ValueError as e:
            # the length of multithresh list does not match the amound of images taken.
            # skip this
            print(csv, e)
            #continue
        to_concat.append(sorted_df)

    if to_concat:
        concat_df = pd.concat(to_concat)

    concat_df['AreaXMeanXMultiThr'] = concat_df['Area'] * concat_df['Mean'] * concat_df['MultiThr']

    concat_df['AreaXMultiThr'] = concat_df['Area'] * concat_df['MultiThr']

    for label in set(concat_df['Label']):
            #print(label, end='\r')

            # creating a list of true/false to tell
            # which records to select from concat_df
            chosen_records = concat_df['Label'] == label

            # Sum(Area x Mean x Multithresh)
            concat_df.loc[chosen_records, 'Sum AreaXMeanXMultiThr'] = concat_df.loc[chosen_records, 'AreaXMeanXMultiThr'].sum()

            # Sum(Area x Multithresh)
            concat_df.loc[chosen_records, 'Sum AreaXMultiThr'] = concat_df.loc[chosen_records, 'AreaXMultiThr'].sum()

    concat_df['Sum_AreaXMeanXMultiThr_over_Sum_AreaXMultiThr'] = concat_df['Sum AreaXMeanXMultiThr'] / concat_df['Sum AreaXMultiThr']

    for label in set(concat_df['Label']):

        # the first value from the second picture
        try:
            F0 = list(concat_df.loc[concat_df['Label'] == label, 'Sum_AreaXMeanXMultiThr_over_Sum_AreaXMultiThr'])
            #print(F0)
        except IndexError as e:
            # an IndexError will be thrown if no records were found for a given plot.
            # this could happen if the plot was not listed in the Plot boundaries.xlsx
            # and the previous step has been run
            print(f'No data found in plot {label}.', e)
            continue

        # extracting image number from the label string and converting it to an int for filtering
        #concat_df['img_num'] = int(str(concat_df['Label']).split('_')[-2][-2:])
        #print(concat_df['img_num'])
        return concat_df


# --------------------------------------------------
def generate_flurorescence(df):
    df_data = []
    for plot in set(df['Plot']):

        # the first value from the second picture
        try:
            F0 = list(df.loc[df['Plot'] == plot, 'Sum_AreaXMeanXMultiThr_over_Sum_AreaXMultiThr'])[5]
        except IndexError as e:
            # an IndexError will be thrown if no records were found for a given plot.
            # this could happen if the plot was not listed in the Plot boundaries.xlsx
            # and the previous step has been run
            print(f'No data found in plot {plot}.', e)
            continue

        # extracting image number from the label string and converting it to an int for filtering
        df['img_num'] = df['Label'].str.slice(-8, -4).astype(int)

        # maximum value of rawData images 2-46
        FM = df.loc[
            (df['Plot'] == plot) &
            ((df['img_num'] > 0) & (df['img_num'] <= 46)),
            'Sum_AreaXMeanXMultiThr_over_Sum_AreaXMultiThr'
        ].max()

        FV = FM - F0

        df_row_dict = {
            "Plot":  plot,
            "F0":    F0,
            "FM":    FM,
            "FV":    FV,
            "FV/FM": FV / FM,
        }

        df_data.append(df_row_dict)

    fluorescence_df = pd.DataFrame(df_data)
    return fluorescence_df


# --------------------------------------------------
def main():
    """Generate fluorescence file here"""

    args = get_args()

    if not os.path.isdir(args.outdir):
        os.makedirs(args.outdir)

    file_list = glob.glob(f'{args.csv}/*/*.csv')

    if not file_list:
        file_list = [args.csv]

    #print(args.csv)
    #csv_list = glob.glob(args.csv)
    concat_df = generate_aggregate(file_list, args.multithresh)
    fluor_df = generate_flurorescence(concat_df)

    fluor_df.to_csv(os.path.join(args.outdir, args.outfile + '.csv'))

    print(f'Process complete. See output in {args.outdir}/')


# --------------------------------------------------
if __name__ == '__main__':
    main()
