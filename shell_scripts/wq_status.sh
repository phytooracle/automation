#!/bin/bash
export CCTOOLS_HOME=${HOME}/cctools_non_centos
export PATH=${CCTOOLS_HOME}/bin:$PATH
watch -n 1 work_queue_status