#!/bin/bash 
salloc --nodes=1 --mem-per-cpu=6gb --ntasks=16 --time=168:00:00 --job-name=phytooracle_manager --account=dukepauli --partition=standard
