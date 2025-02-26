import numpy, h5py
from mpi4py import MPI
from scipy.io import FortranFile


def get_wannier_data_binary(fname):
    with FortranFile(fname, "r") as f:
        # real space lattice vectors
        reals_lat = f.read_reals().reshape((3, 3))
        # reciprocal space lattice vectors
        recip_lat = f.read_reals().reshape((3, 3))
        # maximal number of bands
        num_bands = f.read_ints()[0]
        # number of wannier orbitals
        num_wann = f.read_ints()[0]
        # k-point mesh
        ndiv = f.read_ints()
        # total number of k-points
        nqdiv = ndiv[0]*ndiv[1]*ndiv[2]
        # k-points
        kpts = f.read_reals().reshape((nqdiv, 3))
        # low energy band indices included in the wannier construction
        include_bands = f.read_ints()
        # list of overlap between band wavefunctions and wannier orbitals
        wfwannier_list = f.read_reals().view(numpy.complex).reshape(\
                (1, nqdiv, num_wann, num_bands)).swapaxes(2, 3)
        # list of band energies
        bnd_es = f.read_reals().reshape((1, nqdiv, num_bands))
    return reals_lat, recip_lat, kpts, include_bands, wfwannier_list, bnd_es


def h5get_wannier_data(fname):
    with h5py.File(fname, "r") as f:
        # real space lattice vectors
        reals_lat = f["/rbas"][()]
        # reciprocal space lattice vectors
        recip_lat = f["/gbas"][()]
        # maximal number of bands
        num_bands = f["/num_bands"][0]
        # number of wannier orbitals
        num_wann = f["/num_wann"][0]
        # k-point mesh
        ndiv = f["/ndiv"][()]
        # total number of k-points
        nqdiv = ndiv[0]*ndiv[1]*ndiv[2]
        # k-points
        kpts = f["/kpt_latt"][()]
        # low energy band indices included in the wannier construction
        include_bands = f["/include_bands"][()]
        # list of overlap between band wavefunctions and wannier orbitals
        wfwannier_list = f["/v_matrix"][()].reshape(\
                (1, nqdiv, num_wann, num_bands)).swapaxes(2, 3)
        # list of band energies
        bnd_es = f["/eigenvalues"][()].reshape((1, nqdiv, num_bands))
    return reals_lat, recip_lat, kpts, include_bands, wfwannier_list, bnd_es


def get_wannier_data(path="./"):
    fname = "{}/wannier.dat".format(path)
    try:
        f = h5py.File(fname, "r")
        f.close()
        h5input = True
    except:
        h5input = False
        pass
    if h5input:
        reals_lat, recip_lat, kpts, include_bands, wfwannier_list, bnd_es = \
                h5get_wannier_data(fname)
    else:
        reals_lat, recip_lat, kpts, include_bands, wfwannier_list, bnd_es = \
                get_wannier_data_binary(fname)
    return reals_lat, recip_lat, kpts, include_bands, wfwannier_list, bnd_es


def mpiget_wannier_data(path="./"):
    '''get the contents in wannier.dat Fortran binary file.
    '''
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    if rank == 0:
        reals_lat, recip_lat, kpts, include_bands, wfwannier_list, bnd_es =\
                get_wannier_data(path=path)
    else:
        reals_lat = recip_lat = kpts = include_bands = wfwannier_list = \
                bnd_es = None
    reals_lat = comm.bcast(reals_lat, root=0)
    recip_lat = comm.bcast(recip_lat, root=0)
    kpts = comm.bcast(kpts, root=0)
    include_bands = comm.bcast(include_bands, root=0)
    wfwannier_list = comm.bcast(wfwannier_list, root=0)
    bnd_es = comm.bcast(bnd_es, root=0)
    return reals_lat, recip_lat, kpts, include_bands, wfwannier_list, bnd_es


if __name__ == "__main__":
    get_wannier_data()
