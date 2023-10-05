#! /usr/bin/env python

from argparse import ArgumentParser
import ROOT
from tdrstyle_all import *
from printing_utils import *
from utils import *
from collections import defaultdict, OrderedDict
import os, sys, math
import subprocess
import copy


description = 'Steering script'
parser = ArgumentParser(prog="workspaces",description=description,epilog="Finished successfully!")
parser.add_argument('-s', "--submit",      dest="submit", default=False, action='store_true',
                                           help="Actually submit/run" )
parser.add_argument('-r', "--resubmit",    dest="resubmit", default=False, action='store_true',
                                           help="resubmit crashed conversion jobs" )
parser.add_argument('-c', "--convert",     dest="convert", default=False, action='store_true',
                                           help="(re)submit conversion jobs to the cluster" )
parser.add_argument('-p', "--plot",        dest="plot", default=False, action='store_true',
                                           help="plot from converted files" )
args = parser.parse_args()
if args.convert and args.plot:
    raise ValueError('Cannot do conversion AND plotting in the same step')
if not (args.convert or args.plot):
    raise ValueError('Must do either conversion or plotting, what else am I supposed to do?')


def main():
    print(green('--> Hello from the steer script!'))

    # Define the settings
    samplenames  = ['LQTChannel_BBTauTau_MLQ1000_L1p0']
    resubmit     = args.resubmit

    # Samples that Arne generated
    gensimfolder_base    = 'root://storage01.lcg.cscs.ch//pnfs/lcg.cscs.ch/cms/trivcat/store/user/areimers/GENSIM/UL17/LQFlavorFit'
    gensim_filename_base = 'GENSIM'
    nfiles_gensim = 100

    # General settings
    scriptfolder  = os.path.abspath(os.getcwd())
    filefolder    = scriptfolder.replace('scripts', 'files')
    plotfolder    = scriptfolder.replace('scripts', 'plots')
    commandfolder = os.path.join(scriptfolder, 'commands')
    logfolder     = os.path.join(scriptfolder, 'logs')
    ensureDirectory(filefolder)
    ensureDirectory(plotfolder)
    ensureDirectory(commandfolder)
    ensureDirectory(logfolder)

    if args.submit:
        if args.convert:
            convert(gensimfolder_base=gensimfolder_base, gensim_filename_base=gensim_filename_base, filefolder=filefolder, scriptfolder=scriptfolder, commandfolder=commandfolder, logfolder=logfolder, samplenames=samplenames, nfiles=nfiles_gensim, resubmit=resubmit)
        if args.plot:
            plot(filefolder=filefolder, plotfolder=plotfolder, samplenames=samplenames)
    else:
        if args.convert:
            print(yellow('  --> Would run the conversion step now, set \'-s\' to actually run and \'-r\' to resubmit failed jobs only'))
        if args.plot:
            print(yellow('  --> Would run the plotting step now, set \'-s\' to actually run'))


    print(green('--> All done in the steer script, bye!'))




def convert(gensimfolder_base, gensim_filename_base, filefolder, scriptfolder, commandfolder, logfolder, samplenames, nfiles, resubmit=False):
    for sn in samplenames:
        gensimfolder = os.path.join(gensimfolder_base, sn)
        commands = []
        commands_resubmit = []
        for ifile in range(1, nfiles+1):
            infilename = os.path.join(gensimfolder, '%s_%i.root' % (gensim_filename_base, ifile))
            outfilename = os.path.join(filefolder, sn, 'ntuple_%i.root' % (ifile))
            ensureDirectory(filefolder, sn)
            command = '%s/convert_gensim_root.py -i %s -o %s' % (scriptfolder, infilename, outfilename)
            commands.append(command)

            if not os.path.isfile(outfilename):
                commands_resubmit.append(command)
        
            if os.path.isfile(outfilename) and not resubmit:
                os.remove(outfilename)


        commandfilename = os.path.join(commandfolder, '%s_convert.txt' % (sn))
        with open(commandfilename, 'w') as f:
            for c in commands:
                f.write(c + '\n')

        commandfilename_resub = os.path.join(commandfolder, '%s_convert_resub.txt' % (sn))
        with open(commandfilename_resub, 'w') as f:
            for c in commands_resubmit:
                f.write(c + '\n')

        if resubmit:
            submit(scriptname=commandfilename_resub, njobs=len(commands_resubmit), jobname=sn, logfolder=logfolder, runtime=(0,10,00), ncores=1)
        else:
            submit(scriptname=commandfilename, njobs=len(commands), jobname=sn, logfolder=logfolder, runtime=(0,10,00), ncores=1)

    

def plot(filefolder, plotfolder, samplenames):
    print(blue('  --> Plotting for %i samples...' % (len(samplenames))))
    commands = []
    for sn in samplenames:
        infolder  = os.path.join(filefolder, sn)
        outfolder = os.path.join(plotfolder, sn)
        ensureDirectory(outfolder)
        ntuple_files = [os.path.join(infolder, f) for f in os.listdir(infolder) if os.path.isfile(os.path.join(infolder, f))]
        ntuple_files.sort()
        filestring = ' '.join(ntuple_files)

        command = './plot_ntuples.py -i %s -o %s' % (filestring, outfolder)
        os.system(command)
        commands.append(command)

    # execute_commands_parallel(commands=commands, ncores=8)
    print(blue('\n  --> Done plotting!'))


def submit(scriptname, njobs, jobname, logfolder, runtime=(1,00,00), ncores=1):
    runtime_str, queue = format_runtime(runtime)
    print(blue('--> Submitting %i jobs\n\n' % (njobs)))

    submitcommand = 'sbatch --parsable -a 1-%s -J %s -p %s -t %s --mem-per-cpu 2000 --cpus-per-task %i --ntasks-per-core 1 --chdir %s %s %s %s' % (str(njobs), 'convert_%s' % (jobname), queue, runtime_str, ncores, logfolder, 'submit_generic_array.sh', os.environ['CMSSW_BASE'], scriptname)

    jobid = int(subprocess.check_output(submitcommand.split(' ')))
    print(blue('  --> Submitted generation job \'ntuples_%s\' with ID %i' % (jobname, jobid)))
    print(blue('\n\n--> Done submitting %i jobs' % (njobs)))






if __name__ == '__main__':
    main()

