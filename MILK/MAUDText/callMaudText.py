#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 12 08:53:18 2020

@author: danielsavage
"""

from multiprocessing import Pool, freeze_support
from functools import partial
import argparse
import os
import glob
import shutil
import subprocess as sub
import sys
import tqdm
import csv
from prettytable import (PrettyTable,from_csv)

def resource_file_path(filename):
    for d in sys.path:
        filepath = os.path.join(d, filename)
        if os.path.isfile(filepath):
            return filepath
    return None 
def get_arguments(argsin):
    #Parse user arguments
    welcome = "This is an interface for run .ins file in parallel using MAUD"
    
    parser = argparse.ArgumentParser(description=welcome)
    parser.add_argument('--ins_file_name', '-a', required=True, 
                        help='The ins file name to run. Can use wild to specify a bunch of files e.g. test(wild).ins')
    parser.add_argument('--wild', '-n', type=int, nargs='+',
                        help='used with sub_folder (wild) e.g. 1 3 5 would result in a list [1 3 5]')
    parser.add_argument('--wild_range', '-nr', type=int, nargs='+',
                        help='used with sub_folder (wild) and specified in pairs e.g. 1 4 8 9 would result in a list [1 2 3 4 8 9]')
    parser.add_argument('--work_dir', '-dir',
                        help='Base directory from which sub folders are defined and par files are searched for')
    parser.add_argument('--run_dir', '-rd', required=True,
                        help='folders to run job in relative to work_dir /e.g. /run(wild) where (wild) is replaced by the wild and/or wild_range combined lists. wild need not be used')
    parser.add_argument('--sub_dir', '-sf', required=True,
                        help='folders to run job in relative to work_dir /e.g. /run(wild)/preshock where (wild) is replaced by the wild and/or wild_range combined lists. wild need not be used')
    parser.add_argument('--nMAUD', '-i',type=int, 
                        help='Specify the maximum number of MAUD instance to run at the same time')
    parser.add_argument('--maud_path', '-mp', required=True,
                        help='Specify the full path to the maud directory')
    parser.add_argument('--clean_old_step_data', '-cd',
                        help='Specify whether older step data should be removed')
    parser.add_argument('--cur_step', '-cs', required=True,
                        help='Specify the current step counter')    
    parser.add_argument('--riet_append_result_to', '-results', 
                        help='Results are parameters specified by autotrace e.g. results.csv')
    parser.add_argument('--riet_append_simple_result_to', '-simple_results', 
                        help='Simple results are those prechosen by MAUD i.e. biso, fit, lattice parameter etc... e.g. results_simple.csv')
    if argsin==[]:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argsin.split(' '))

    return args

def build_paths(args):
    
    #Generate the working directory
    if args.work_dir!=None:
        args.work_dir=args.work_dir[0][0]
    else:
        args.work_dir = os.getcwd()     
    
    #Get wild cases if any and combine range and wild
    wilds=[]
    if args.wild!=None:
        for i in args.wild:
            wilds.append(i)
            
    if args.wild_range!=None:
        for pair in range(0,len(args.wild_range),2):
            tmp_id=range(args.wild_range[pair],args.wild_range[pair+1]+1)
            for i in tmp_id:
                wilds.append(i)            
     
    wild=list(set(wilds))            
    setattr(args, 'wild', wild)
    
    #Generate full inspaths
    ins_file_name=os.path.join(args.work_dir,args.run_dir,args.sub_dir,args.ins_file_name)  
    results_file_name=os.path.join(args.work_dir,args.run_dir,args.sub_dir,args.riet_append_result_to)  
    simple_results_file_name=os.path.join(args.work_dir,args.run_dir,args.sub_dir,args.riet_append_simple_result_to)  
    refinement_id_name=os.path.join(args.run_dir,args.sub_dir)
    ins=[]
    results=[]
    simple_results=[]
    refinement_id=[]
    for i in wild: 
        ins.append(ins_file_name.replace('(wild)',str(i).zfill(3)))
        results.append(results_file_name.replace('(wild)',str(i).zfill(3)))
        simple_results.append(simple_results_file_name.replace('(wild)',str(i).zfill(3)))
        refinement_id.append(refinement_id_name.replace('(wild)',str(i).zfill(3)))
    
    return ins,results,simple_results,refinement_id

def run_MAUD(maud_path,ins_paths):
    
    #This may be modified once general paths are filled out
    #root = os.getcwd() 

    if "linux" in sys.platform:
        # linux
        bfname=resource_file_path('maud_linux.sh')
    elif "darwin" in sys.platform:
        # OS X
        bfname=resource_file_path('maud_osx.sh')
    elif "win" in sys.platform:
        # Windows...
        bfname=resource_file_path('maud_win.bat')
        
    
    maudexc=os.path.join(bfname)
    command=[maudexc,maud_path,ins_paths]
    
    p = sub.Popen(command,stdin=sub.PIPE,stdout=sub.PIPE,stderr=sub.PIPE)
    
    #Write outputs to files
    out,err = p.communicate()
    out=out.splitlines()
    err=err.splitlines()
    fID = open(ins_paths[:-4]+'.log', "w")
    for line in out:
        fID.write('%s\n' % line)
        #if 'Unable to open file' in line:
         #   print(line)
            
    fID.close()
    
    fID = open(ins_paths[:-4]+'.err', "w")
    for line in err:
        fID.write('%s\n' % line)
    fID.close()
    
    
    
    return 0
   
def scrap_results(scrapeFileName,resultFileName,refinement_id):
    
    #Create header 
    with open(scrapeFileName[0]) as f:
            lines = f.readlines()[0]
            with open(resultFileName, "w") as f1:
                f1.writelines(lines)
    
    #Write content
    for i,sfn in enumerate(scrapeFileName):
        with open(sfn) as f:
            lines = f.readlines()[-1]
            lines = refinement_id[i]+lines
            with open(resultFileName, "a+") as f1:
                f1.writelines(lines)

    #Print the table
    with open(resultFileName, "r") as fp: 
        x = list(csv.reader(fp,delimiter='\t'))
        #append a number to make header unique
        ncol=len(x[0])
        nrow=len(x)
        xx = PrettyTable()
        for col in range(0,ncol):
            colname=x[0][col]
            data=[]
            for row in range(1,nrow):
                data.append(x[row][col])
            xx.add_column(colname,data)                               

        #print(xx)
        lines=str(xx).split('\n')  
        with open(resultFileName, "w") as f1:
            #f1.writelines(lines)
            f1.writelines("%s\n" % line for line in lines)
        lines=str(xx).split('\n')    
        for line in lines:
            print(line)

def main(argsin):

    
    args=get_arguments(argsin)
    paths=build_paths(args)
    
    print('')
    print('Starting MAUD refinement for step '+args.cur_step)
    print('=========================')
    
    #cleanup the steps if specified
    if args.clean_old_step_data!=None and (args.clean_old_step_data=='True' or args.clean_old_step_data=='true'):
        print('Removing old step data')
        for path in paths[0]: 
            wdir,filename=os.path.split(path)
            stepdir=os.path.join(wdir,'steps')
            shutil.rmtree(stepdir, ignore_errors = True) 
        for path in paths[1]:
            if os.path.isfile(path):
                os.remove(path)
        for path in paths[2]:
            if os.path.isfile(path):
                os.remove(path)
        path = os.path.join(os.getcwd(),args.riet_append_simple_result_to[:-4]+str(args.cur_step).zfill(2)+'.txt')
        if os.path.isfile(path):
            os.remove(path)
        path = os.path.join(os.getcwd(),args.riet_append_simple_result_to[:-4]+str(args.cur_step).zfill(2)+'.txt')
        if os.path.isfile(path):
            os.remove(path)
        
    if args.nMAUD!=None:
        if args.nMAUD > os.cpu_count():
            pool = Pool(os.cpu_count())
        else:
            pool = Pool(args.nMAUD)
    else:
        pool = Pool(os.cpu_count())
    
    out=list(tqdm.tqdm(pool.imap(partial(run_MAUD, args.maud_path), paths[0]), total=len(paths[0])))
    
    #Backup the files
    print('')
    print('Archiving step data')    
    for path in paths[0]: 
        
        #Try making the step folder
        wdir,filename=os.path.split(path)
        stepdir=os.path.join(wdir,'steps')
        if not os.path.isdir(stepdir):  
            os.makedirs(stepdir, exist_ok=True)
            list_of_gda = glob.glob(os.path.join(wdir,'*.gda'))
            for gda in list_of_gda:
                wdir,gdaname=os.path.split(gda)
                shutil.copy(gda,os.path.join(stepdir,gdaname))
            list_of_esg = glob.glob(os.path.join(wdir,'*.esg'))
            for esg in list_of_esg:
                wdir,esgname=os.path.split(esg)
                shutil.copy(esg,os.path.join(stepdir,esgname))
        #Copy know files
        shutil.copy(os.path.join(wdir,filename[:-4]+'.log'),os.path.join(stepdir,filename[:-4]+args.cur_step.zfill(2)+'.log'))
        shutil.copy(os.path.join(wdir,filename[:-4]+'.err'),os.path.join(stepdir,filename[:-4]+args.cur_step.zfill(2)+'.err'))
        shutil.copy(os.path.join(wdir,filename),os.path.join(stepdir,filename[:-4]+args.cur_step.zfill(2)+'.ins'))
        #Get latest .par
        list_of_pars = glob.glob(os.path.join(wdir,'*.par')) # * means all if need specific format then *.csv
        parpath = max(list_of_pars, key=os.path.getctime)
        wdir,parname=os.path.split(parpath)
        shutil.copy(parpath,os.path.join(stepdir,parname[:-4]+args.cur_step.zfill(2)+'.par'))  
        try:
            shutil.copy(parpath+'.lst',os.path.join(stepdir,parname[:-4]+args.cur_step.zfill(2)+'.par.lst'))  
        except: 
            pass #print('no par.lst to copy')
        
    #Scrape results if applicable
    try:
        scrap_results(paths[1],os.path.join(os.getcwd(),args.riet_append_result_to[:-4]+str(args.cur_step).zfill(2)+'.txt'),paths[3])
    except: 
        print('unable to compile results from folders. This usually means a maud simulation didnt run')
        
    try:
        scrap_results(paths[2],os.path.join(os.getcwd(),args.riet_append_simple_result_to[:-4]+str(args.cur_step).zfill(2)+'.txt'),paths[3])
    except: 
        print('unable to compile results from folders. This usually means a maud simulation didnt run')
        
                
if __name__ == '__main__':
    freeze_support() 
    main([])
