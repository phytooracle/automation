#!/bin/bash
export CCTOOLS_HOME=${HOME}/cctools
export PATH=${CCTOOLS_HOME}/bin:$PATH
work_queue_factory -T local -M phytooracle_manager --cores 1 --gpus 0 --memory 4000 --workers-per-cycle 15 --timeout 12000 -w 100 -W 200
