#!/bin/bash -l
#SBATCH --account=frost_lab
#SBATCH --partition=standard
#SBATCH --job-name="phytooracle_manager"
#SBATCH --nodes=1
#SBATCH --ntasks=94
#SBATCH --time=168:00:00
PIPE_COMMAND=${1}
$PIPE_COMMAND
