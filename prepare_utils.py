#!/usr/bin/env python3
"""
Author : Emmanuel Gonzalez
Date   : 2021-10-18
Purpose: Generate raw data dictionary
"""

import argparse
import os
import sys
import re
from datetime import datetime
import json
import subprocess as sp

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
        # sp.call("export CCTOOLS_HOME=${HOME}/cctools-7.1.12-x86_64-centos7 && export PATH=${CCTOOLS_HOME}/bin:$PATH", shell=True)
        print(f'Download complete. CCTools version {cctools_version} is ready!')

    else:
        print('Required CCTools version already exists.')


# --------------------------------------------------
def run_workflow_1(season, sensor, season_dict):

    home = os.path.join(os.path.expanduser('~'), 'cctools-7.1.12-x86_64-centos7', 'bin/')
    sp.run(["sbatch", "worker_scripts/po_work_puma_slurm.sh"])

    for item in season_dict[season][sensor]['workflow_1']['commands']:
        cmd = ''.join([home, item])
        
        result = sp.run(cmd, stdout=sp.PIPE, shell=True)

        if result.returncode==0:
            continue
        else:
            sp.call(cmd, shell=True)
            # raise ValueError('Did not create Makeflow JSON file.')

    sp.run(["scancel", "--name=po_worker"])

    
# --------------------------------------------------
def run_intermediate(season, sensor, season_dict):
    for item in season_dict[season][sensor]['intermediate']['commands']:

        sp.call(item, shell=True)


# --------------------------------------------------
def run_workflow_2(season, sensor, season_dict):

    home = os.path.join(os.path.expanduser('~'), 'cctools-7.1.12-x86_64-centos7', 'bin/')

    sp.run(["ocelote", "&& sbatch worker_scripts/po_work_puma_slurm.sh"])
    sp.run(["elgato", "&& sbatch worker_scripts/po_work_puma_slurm.sh"])
    sp.run(["puma", "&& sbatch worker_scripts/po_work_puma_slurm.sh"])

    for item in season_dict[season][sensor]['workflow_2']['commands']:
        
        cmd = ''.join([home, item])
        
        result = sp.run(cmd, stdout=sp.PIPE, shell=True)

        if result.returncode==0:
            continue
        else:
            sp.call(cmd, shell=True)
            # raise ValueError('Did not create Makeflow JSON file.')

    sp.run(["ocelote", "&& scancel --name=po_worker"])
    sp.run(["elgato", "&& scancel --name=po_worker"])
    sp.run(["puma", "&& scancel --name=po_worker"])


# --------------------------------------------------
def run_workflow_3(season, sensor, season_dict):

    home = os.path.join(os.path.expanduser('~'), 'cctools-7.1.12-x86_64-centos7', 'bin/')
    sp.run(["ocelote", "&& sbatch worker_scripts/po_work_puma_slurm.sh"])
    sp.run(["elgato", "&& sbatch worker_scripts/po_work_puma_slurm.sh"])
    sp.run(["puma", "&& sbatch worker_scripts/po_work_puma_slurm.sh"])

    for item in season_dict[season][sensor]['workflow_3']['commands']:
        
        cmd = ''.join([home, item])
        
        result = sp.run(cmd, stdout=sp.PIPE, shell=True)

        if result.returncode==0:
            continue
        else:
            sp.call(cmd, shell=True)
            # raise ValueError('Did not create Makeflow JSON file.')

    sp.run(["ocelote", "&& scancel --name=po_worker"])
    sp.run(["elgato", "&& scancel --name=po_worker"])
    sp.run(["puma", "&& scancel --name=po_worker"])


# --------------------------------------------------
def get_tags(season_dict, season, sensor, wf):

    pipeline_out = season_dict[season][sensor][wf]['outputs']['pipeline_out']
    pipeline_tag = season_dict[season][sensor][wf]['outputs']['tag']
    processed_outdir = season_dict[season][sensor][wf]['outputs']['outdir']
   
    return pipeline_out, pipeline_tag, processed_outdir

