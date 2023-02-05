# Background
PhytoOracle Automation (POA) fully automates phenomics data processing by handling raw data download, parallel data processing, and output data upload. To further facilitate automated data processing, a Cron job can be set to automatically launch POA. Below you can find how to do just that.

# Setting up a Cron job
Cron jobs can be set on the University of Arizona high performance computing (HPC) cluster. To do this, run the following:

```bash
crontab -e
```

This will open your Cron file, which will be empty at first. In this file, you can set two specifications: schedule and command. In general, the Cron format is as follows:

```bash
<schedule> <command>
```

## Schedule
The first section of a Cron file is the scheduling specification. The scheduling section is made up of 5 characters: 

|minute|hour|day of month|month|day of week|
|------|----|------------|-----|-----------|
|0-59  |0-23|1-31|1-12|0 - 6|

For example, if you want to schedule a job to run at midnight every Monday, your Cron scheduling syntax would be:

```bash
00 0 * * 1
```

If you want to schedule a job to run at 5:30 PM every Saturday, your Cron scheduling syntax would be:

```bash
30 17 * * 6
```

## Command
The second field of a Cron file is the command specification. This field can be any command, but in our case, we would want the general format:

```bash
<schedule> cd <PO Autoation repo on XDISK> && sbatch shell_scripts/slurm_submission.sh <YAML file>
```

## Running POA using Cron

For example, let's say that we want to run POA 3D data processing for season 15 at midnight every Monday. 

We would first edit our Cron file by running:

```bash
crontab -e
```

This will open a VIM editor. To edit the file, click ```i``` on your keyboard to enter edit mode. We can then add the following:

```bash
00 0 * * 1 cd /xdisk/dukepauli/emmanuelgonzalez/automation && sbatch shell_scripts/slurm_submission.sh yaml_files/season_15/s13_3d_level01.yaml
```

Then, hit ```Esc``` to exit edit mode. To save your file, type ```:wq``` to save and quit.