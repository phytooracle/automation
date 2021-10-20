#!/usr/bin/env python3
"""
Author : Emmanuel Gonzalez
Date   : 2021-04-29
Purpose: Pipeline automation
"""

import argparse
import os
import sys
import numpy as np
import subprocess
import re
import pandas as pd
from datetime import datetime
import subprocess as sp
import shutil
from prepare_utils import *
from replace_utils import *
from season_dictionary import *

# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Pipeline automation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-sea',
                        '--season',
                        help='Season to query.\
                            Allowed values are: 10, 11, 12.',
                        metavar='',
                        type=str,
                        required=True,
                        choices=['10', '11', '12'])

    parser.add_argument('-o',
                        '--ortho',
                        help='Download geoTIFF orthomosaic. For 3D pipeline only.',
                        action='store_true')

    parser.add_argument('-r',
                        '--reverse',
                        help='Reverse the order of processing list.',
                        action='store_true')

    parser.add_argument('-c',
                        '--crop',
                        help='Crop to process.',
                        choices=['sunflower', 'bean', 'sorghum'])

    parser.add_argument('-hpc',
                        '--hpc',
                        help='Add flag if running on an HPC system.',
                        action='store_true')

    parser.add_argument('-sen',
                        '--sensor',
                        help='Sensor to query.\
                            Allowed values are: EnvironmentLogger, flirIrCamera, ps2Top, scanner3DTop, stereoTop, VNIR, SWIR, PikaVNIR.',
                        metavar='',
                        type=str,
                        required=True,
                        choices=['EnvironmentLogger', 'flirIrCamera', 'ps2Top', 'scanner3DTop', 'stereoTop', 'VNIR', 'SWIR', 'PikaVNIR'])

    
    parser.add_argument('-b',
                        '--bundle_size',
                        help='Processing bundle size (number of data processed by a single worker).',
                        metavar='int',
                        type=int,
                        default=1)

    return parser.parse_args()


# --------------------------------------------------
def return_date_list(level_0_list):
    date_list = []
    for item in level_0_list:
        match = re.search(r'\d{4}-\d{2}-\d{2}', item)
        if match:
            date = str(datetime.strptime(match.group(), '%Y-%m-%d').date())
            date_list.append(date)
            
    return date_list


# --------------------------------------------------
def get_paths(season, sensor):

    season_dict = {'10': '/iplant/home/shared/phytooracle/season_10_lettuce_yr_2020/',
                    '11': '/iplant/home/shared/phytooracle/season_11_sorghum_yr_2020/',
                    '12': '/iplant/home/shared/phytooracle/season_12_sorghum_soybean_sunflower_tepary_yr_2021/'}

    season_path = season_dict[season]
    sensor_path = sensor

    return season_path, sensor_path


# --------------------------------------------------
def get_rgb_ortho(season_path, sensor_path, date):

    date_string = datetime.strptime(re.search(r'\d{4}-\d{2}-\d{2}', date).group(), '%Y-%m-%d').date()
    time_string = '12:00:00'

    date_list = [str(os.path.splitext(os.path.basename(line.strip().replace('C- ', '')))[0]) for line in os.popen(f'ils {os.path.join(season_path, "level_1", sensor_path)}').readlines()][1:]
    cyverse_paths = [line.strip().replace('C- ', '') for line in os.popen(f'ils {os.path.join(season_path, "level_1", sensor_path)}').readlines()][1:]
    date_list_cleaned = []
    cyverse_paths_cleaned = []

    for date_path, path in zip(date_list, cyverse_paths):
        try:
            dt = datetime.strptime(re.search(r'\d{4}-\d{2}-\d{2}', date_path).group(), '%Y-%m-%d').date()
            dt_time = ':'.join(re.search(r'\d{2}-\d{2}-\d{2}-\d{3}', date_path).group().replace('-', ':').split(':')[:-1])
            dt = pd.to_datetime(f'{dt} {dt_time}')
            date_list_cleaned.append(dt)
            cyverse_paths_cleaned.append(path)
        except:
            pass

    df = pd.DataFrame()
    df['datetime'] = date_list_cleaned
    # df['datetime'] = pd.to_datetime(df['datetime'])
    df['cyverse_path'] = cyverse_paths_cleaned
  
    df = df.set_index('datetime')
    df = df.between_time('11:00', '15:00')
    matching_date = df.iloc[df.index.get_loc(pd.to_datetime(f'{date_string} {time_string}'), method='nearest')]
    query_path = matching_date['cyverse_path']
    ortho = [item.strip() for item in os.popen(f'ils {query_path}').readlines()[1:] if '.tif' in item]
    if ortho: 
        orthomosaic_path = os.path.join(query_path, ortho[0])

    else:
        drop_path = df.iloc[df.index.get_loc(pd.to_datetime(f'{date_string} {time_string}'), method='nearest')]['cyverse_path']
        df = df[~df['cyverse_path'].isin([drop_path])]
        matching_date = df.iloc[df.index.get_loc(pd.to_datetime(f'{date_string} {time_string}'), method='nearest')]
        query_path = matching_date['cyverse_path']
        ortho = [item.strip() for item in os.popen(f'ils {query_path}').readlines()[1:] if '.tif' in item]
        orthomosaic_path = os.path.join(query_path, ortho[0])
    
    return orthomosaic_path


# --------------------------------------------------
def download_ortho(season_path, date):

    ortho_path = get_rgb_ortho(season_path, 'stereoTop', date)
    if ortho_path:

        if not os.path.isfile(os.path.basename(ortho_path)):
            cmd1 = f'iget -N 0 -PVT {ortho_path}'
            print(cmd1)
            subprocess.call(cmd1, shell=True)
    else: 
        pass
    return None


# --------------------------------------------------
def create_dict(directory):
    dir_list = []
    dir_dict = {}
    cnt = 0

    for root, dirs, files in os.walk(directory):
        match = re.search(r'\d{4}-\d{2}-\d{2}', root)
        date = datetime.strptime(match.group(), '%Y-%m-%d').date()
    
        for f in files:
       
            if '.json' in f:
                match = re.search(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', f)
       
                file_dict = {
                    "DATE": os.path.join(str(date), ''),
                    "RAW_DATA_PATH": os.path.join(root, ''),
                    "SUBDIR": os.path.basename(root),
                    "UUID": match.group()
                }

                dir_list.append(file_dict)

    dir_dict["DATA_FILE_LIST"] = dir_list

    return dir_dict


# --------------------------------------------------
def bundle_data(file_list, data_per_bundle):
    data_sets = []
    bundle_list = []
    for index, file in enumerate(file_list):
        if index % data_per_bundle == 0 and index != 0:
            bundle = {}
            bundle["DATA_SETS"] = data_sets
            bundle["ID"] = len(bundle_list)
            bundle_list.append(bundle)
            data_sets = []
        data_sets.append(file)
    bundle = {}
    bundle["DATA_SETS"] = data_sets
    bundle["ID"] = len(bundle_list)
    bundle_list.append(bundle)
    
    return bundle_list


# --------------------------------------------------
def write_to_file(out_filename, bundle_list):
    json_obj = {}
    json_obj["BUNDLE_LIST"] = bundle_list
    with open(out_filename, "w") as outfile:
        dump_str = json.dumps(json_obj, indent=2, sort_keys=True)
        outfile.write(dump_str)


# --------------------------------------------------
def gen_json_for_all_bundle(bundle_list):
    for i in range(len(bundle_list)):
        outfilename = "bundle_{0}.json".format(i)
        with open(os.path.join('bundle', outfilename), "w") as outfile:
            dump_str = json.dumps(bundle_list[i], indent=2, sort_keys=True)
            outfile.write(dump_str)


# --------------------------------------------------
def download_cctools(cctools_version = '7.1.12', architecture = 'x86_64', sys_os = 'centos7'):

    cwd = os.getcwd()
    home = os.path.expanduser('~')
    
    cctools_file = '-'.join(['cctools', cctools_version, architecture, sys_os])
    
    if not os.path.isdir(os.path.join(home, cctools_file)):
        print(f'Downloading {cctools_file}.')
        cctools_url = ''.join(['http://ccl.cse.nd.edu/software/files/', cctools_file])
        cmd1 = f'cd {home} && wget {cctools_url}.tar.gz && tar -xzvf {cctools_file}.tar.gz'
        sp.call(cmd1, shell=True)
        sp.call(f'cd {cwd}')
        print(f'Download complete. CCTools version {cctools_version} is ready!')

    else:
        print('Required CCTools version already exists.')


# --------------------------------------------------
def download_raw_data(irods_path):
    args = get_args()
    file_name = os.path.basename(irods_path)
    cmd1 = f'iget -fKPVT {irods_path}'
    cwd = os.getcwd()

    if '.gz' in file_name: 
        cmd2 = f'tar -xzvf {file_name}'
        cmd3 = f'rm {file_name}'

    else: 
        cmd2 = f'tar -xvf {file_name}'
        cmd3 = f'rm {file_name}'
    
    if args.hpc: 
        sp.call(f'ssh filexfer cd {cwd} && {cmd1} && {cmd2} && {cmd3} && exit', shell=True)
    else: 
        sp.call(cmd1, shell=True)
        sp.call(cmd2, shell=True)
        sp.call(cmd3, shell=True)


# --------------------------------------------------
def move_directory(sensor, scan_date):
    dir_move = os.path.join(sensor, scan_date)
    cwd = os.getcwd()
    shutil.move(dir_move, cwd)
    shutil.rmtree(sensor)


# --------------------------------------------------
def pipeline_prep(scan_date, bundle_size=1):
    download_cctools()

    # Create data list
    file_dict = create_dict(scan_date)["DATA_FILE_LIST"]
    bundle_list = bundle_data(file_list=file_dict, data_per_bundle=bundle_size)

    # Write data list
    write_to_file(out_filename='bundle_list.json', bundle_list=bundle_list) 

    # Split data into bundles
    if not os.path.isdir('bundle'):
        os.makedirs('bundle')
        
    gen_json_for_all_bundle(bundle_list=bundle_list)


# --------------------------------------------------
def update_process_one(replacement):

    with open('process_one_set.sh', 'r') as f:
        line_list = f.readlines()

        for line in line_list:

            if 'HPC_PATH=' in line:
                replacing = line.split('=')[-1]

                replace_file_one(replacing, f'"{replacement}"\n')
                replace_file_two(replacing, f'"{replacement}"\n')


def send_slack_update(message, channel='gantry_test'):

    sp.call(f'singularity run gantry_notifications.simg -m {message} -c {channel}', shell=True)

# # --------------------------------------------------
# def update_entry_point(entry, replacement):
 
#     with open(entry, 'r') as f:
#         lines = f.readlines()[2]
#         line2replace = lines.split()[2]

#     f = open(entry, 'r')
#     fdata = f.read()
#     f.close()
#     nline = fdata.replace(line2replace, replacement)
#     #print("Writing: " + nline)
#     f = open(entry, 'w')
#     f.write(nline)
#     f.close()
#     #print("Change complete")


# --------------------------------------------------
def main():
    """Make a jazz noise here"""

    args = get_args()

    # Get iRODS season path
    season_path, sensor_path = get_paths(args.season, args.sensor)

    # Find unprocessed data
    level_0 = os.path.join(season_path, 'level_0', sensor_path)
    level_1 = os.path.join(season_path, 'level_1', sensor_path)
    
    level_0_list, level_1_list = [item.lstrip() for item in [line.rstrip() for line in os.popen(f'ils {level_0}').readlines()][1:]] \
                                , [item.lstrip() for item in [line.rstrip() for line in os.popen(f'ils {level_1}').readlines()][1:]]
    
    level_0_dates, level_1_dates = return_date_list(level_0_list) \
                                , return_date_list(level_1_list)
    
    process_list = list(np.setdiff1d(level_0_dates, level_1_dates))

    matching = [os.path.splitext(os.path.basename(s))[0].replace(f'{args.sensor}-', '').replace('.tar', '') for s in level_0_list if any(xs in s for xs in process_list)]
    
    if args.reverse:
        matching.reverse()
    
    # Download pipeline requirements
    download_cctools()
    season_dict = season_dictionary()
    build_containers('10', 'scanner3DTop', season_dict)

    # Download, extract, and process raw data
    for scan_date in matching[:1]:

        for tarball in level_0_list:

            if scan_date in tarball and 'none' not in tarball: 
                
                send_slack_update(f'Downloading {scan_date}.', channel='gantry_test')
                irods_data_path = os.path.join(level_0, tarball)
                
                if not os.path.isdir(scan_date):
                    download_raw_data(irods_data_path)

                    if args.season == '10':
                        move_directory(args.sensor, scan_date)

                pipeline_prep(scan_date, bundle_size=args.bundle_size)
                # update_entry_point(args.entry, scan_date)
                update_process_one(os.getcwd())

                send_slack_update(f'Processing {scan_date}.', channel='gantry_test')
                sp.call('./entrypoint_p1.sh')

                # if args.crop:
                #     if args.crop in scan_date:
                #         print(tarball)
                #         print(scan_date)
                        
                #         # cmd1 = f'./run.sh {scan}'
                #         # subprocess.call(cmd1, shell=True)
                #         # print(f'INFO: {scan} processing complete.')
                        
                # else:
                #     print(level_0)
                #     print(tarball)
                #     print(scan_date)
                #     # cmd1 = f'./run.sh {scan}'
                #     # subprocess.call(cmd1, shell=True)
                #     # print(f'INFO: {scan} processing complete.')


# --------------------------------------------------
if __name__ == '__main__':
    main()
