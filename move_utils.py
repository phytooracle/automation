import os
import sys
import shutil
import tarfile

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
    data_type = ['west', 'west_downsampled', 'east', 'east_downsampled', 'merged', 'merged_downsampled', 'metadata']
    # os.chdir(dir_path)

    for d_type in data_type:

        if os.path.isdir(os.path.join(cwd, dir_path, d_type)):

            if not os.path.isdir(os.path.join(cwd, scan_date, outdir)):
                os.makedirs(os.path.join(cwd, scan_date, outdir))

            file_path = os.path.join(cwd, scan_date, outdir, f'{scan_date}_{d_type}_{tag}.tar') 
            tar = tarfile.open(file_path, 'w')
            
            for item in os.listdir(os.path.join(cwd, dir_path, d_type)):
                print(os.path.join(cwd, dir_path, d_type, item))
                tar.add(item, recursive=True)
