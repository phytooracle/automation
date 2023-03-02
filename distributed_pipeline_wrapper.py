#!/usr/bin/env python3
"""
Author : Emmanuel Gonzalez
Date   : 2021-12-17
Purpose: PhytoOracle | Scalable, modular phenomic data processing pipelines
"""

import argparse
from genericpath import isfile
import pdb # pdb.set_trace()
import os
import sys
import json
import subprocess as sp
import yaml
import shutil
import glob
import tarfile
import multiprocessing
import re
from datetime import datetime
import numpy as np
import platform
import socket
import time

# Our libraries...
import server_utils

# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='PhytoOracle | Scalable, modular phenomic data processing pipelines',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-hpc',
                        '--hpc',
                        help='Add flag if running on an HPC system.',
                        action='store_true')

    parser.add_argument('-d',
                        '--date',
                        help='Date to process',
                        nargs='*',
                        type=str)
                        # required=True)

    # Season 12 and on should have a value for experiment set (e.g. sorghum, sunflower)
    # For Season 11 it should be left '' (so no experiment dir is created)
    parser.add_argument('-x',
                        '--experiment',
                        help='Experiment (e.g. Sorghum, Sunflower)',
                        type=str,
                        default='')

    parser.add_argument('-c',
                        '--cctools_version',
                        help='CCTools version',
                        type=str,
                        default='7.4.2')

    parser.add_argument('-l',
                        '--local_cores',
                        help='Percentage of cores to use for local processing',
                        type=float,
                        default=1.0)#0.70)

    parser.add_argument('-y',
                        '--yaml',
                        help='YAML file specifying processing tasks/arguments',
                        metavar='str',
                        type=str,
                        required=True)

    parser.add_argument('-wm',
                        '--workload_manager_yaml',
                        help='YAML file specifying workload_manager arguments',
                        metavar='str',
                        type=str,
                        required=False)

    parser.add_argument('--noclean',
                        help='Do not rm results locally',
                        #metavar='noclean',
                        #default=False,
                        action='store_true',
                       )

    parser.add_argument('--module_breakpoints',
                        help='Useful for testing yaml modules.  Code will breakpoint() just before each module.  You can type `continue` to have it continue like nothing happened, or you can `^d` to stop the script and look at the wf_file_n.json and run it by hand.',
                        action='store_true',
                       )

    parser.add_argument('--archiveonly',
                        help='just archive and exit (for testing)',
                        action='store_true',
                       )

    parser.add_argument('--uploadonly',
                        help='just do cyverse ul and exit (for testing)',
                        action='store_true',
                       )
    
    parser.add_argument('--noupload',
                        help='do not tar and upload outputs',
                        action='store_true',
                       )

    parser.add_argument('-r',
                        '--reverse',
                        help='Reverse processing date list.',
                        action='store_true')
    
    parser.add_argument('-sfs',
                        '--shared_file_system',
                        help='Shared filesystem.',
                        action='store_false')


    parser.add_argument('-t',
                        '--timeout',
                        help='Command timeout in units minute.',
                        type=float,
                        default=6)#0.5)

    parser.add_argument('-m',
                        '--multi_date',
                        type=int,
                        help='Choose what date to process in the list 0 for the first element',
                        default=99)


    return parser.parse_args()


# --------------------------------------------------
def build_containers(yaml_dictionary):
    """Build module containers outlined in YAML file
    
    Input: 
        - yaml_dictionary: Dictionary generated from the YAML file
    
    Output: 
        - Singularity images (SIMG files)
    """
    for k, v in yaml_dictionary['modules'].items():
        container = v['container']
        if not os.path.isfile(container["simg_name"]):
            print(f'Building {container["simg_name"]}.')
            sp.call(f'singularity build {container["simg_name"]} {container["dockerhub_path"]}', shell=True)


# --------------------------------------------------
def download_cctools(cctools_version = '7.1.12', architecture = 'x86_64', sys_os = 'centos7'):
    '''
    Download CCTools (https://cctools.readthedocs.io/en/latest/) and extracts the contents of the file. 

    Input:
        - cctools_version: CCTools version to install 
        - architecture:  Bit software to download
        - sys_os: Operating system on current machine
    Output: 
        - path to cctools on working machine
    '''
    cwd = os.getcwd()
    home = os.path.expanduser('~')
    
    # builds from latest stable source if not on a centos system
    if server_utils.distro_name() != 'CentOS Linux':
        cctools_file = 'cctools-stable-source'
        if not os.path.isdir(os.path.join(home, 'cctools')):
            print(f'Downloading {cctools_file}.')
            cctools_url = ''.join(['http://ccl.cse.nd.edu/software/files/', cctools_file])
            print(cctools_url)
            cmd1 = f'cd {home} && wget {cctools_url}.tar.gz'
            sp.call(cmd1, shell=True)
            os.chdir(home)
            cmd2 = f'mkdir non_centos_cctools && tar xzvf {cctools_file}.tar.gz -C non_centos_cctools'
            sp.call(cmd2, shell = True)
            os.chdir('non_centos_cctools')

            print('Building cctools from source...')

            os.chdir(glob.glob('./*')[0])

            cmd3 = './configure --prefix $HOME/cctools && make && make install'
            sp.call(cmd3, shell = True)



            os.remove(os.path.join(home, f'{cctools_file}.tar.gz'))
            
            print(f'Download complete. CCTools is ready!')

        else:
            print('Required CCTools version already exists.')

        return 'cctools/'

    # builds from centos specific package if on centos
    else:

        cctools_file = '-'.join(['cctools', cctools_version, architecture, sys_os])
    
        if not os.path.isdir(os.path.join(home, cctools_file)):
            print(f'Downloading {cctools_file}.')
            cctools_url = ''.join(['http://ccl.cse.nd.edu/software/files/', cctools_file])
            cmd1 = f'cd {home} && wget {cctools_url}.tar.gz'
            sp.call(cmd1, shell=True)
            os.chdir(home)
            file = tarfile.open(f'{cctools_file}.tar.gz')
            file.extractall('.')
            file.close()
            os.remove(f'{cctools_file}.tar.gz')

            try:
                shutil.move('-'.join(['cctools', cctools_version, architecture, sys_os+'.tar.gz', 'dir']), '-'.join(['cctools', cctools_version, architecture, sys_os]))

            except:
                pass

            os.chdir(cwd)
            print(f'Download complete. CCTools version {cctools_version} is ready!')

        else:
            print('Required CCTools version already exists.')

        return '-'.join(['cctools', cctools_version, architecture, sys_os])


def build_irods_path_to_sensor_from_yaml(yaml_dictionary, args):
    """
    Every path (level zero or otherwise) starts the same:
    .../phytooracle/season_11_sorghum_yr_2020/level_0/scanner3DTop
    """

    cyverse_basename  = yaml_dictionary['paths']['cyverse']['basename']
    #season_name       = yaml_dictionary['tags']['season_name']
    season_name       = get_season_name()
    cyverse_datalevel = yaml_dictionary['paths']['cyverse']['input']['level']
    sensor            = yaml_dictionary['tags']['sensor']

    path = os.path.join(
            cyverse_basename,
            season_name,
            cyverse_datalevel,
            sensor
    )

    experiment = args.experiment

    # If level is greater than level zero, then we need to add
    # two directories: .../expirment/date
    # for example: level_1/scanner3DTop/sunflower/2222-22-22
    if cyverse_datalevel > 'level_0':
        path = os.path.join(
                             path,
                             (experiment if experiment else "")
        )

    return path

def download_irods_input_dir(yaml_dictionary, date, args):
    """
    (0) Make the local input_dir
    (1) Download all contents from the cyverse location pointed to
    by yaml_dictionary['paths']['cyverse']['input']['input_dir']
    (2) Untar stuff if needed

    Usecase example...  The level 1 3D data after landmark selection is a bunch of tarballs
    and a json file that live in a directory called `alignment`.  So we have to make that
    dir locally, and then DL and untar each tarball and then DL the json file too.
    """
    args = get_args()
    # print('DOWNLOADING')

    # Step (0)
    input_dir = yaml_dictionary['paths']['cyverse']['input']['input_dir']
    server_utils.make_dir(input_dir)

    # Step (1)
    sensor_path = build_irods_path_to_sensor_from_yaml(yaml_dictionary, args)
    irods_input_dir_path = os.path.join(sensor_path, date, input_dir)

    # if args.experiment:
     
    #     if int(str(yaml_dictionary['paths']['cyverse']['input']['level']).split('_')[1]) >= 1:

    #         irods_input_dir_path = os.path.join(sensor_path, date, input_dir, args.experiment)
    #         print(irods_input_dir_path)
    
    files_in_dir = server_utils.get_filenames_in_dir_from_cyverse(irods_input_dir_path)
    file_paths = [os.path.join(irods_input_dir_path, x) for x in files_in_dir]

    os.chdir(input_dir)

    server_utils.download_files_from_cyverse(files=file_paths, experiment=args.experiment)

    # Step (2)

    server_utils.untar_files(files_in_dir)

    os.chdir('../')
    return

# --------------------------------------------------
def find_matching_file_in_irods_dir(yaml_dictionary, date, args, irods_dl_dir):
    """
    Get IRODS path to download
    
    Input: 
        - yaml_dictionary: Dictionary generated from the YAML file
    
    Output: 
        - irods_path: CyVerse filepath
    """


    args = get_args()
    experiment        = args.experiment
    cyverse_datalevel = yaml_dictionary['paths']['cyverse']['input']['level']
    prefix            = yaml_dictionary['paths']['cyverse']['input']['prefix']
    suffix            = yaml_dictionary['paths']['cyverse']['input']['suffix']

    all_files_in_dir = server_utils.get_filenames_in_dir_from_cyverse(irods_dl_dir)
    # Now lets see if our file is in all_files_in_dir

    if args.experiment:
        date_sub = match = re.search(r'\d{4}-\d{2}-\d{2}', date)
        date_sub = str(datetime.strptime(date_sub.group(), '%Y-%m-%d').date())
        pattern = (prefix if prefix else "") + date_sub + (suffix if suffix else "")

    else:
        pattern = (prefix if prefix else "") + date + (suffix if suffix else "")

    import pathlib
    matching_files = [x for x in all_files_in_dir if pathlib.PurePath(x).match(pattern)]

    if len(matching_files) < 1:
        print (f"WARNING Could not find appropriate tarball for date: {date}\n \
                           Found: {matching_files}")
        return None
    if len(matching_files) > 1:
        
        if args.experiment:
            matching_files = [item for item in matching_files if date in item]

        else:
            return None
        # if args.multi_date != 99:
        #     file_dl_path = os.path.join(irods_dl_dir,matching_files[args.multi_date])
    
        #     print(f"multi date used, get_irods_input_path() found a file: {file_dl_path}")
        #     return file_dl_path

        # return None


    file_dl_path = os.path.join(
                    irods_dl_dir,
                    matching_files[0]
    )
    
    print(f"get_irods_input_path() found a file: {file_dl_path}")


    return file_dl_path


# --------------------------------------------------
def download_irods_input_file(irods_path):
    """Download raw dataset from CyVerse DataStore
    
        Input:
            - irods_path: CyVerse path to the raw data
            
        Does: 
            - Downloads tarball if it isn't found locally.
            - Extracts files from the tarball.

        Returns:
            - dir_name: name of directory created from tarball.
    """

    args = get_args()

    tarball_filename = os.path.basename(irods_path)
    if not os.path.isfile(tarball_filename):
        # We need to DL the tarball.
        cmd1 = f'iget -fKPVT {irods_path}'
        if args.hpc: 
            print('>>>>>>Using data transfer node.')
            cwd = os.getcwd()
            sp.call(f"ssh filexfer 'cd {cwd}' '&& {cmd1}' '&& exit'", shell=True)
        else: 
            sp.call(cmd1, shell=True)

    time.sleep(30)
    #tarball = tarfile.open(tarball_filename, mode='r')
    #print(f"Examining {tarball_filename}, this can take a minute.")
    #dir_name = os.path.commonprefix(tarball.getnames())

    # We want to find the root directory of the tar ball.  It's very large and
    # compressed, So using something like os.path.commonprefix(tarball.getnames())
    # will take forever.  So we do this instead...
    import shlex
    print(f"Examining {tarball_filename}, this can take a second...")
    gzip_extensions = ['.tgz', '.tar.gz']
    
    if any(x in tarball_filename for x in gzip_extensions):
#     if gzip_extension in tarball_filename:

        command = f"tar -ztf {tarball_filename}"

    else:
        command = f"tar -tf {tarball_filename}"
        
    with sp.Popen(shlex.split(command),
            stdout=sp.PIPE,
            bufsize=1,
            universal_newlines=True) as process:
        first_line = next(process.stdout)
        process.kill
    if not first_line.strip().endswith('/'):
        raise ValueError(f"ERROR. We can't figure out the root dir of {tarball_filename}")
    dir_name = first_line.strip()[:-1]
    #print(f"... found: {dir_name}")

    if not os.path.isdir(dir_name):
        # cmd1 = f'iget -fKPVT {irods_path}'
        #cmd1 = f'iget -fPVT {irods_path}'

        if any(x in tarball_filename for x in gzip_extensions):
            cmd2 = f'tar -xzvf {tarball_filename}'
            cmd3 = f'rm {tarball_filename}'

        else: 
            cmd2 = f'tar -xvf {tarball_filename}'
            cmd3 = f'rm {tarball_filename}'
        
        if args.hpc: 
            # print('>>>>>>Using data transfer node.')
            cwd = os.getcwd()
            # sp.call(f"ssh filexfer 'cd {cwd}' '&& {cmd2}' '&& {cmd3}' '&& exit'", shell=True)
            sp.call(f"cd {cwd} && {cmd2} && {cmd3}", shell=True)

        else: 
            sp.call(cmd2, shell=True)
            sp.call(cmd3, shell=True)

    return dir_name


def get_file_list(directory, level, match_string='.ply'):
    '''
    Walks through a given directory and grabs all files with the given search string.

    Input: 
        - directory: Local directory to search 
        - match_string: Substring to search and add only elements with items containing 
                        this string being added to the file list. 

    Output: 
        - subdir_list: List containing all subdirectories within the raw data.
        - files_list: List containing all files within each subdirectory within the raw data.
    '''
    files_list = []
    subdir_list = []

    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            if match_string in name:
                files_list.append(os.path.join(root, name))
            
        for name in dirs:
            subdir_list.append(os.path.join(root, name))
            
    if level=='subdir':
        if 'west' in directory: 
            directory = directory.replace('west', 'east')
            
        elif 'east' in directory:
            directory = directory.replace('east', 'west')
            
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files:
                if match_string in name:
                    files_list.append(os.path.join(root, name))
                    
        plant_names = [os.path.basename(os.path.dirname(dir_path)) for dir_path in files_list]
        plant_names = list(set(plant_names))
        plant_names = [os.path.join(directory, plant_name, 'null.ply') for plant_name in plant_names]
        files_list = plant_names

    if level == 'whole_subdir':
        files_list = []
        for root, dirs, files in os.walk(directory, topdown=False):
            for d in dirs:
                files_list.append(d)
    
    if level == 'dir':
        files_list = [directory]
        return files_list


    if len(files_list) == 0:
        print('---------------------------no files found---------------------------------------')


    return files_list


# --------------------------------------------------
def write_file_list(input_list, out_path='file.txt'):
    '''
    Write either files/subdir list to file.

    Input: 
        - input_list: List containing files
        - out_path: Filename of the output
    Output: 
        - TXT file.  
    '''
    textfile = open(out_path, "w")
    for element in input_list:
        textfile.write(element + "\n")
    textfile.close()



# --------------------------------------------------
def get_support_files(yaml_dictionary, date):
    '''
    Input:
        - yaml_dictionary: Dictionary variable (YAML file)
        - date: Scan date being processed
    
    Output: 
        - Downloaded files/directories in the current working directory
    '''

    #season_name = yaml_dictionary['tags']['season_name']
    season_name = get_season_name()
    cyverse_basename  = yaml_dictionary['paths']['cyverse']['basename']

    irods_basename = os.path.join(
            cyverse_basename,
            season_name
    )

    support_files = yaml_dictionary['paths']['cyverse']['input']['necessary_files']

    for file_path in support_files:
        print(f"Looking for {file_path}...")
        filename = os.path.basename(file_path)
        #pdb.set_trace()
        if not os.path.isfile(filename):
            cyverse_path = os.path.join(irods_basename, file_path)
            print(f"    We need to get: {cyverse_path}")
            server_utils.download_file_from_cyverse(os.path.join(irods_basename, file_path))
        else:
            print(f"FOUND")
        server_utils.untar_files([filename])

    sensor = yaml_dictionary["tags"]["sensor"]
   
    if (sensor == "stereoTop") or (sensor == 'flirIrCamera'):
        if not os.path.isdir('Lettuce_Image_Stitching'):
            sp.call("git clone https://github.com/ariyanzri/Lettuce_Image_Stitching.git", shell=True)


# --------------------------------------------------
def get_season_name():
    season_name = yaml_dictionary['tags']['season_name']
    if not season_name:
        raise ValueError(
          f"ERROR.  You need to specify yaml_dictionary['tags']['season_name'] in your yaml file.  For example: \n" + \
          "season_name: season_11_sorghum_yr_2020"
        )
    return season_name


# --------------------------------------------------
def get_model_files(yaml_dictionary):
    """Download model weights from CyVerse DataStore
    
    Input:
        - seg_model_path: CyVerse path to the segmentation model (.pth file)
        - det_model_path: CyVerse path to the object detection model (.pth file)
        
    Output: 
        - Downloaded model weight files.
    """
    
    if 'segmentation' in yaml_dictionary['paths']['models'].keys():

        seg_model_path = yaml_dictionary['paths']['models']['segmentation']

        if not os.path.isfile(os.path.basename(seg_model_path)):
            cmd1 = f'iget -fKPVT {seg_model_path}'
            sp.call(cmd1, shell=True)

    if 'detection' in yaml_dictionary['paths']['models'].keys():
        
        det_model_path = yaml_dictionary['paths']['models']['detection']

        if not os.path.isfile(os.path.basename(det_model_path)):
            cmd1 = f'iget -fKPVT {det_model_path}'
            sp.call(cmd1, shell=True)

    if 'lid' in yaml_dictionary['paths']['models'].keys():
        
        lid_model_path = yaml_dictionary['paths']['models']['lid']

        if not os.path.isfile(os.path.basename(lid_model_path)):
            cmd1 = f'iget -fKPVT {lid_model_path}'
            sp.call(cmd1, shell=True)

    return os.path.basename(seg_model_path), os.path.basename(det_model_path) 


# --------------------------------------------------
def launch_workers(cctools_path, account, job_name, nodes, time, mem_per_core, manager_name, number_worker_array, cores_per_worker, worker_timeout, cwd, outfile='worker.sh', worker_type='work_queue_worker'):
    '''
    Launches workers on a SLURM workload management system.

    Input:
        - account: Account to charge compute resources
        - partition: Either standard or windfall hours
        - job_name: Name for the job 
        - nodes: Number of nodes to use per Workqueue factory
        - time: Time alloted for job to run 
        - manager_name: Name of workflow manager
        - min_worker: Minimum number of workers per Workqueue factory
        - max_worker: Maximum number of workers per Workqueue factory
        - cores_per_worker: Number of cores per worker
        - worker_timeout: Time to wait for worker to receive a task before timing out (units in seconds)
        - outfile: Output filename for SLURM submission script
    
    Output: 
        - Running workers on an HPC system
    '''
    time_seconds = int(time)*60

    if 'worker_type' in yaml_dictionary['workload_manager'].keys():
        worker_type=yaml_dictionary['workload_manager']['worker_type']
    
    with open(outfile, 'w') as fh:
        fh.writelines("#!/bin/bash\n")
        fh.writelines(f"#SBATCH --account={account}\n")
        fh.writelines(f"#SBATCH --job-name={job_name}\n")
        fh.writelines(f"#SBATCH --nodes={nodes}\n")
        fh.writelines(f"#SBATCH --mem-per-cpu={mem_per_core}gb\n")
        fh.writelines(f"#SBATCH --time={time}\n")
        fh.writelines(f"#SBATCH --array 1-{number_worker_array}\n")

        if yaml_dictionary['workload_manager']['standard_settings']['use']==True:
            fh.writelines(f"#SBATCH --partition={yaml_dictionary['workload_manager']['standard_settings']['partition']}\n")

        elif yaml_dictionary['workload_manager']['high_priority_settings']['use']==True:
            fh.writelines(f"#SBATCH --qos={yaml_dictionary['workload_manager']['high_priority_settings']['qos_group']}\n")
            fh.writelines(f"#SBATCH --partition={yaml_dictionary['workload_manager']['high_priority_settings']['partition']}\n")
        

        if worker_type == 'work_queue_worker':

            fh.writelines(f"#SBATCH --ntasks={int(cores_per_worker)}\n")
            fh.writelines("export CCTOOLS_HOME=${HOME}/"+f"{cctools_path}\n")
            fh.writelines("export PATH=${CCTOOLS_HOME}/bin:$PATH\n")
            fh.writelines(f"{worker_type} -M {manager_name} --cores {cores_per_worker} -t {worker_timeout} --memory {mem_per_core*cores_per_worker*1000}\n")

        elif worker_type == 'work_queue_factory':

            if 'max_workers' in yaml_dictionary['workload_manager'].keys():
                fh.writelines(f"#SBATCH --ntasks={int(yaml_dictionary['workload_manager']['max_workers'])}\n")
                fh.writelines("export CCTOOLS_HOME=${HOME}/"+f"{cctools_path}\n")
                fh.writelines("export PATH=${CCTOOLS_HOME}/bin:$PATH\n")
                fh.writelines(f"{worker_type} -T local -M {manager_name} --max-workers {yaml_dictionary['workload_manager']['max_workers']} --cores {cores_per_worker} -t {worker_timeout} --memory {mem_per_core*cores_per_worker*1000}\n")

            else:
                fh.writelines(f"#SBATCH --ntasks={cores_per_worker}\n")
                fh.writelines("export CCTOOLS_HOME=${HOME}/"+f"{cctools_path}\n")
                fh.writelines("export PATH=${CCTOOLS_HOME}/bin:$PATH\n")
                fh.writelines(f"{worker_type} -T local -M {manager_name} --max-workers {cores_per_worker} --cores 1 -t {worker_timeout} --memory {mem_per_core*cores_per_worker*1000}\n")

    
    if 'total_submission' in yaml_dictionary['workload_manager'].keys():
        num = yaml_dictionary['workload_manager']['total_submission']
        for i in range(0, num):
            return_code = sp.call(f"sbatch {outfile}", shell=True)
    else:
        return_code = sp.call(f"sbatch {outfile}", shell=True)

    if return_code == 1:
        raise Exception(f"sbatch Failed")


# --------------------------------------------------
def kill_workers(job_name):
    '''
    Kills workers once workflow has terminated.

    Input:
        - job_name: Name of the job 
    
    Output: 
        - Kills workers on an HPC system
    '''
    os.system(f"scancel --name {job_name}")
    # os.system(f"ocelote && scancel --name {job_name} && puma")
    # os.system(f"elgato && scancel --name {job_name} && puma")

    
# --------------------------------------------------
def generate_makeflow_json(cctools_path, level, files_list, command, container, inputs, outputs, date, sensor, yaml_dictionary, n_rules=1, json_out_path='wf_file.json'):
    '''
    Generate Makeflow JSON file to distribute tasks. 

    Input: 
        - files_list: Either files or subdirectory list
        - n_rules: Number of rules per JSON file
        - json_out_path: Path to the resulting JSON file

    Output:
        - json_out_path: Path to the resulting JSON file
    '''
    args = get_args()
    files_list = [file.replace('-west.ply', '').replace('-east.ply', '').replace('-merged.ply', '').replace('__Top-heading-west_0.ply', '') for file in files_list]
    timeout = f'timeout {args.timeout}h '
    cwd = os.getcwd()
    command = command.replace('${CWD}', cwd)
    
    if sensor=='scanner3DTop':

        match_str = re.search(r'\d{4}-\d{2}-\d{2}', date)
        date = str(datetime.strptime(match_str.group(), '%Y-%m-%d').date())

    if inputs:
        if sensor=='scanner3DTop':
            
            if level == 'subdir':

                # if args.hpc:
                #     kill_workers(dictionary['workload_manager']['job_name'])
                #     launch_workers(cctools_path=cctools_path,
                #             account=dictionary['workload_manager']['account'], 
                #             # partition=dictionary['workload_manager']['partition'], 
                #             job_name=dictionary['workload_manager']['job_name'], 
                #             nodes=dictionary['workload_manager']['nodes'], 
                #             #number_tasks=dictionary['workload_manager']['number_tasks'], 
                #             #number_tasks_per_node=dictionary['workload_manager']['number_tasks_per_node'], 
                #             time=dictionary['workload_manager']['time_minutes'], 
                #             mem_per_core=dictionary['workload_manager']['mem_per_core'], 
                #             manager_name=dictionary['workload_manager']['manager_name'], 
                #             number_worker_array=dictionary['workload_manager']['number_worker_array'], 
                #             cores_per_worker=dictionary['workload_manager']['cores_per_worker'], 
                #             worker_timeout=dictionary['workload_manager']['worker_timeout_seconds'],
                #             cwd=cwd)
                #             # qos_group=dictionary['workload_manager']['qos_group'])

                subdir_list = []
                for item in files_list:
                    subdir = os.path.basename(os.path.dirname(item))
                    subdir_list.append(subdir)
                subdir_list = list(set(subdir_list))

                write_file_list(subdir_list)
                
                jx_dict = {
                    "rules": [
                                {
                                    "command" : timeout + command.replace('${FILE}', file).replace('${SEG_MODEL_PATH}', seg_model_name).replace('${DET_MODEL_PATH}', det_model_name).replace('${PLANT_NAME}', file),
                                    "outputs" : [out.replace('$PLANT_NAME', file) for out in outputs],
                                    "inputs"  : [input.replace('$PLANT_NAME', file) for input in inputs if os.path.isdir(input.replace('$PLANT_NAME', file))]
                                                # [container, 
                                                # seg_model_name, 
                                                # det_model_name] + 

                                } for file in  subdir_list
                            ]
                } 

            # This the one for 3D
            else: 
                jx_dict = {
                    "rules": [
                                {
                                    "command" : timeout + command.replace('${FILE}', file).replace('${PLANT_PATH}', os.path.dirname(file)).replace('${SEG_MODEL_PATH}', seg_model_name).replace('${PLANT_NAME}', os.path.basename(os.path.dirname(file))).replace('${DET_MODEL_PATH}', det_model_name).replace('${SUBDIR}', os.path.basename(os.path.dirname(file))).replace('${DATE}', date)\
                                                .replace('${INPUT_DIR}', os.path.dirname(file)),
                                    "outputs" : [out.replace('$UUID', '_'.join(os.path.basename(file).split('_')[:2])).replace('$PLANT_NAME', os.path.basename(os.path.dirname(file))).replace('$SUBDIR', os.path.join(os.path.basename(os.path.dirname(file)), os.path.basename(file))).replace('${DATE}', date).replace('$BASENAME', os.path.basename(os.path.dirname(file))) for out in outputs],
                                    "inputs"  : [input.replace('$PLANT_NAME', os.path.basename(os.path.dirname(file))).replace('$SUBDIR', os.path.join(os.path.basename(os.path.dirname(file)), os.path.basename(file))).replace('${DATE}', date)\
                                                                        .replace('$FILE', file).replace('$BASENAME', os.path.basename(os.path.dirname(file))) for input in inputs]
                                                # [container, 
                                                # seg_model_name, 
                                                # det_model_name] + 

                                } for file in  files_list
                            ]
                } 
        if sensor == 'ps2Top':
                files_list = [item for item in files_list if not 'rawData0101' in item]
                jx_dict = {
                    "rules": [
                                {
                                    "command" : timeout + command\
                                        .replace('${FILE}', file)\
                                        .replace('${M_DATA_FILE}', file.replace(file[-15:], 'metadata.json'))\
                                        .replace('${FILE_DIR}', os.path.dirname(file))\
                                        .replace('${UUID}', os.path.basename(file).replace('.tif', ''))\
                                        .replace('${DATE}', date),

                                    "outputs" : [out\
                                        .replace('$FILE_BASE', os.path.basename(file).replace('.bin', ''))\
                                        .replace('$SEG', os.path.basename(file).replace('.tif', '_segmentation.csv'))\
                                        .replace('$UUID', os.path.basename(file).replace('.tif', ''))\
                                        .replace('$FILE', file)\
                                        .replace('$DATE', date)\
                                         for out in outputs],

                                    "inputs"  : [container, 
                                                seg_model_name, 
                                                det_model_name] + [input\
                                                    .replace('$FILE', file)\
                                                    .replace('$UUID', os.path.basename(file).replace('.tif', ''))\
                                                    .replace('$M_DATA_FILE', file.replace(file[-15:], 'metadata.json'))\
                                                    .replace('$FILE_DIR', os.path.dirname(file))\
                                                        for input in inputs]
                                } for file in  files_list
                            ]
                }                                                       

        elif (sensor == 'stereoTop') or (sensor == 'flirIrCamera'):

            jx_dict = {
                'rules': [
                            {
                                "command": timeout + command.replace('${FILE}', file).replace('${UUID}', os.path.join(os.path.dirname(file), os.path.basename(file).split("_")[0])).replace('${DATE}', date).replace('${FLIR_META}', file.replace('ir.bin', 'metadata.json')),
                                "outputs": [out.replace('$FILE_BASE', os.path.basename(file).split('.')[0]).replace('$DATE', date).replace('$FLIR_TIF', file.replace('.bin', '.tif')) for out in outputs],
                                "inputs": [container, seg_model_name, det_model_name] + [input.replace('$FILE', file).replace('$UUID', os.path.join(os.path.dirname(file), os.path.basename(file).split("_")[0])).replace('$FLIR_META', file.replace('ir.bin', 'metadata.json')) for input in inputs]
                            } for file in files_list
                        ]
            }


        else: 
            jx_dict = {
                "rules": [
                            {
                                "command" : timeout + command.replace('${FILE}', file).replace('${PLANT_PATH}', os.path.dirname(file)).replace('${SEG_MODEL_PATH}', seg_model_name).replace('${PLANT_NAME}', os.path.basename(os.path.dirname(file))).replace('${DET_MODEL_PATH}', det_model_name).replace('${SUBDIR}', os.path.basename(os.path.dirname(file))).replace('${DATE}', date).replace('${INPUT_DIR}', os.path.dirname(file)),
                                "outputs" : [out.replace('$UUID', '_'.join(os.path.basename(file).split('_')[:2])).replace('$PLANT_NAME', os.path.basename(os.path.dirname(file))).replace('$SUBDIR', os.path.join(os.path.basename(os.path.dirname(file)), os.path.basename(file))).replace('${DATE}', date).replace('$BASENAME', os.path.basename(os.path.dirname(file)))  for out in outputs],
                                "inputs"  : [input.replace('$PLANT_NAME', os.path.basename(os.path.dirname(file))).replace('$SUBDIR', os.path.join(os.path.basename(os.path.dirname(file)), os.path.basename(file))).replace('${DATE}', date).replace('$FILE', file).replace('$BASENAME', os.path.basename(os.path.dirname(file)))  for input in inputs]
                                            # [file, 
                                            #  container, 
                                            #  seg_model_name, 
                                            #  det_model_name] + 

                            } for file in  files_list
                        ]
            } 

    else: 
        print('No inputs specified. Assuming local.')
        jx_dict = {
            "rules": [
                        {
                                "command" : timeout + command.replace('${FILE}', file).replace('${PLANT_PATH}', os.path.dirname(file)).replace('${SEG_MODEL_PATH}', seg_model_name).replace('${PLANT_NAME}', os.path.basename(os.path.dirname(file))).replace('${DET_MODEL_PATH}', det_model_name).replace('${SUBDIR}', os.path.basename(os.path.dirname(file))).replace('${DATE}', date).replace('${INPUT_DIR}', os.path.dirname(file)),
                                "outputs" : [out.replace('$PLANT_NAME', os.path.basename(os.path.dirname(file))).replace('$SUBDIR', os.path.join(os.path.basename(os.path.dirname(file)), os.path.basename(file))).replace('${DATE}', date).replace('$BASENAME', os.path.basename(os.path.dirname(file))) for out in outputs],
                                "inputs"  : [seg_model_name,
                                             det_model_name]
                                            #[file, 
                                            #container, 
                                            #seg_model_name, 
                                            #det_model_name]

                        } for file in  files_list
                    ]
        } 

    ### Nathan was here...
    #    Sorry this on got away from me
    #    Heres the general idea of what's in the substitutions dictionary...
    #
    #    'STRING THAT IS REPLACED' : [ evaluated variable name, function to manipulate it ] 
    #
    #    Then we loop through each jx_dict -> "rules" (i.e. command, outputs, inputs) and replace stuff.
    substitutions = {
            '{{$FILE_BASE}}' : ['_f', lambda x: os.path.splitext(os.path.basename(x))[0]],
                             # _f is the file from files_list 
    }


    def do_replacement(substitutions, original_string):
        for match_string, _v in substitutions.items():
            eval_var  = eval(_v[0])
            lfunction = _v[1]
            replacement_string = lfunction(eval_var)
            return original_string.replace(match_string, replacement_string)

    _d = jx_dict['rules']
    for idx, _f in enumerate(files_list):
        for rule_section, entry in _d[idx].items():
            # [rule_section] can be a string or a list, so we have to deal with that...
            if type(entry) is list:
                for _eidx, e in enumerate(entry):
                    #_d[idx][rule_section][_eidx] = do_replacement(substitutions, e)
                    for match_string, _v in substitutions.items():
                        eval_var  = eval(_v[0])
                        lfunction = _v[1]
                        replacement_string = lfunction(eval_var)
                        _d[idx][rule_section][_eidx] = e.replace(match_string, replacement_string)
            else:
                #_d[idx][rule_section] = do_replacement(substitutions, entry)
                for match_string, _v in substitutions.items():
                    eval_var  = eval(_v[0])
                    lfunction = _v[1]
                    replacement_string = lfunction(eval_var)
                    _d[idx][rule_section] = entry.replace(match_string, replacement_string)
    ### ...end Nathan was here.

    with open(json_out_path, 'w') as convert_file:
        convert_file.write(json.dumps(jx_dict))


    #print("BREAK: At end of generate_makeflow_json()")
    #pdb.set_trace()
    return json_out_path


# --------------------------------------------------
def run_jx2json(json_out_path, cctools_path, batch_type, manager_name, cwd, retries=3, port=0, out_log='dall.log'):
    '''
    Create a JSON file for Makeflow distributed computing framework. 

    Input: 
        - json_out_path: Path to the JSON file containing inputs
        - cctools_path: Path to local installation of CCTools

    Output: 
        - Running workflow
    '''

    args = get_args()

    if args.module_breakpoints:
        pdb.set_trace()

    cores_max = int(multiprocessing.cpu_count()*args.local_cores)
    home = os.path.expanduser('~')
    cctools = os.path.join(home, cctools_path, 'bin', 'makeflow')
    cctools = os.path.join(home, cctools)
    arguments = f'-T {batch_type} --json {json_out_path} -a -N {manager_name} -M {manager_name} --local-cores {cores_max} -r {retries} -p {port} -dall -o {out_log} --skip-file-check' #--disable-cache $@'

    if args.shared_file_system:
        arguments = f'-T {batch_type} --json {json_out_path} -a --shared-fs {cwd} -X {cwd} -N {manager_name} -M {manager_name} --local-cores {cores_max} -r {retries} -p {port} -dall -o {out_log} --skip-file-check' #--disable-cache $@' 
    
    cmd1 = ' '.join([cctools, arguments])
    sp.call(cmd1, shell=True)


# --------------------------------------------------
def tar_outputs(scan_date, yaml_dictionary):
    '''
    Bundles outputs for upload to the CyVerse DataStore.

    Input:
        - scan_date: Date of the scan
        - yaml_dictionary: Dictionary variable (YAML file)
    
    Output: 
        - Tar files containing all output data
    '''
    cwd = os.getcwd()

    for item in yaml_dictionary['paths']['pipeline_outpath']:
        if os.path.isdir(item):
            os.chdir(item)

        outdir = item
        
        if not os.path.isdir(os.path.join(cwd, scan_date, outdir)):
            os.makedirs(os.path.join(cwd, scan_date, outdir))

        for v in yaml_dictionary['paths']['outpath_subdirs']:

            _full_v = os.path.join(cwd, outdir, v)

            if not os.path.isdir(_full_v):
                print(f"Skipping the tarring of '{_full_v}' from yaml paths:outpath_subdirs because it was not found")
                continue
            # if v == 'plant_reports':
            #     # This is a hack created by Nathan.
            #     src_dir = os.path.join(cwd, outdir, v)
            #     dest_dir = os.path.join(cwd, scan_date, outdir, v)
            #     print(f"Copying plant_reports")
            #     shutil.copytree(src_dir, dest_dir)
            # else:
            file_path = os.path.join(cwd, scan_date, outdir, f'{scan_date}_{v}.tar') 
            print(f'Creating {file_path}.')
            if not os.path.isfile(file_path):
                with tarfile.open(file_path, 'w') as tar:
                    tar.add(v, recursive=True)

    os.chdir(cwd)


# --------------------------------------------------
def create_pipeline_logs(scan_date):
    '''
    Moves all Makeflow/Workqueue logs to the <scan_date>/logs directory. Will be uploaded to CyVerse.

    Input:
        - scan_date: Date of the scan
    
    Output: 
        - Makeflow/Workqueue logs in the <scan_date>/logs directory
    '''
    args = get_args()
    cwd = os.getcwd()

    if not os.path.isdir(os.path.join(cwd, scan_date, 'logs')):
        os.makedirs(os.path.join(cwd, scan_date, 'logs'))

    for item in glob.glob('./*.json*'):
        shutil.move(item, os.path.join(cwd, scan_date, 'logs', item))
    
    if os.path.isfile(os.path.join(cwd, args.yaml)):
        shutil.copy(os.path.join(cwd, args.yaml), os.path.join(cwd, scan_date, 'logs', 'processing_instructions.yaml'))

    for log in glob.glob('./*dall*'):
        shutil.move(log, os.path.join(cwd, scan_date, 'logs', log))

    if os.path.isfile('geo_correction_config.txt'):
        shutil.move('geo_correction_config.txt', os.path.join(cwd, scan_date, 'logs', 'geo_correction_config.txt'))



# --------------------------------------------------
def get_irods_data_path(yaml_dictionary):

    args= get_args()
    #root = yaml_dictionary['paths']['cyverse']['output']['basename']
    #subdir = yaml_dictionary['paths']['cyverse']['output']['subdir']

    #season_name = yaml_dictionary['tags']['season_name']
    season_name = get_season_name()
    experiment  = args.experiment
    sensor      = yaml_dictionary['tags']['sensor']
    cyverse_basename  = yaml_dictionary['paths']['cyverse']['basename']
    cyverse_datalevel = yaml_dictionary['paths']['cyverse']['output']['level']

    # Every path (level zero or otherwise) starts the same:
    # .../phytooracle/season_11_sorghum_yr_2020/level_0/scanner3DTop
    irods_output_path = os.path.join(
            cyverse_basename,
            season_name,
            cyverse_datalevel,
            sensor)

    # If level is greater than level zero, then we need to add
    # two directories: .../experiment/date
    # for example: level_1/scanner3DTop/sunflower/2222-22-22
    # but we only add experiment if it exists in YAML
    if cyverse_datalevel > 'level_0':
        irods_output_path = os.path.join(
                                         irods_output_path,
                                         (experiment if experiment else "")
        )

    return irods_output_path


# --------------------------------------------------
def upload_outputs(date, yaml_dictionary):
    '''
    Uploads bundled data to the CyVerse path ('paths/cyverse/output/basename' value) specified in the YAML file.

    Input:
        - date: Date of the scan
        - yaml_dictionary: Dictionary variable (YAML file)
    
    Output: 
        - Uploaded data on CyVerse DataStore
    '''  
    args= get_args()

    irods_output_path = get_irods_data_path(yaml_dictionary)
    
    cwd = os.getcwd()

    if args.hpc: 
        print(':: Using data transfer node.')
        sp.call(f"ssh filexfer 'cd {cwd}' '&& imkdir -p {irods_output_path}' '&& icd {irods_output_path}' '&& iput -rfKPVT {date}' '&& exit'", shell=True)

    else:
        
        cmd1 = f'imkdir -p {irods_output_path}'
        sp.call(cmd1, shell=True)

        cmd2 = f'icd {irods_output_path}'
        sp.call(cmd2, shell=True)

        cmd3 = f'iput -rfKPVT {date}'
        sp.call(cmd3, shell=True)


# --------------------------------------------------
def clean_directory():
    '''
    Cleans directory from distributed pipeline output logs and files lists.

    Input:
        - NA
    
    Output: 
        - Clean working directory
    '''
    
    if os.path.isfile("file.txt"):
        os.remove("file.txt")

    dir_list = glob.glob('./makeflow.failed*')

    if dir_list:
        for direc in dir_list:
            shutil.rmtree(direc)

    worker_list = glob.glob('./worker-*')
    if worker_list:
        for worker in worker_list:
            shutil.rmtree(worker)


# --------------------------------------------------
def clean_inputs(date, yaml_dictionary):
    '''
    Cleans directory from distributed pipeline input directories and files.

    Input:
        - NA
    
    Output: 
        - Clean working directory
    '''
    if os.path.isdir('preprocessing'):
        shutil.rmtree('preprocessing')
    
    if os.path.isdir('alignment'):
        shutil.rmtree('alignment')

    if os.path.isdir('individual_plants_out'):
        shutil.rmtree('individual_plants_out')

    if os.path.isdir('postprocessing_out'):
        shutil.rmtree('postprocessing_out')

    if os.path.isdir('segmentation_pointclouds'):
        shutil.rmtree('segmentation_pointclouds')

    if os.path.isfile('transfromation.json'):
        os.remove('transfromation.json')

    if os.path.isfile('mosaic.vrt'):
        os.remove('mosaic.vrt')

    if os.path.isfile('my.vrt'):
        os.remove('my.vrt')

    if os.path.isdir('bundle'):
        shutil.rmtree('bundle')

    if os.path.isfile('bundle_list.json'):
        os.remove('bundle_list.json')
        
    if os.path.isdir('edited_tifs'):
        shutil.rmtree('edited_tifs', ignore_errors=True)

    if os.path.isdir('image_stiching'):
        shutil.rmtree('image_stiching', ignore_errors=True)

    if os.path.isdir('img_coords_out'):
        shutil.rmtree('img_coords_out', ignore_errors=True)

    if os.path.isdir('plotclip_orthos'):
        shutil.rmtree('plotclip_orthos', ignore_errors=True)

    if os.path.isdir('plotclip_out'):
        shutil.rmtree('plotclip_out', ignore_errors=True)

    if os.path.isdir('detect_out'):
        shutil.rmtree('detect_out', ignore_errors=True)

    if os.path.isdir('bin2tif_out'):
        shutil.rmtree('bin2tif_out', ignore_errors=True)

    if os.path.isdir(date):
        shutil.rmtree(date, ignore_errors=True)

    if os.path.isdir('scanner3DTop'):
        shutil.rmtree('scanner3DTop')

    if len(glob.glob(f'scanner3DTop-{date}*')) > 0:

        for item in glob.glob(f'scanner3DTop-{date}*'):
            if os.path.isdir(item):
                shutil.rmtree(item)

            if os.path.isfile(item):
                os.remove(item)


    if len(glob.glob(f'stereoTop-{date}*')) > 0:

        for item in glob.glob(f'stereoTop-{date}*'):
            if os.path.isdir(item):
                shutil.rmtree(item)

            if os.path.isfile(item):
                os.remove(item)

    if len(glob.glob(f'flirIrCamera-{date}*')) > 0:
        
        for item in glob.glob(f'flirIrCamera-{date}*'):
            if os.path.isdir(item):
                shutil.rmtree(item)

            if os.path.isfile(item):
                os.remove(item)

    if len(glob.glob(f'ps2Top-{date}*')) > 0:
        
        for item in glob.glob(f'ps2Top-{date}*'):
            if os.path.isdir(item):
                shutil.rmtree(item)

            if os.path.isfile(item):
                os.remove(item)

    for item in yaml_dictionary['paths']['pipeline_outpath']:
        if item == '.':
            for x in yaml_dictionary["paths"]["outpath_subdirs"]:
                if os.path.isdir(x):
                    shutil.rmtree(x, ignore_errors=True)

        elif os.path.isdir(item):
            shutil.rmtree(item)

    slurm_list = glob.glob('./slurm-*')
    if slurm_list:
        for slurm in slurm_list:
            os.remove(slurm)
    
    wq_list = glob.glob('./wq-pool-*')
    if wq_list:
        for wq in wq_list:
            shutil.rmtree(wq)
    
    if os.path.isfile('worker.sh'):
        os.remove('worker.sh')
        
    if os.path.isfile('worker_priority.sh'):
        os.remove('worker_priority.sh')

    if os.path.isfile(f"upload.sh"):
        os.remove(f"upload.sh")

    if len(glob.glob('*.tar')) > 0:
        
        for item in glob.glob('*.tar'):
            if os.path.isdir(item):
                shutil.rmtree(item)

            if os.path.isfile(item):
                os.remove(item)

    if len(glob.glob('*.tar.gz')) > 0:
        
        for item in glob.glob('*.tar.gz'):
            if os.path.isdir(item):
                shutil.rmtree(item)

            if os.path.isfile(item):
                os.remove(item)

# --------------------------------------------------
def return_date_list(level_0_list):
    args= get_args()
    date_list = []
    for item in level_0_list:
        try:
            
            if args.experiment:
                match = re.search(r'\d{4}-\d{2}-\d{2}__\d{2}-\d{2}-\d{2}-\d{3}', item)
            else:
                match = re.search(r'\d{4}-\d{2}-\d{2}', item)

            if match:
                if args.experiment:
                    date = str(match.group())
                    date = '_'.join([date, args.experiment])
                else:
                    date = str(datetime.strptime(match.group(), '%Y-%m-%d').date())
                
                date_list.append(date)
        except:
            pass
            
    return date_list


# --------------------------------------------------
def get_process_date_list(yaml_dictionary):

    args= get_args()
    basename = yaml_dictionary['paths']['cyverse']['basename']
    input_level = yaml_dictionary['paths']['cyverse']['input']['level']

    try:
        pre, input_num = input_level.split('_')
        output_level = '_'.join([pre, str(int(input_num) + 1)])

    except ValueError:
        print('Error')
    
    input_path = os.path.join(basename, yaml_dictionary['tags']['season_name'], input_level, yaml_dictionary['tags']['sensor'])

    if args.experiment:
        output_path = os.path.join(basename, yaml_dictionary['tags']['season_name'], output_level, yaml_dictionary['tags']['sensor'], args.experiment)
     
        if int(str(yaml_dictionary['paths']['cyverse']['input']['level']).split('_')[1]) >= 1:

            input_path = os.path.join(basename, yaml_dictionary['tags']['season_name'], input_level, yaml_dictionary['tags']['sensor'], args.experiment)
    
    else:
        output_path = os.path.join(basename, yaml_dictionary['tags']['season_name'], output_level, yaml_dictionary['tags']['sensor'])
    
    level_0_list, level_1_list = [os.path.splitext(os.path.basename(item))[0].lstrip() for item in [line.rstrip() for line in os.popen(f'ils {input_path}').readlines()][1:]] \
                                ,[os.path.splitext(os.path.basename(item))[0].lstrip() for item in [line.rstrip() for line in os.popen(f'ils {output_path}').readlines()][1:]]
    
    if args.experiment:

        level_0_list = [item for item in level_0_list if args.experiment in item]
        level_1_list = [item for item in level_1_list if args.experiment in item]
    
    level_0_dates, level_1_dates = return_date_list(level_0_list) \
                                , return_date_list(level_1_list) 

    process_list = np.setdiff1d(level_0_dates, level_1_dates)

    if args.reverse:
        process_list = process_list.tolist()
        process_list.reverse()
        
    return process_list


# --------------------------------------------------
def slack_notification(message, date):

    sensor = yaml_dictionary['tags']['sensor']
    if 'slack_notifications' in yaml_dictionary['tags'].keys():
        
        if yaml_dictionary['tags']['slack_notifications']['use']==True:

            simg = yaml_dictionary['tags']['slack_notifications']['container']['simg_name']
            dockerhub_path = yaml_dictionary['tags']['slack_notifications']['container']['dockerhub_path']
            channel = yaml_dictionary['tags']['slack_notifications']['channel']
            season = ''.join(['Season', str(yaml_dictionary['tags']['season'])])
            user = os.environ['LOGNAME']
            host_name = socket.gethostname()
            user_host = '@'.join([user, host_name])

            description = ''.join(['[', ' '.join([season, sensor, date, user_host]), ']'])
            
            message = ' | '.join([description, message])

            if not os.path.isfile(simg):
                print(f'Building {simg}.')
                sp.call(f"singularity build {simg} {dockerhub_path}", shell=True)
            print('Sending message.')
            sp.call(f'singularity run {simg} -m "{message}" -c "{channel}"', shell=True)


# --------------------------------------------------
def create_mf_monitor(cctools_path, outfile='./shell_scripts/mf_monitor.sh'):

    with open(outfile, 'w') as fh:
                fh.writelines("#!/bin/bash\n")
                fh.writelines("export CCTOOLS_HOME=${HOME}/"+f"{cctools_path}\n")
                fh.writelines("export PATH=${CCTOOLS_HOME}/bin:$PATH\n")
                fh.writelines("makeflow_monitor wf_file_${1}.json.makeflowlog")
    

# --------------------------------------------------
def create_wq_status(cctools_path, outfile='./shell_scripts/wq_status.sh'):

    with open(outfile, 'w') as fh:
                fh.writelines("#!/bin/bash\n")
                fh.writelines("export CCTOOLS_HOME=${HOME}/"+f"{cctools_path}\n")
                fh.writelines("export PATH=${CCTOOLS_HOME}/bin:$PATH\n")
                fh.writelines("watch -n 1 work_queue_status")


# --------------------------------------------------
def move_outputs(scan_date, yaml_dictionary):

    print('Moving outputs')
    cwd = os.getcwd()
    temp_path = yaml_dictionary['paths']['cyverse']['upload_directories']['temp_directory']
    dir_list = yaml_dictionary['paths']['cyverse']['upload_directories']['directories_to_move']
    pipeline_out_path = yaml_dictionary['paths']['pipeline_outpath']

    for out_path in pipeline_out_path:

        for item in dir_list:

            if os.path.isdir(os.path.join(cwd, out_path, item)):
            
                if not os.path.isdir(os.path.join(cwd, scan_date)):
                    os.makedirs(os.path.join(cwd, scan_date))
                
                shutil.move(os.path.join(cwd, out_path, item), os.path.join(cwd, scan_date, out_path))

                if not os.path.isdir(os.path.join(temp_path, scan_date, out_path)):
                    os.makedirs(os.path.join(temp_path, scan_date, out_path))

                if os.path.isdir(os.path.join(temp_path, scan_date)):
                    if not os.path.isdir(os.path.join(temp_path, 'previously_processed')):
                        os.makedirs(os.path.join(temp_path, 'previously_processed'))
                    shutil.move(os.path.join(temp_path, scan_date), os.path.join(temp_path, 'previously_processed'))

                shutil.move(os.path.join(cwd, scan_date, out_path, item), os.path.join(temp_path, scan_date, out_path))


# --------------------------------------------------
def handle_date_failure(args, date, yaml_dictionary):
    user = os.environ['LOGNAME']
    slack_notification(message=f"PIPELINE ERROR. Stopping now.", date=date)
    if not args.noclean:
        slack_notification(message=f"PIPELINE ERROR. Cleaning inputs.", date=date)
        print(f"Cleaning directory")
        clean_directory()
        clean_inputs(date, yaml_dictionary)  
        slack_notification(message=f"PIPELINE ERROR. Cleaning inputs complete.", date=date)

    kill_workers('_'.join([yaml_dictionary['workload_manager']['job_name'], user]))
    

# --------------------------------------------------
def generate_megastitch_config(cwd, yaml_dictionary):
    
    lid_model_path = yaml_dictionary['paths']['models']['lid']
    outpath = os.path.join(cwd, 'geo_correction_config.txt')
    sensor = yaml_dictionary["tags"]["sensor"]
   
    if sensor == 'flirIrCamera':
        with open(outpath, 'w') as f:

            f.write('METHOD:TransformationOnly\n')
            f.write(f'NO_CORES:{int(multiprocessing.cpu_count()*0.20)}\n')
            f.write(f'NO_CORES_MAX:{int(multiprocessing.cpu_count()*0.70)}\n')
            f.write('SCALE:0.2\n')
            f.write('HEIGHT_RATIO_FOR_ROW_SEPARATION:0.1\n')
            f.write('PERCENTAGE_OF_GOOD_MATCHES:0.5\n')
            f.write('MINIMUM_PERCENTAGE_OF_INLIERS:0.1\n')
            f.write('MINIMUM_NUMBER_OF_MATCHES:15\n')
            f.write('RANSAC_MAX_ITER:1000\n')
            f.write('RANSAC_ERROR_THRESHOLD:5\n')
            f.write('PERCENTAGE_NEXT_NEIGHBOR_FOR_MATCHES:0.8\n')
            f.write('OVERLAP_DISCARD_RATIO:0.05\n')
            f.write('TRANSFORMATION_SCALE_DISCARD_THRESHOLD:0.03\n')
            f.write('TRANSFORMATION_ANGLE_DISCARD_THRESHOLD:4\n')
            f.write('LETTUCE_AREA_THRESHOLD:5000\n')
            f.write('CONTOUR_MATCHING_MIN_MATCH:2\n')
            f.write('ORTHO_SCALE:0.05\n')
            f.write('OPEN_MORPH_LID_SIZE:40\n')
            f.write('CLOSE_MORPH_LID_SIZE:220\n')
            f.write('FFT_PARALLEL_CORES_TO_USE:20\n')
            f.write('use_camera:Left\n')
            f.write('override_sifts:True\n')
            f.write('number_of_rows_in_groups:12\n')
            f.write('is_single_group:True\n')
            f.write('Initial_Size:3296,2472\n')
            f.write('LID_SIZE_MIN_MAX:170,230\n')
            f.write('LID_METHOD:FLIR\n')
            f.write('circle_error:30\n')
            f.write('lid_search_surrounding_patch_number:0\n')
            f.write('TRANSFORMATION_ERR_STD:9.32e-6,10.56e-6\n')
            f.write('GPS_ERR_STD:9.02e-6,10.48e-6\n')
            f.write('LID_ERR_STD:1e-9\n')
            f.write(f'LID_MODEL_PATH:{os.path.join(cwd, os.path.basename(lid_model_path))}\n')
            f.write('SAVE_COORDS_ON_CSV:True\n')
            f.write('SAVE_NEW_TIFF_FILES:False\n')
    else:
        with open(outpath, 'w') as f:

            f.write('METHOD:TransformationOnly\n')
            f.write(f'NO_CORES:{int(multiprocessing.cpu_count()*0.20)}\n')
            f.write(f'NO_CORES_MAX:{int(multiprocessing.cpu_count()*0.70)}\n')
            f.write('SCALE:0.2\n')
            f.write('HEIGHT_RATIO_FOR_ROW_SEPARATION:0.1\n')
            f.write('PERCENTAGE_OF_GOOD_MATCHES:0.5\n')
            f.write('MINIMUM_PERCENTAGE_OF_INLIERS:0.1\n')
            f.write('MINIMUM_NUMBER_OF_MATCHES:15\n')
            f.write('RANSAC_MAX_ITER:1000\n')
            f.write('RANSAC_ERROR_THRESHOLD:5\n')
            f.write('PERCENTAGE_NEXT_NEIGHBOR_FOR_MATCHES:0.8\n')
            f.write('OVERLAP_DISCARD_RATIO:0.05\n')
            f.write('TRANSFORMATION_SCALE_DISCARD_THRESHOLD:0.03\n')
            f.write('TRANSFORMATION_ANGLE_DISCARD_THRESHOLD:4\n')
            f.write('LETTUCE_AREA_THRESHOLD:5000\n')
            f.write('CONTOUR_MATCHING_MIN_MATCH:2\n')
            f.write('ORTHO_SCALE:0.05\n')
            f.write('OPEN_MORPH_LID_SIZE:40\n')
            f.write('CLOSE_MORPH_LID_SIZE:220\n')
            f.write('FFT_PARALLEL_CORES_TO_USE:20\n')
            f.write('use_camera:Left\n')
            f.write('override_sifts:True\n')
            f.write('number_of_rows_in_groups:12\n')
            f.write('is_single_group:True\n')
            f.write('Initial_Size:3296,2472\n')
            f.write('LID_SIZE_MIN_MAX:170,230\n')
            f.write('LID_METHOD:ML\n')
            f.write('circle_error:30\n')
            f.write('lid_search_surrounding_patch_number:0\n')
            f.write('TRANSFORMATION_ERR_STD:9.32e-6,10.56e-6\n')
            f.write('GPS_ERR_STD:9.02e-6,10.48e-6\n')
            f.write('LID_ERR_STD:1e-9\n')
            f.write(f'LID_MODEL_PATH:{os.path.join(cwd, os.path.basename(lid_model_path))}\n')
            f.write('SAVE_COORDS_ON_CSV:True\n')
            f.write('SAVE_NEW_TIFF_FILES:False\n')     


# --------------------------------------------------
def download_packages():
    """
    Installs Python packages required by POA.
    """
    sp.call(f'{sys.executable} -m pip install --user pyyaml requests')

# --------------------------------------------------
def main():
    """Run distributed data processing here"""
    user = os.environ['LOGNAME']
    args = get_args()
    cctools_path = download_cctools(cctools_version=args.cctools_version)
    create_mf_monitor(cctools_path)
    create_wq_status(cctools_path)
    download_packages()
    cwd = os.getcwd()


    with open(args.yaml, 'r') as stream:
        global original_yaml_dictionary
        original_yaml_dictionary = yaml.safe_load(stream)

    if "workload_manager_yaml" in args:
        if args.workload_manager_yaml is not None:
            with open(args.workload_manager_yaml, 'r') as stream:
                workload_managaer_dictionary = yaml.safe_load(stream)
            original_yaml_dictionary['workload_manager'] = workload_managaer_dictionary['workload_manager']

    if not args.date:
        args.date = get_process_date_list(original_yaml_dictionary)

    for date in args.date:
        
        os.chdir(cwd)
        
        try:
            global yaml_dictionary
            if 'pre_parse_yaml' not in original_yaml_dictionary['tags'].keys():
                yaml_dictionary = original_yaml_dictionary
            elif original_yaml_dictionary['tags']['pre_parse_yaml']:
                import yaml_preprocessor as yamlpre
                yaml_dictionary = yamlpre.preprocess_yaml_file(yaml_path = args.yaml,
                                                    date      = date,
                                                    args      = args
                )
            else:
                yaml_dictionary = original_yaml_dictionary

            slack_notification(message=f"Starting data processing.", date=date)

            build_containers(yaml_dictionary)
            
            sensor = yaml_dictionary["tags"]["sensor"]
   
            if (sensor == "stereoTop") or (sensor == 'flirIrCamera'):
                generate_megastitch_config(cwd, yaml_dictionary)

            if args.uploadonly:
                upload_outputs(date, yaml_dictionary)
                return
            if args.archiveonly:
                tar_outputs(date, yaml_dictionary)
                return
            
            server_utils.hpc = args.hpc
                
            ###############################################
            # Figure out what we need to DL
            # There are three scenarios...
            # (1) No input_dir.  Use suffix and prefix.  Original method.
            # (2) input_dir, but not suffix or prefix: DL all files from input_dir
            # (3) both...  add input_dir to irods_path and continue as (1)

            slack_notification(message=f"Downloading raw data.", date=date)
            yaml_input_keys = yaml_dictionary['paths']['cyverse']['input'].keys()

            # figure out if yaml has prefix and/or sufix keys...
            cyverse_datalevel = yaml_dictionary['paths']['cyverse']['input']['level']
            irods_sensor_path = build_irods_path_to_sensor_from_yaml(yaml_dictionary, args)
            if len(set(['prefix', 'suffix']).intersection(yaml_input_keys)) > 0:
                print("Found prefix or suffix.  Building irods_path...")
                irods_dl_dir = irods_sensor_path
                print(irods_dl_dir)
                if 'input_dir' in yaml_input_keys:
                    _dir = yaml_dictionary['paths']['cyverse']['input']['input_dir']
                    irods_dl_dir = os.path.join(irods_dl_dir, date, _dir)
                    print(f"Adding input_dir ({_dir}) to irods_dl_dir...")
                    print(irods_dl_dir)
                file_to_dl = find_matching_file_in_irods_dir(yaml_dictionary, date, args, irods_dl_dir)

                if file_to_dl is None:
                    handle_date_failure(args, date, yaml_dictionary)
                    continue
                dir_name = download_irods_input_file(file_to_dl)
            elif 'input_dir' in yaml_input_keys:
                print("Using input dir")
                dir_name = yaml_dictionary['paths']['cyverse']['input']['input_dir']
                if len(dir_name) < 1:
                    raise ValueError(f"input_dir shouldn't be empty.  Remove it.")

                download_irods_input_dir(yaml_dictionary, date, args)

            else:
                raise Exception(f"Couldn't figure out what to do with yaml input")

            get_support_files(yaml_dictionary=yaml_dictionary, date=date)
            slack_notification(message=f"Downloading raw data complete.", date=date)

            ###########################################################
            ### All files should be found, DL'd and unarchived by here.
            ###########################################################

            if args.hpc:
                kill_workers('_'.join([yaml_dictionary['workload_manager']['job_name'], user]))
          
                launch_workers(cctools_path = cctools_path,
                        account=yaml_dictionary['workload_manager']['account'], 
                        job_name='_'.join([yaml_dictionary['workload_manager']['job_name'], user]), 
                        nodes=yaml_dictionary['workload_manager']['nodes'], 
                        time=yaml_dictionary['workload_manager']['time_minutes'], 
                        mem_per_core=yaml_dictionary['workload_manager']['mem_per_core'], 
                        manager_name='_'.join([yaml_dictionary['workload_manager']['manager_name'], user]), 
                        number_worker_array=yaml_dictionary['workload_manager']['number_worker_array'], 
                        cores_per_worker=yaml_dictionary['workload_manager']['cores_per_worker'], 
                        worker_timeout=yaml_dictionary['workload_manager']['worker_timeout_seconds'], 
                        cwd=cwd)

            global seg_model_name, det_model_name
            seg_model_name, det_model_name = get_model_files(yaml_dictionary)

            for k, v in yaml_dictionary['modules'].items():
                
                if 'input_dir' in v.keys():
                    dir_name = os.path.join(*v['input_dir'])

                slack_notification(message=f"Processing step {k}/{len(yaml_dictionary['modules'])}.", date=date)

                files_list = get_file_list(dir_name, level=v['file_level'], match_string=v['input_file'])
                if len(files_list) < 1:
                    if v['distribution_level'] == 'local':
                        print("No input files specified.  Allowed to continue because distribution level is 'local'")
                    else:
                        raise ValueError(f"file_list for module #{k} is empty")
                    
                write_file_list(files_list)
                json_out_path = generate_makeflow_json(cctools_path=cctools_path, level=v['file_level'], files_list=files_list, command=v['command'], container=v['container']['simg_name'], inputs=v['inputs'], outputs=v['outputs'], date=date, sensor=yaml_dictionary['tags']['sensor'], yaml_dictionary=yaml_dictionary, json_out_path=f'wf_file_{k}.json')
                run_jx2json(json_out_path, cctools_path, batch_type=v['distribution_level'], manager_name='_'.join([yaml_dictionary['workload_manager']['manager_name'], user]), retries=yaml_dictionary['workload_manager']['retries'], port=yaml_dictionary['workload_manager']['port'], out_log=f'dall_{k}.log', cwd=cwd)

                if not args.noclean:
                    print(f"Cleaning directory")
                    clean_directory()

                slack_notification(message=f"Processing step {k}/{len(yaml_dictionary['modules'])} complete.", date=date)

            slack_notification(message=f"All processing steps complete.", date=date)
            kill_workers('_'.join([yaml_dictionary['workload_manager']['job_name'], user]))
            if not args.noupload:
                # Archive output directories
                slack_notification(message=f"Archiving data.", date=date)
                tar_outputs(date, yaml_dictionary)
                slack_notification(message=f"Archiving data complete.", date=date)


                # Upload data
                create_pipeline_logs(date)
                slack_notification(message=f"Uploading data.", date=date)
                upload_outputs(date, yaml_dictionary)
                slack_notification(message=f"Uploading data complete.", date=date)

                # # Move directories if specified in the processing YAML
                # if 'upload_directories' in yaml_dictionary['paths']['cyverse'].keys() and yaml_dictionary['paths']['cyverse']['upload_directories']['use']==True:
                    
                #     slack_notification(message=f"Move data to {yaml_dictionary['paths']['cyverse']['upload_directories']['temp_directory']}.", date=date)
                #     move_outputs(date, yaml_dictionary)
                #     slack_notification(message=f"Moving data complete.", date=date)

                if not args.noclean:
                    slack_notification(message=f"Cleaning inputs.", date=date)
                    print(f"Cleaning inputs")
                    clean_inputs(date, yaml_dictionary) 
                    slack_notification(message=f"Cleaning inputs complete.", date=date)

        except:
            os.chdir(cwd)
            create_pipeline_logs(date)
            handle_date_failure(args, date, yaml_dictionary)
#             slack_notification(message=f"SKIP SCAN. Raw data faulty, cannot be processed.", date=date)
#             slack_notification(message=f"SKIP SCAN. Cleaning inputs.", date=date)
#             print(f"Cleaning inputs")
#             clean_inputs(date, yaml_dictionary) 
#             slack_notification(message=f"SKIP SCAN. Cleaning inputs complete.", date=date)

# --------------------------------------------------
if __name__ == '__main__':
    main()
