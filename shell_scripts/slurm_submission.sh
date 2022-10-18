#!/bin/bash -l
#SBATCH --account=dukepauli
#SBATCH --partition=standard
#SBATCH --job-name="phytooracle_manager"
#SBATCH --nodes=1
#SBATCH --ntasks=2
#SBATCH --mem-per-cpu=6GB
#SBATCH --time=168:00:00
#DATE=${1}
#YAML=${2}

YAML=${1}
./distributed_pipeline_wrapper.py -hpc -y ${YAML} -x sorghum -r 
