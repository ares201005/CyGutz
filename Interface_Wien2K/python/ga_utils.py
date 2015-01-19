#!/usr/bin/env python

import os, sys, glob
from numpy import imag



class DmftEnvironment:
    '''This class provides the following member variables:
    ROOT    - location of WIEN+DMFT executables
    MPI     - command to launch MPI process
    '''

    __shared_state = {}  # class has one common state, but (possibly) many instances

    def __init__(self):
        self.__dict__ = self.__shared_state

        if self.__dict__ == {}:  # only initialize once
            self.__get_root()
            self.__get_mpi()

    def __get_root(self):
        ROOT = os.environ.get('WIEN_GUTZ_ROOT')

        if ROOT and os.path.isdir(ROOT):
            self.ROOT = ROOT
        else:
            errstr = "Cannot determine location of WIEN+DMFT executables because"
            errstr += "%s does not exist." % ROOT
            errstr += "Check your WIEN_DMFT_ROOT environment variables."
            raise Exception, errstr

        if self.ROOT not in sys.path:
            sys.path.append(self.ROOT)

    def __get_mpi(self):
        self.MPI = ''
        mpifile = 'mpi_prefix.dat'
        if os.path.isfile(mpifile):
            self.MPI = open(mpifile, 'r').next().strip()
            print "DmftEnvironment: mpi_prefix.dat exists -- running in parallel mode."
            print "  ", self.MPI
        else:
            print "DmftEnvironment: mpi_prefix.dat does not exist -- running in single-processor mode."



class W2kEnvironment:
    '''This class provides the following member variables:
    SCRATCH  - WIEN2k scratch directory
    EDITOR   - editor (vi/emacs) user chose for viewing WIEN2k files
    WIENROOT - location of WIEN2k executables
    case     - casename of current directory
    '''

    __shared_state = {}  # class has one common state, but (possibly) many instances

    def __init__(self):
        self.__dict__ = self.__shared_state

        if self.__dict__ == {}:  # only initialize once
            self.SCRATCH = os.environ.get('SCRATCH')
            self.EDITOR = os.environ.get('EDITOR')
            self.__get_wienroot()
            self.__get_case()

    def __get_wienroot(self):
        # not used at the moment
        ROOT = os.environ.get('WIENROOT')
        if ROOT:
            if os.path.isdir(ROOT):
                self.WIENROOT = ROOT
            else:
                raise Exception, 'WIENROOT is set, but %s is not a valid directory.' % ROOT
        else:
            raise Exception, 'Cannot determine location of WIEN executables because WIENROOT is not set.'

    def __get_case(self):
        # Determine WIEN2k case name
        self.case = os.path.basename(os.getcwd())
  
        if not os.path.isfile(self.case+'.struct'):  # directory name is not case (happens when submitting to cluster)
            files = glob.glob('*.struct')
            if len(files) < 1:
                raise Exception, 'No struct file present.'
            elif len(files) > 1:
                # heuristic algorithm to determine case:
                # the struct file whose head is the same as the most files in this directory is most likely the case
                candidates = [os.path.splitext(f)[0] for f in files]
                allheads = [os.path.splitext(f)[0] for f in os.listdir('.')]
                counts = [len([1 for f in allheads if f == candidate]) for candidate in candidates]
                index = counts.index(max(counts))
                self.case = candidates[index]
                # before, raised an exception -- now, maybe we should at least print a warning?
                # raise Exception, 'Multiple struct files present.  Found following struct files:\n' + '\n'.join(files)
            else:
                self.case, ext = os.path.splitext(os.path.basename(files[0]))

# energy units conversion between eV and Ry
Ry_in_eV = 13.6056923
eV_in_Ry = 1./Ry_in_eV

def eV2Ry(x):
    return float(x) / Ry_in_eV

def Ry2eV(x):
    return float(x) * Ry_in_eV

# orbital angular momentum conversion between (s,p,d,f,...) and (0,1,2,3,...)
__Lnum2str = ['s', 'p', 'd', 'f', 'g', 'h']

def L2str(Lnum):
    return __Lnum2str[Lnum]

def L2num(Lstr):
    return [L for L,s in enumerate(__Lnum2str) if s==Lstr][0]