#!/bin/bash
export CCTOOLS_HOME=${HOME}/cctools
export PATH=${CCTOOLS_HOME}/bin:$PATH
work_queue_factory -T local -M phytooracle_manager --memory 5000 -w 100 -W 200
