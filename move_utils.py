from genericpath import isdir
import os
import sys
import shutil
import tarfile
import glob
import subprocess as sp

# --------------------------------------------------
def move_scan_date(scan_date):

    if not os.path.isdir('processed_scans'):
        os.makedirs('processed_scans')

    shutil.move(scan_date, 'processed_scans')

    if not os.path.isdir(scan_date):
        os.makedirs(scan_date)


# --------------------------------------------------
def tar_outputs(scan_date, dir_path, tag, outdir):
    
    cwd = os.getcwd()
    data_type = ['west', 'west_downsampled', 'east', 'east_downsampled', 'merged', 'merged_downsampled', 'metadata', 'combined_pointclouds', 'plant_reports']

    for d_type in data_type:
        
        if os.path.isdir(os.path.join(cwd, dir_path, d_type)):
            os.chdir(os.path.join(cwd, dir_path))

            if not os.path.isdir(os.path.join(cwd, scan_date, outdir)):
                os.makedirs(os.path.join(cwd, scan_date, outdir))

            file_path = os.path.join(cwd, scan_date, outdir, f'{scan_date}_{d_type}_{tag}.tar') 
            print(f'Creating {file_path}.')
            if not os.path.isfile(file_path):
                with tarfile.open(file_path, 'w') as tar:
                    tar.add(d_type, recursive=True)
    os.chdir(cwd)


# --------------------------------------------------
def create_pipeline_logs(scan_date, bundle=False):
    cwd = os.getcwd()

    if not os.path.isdir(os.path.join(cwd, scan_date, 'logs')):
        os.makedirs(os.path.join(cwd, scan_date, 'logs'))

    if os.path.isdir('sequential_alignment_out'):
        shutil.move('sequential_alignment_out/log.json', os.path.join(cwd, scan_date, 'logs/'))

    for item in glob.glob('./*.json*'):
        shutil.move(item, os.path.join(cwd, scan_date, 'logs', item))

    if bundle:
        if os.path.isdir('bundle'):
            shutil.move('bundle', os.path.join(cwd, scan_date, 'logs'))
    else:
        if os.path.exists(os.path.join(cwd, scan_date, 'logs', 'bundle_list.json')):
            os.remove(os.path.join(cwd, scan_date, 'logs', 'bundle_list.json'))


# --------------------------------------------------
def clean_directory(scan_date):

    if os.path.isdir(scan_date):
        shutil.rmtree(scan_date)

    if os.path.isdir(os.path.join('processed_scans', scan_date)):
        shutil.rmtree(os.path.join('processed_scans', scan_date))

    if os.path.isfile('clean.sh'):
        sp.call('./clean.sh', shell=True)