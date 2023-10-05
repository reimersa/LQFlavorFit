#!/bin/bash
#
#SBATCH --account=t3
#SBATCH -e %x-%A-%a.log
#SBATCH -o %x-%A-%a.log
#SBATCH --export NONE

echo USER:                $USER
echo SLURM_JOB_ID:        $SLURM_JOB_ID
echo SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID
echo HOSTNAME:            $HOSTNAME

echo "--> User input:"
CMSSWDIR=$1
JOBLIST=$2
echo CMSSWDIR: $CMSSWDIR
echo JOBLIST:  $JOBLIST
echo "<-- End user input."


function peval { echo "--> $@"; eval "$@"; }

# set up CMSSW and root
source $VO_CMS_SW_DIR/cmsset_default.sh
export SCRAM_ARCH=slc7_amd64_gcc700
cd $CMSSWDIR/src
eval `scramv1 runtime -sh`



TASKCMD=$(cat $JOBLIST | sed "${SLURM_ARRAY_TASK_ID}q;d")
peval "${TASKCMD}"

echo Done with mother-job.
