# Command line arguments
* Required
  * -y, --yaml | YAML file to use for processing
* Optional
  * -hpc, --hpc | Download data using UA HPC data transfer node
  * -d, --date | Test date/s to process (in YYYY-MM-DD format, i.e."2020-01-22")
  * -c, --cctools_version | CCTools version to download and use for distributed computing
  * -l, --local_cores | Number of cores to use for local processing 
  * --noclean | Do not delete local results
  * --uploadonly | Run CyVerse upload and exit
  * -r, --reverse | Reverse date processing list 
  * -sfs, --sfs | Indicate shared filesystem (default=True, set flag to turn off)