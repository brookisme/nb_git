from __future__ import print_function
import os
import subprocess
import re
import argparse
import difflib
import gitnb.paths as paths
import gitnb.utils as utils
from gitnb.topy import NB2Py
from gitnb.tonb import Py2NB
import gitnb.config as con
from gitnb.project import GitNBProject as GNB



#
# CONFIG
#
ALL_NOTEBOOKS='all'
TRACKED_NOTEBOOKS='tracked'
UNTRACKED_NOTEBOOKS='untracked'
NBPYS='nbpy'
LIST_TYPES=[
    ALL_NOTEBOOKS,
    TRACKED_NOTEBOOKS,
    UNTRACKED_NOTEBOOKS,
    NBPYS]

DIFF_TMP_PATH='./.gitnb/diff_tmp_nbpy_py'


#
# METHODS
#
def initialize():
    """ Installs GITNB
        - installs git pre-commit hook
        - creates .gitnb dir
    """
    GNB.initialize()


def configure():
    """ Install config file
        allows user to change config
    """
    GNB.configure()


def gitignore():
    """ UPDATE GIT IGNORE
        ignore:
            - ipynb_checkpoints/
            - *.ipynb
            - .gitnb/
            - nbpy/
            - nbpy_nb/
    """ 
    GITIGNORE='.gitignore'
    if os.path.isfile(GITIGNORE):
        nb_match=utils.nb_matching_lines('AUTO-GENERATED BY GITNB',GITIGNORE)
    else:
        nb_match=0
    if nb_match>0:
        print("\ngitnb[WARNING]:")
        print("\tit appears you have already run gitignore")
        print("\tverify: cat .gitignore\n")
    else:
        utils.copy_append(paths.DEFAULT_GITIGNORE,GITIGNORE)
        print("gitnb: appened user .gitignore with defaults")


def diff(path):
    """ DIFF NOTEBOOKS
        1. create tmp copy
        2. diff tmp with current
    """
    nbpy_path=GNB().notebooks().get(path)
    if nbpy_path:
        NB2Py(path,DIFF_TMP_PATH).convert()  
        print("\ngitnb[diff]: {}[->nbpy.py] - {}".format(path,nbpy_path))
        _print_file_diff(nbpy_path,DIFF_TMP_PATH)
        os.remove(DIFF_TMP_PATH)
    else:
        msg="requested notebook <{}> is not being tracked by gitnb".format(path)
        print("gitnb[WARNING]: {}".format(msg))


def list_files(list_type=ALL_NOTEBOOKS):
    """ Notebook paths as list
    """
    prj=GNB()
    if list_type==ALL_NOTEBOOKS:
        return prj.list_notebooks(), prj.list_untracked()
    elif list_type==TRACKED_NOTEBOOKS:
        return prj.list_notebooks()
    elif list_type==UNTRACKED_NOTEBOOKS:
        return prj.list_untracked()
    elif list_type==NBPYS:
        return prj.list_nbpys()




def update():
    """ 
        - Update all nbpy files
    """
    GNB().update()



def add(path,destination_path=None):
    """ 
        - Convert Notebook to NBPY FILE
        - Add to Notebooks list: .gitnb/notebooks
        - Add NBPY file to git repo (if GIT_ADD_ON_GITNB_ADD=True)
    """
    nbpy_path=_safe_path_exec(
        GNB().add,
        'add',
        path,
        destination_path)



def remove(path):
    """ remove ipynb-nbpy line from notebooks list
        - does not delete file
        - does not change git tracking
    """
    return _safe_path_exec(
        GNB().remove,
        'remove',
        path,
        False)
  


def topy(path,destination_path=None):
    """ Convert Notebook to Py
    """
    print('\ngitnb[topy]:'.format(path))
    print('\tPlease note that you are creating a nbpy file but')
    print('\tnot tracking it. To track the file use "gitnb add"\n')
    return NB2Py(path,destination_path).convert()  


def tonb(path,destination_path=None):
    """ Convert NBPy to Noteook
    """
    return Py2NB(path,destination_path).convert()


def commit(param_list):
    """ ALLOW FOR EMPTY COMMITS
        * if (UPDATE_ON_GITNB_COMMIT) perform 'gitnb update'
        * -a flag (add all - same as git commit -a)
        * -m flag (add all - same as git commit -m)
    """
    if con.fig('UPDATE_ON_GITNB_COMMIT'): update()
    param_list.insert(0,'git commit --allow-empty')
    cmd=' '.join(param_list)
    os.system(cmd)


#
# HELPERS
#
def _safe_path_exec(func,action,path,destination_path=None):
    if os.path.isfile(path):
        _exec(func,path,destination_path)
    elif os.path.isdir(path):
        file_paths=utils.rglob(
            match='*.ipynb',root=path,exclude_dirs=con.fig('EXCLUDE_DIRS'))
        file_paths=[_clean_path(file_path) for file_path in file_paths]
        if destination_path:
            print('\ngitnb[WARNING]: destination_path ignored')
            print('\t- `gitnb {}` for directories always uses default path'.format(
                action))
            print('\t- the default path is configurable (see gitnb configure)\n')
            destination_path=None
        for file_path in file_paths:
            _exec(func,file_path,destination_path)
    else:
        print('gitnb[ERROR]: {} does not exist'.format(path))


def _exec(func,path,destination_path=None):
    if destination_path is False:
        func(path)
    else:
        func(path,destination_path)


def _print_list(list_type,items):
    if items:
        print('\ngitnb[{}]:'.format(list_type))
        for item in items:
            print('\t{}'.format(item))
        print('')


def _print_file_diff(path_a,path_b):
    with open(path_a,'r') as file_a, open(path_b,'r') as file_b:
        diff = difflib.unified_diff(
            file_a.readlines(), 
            file_b.readlines(), 
            lineterm='')
        print(''.join(list(diff)))


def _clean_path(string):
    return re.sub('^\.\/','',string)




#######################################################
#
# CLI 
#
#######################################################


#
# args methods:
#
def _init(args):
    return initialize()


def _configure(args):
    return configure()


def _gitignore(args):
    return gitignore()

def _diff(args):
    return diff(args.path)

def _update(args):
    return update()


def _list(args):
    list_type=args.type
    if list_type not in LIST_TYPES:
        print('gitnb[list]: ERROR - {} is not a vaild list type'.format(list_type))
    else:
        if list_type==ALL_NOTEBOOKS:
            tracked,untracked=list_files(list_type)
            _print_list('tracked',tracked)
            _print_list('untracked',untracked)
        else:
            _print_list(list_type,list_files(list_type))


def _add(args):
    destination_path=args.destination_path
    if not utils.truthy(destination_path): destination_path=None
    return add(args.path,destination_path)


def _remove(args):
    return remove(args.path)


def _topy(args):
    destination_path=args.destination_path
    if not utils.truthy(destination_path): destination_path=None
    return topy(args.path,destination_path)


def _tonb(args):
    destination_path=args.destination_path
    if not utils.truthy(destination_path): destination_path=None
    return tonb(args.path,destination_path)


def _commit(args):
    param_list=[]
    if args.all: param_list.append('-a')
    if args.message: 
        param_list.append('-m "{}"'.format(args.message))
    commit(param_list)




#
# MAIN
#
def main():
    parser=argparse.ArgumentParser(description='GITNB: TRACKING FOR PYTHON NOTEBOOKS')
    subparsers=parser.add_subparsers()
    
    """ install """
    parser_init=subparsers.add_parser(
        'init',
        help='initialize gitnb for local project')
    parser_init.set_defaults(func=_init)    
    
    """ configure """
    parser_configure=subparsers.add_parser(
        'configure',
        help='creates local configuration file ({})'.format(paths.USER_CONFIG))
    parser_configure.set_defaults(func=_configure)    
    

    """ gitignore """
    parser_gitignore=subparsers.add_parser(
        'gitignore',
        help='updates user .gitignore with defaults')
    parser_gitignore.set_defaults(func=_gitignore)  

    """ diff """
    parser_diff=subparsers.add_parser(
        'diff',
        help='diff current version of notebook with last updated version')
    parser_diff.add_argument('path',
        help='path to ipynb file')   
    parser_diff.set_defaults(func=_diff)

    """ list """
    parser_list=subparsers.add_parser(
        'list',
        help='list notebooks or nbpy files')
    parser_list.add_argument('type',
        nargs='?',
        default='all',
        help='notebooks: ( {} | {} | {} ), or nbpy'.format(
            ALL_NOTEBOOKS,TRACKED_NOTEBOOKS,UNTRACKED_NOTEBOOKS))
    parser_list.set_defaults(func=_list)  
    
    """ update """
    parser_update=subparsers.add_parser(
        'update',
        help='updates nbpy files from tracked notebooks')
    parser_update.set_defaults(func=_update) 

    
    """ add """
    parser_add=subparsers.add_parser(
        'add',
        help='converts notebook to nbpy and adds nbpy to repo')
    parser_add.add_argument('path',
        help='path to ipynb file')   
    parser_add.add_argument('destination_path',
        nargs='?',
        default=None,
        help='if falsey uses default destination path')
    parser_add.set_defaults(func=_add)
    
    """ remove """
    parser_remove=subparsers.add_parser(
        'remove',
        help='stops gitnb from tracking notebook')
    parser_remove.add_argument('path',
        help='path to ipynb file')   
    parser_remove.set_defaults(func=_remove)

    
    """ topy """
    parser_topy=subparsers.add_parser(
        'topy',
        help='topy .ipynb files to .nbpy.py files')
    parser_topy.add_argument('path',
        help='path to ipynb file')   
    parser_topy.add_argument('destination_path',
        nargs='?',
        default=None,
        help='if falsey uses default destination path')
    parser_topy.set_defaults(func=_topy)
    
    
    """ tonb """
    parser_tonb=subparsers.add_parser(
        'tonb',
        help='tonb .ipynb files to .nbpy.py files')
    parser_tonb.add_argument('path',
        help='tracked path to notebook or nbpy file')   
    parser_tonb.add_argument('destination_path',
        nargs='?',
        default=None,
        help='if falsey uses default destination path')
    parser_tonb.set_defaults(func=_tonb)   
    

    """ commit """
    parser_commit=subparsers.add_parser(
        'commit',
        help='gitnb update, followed git add on all tracked nbpy files, followed by git commit')
    parser_commit.add_argument(
        '-a','--all', action='store_true',help='git add all')
    parser_commit.add_argument(
        '-m','--message',default=None,help='git commit message')
    parser_commit.set_defaults(func=_commit)


    """ run """
    args=parser.parse_args()
    args.func(args)



if __name__ == "__main__": 
    main()



