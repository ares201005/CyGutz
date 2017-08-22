from __future__ import print_function
import numpy as np
import sys, os, glob, subprocess, shutil, fileinput, h5py
import pyglib.basic.splot as splot
import pyglib.basic.units as units
from pyglib.run import gwien


'''help routines for processing wien2k data. Assume the current work directory
has a subfolder template with reference case.struct and possibly case.inso.
'''


def get_rotations(case_fname):
    '''get the rotation list in struct file.
    '''
    with open(str(case_fname), 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if 'SYMMETRY OPERATIONS' in line:
                break
        nops = int(lines[i].split()[0])
        lines = lines[i+1:]
        rot_list = []
        for i in range(0,nops*4,4):
            rot = []
            lok = True
            for j in range(3):
                line = lines[i+j]
                rot.append([int(line[:2]), int(line[2:4]), int(line[4:6])])
                if abs(float(line[6:17])) > 1.e-6:
                    lok = False
                    break
            if lok:
                if abs(np.linalg.det(rot)-1)<1.e-6:
                    rot_list.append(rot)
    return rot_list


def get_equivalent_atom_indices(case_fname):
    '''get equivalent atomic indices according to the atom labels in
    case.struct file.
    '''
    with open(str(case_fname), 'r') as f:
        idx_equivalent_atoms = []
        ibase = 0
        for line in f:
            if 'MULT=' in line:
                mult = int(line.split()[1])
                for i in range(mult):
                    idx_equivalent_atoms.append(ibase)
                ibase += mult
    return idx_equivalent_atoms


def get_local_rotations(case_fname):
    '''get list of locrot in struct file.
    '''
    with open(str(case_fname), 'r') as f:
        locrot_list = []
        readline = 100
        for line in f:
            if 'MULT=' in line:
                mult = int(line.split()[1])
            elif 'LOCAL ROT MATRIX' in line:
                readline = 0
                locrot = []
            if readline < 3:
                locrot.append(map(float, [line[20:30], line[30:40], \
                        line[40:50]]))
                readline += 1
                if readline == 3:
                    # wien2k convention
                    locrot = np.asarray(locrot).T
                    for i in range(mult):
                        # maybe there are problems here.
                        locrot_list.append(locrot)
    return locrot_list


def get_volume(file_scf='./case.scf'):
    '''Get primitive unit volume from scf file f_scf.
    '''
    with open(file_scf, 'r') as f:
        for line in f:
            if ':VOL' in line:
                line = line.split('=')
                vol = float(line[1])
        return vol


def get_scf_energy(file_scf='./case.scf'):
    '''Get primitive unit volume from scf file f_scf.
    '''
    with open(file_scf, 'r') as f:
        for line in f:
            if ':ENE' in line:
                line = line.split('=')
                etot = float(line[1])
        return etot


def create_struct(dir_template, vfrac, case='case'):
    '''Create a case.struct file with volume of vfrac of the reference
    struct file in dir_template.
    '''
    f_struct = glob.glob(dir_template+'/*struct')
    if len(f_struct) == 0:
        raise IOError('No struct file existing in {}!'.format(dir_template))
    f_struct = f_struct[0]
    with open(f_struct, 'r') as fs:
        with open(case+'.struct', 'w') as fd:
            for i, line in enumerate(fs.readlines()):
                if i == 3:
                    a_list = []
                    for j in range(3):
                        a_list.append(float(line[j*10:(j+1)*10]))
                    a_list = np.array(a_list)
                    a_list *= vfrac**(1./3)
                    line = '{:10.6f}{:10.6f}{:10.6f}'.format(*a_list) + \
                            line[30:]
                fd.write(line)


def update_case_ref(vfrac_min):
    '''Update case.struct based on the initial run of the Vmin sample.
    '''
    cwd = os.getcwd()+'/'
    os.chdir('./template')
    create_struct('../Ref_Vmin/case', 1./vfrac_min, case='case')
    os.chdir(cwd)


def create_dir1(vfrac, dname, dir_template='./template'):
    '''Create a subdirectory dname in the current directory with
    volumes changing by a vfrac wth repect to the reference structure
    in the dir_template.
    '''
    # create it if necessary
    if not os.path.isdir(dname):
        os.mkdir(dname)
    if not os.path.isdir(dname+'/case'):
        os.mkdir(dname+'/case')

    cwd = os.getcwd()+'/'
    # go to the subdirectory
    os.chdir(dname+'/case')

    # cretae the case.struct file
    create_struct(cwd+dir_template, vfrac)

    # return to the upper work directory
    os.chdir(cwd)


def create_dir_list(vfrac_min=0.7, vfrac_max=1.3, vfrac_step=0.05, \
        dir_template='./template'):
    '''Create a list of subdirectories in the current directory with
    volumes changing by a fraction of vfrac_step in the range of
    [vfrac_min, vfrac_max] wth repect to the reference structure
    in the dir_template.
    '''

    if not os.path.isdir(dir_template):
        raise IOError('{} does not exist!'.format(dir_template))
    # Get volume fraction list
    vfrac_list = np.arange(vfrac_min, vfrac_max+1.e-5, vfrac_step)

    # loop over to create subdirectory list
    f_log = open('vol_record.txt', 'w')
    for i, vfrac in enumerate(vfrac_list):

        # subdirectory name
        dname = 'V{}'.format(i)
        f_log.write('{}  {}\n'.format(dname, vfrac))

        create_dir1(vfrac, dname, dir_template=dir_template)


def batch_init_lapw(args=['-vxc', '5', '-rkmax', '8.5', '-numk', '5000']):
    '''Loop over all the directories to run init_lapw.
    '''
    f = open('binit_lapw.log', 'w')
    cmd = [os.environ['WIENROOT']+'/init_lapw', '-b'] + args
    cwd = os.getcwd()+'/'
    for dname in glob.glob('V*'):
        os.chdir(dname+'/case')
        subprocess.call(cmd, stdout=f)
        os.chdir(cwd)
    f.close()


def modify_emax_case_in1(case_in1='case.in1', emax=7.5):
    '''Modify the emax value in case_in1 for the case with
    spin-orbit calculation.
    '''
    for line in fileinput.input(files=case_in1, inplace=True):
        if 'emax' in line:
            line = line.replace(line[33:38], '{:5.1f}'.format(emax))
        print(line, end='')


def batch_initso_lapw(dir_template='./template', emax=7.5):
    '''Loop over all the directories to run initso_lapw -- actually,
    because there is no batch mode provided, it simply copy the case.inso
    from dir_template and modify the EMAX value to 7.5 in case.in1.
    '''
    cwd = os.getcwd()+'/'
    for dname in glob.glob('V*'):
        os.chdir(dname+'/case')
        shutil.copy(cwd+'/'+dir_template+'/case.inso', './')
        shutil.copy(cwd+'/'+dir_template+'/case.in2c', './')
        modify_emax_case_in1(case_in1='case.in1', emax=emax)
        os.chdir(cwd)


def h2get_energy_volume_list(path='lapw'):
    '''Loop over all the directories to get the energy vs volume data,
    and save it to the metadata file results.h5 at path.
    '''
    v_list = []
    e_list = []
    cwd = os.getcwd()+'/'
    for dname in glob.glob('V*'):
        os.chdir(dname+'/case/'+path)
        v_list.append(get_volume())
        e_list.append(get_scf_energy())
        os.chdir(cwd)

    # Ryd/Bohr units to eV/A units
    v_list = np.array(v_list)*units.Bohr_A**3
    e_list = np.array(e_list)*units.Ryd_eV

    with h5py.File('results.h5', 'a') as f:
        if not 'vol_list' in f:
            f['/vol_list'] = v_list
        epath = '/'+path+'/etot_list'
        if epath in f:
            del f[epath]
        f[epath] = e_list
    splot.xy_plot(v_list, e_list, xlabel='V ($\AA^{3}$/primitive cell)',
            ylabel='E (eV/primitive cell)', fsave='ev_{}.pdf'.format(path))


def compare_ev_plot(fres='results.h5'):
    '''Compare lapw/lapwso/lapwsog in a plot compare_ev.pdf.
    '''
    v_list = []
    e_list = []
    pattern_list = []
    label_list = []
    with h5py.File(fres, 'r') as f:
        if '/lapw' in f:
            label_list.append('lapw')
            e_list.append(f['/lapw/etot_list'][...])
            v_list.append(f['/vol_list'][...])
            pattern_list.append('o')
        if '/lapwso' in f:
            label_list.append('lapwso')
            e_list.append(f['/lapwso/etot_list'][...])
            v_list.append(f['/vol_list'][...])
            pattern_list.append('d')
        if '/lapwsog' in f:
            label_list.append('lapwsog')
            e_list.append(f['/lapwsog/etot_list'][...])
            v_list.append(f['/vol_list'][...])
            pattern_list.append('h')
        if v_list != []:
            splot.xy2_plot(v_list, e_list, pattern_list, label_list,
                    xlabel='V ($\AA^{3}$/primitive cell)',
                    ylabel='E (eV/primitive cell)',
                    fsave='ev_compare.pdf')


def batch_save_lapw(sdir='lapw', args=['-f']):
    '''Loop over all the directories to save_lapw.
    '''
    cmd = [os.environ['WIENROOT']+'/save_lapw', '-d'] + [sdir] + args
    cwd = os.getcwd()+'/'
    for dname in glob.glob('V*'):
        os.chdir(dname+'/case')
        subprocess.call(cmd)
        os.chdir(cwd)


def run_lapw(args=['-i', '70'], nproc=1):
    '''Loop over all the directories to run_lapw using nproc processors
    with arguments provided in args.
    '''
    cmd = [os.environ['WIENROOT']+'/run_lapw'] + args
    cwd = os.getcwd()+'/'
    if '-p' in sys.argv:
        nproc = int(sys.argv[sys.argv.index('-p')+1])
    for i,dname in enumerate(glob.glob('V*')):
        os.chdir(dname+'/case')
        proc = subprocess.Popen(cmd)
        os.chdir(cwd)
        if (i+1) % nproc == 0:
            proc.communicate()


def steps(vfrac_min=0.7, vfrac_max=1.3, vfrac_step=0.05, \
        dir_template='./template'):
    if len(sys.argv) == 1 or '-h' in sys.argv[1]:
        print('Please provide with inline argument chosen from below:\n' +
                '  Vmin -- setup init. calculation of the min. vol. point;\n' +
                '  update_case_ref -- update esp. RMT values of ref. case;\n' +
                '  Vlist -- generate directories for a range of volumes;\n' +
                '  batch_init_lapw -- init_lapw all the directories;\n' +
                '  batch_initso_lapw -- initso_lapw all the directories;\n' +
                '  batch_init_ga -- initso_lapw all the directories;\n' +
                '  batch_run_lapw -- run_lapw all the directories 1 by 1;\n' +
                '  batch_run_lapwso -- run_lapw -so all the directories;\n' +
                '  batch_run_ga -- run_ga all the directories; \n' +
                '  batch_save_lapw -- save_lapw all the directories; \n' +
                '  batch_save_lapwso -- save_lapwso all the directories; \n' +
                '  batch_gsave_uxjx -- save DFT+G results to uxjx dirs; \n' +
                '  ev_lapw -- save_energy volume data for lapw calc.; \n' +
                '  ev_lapwso -- save_energy volume data for lapwso calc.\n' +
                '  ev_uxjy -- save_energy volume data for DFT+G calc.\n' +
                '  eos_fit_lapw -- Murnaghan EOS fir for lapw results;\n' +
                '  eos_fit_lapwso -- Murnaghan EOS fir for lapwso results.\n' +
                '  eos_fit_uxjx -- Murnaghan EOS fir for DFT+G results.\n' +
                '  compare_ev -- Compare the EOS for lapw/lapwso/lapwsog.\n' +
                '  You may append "-p nproc" to specify # of procs in use.')
        sys.exit('Please choose proper inline argument!')
    if 'Vmin' in sys.argv[1]:
        create_dir1(vfrac_min, 'Ref_Vmin', dir_template=dir_template)
        print('Please goto Ref_Vmin/case and finish manual test.')
    elif 'update_case_ref' == sys.argv[1]:
        update_case_ref(vfrac_min)
    elif 'Vlist' == sys.argv[1]:
        create_dir_list(vfrac_min=vfrac_min, vfrac_max=vfrac_max,
                vfrac_step=vfrac_step, dir_template=dir_template)
    elif 'batch_init_lapw' == sys.argv[1]:
        batch_init_lapw()
    elif 'batch_run_lapw' == sys.argv[1]:
        run_lapw()
    elif 'batch_run_lapwso' == sys.argv[1]:
        run_lapw(args=['-so', '-i', '70'])
    elif 'batch_save' in sys.argv[1]:
        batch_save_lapw(sdir=sys.argv[1].split('_')[2])
    elif 'batch_gsave' in sys.argv[1]:
        gwien.batch_gsave(sdir=sys.argv[1].split('_')[2])
    elif 'ev_' in sys.argv[1]:
        h2get_energy_volume_list(path=sys.argv[1].split('_')[1])
    elif 'batch_initso_lapw' == sys.argv[1]:
        batch_initso_lapw()
    elif 'eos_fit' in sys.argv[1]:
        from pyglib.dft.eos import h5get_mfit_ev
        h5get_mfit_ev(path='/'+sys.argv[1].split('_')[2])
    elif 'compare_ev' == sys.argv[1]:
        compare_ev_plot()
    elif 'batch_init_ga' == sys.argv[1]:
        gwien.batch_init_ga()
    elif 'batch_run_ga' == sys.argv[1]:
        gwien.run_ga()
    else:
        raise ValueError('Inline option not defined!')



if __name__=='__main__':
    steps(vfrac_step=0.05)
