#!/bin/bash -l
#SBATCH --account=dukepauli
#SBATCH --partition=standard
#SBATCH --job-name="phytooracle_manager"
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=94
#SBATCH --time=96:00:00
PIPE_COMMAND=${1}
CWD=${2}
cd ${CWD}
${PIPE_COMMAND}
