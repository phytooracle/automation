# PhytoOracle Pipeline Automation
This project was developed to search the ```phytooracle``` CyVerse Data Store for unprocessed data and recursively process them. The data are downloaded, processed, and uploaded automatically. Processing occurs using a Makeflow/Workqueue distributed computing framework. The data are uploaded to the respective sensor directory within the ```phytooracle/.../level_1``` CyVerse data store.

## Running the script
### Flags 
* -sea, --season | Season to process 
* -sen, --sensor | Sensor to process 
* -r, --reverse | Reverse the order of processing list (optional, default=False)
* -c, --crop | Crop to process
* -hpc, --hpc | Running on UArizona HPC, use filexfer node (optinal, default=False)
* -scan, --scan_date | Rather than processing entire list, select a single date to process (optional)
* -b, --bundle_size | Size of processing bundle (how many datum each worker processes, deault=1)
### Example command 
```bash
./pipeline.py -sea 10 -sen scanner3DTop -r -hpc
```
This command would process Season 10 Scanner3DTop data, reverse the processing list (starting from last scan date), and use a data transfer node to download data. 
