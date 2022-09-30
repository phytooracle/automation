#!/bin/bash 
salloc --nodes=1 --mem-per-cpu=5GB --ntasks=94 --time=168:00:00 --job-name=phytooracle_manager --account=ericlyons --partition=high_priority --qos=user_qos_ericlyons
