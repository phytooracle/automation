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
import glob
from prepare_utils import *
from replace_utils import *
from season_dictionary import *
from move_utils import *

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

    parser.add_argument('-scan',
                        '--scan_date',
                        help='Scan date to process.',
                        metavar='scan_date',
                        type=str,
                        nargs='+',
                        required=False)

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

    parser.add_argument('-w',
                        '--workflow',
                        help='Workflow to run. Options are [1, 2, 3]',
                        metavar='workflow',
                        type=str,
                        nargs='+')

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
                match2 = re.search(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', f)

                file_dict = {
                    "DATE": os.path.join(str(date), ''),
                    "RAW_DATA_PATH": os.path.join(root, ''),
                    "SUBDIR": os.path.basename(root),
                    "UUID": match2.group()
                }

                dir_list.append(file_dict)

    dir_dict["DATA_FILE_LIST"] = dir_list

    return dir_dict


# # --------------------------------------------------
# def create_dict_plant(directory):
#     dir_list = []
#     dir_dict = {}
#     cnt = 0

#     for root, dirs, files in os.walk(directory):
#         # print(files)
    
#         for f in files:
       
#             if '.ply' in f:

#                 raw, plant_name = os.path.split(root)
#                 uuid, _ = os.path.splitext(os.path.basename(f))
                
#                 file_dict = {
#                     "RAW_DATA_PATH": os.path.join(raw, ''),
#                     "PLANT_NAME": os.path.basename(plant_name),
#                     "UUID": uuid
#                 }

#                 dir_list.append(file_dict)

#     dir_dict["DATA_FILE_LIST"] = dir_list

#     return dir_dict



def create_dict_plant(directory):
    dir_list = []
    dir_dict = {}
    cnt = 0
    files_list = []


    for root, dirs, files in os.walk(directory):
    
        for f in files:
       
            if '.ply' in f:

                raw, plant_name = os.path.split(root)
                files_list.append(plant_name)
    
    files_list = np.unique(files_list).tolist()
    
    for item in files_list:

        file_dict = {
            "PLANT_NAME": os.path.basename(item),
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
    cwd = os.getcwd()
    json_obj = {}
    json_obj["BUNDLE_LIST"] = bundle_list

    with open(os.path.join(cwd, out_filename), "w") as outfile:
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
        print(os.getcwd())
        #sp.call(f'cd {cwd}')
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
        print('>>>>>>Using data transfer node.')
        sp.call(f"ssh filexfer 'cd {cwd}' '&& {cmd1}' '&& {cmd2}' '&& {cmd3}' '&& exit'", shell=True)
    else: 
        sp.call(cmd1, shell=True)
        sp.call(cmd2, shell=True)
        sp.call(cmd3, shell=True)


# --------------------------------------------------
def download_level_1_data(irods_path):
    args = get_args()
    file_name = os.path.basename(irods_path)
    direc = irods_path.split('/')[-1]
    print(file_name)
    cmd1 = f'iget -rfPVT {irods_path}'
    # cmd1 = f'iget -fKPVT {irods_path}'
    cwd = os.getcwd()

    if '.gz' in file_name: 
        cmd2 = 'ls *.tar.gz | xargs -I {} tar -xzvf {}'
        cmd3 = f'rm *.tar.gz'

    else: 
        cmd2 = 'ls *.tar | xargs -I {} tar -xvf {}'
        cmd3 = f'rm *.tar'
    
    if args.hpc: 
        print('>>>>>>Using data transfer node.')
        sp.call(f"ssh filexfer 'cd {cwd}' '&& {cmd1}' '&& cd {os.path.join(cwd, direc)}' '&& {cmd2}' '&& {cmd3}' '&& exit'", shell=True)
    else: 
        sp.call(cmd1, shell=True)
        sp.call(f"cd {os.path.join(cwd, direc)}")
        sp.call(cmd2, shell=True)
        sp.call(cmd3, shell=True)


# --------------------------------------------------
def get_transformation_file(irods_path, cwd):

    cmd1 = f'iget -KPVT {os.path.join(irods_path, "preprocessing", "transfromation.json")}'
    sp.call(cmd1, shell=True)
    
    if not os.path.isfile(os.path.join(cwd, 'transfromation.json')):
        cmd2 = f'iget -KPVT {os.path.join(irods_path, "alignment", "transfromation.json")}'
        sp.call(cmd2, shell=True)


# --------------------------------------------------
def get_bundle_dir(irods_path):

    cmd1 = f'iget -rKPVT {os.path.join(irods_path, "logs", "bundle")}'

    sp.call(cmd1, shell=True)

# --------------------------------------------------
def get_bundle_json(irods_path):

    cmd1 = f'iget -KPVT {os.path.join(irods_path, "logs", "bundle_list.json")}'

    sp.call(cmd1, shell=True)


# --------------------------------------------------
def move_directory(sensor, scan_date):
    dir_move = os.path.join(sensor, scan_date)
    cwd = os.getcwd()
    shutil.move(dir_move, cwd)
    shutil.rmtree(sensor)


# --------------------------------------------------
def pipeline_prep(scan_date, bundle_size=1, plant=False):
    # download_cctools()

    # Create data list
    if plant:
        file_dict = create_dict_plant(scan_date)["DATA_FILE_LIST"]
    else:
        file_dict = create_dict(scan_date)["DATA_FILE_LIST"]

    bundle_list = bundle_data(file_list=file_dict, data_per_bundle=bundle_size)

    # Write data list
    write_to_file(out_filename='bundle_list.json', bundle_list=bundle_list)
    sp.run(['chmod', '755', 'bundle_list.json']) 

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

    with open('process_one_set2.sh', 'r') as f:
        line_list = f.readlines()

        for line in line_list:

            if 'HPC_PATH=' in line:
                replacing = line.split('=')[-1]
                replace_file_two(replacing, f'"{replacement}"\n')

    with open('process_one_set3.sh', 'r') as f:
        line_list = f.readlines()

        for line in line_list:

            if 'HPC_PATH=' in line:
                replacing = line.split('=')[-1]
                replace_file_three(replacing, f'"{replacement}"\n')


# --------------------------------------------------
def send_slack_update(message, channel='gantry_test'):

    sp.call(f'singularity run gantry_notifications.simg -m "{message}" -c "{channel}"', shell=True)


# --------------------------------------------------
def uncompress_plants():
    print('Uncompressing plants.')
    sp.call('ls *_individual_plants.tar | xargs -I {} tar -xvf {}', shell=True)
    sp.call('rm *_individual_plants.tar', shell=True)


# --------------------------------------------------
def uncompress_inference(cwd):
    os.chdir('individual_plants_out')
    print('Uncompressing plants.')
    sp.call('ls *_combined_pointclouds.tar | xargs -I {} tar -xvf {}', shell=True)
    sp.call('rm *_combined_pointclouds.tar', shell=True)

    sp.call('ls *_plant_reports.tar | xargs -I {} tar -xvf {}', shell=True)
    sp.call('rm *_plant_reports.tar', shell=True)
    os.chdir(cwd)

# --------------------------------------------------
def run_plant_volume(dir_path):
    sp.call(f'singularity run hull_volume_estimation.simg -i {dir_path}', shell=True)


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
    build_containers(args.season, args.sensor, season_dict)

    # Download, extract, and process raw data
    if args.crop: 

        matching = [scan_date for scan_date in matching if args.crop in scan_date]

    if args.scan_date: 

        matching = args.scan_date

    for scan_date in matching:
        
        for tarball in level_0_list:

            if scan_date in tarball and 'none' not in tarball: 
                cwd = os.getcwd()

                if set(['1','2']).issubset(args.workflow):
                    
                    irods_data_path = os.path.join(level_0, tarball)

                    if args.season != '10':
                        scan_date = tarball.split('.')[0]
                        print(scan_date)

                    if not os.path.isdir(scan_date):
                        download_raw_data(irods_data_path)

                        if args.season == '10':
                            move_directory(args.sensor, scan_date)

                    pipeline_prep(scan_date, bundle_size=args.bundle_size)
                    update_process_one(os.getcwd()+'/')

                    if not os.path.isdir(season_dict[args.season][args.sensor]['workflow_1']['outputs']['pipeline_out']):
                        run_workflow_1(args.season, args.sensor, season_dict)
                    
                    if not os.path.isdir(season_dict[args.season][args.sensor]['intermediate']['outputs']['pipeline_out']):
                        run_intermediate(args.season, args.sensor, season_dict)
                        move_scan_date(scan_date)

                    for item in ['intermediate']:

                        pipeline_out, pipeline_tag, processed_outdir = get_tags(season_dict, args.season, args.sensor, item)
                        tar_outputs(scan_date, pipeline_out, pipeline_tag, processed_outdir)

                    create_pipeline_logs(scan_date, bundle=True)

                    sp.call(f"ssh filexfer 'cd {cwd}' '&& ./upload.sh {scan_date} {cwd}' '&& exit'", shell=True) 
 
                    clean_directory(scan_date)   

                if set(['3', '4']).issubset(args.workflow): 
                    update_process_one(os.getcwd()+'/')
                    irods_data_path = os.path.join(level_1, scan_date, 'alignment')

                    if args.sensor=='scanner3DTop':
                        if not os.path.isdir('alignment'):
                            download_level_1_data(irods_data_path)

                        if not os.path.isfile('transfromation.json'):
                            
                            get_transformation_file(os.path.join(level_1, scan_date), cwd)

                        if not os.path.isdir('bundle'):

                            get_bundle_dir(os.path.join(level_1, scan_date))
                            
                        if not os.path.isfile('bundle_list.json'):

                            get_bundle_json(os.path.join(level_1, scan_date))
                    
                    if not os.path.isdir(season_dict[args.season][args.sensor]['workflow_2']['outputs']['pipeline_out']):
                        run_workflow_2(args.season, args.sensor, season_dict)
                    
                    if not os.path.isdir('individual_plants_out'):
                        uncompress_plants()

                    update_process_one(os.getcwd()+'/')
                    pipeline_prep('individual_plants_out', bundle_size=args.bundle_size, plant=True)

                    if not os.path.isdir(os.path.join(cwd, season_dict[args.season][args.sensor]['workflow_3']['outputs']['pipeline_out'], 'combined_pointclouds')):
                        run_workflow_3(args.season, args.sensor, season_dict)
                        uncompress_inference(cwd)

                    processing_dir = os.path.join(cwd, season_dict[args.season][args.sensor]['workflow_3']['outputs']['pipeline_out'], 'combined_pointclouds')

                    if not os.path.isfile(os.path.join(processing_dir, 'hull_volumes.csv')):
                        print('Estimating volume.')
                        run_plant_volume(processing_dir)
                        os.rename(os.path.join(processing_dir, 'hull_volumes.csv'), os.path.join(processing_dir, f'{scan_date}_hull_volumes.csv'))

                    for item in ['workflow_3']:

                        pipeline_out, pipeline_tag, processed_outdir = get_tags(season_dict, args.season, args.sensor, item)
                        tar_outputs(scan_date, pipeline_out, pipeline_tag, processed_outdir)

                    if not os.path.isdir(os.path.join(scan_date, 'logs')):
                        create_pipeline_logs(scan_date)

                    if os.path.isfile(os.path.join(processing_dir, f'{scan_date}_hull_volumes.csv')):
                        shutil.move(os.path.join(processing_dir, f'{scan_date}_hull_volumes.csv'), os.path.join(cwd, scan_date))

                    send_slack_update(f'{scan_date}: Uploading...', channel='gantry_test')
                    sp.call(f"ssh filexfer 'cd {cwd}' '&& ./upload.sh {scan_date} {cwd}' '&& exit'", shell=True)

                    send_slack_update(f'{scan_date}: Upload complete...', channel='gantry_test') 
                    clean_directory(scan_date)                       


# --------------------------------------------------
if __name__ == '__main__':
    main()
