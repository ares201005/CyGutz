from __future__ import print_function

# modiofied based on PythTB python tight binding module.

import numpy as np # numerics for matrices
from builtins import range, zip


class tb_model(object):
    r"""
    This is the main class of the PythTB package which contains all
    information for the tight-binding model.

    :param lat: Array containing lattice vectors in Cartesian
      coordinates (in arbitrary units). In example the below, the first
      lattice vector has coordinates [1.0,0.5] while the second
      one has coordinates [0.0,2.0].  By default, lattice vectors
      are an identity matrix.

    :param orb: Array containing reduced coordinates of all
      tight-binding orbitals. In the example below, the first
      orbital is defined with reduced coordinates [0.2,0.3]. Its
      Cartesian coordinates are therefore 0.2 times the first
      lattice vector plus 0.3 times the second lattice vector.
      If *orb* is an integer code will assume that there are these many
      orbitals all at the origin of the unit cell.  By default
      the code will assume a single orbital at the origin.

    """

    def __init__(self,lat,orb,deg_ws,Rvec_list,Hmat_list,nspin=1):
        self._dim_k = 3
        self._dim_r = 3

        self._lat=np.array(lat,dtype=float)
        if self._lat.shape != (self._dim_r,self._dim_r):
            raise Exception("\nWrong lat array dimensions")
        # check that volume is not zero and that have right handed system
        if np.abs(np.linalg.det(self._lat))<1.0E-6:
            raise Exception("\n\nLattice vectors length/area/volume too close to zero, or zero.")
        if np.linalg.det(self._lat)<0.0:
            raise Exception("\n\nLattice vectors need to form right handed system.")

        # initialize _norb = number of basis orbitals per cell
        #   and       _orb = orbital locations, in reduced coordinates
        #   format is _orb(orb_index,lat_vec_index)
        self._orb = np.array(orb, dtype=float)
        if len(self._orb.shape) != 2:
            raise Exception("\nWrong orb array rank")
        self._norb=self._orb.shape[0] # number of orbitals
        if self._orb.shape[1] != self._dim_r:
            raise Exception("\nWrong orb array dimensions")
        # remember number of spin components
        if nspin not in [1,2]:
            raise Exception("\nWrong value of nspin, must be 1 or 2!")
        self._nspin = nspin
        self.deg_ws = deg_ws
        self.Rvec_list = Rvec_list
        self.Hmat_list = Hmat_list

    def _gen_ham(self,k_input=None):
        """Generate Hamiltonian for a certain k-point,
        K-point is given in reduced coordinates!"""
        kpnt=np.array(k_input)
        if k_input is not None:
            # if kpnt is just a number then convert it to an array
            if len(kpnt.shape)==0:
                kpnt=np.array([kpnt])
        else:
            raise Exception("\n\nHave to provide a k-vector!")
        # zero the Hamiltonian matrix
        ham = np.zeros((self._norb,self._norb),dtype=complex)
        for deg,vecR,ham1 in zip(self.deg_ws, self.Rvec_list, self.Hmat_list):
            for ham12 in ham1:
                i,j,amp = ham12
                # vector from one site to another
                rv = -self._orb[i,:]+self._orb[j,:]+vecR
                # Calculate the hopping, see details in info/tb/tb.pdf
                phase=np.exp((2.0j)*np.pi*kpnt.dot(rv))
                amp *= phase/deg
                ham[i,j] += amp
        return ham

    def _sol_ham(self,ham,eig_vectors=False):
        """Solves Hamiltonian and returns eigenvectors, eigenvalues"""
        # check that matrix is hermitian
        if np.max(ham-ham.T.conj())>1.0E-9:
            raise Exception("\n\nHamiltonian matrix is not hermitian?!")
        #solve matrix
        if eig_vectors==False: # only find eigenvalues
            eval = np.linalg.eigvalsh(ham)
            # sort eigenvalues and convert to real numbers
            eval = _nicefy_eig(eval)
            return np.array(eval,dtype=float)
        else: # find eigenvalues and eigenvectors
            eval,eig = np.linalg.eigh(ham)
            # sort evectors, eigenvalues and convert to real numbers
            eval,eig = _nicefy_eig(eval,eig)
            # reshape eigenvectors if doing a spinfull calculation
            return eval, eig

    def k_uniform_mesh(self,mesh_size):
        r"""
        Returns a uniform grid of k-points that can be passed to
        passed to function :func:`pythtb.tb_model.solve_all`.  This
        function is useful for plotting density of states histogram
        and similar.

        Returned uniform grid of k-points always contains the origin.

        :param mesh_size: Number of k-points in the mesh in each
          periodic direction of the model.

        :returns:

          * **k_vec** -- Array of k-vectors on the mesh that can be
            directly passed to function  :func:`pythtb.tb_model.solve_all`.

        Example usage::

          # returns a 10x20x30 mesh of a tight binding model
          # with three periodic directions
          k_vec = my_model.k_uniform_mesh([10,20,30])
          # solve model on the uniform mesh
          my_model.solve_all(k_vec)

        """

        # get the mesh size and checks for consistency
        use_mesh=np.array(list(map(round,mesh_size)),dtype=int)
        if use_mesh.shape!=(self._dim_k,):
            print(use_mesh.shape)
            raise Exception("\n\nIncorrect size of the specified k-mesh!")
        if np.min(use_mesh)<=0:
            raise Exception("\n\nMesh must have positive non-zero number of elements.")

        # construct the mesh
        if self._dim_k==1:
            # get a mesh
            k_vec=np.mgrid[0:use_mesh[0]]
            # normalize the mesh
            norm=np.tile(np.array(use_mesh,dtype=float),use_mesh)
            norm=norm.reshape(use_mesh.tolist()+[1])
            norm=norm.transpose([1,0])
            k_vec=k_vec/norm
            # final reshape
            k_vec=k_vec.transpose([1,0]).reshape([use_mesh[0],1])
        elif self._dim_k==2:
            # get a mesh
            k_vec=np.mgrid[0:use_mesh[0],0:use_mesh[1]]
            # normalize the mesh
            norm=np.tile(np.array(use_mesh,dtype=float),use_mesh)
            norm=norm.reshape(use_mesh.tolist()+[2])
            norm=norm.transpose([2,0,1])
            k_vec=k_vec/norm
            # final reshape
            k_vec=k_vec.transpose([1,2,0]).reshape([use_mesh[0]*use_mesh[1],2])
        elif self._dim_k==3:
            # get a mesh
            k_vec=np.mgrid[0:use_mesh[0],0:use_mesh[1],0:use_mesh[2]]
            # normalize the mesh
            norm=np.tile(np.array(use_mesh,dtype=float),use_mesh)
            norm=norm.reshape(use_mesh.tolist()+[3])
            norm=norm.transpose([3,0,1,2])
            k_vec=k_vec/norm
            # final reshape
            k_vec=k_vec.transpose([1,2,3,0]).reshape([use_mesh[0]*use_mesh[1]*use_mesh[2],3])
        else:
            raise Exception("\n\nUnsupported dim_k!")

        return k_vec

    def k_path(self,kpts,nk,report=True):
        r"""

        Interpolates a path in reciprocal space between specified
        k-points.  In 2D or 3D the k-path can consist of several
        straight segments connecting high-symmetry points ("nodes"),
        and the results can be used to plot the bands along this path.

        The interpolated path that is returned contains as
        equidistant k-points as possible.

        :param kpts: Array of k-vectors in reciprocal space between
          which interpolated path should be constructed. These
          k-vectors must be given in reduced coordinates.  As a
          special case, in 1D k-space kpts may be a string:

          * *"full"*  -- Implies  *[ 0.0, 0.5, 1.0]*  (full BZ)
          * *"fullc"* -- Implies  *[-0.5, 0.0, 0.5]*  (full BZ, centered)
          * *"half"*  -- Implies  *[ 0.0, 0.5]*  (half BZ)

        :param nk: Total number of k-points to be used in making the plot.

        :param report: Optional parameter specifying whether printout
          is desired (default is True).

        :returns:

          * **k_vec** -- Array of (nearly) equidistant interpolated
            k-points. The distance between the points is calculated in
            the Cartesian frame, however coordinates themselves are
            given in dimensionless reduced coordinates!  This is done
            so that this array can be directly passed to function
            :func:`pythtb.tb_model.solve_all`.

          * **k_dist** -- Array giving accumulated k-distance to each
            k-point in the path.  Unlike array *k_vec* this one has
            dimensions! (Units are defined here so that for an
            one-dimensional crystal with lattice constant equal to for
            example *10* the length of the Brillouin zone would equal
            *1/10=0.1*.  In other words factors of :math:`2\pi` are
            absorbed into *k*.) This array can be used to plot path in
            the k-space so that the distances between the k-points in
            the plot are exact.

          * **k_node** -- Array giving accumulated k-distance to each
            node on the path in Cartesian coordinates.  This array is
            typically used to plot nodes (typically special points) on
            the path in k-space.

        Example usage::

          # Construct a path connecting four nodal points in k-space
          # Path will contain 401 k-points, roughly equally spaced
          path = [[0.0, 0.0], [0.0, 0.5], [0.5, 0.5], [0.0, 0.0]]
          (k_vec,k_dist,k_node) = my_model.k_path(path,401)
          # solve for eigenvalues on that path
          evals = tb.solve_all(k_vec)
          # then use evals, k_dist, and k_node to plot bandstructure
          # (see examples)

        """

        # processing of special cases for kpts
        if kpts=='full':
            # full Brillouin zone for 1D case
            k_list=np.array([[0.],[0.5],[1.]])
        elif kpts=='fullc':
            # centered full Brillouin zone for 1D case
            k_list=np.array([[-0.5],[0.],[0.5]])
        elif kpts=='half':
            # half Brillouin zone for 1D case
            k_list=np.array([[0.],[0.5]])
        else:
            k_list=np.array(kpts)

        # in 1D case if path is specified as a vector, convert it to an (n,1) array
        if len(k_list.shape)==1 and self._dim_k==1:
            k_list=np.array([k_list]).T

        # make sure that k-points in the path have correct dimension
        if k_list.shape[1]!=self._dim_k:
            print('input k-space dimension is',k_list.shape[1])
            print('k-space dimension taken from model is',self._dim_k)
            raise Exception("\n\nk-space dimensions do not match")

        # must have more k-points in the path than number of nodes
        if nk<k_list.shape[0]:
            raise Exception("\n\nMust have more points in the path than number of nodes.")

        # number of nodes
        n_nodes=k_list.shape[0]

        # extract the lattice vectors from the TB model
        lat_per=np.copy(self._lat)
        # compute k_space metric tensor
        k_metric = np.linalg.inv(np.dot(lat_per,lat_per.T))

        # Find distances between nodes and set k_node, which is
        # accumulated distance since the start of the path
        #  initialize array k_node
        k_node=np.zeros(n_nodes,dtype=float)
        for n in range(1,n_nodes):
            dk = k_list[n]-k_list[n-1]
            dklen = np.sqrt(np.dot(dk,np.dot(k_metric,dk)))
            k_node[n]=k_node[n-1]+dklen

        # Find indices of nodes in interpolated list
        node_index=[0]
        for n in range(1,n_nodes-1):
            frac=k_node[n]/k_node[-1]
            node_index.append(int(round(frac*(nk-1))))
        node_index.append(nk-1)

        # initialize two arrays temporarily with zeros
        #   array giving accumulated k-distance to each k-point
        k_dist=np.zeros(nk,dtype=float)
        #   array listing the interpolated k-points
        k_vec=np.zeros((nk,self._dim_k),dtype=float)

        # go over all kpoints
        k_vec[0]=k_list[0]
        for n in range(1,n_nodes):
            n_i=node_index[n-1]
            n_f=node_index[n]
            kd_i=k_node[n-1]
            kd_f=k_node[n]
            k_i=k_list[n-1]
            k_f=k_list[n]
            for j in range(n_i,n_f+1):
                frac=float(j-n_i)/float(n_f-n_i)
                k_dist[j]=kd_i+frac*(kd_f-kd_i)
                k_vec[j]=k_i+frac*(k_f-k_i)

        if report==True:
            if self._dim_k==1:
                print(' Path in 1D BZ defined by nodes at '+str(k_list.flatten()))
            else:
                print('----- k_path report begin ----------')
                original=np.get_printoptions()
                np.set_printoptions(precision=5)
                print('real-space lattice vectors\n', lat_per)
                print('k-space metric tensor\n', k_metric)
                print('internal coordinates of nodes\n', k_list)
                if (lat_per.shape[0]==lat_per.shape[1]):
                    # lat_per is invertible
                    lat_per_inv=np.linalg.inv(lat_per).T
                    print('reciprocal-space lattice vectors\n', lat_per_inv)
                    # cartesian coordinates of nodes
                    kpts_cart=np.tensordot(k_list,lat_per_inv,axes=1)
                    print('cartesian coordinates of nodes\n',kpts_cart)
                print('list of segments:')
                for n in range(1,n_nodes):
                    dk=k_node[n]-k_node[n-1]
                    dk_str=_nice_float(dk,7,5)
                    print('  length = '+dk_str+'  from ',k_list[n-1],' to ',k_list[n])
                print('node distance list:', k_node)
                print('node index list:   ', np.array(node_index))
                np.set_printoptions(precision=original["precision"])
                print('----- k_path report end ------------')
            print()

        return (k_vec,k_dist,k_node)

def _nicefy_eig(eval,eig=None):
    "Sort eigenvaules and eigenvectors, if given, and convert to real numbers"
    # first take only real parts of the eigenvalues
    eval=np.array(eval.real,dtype=float)
    # sort energies
    args=eval.argsort()
    eval=eval[args]
    if not (eig is None):
        eig=eig[args]
        return (eval,eig)
    return eval

# for nice justified printout
def _nice_float(x,just,rnd):
    return str(round(x,rnd)).rjust(just)
def _nice_int(x,just):
    return str(x).rjust(just)
def _nice_complex(x,just,rnd):
    ret=""
    ret+=_nice_float(complex(x).real,just,rnd)
    if complex(x).imag<0.0:
        ret+=" - "
    else:
        ret+=" + "
    ret+=_nice_float(abs(complex(x).imag),just,rnd)
    ret+=" i"
    return ret


class w90(object):
    r"""

    This class of the PythTB package imports tight-binding model
    parameters from an output of a `Wannier90
    <http://www.wannier.org>`_ code.

    The `Wannier90 <http://www.wannier.org>`_ code is a
    post-processing tool that takes as an input electron wavefunctions
    and energies computed from first-principles using any of the
    following codes: Quantum-Espresso (PWscf), AbInit, SIESTA, FLEUR,
    Wien2k, VASP.  As an output Wannier90 will create files that
    contain parameters for a tight-binding model that exactly
    reproduces the first-principles calculated electron band
    structure.

    The interface from Wannier90 to PythTB will use only the following
    files created by Wannier90:

    - *prefix*.win
    - *prefix*\_hr.dat
    - *prefix*\_centres.xyz
    - *prefix*\_band.kpt (optional)
    - *prefix*\_band.dat (optional)

    The first file (*prefix*.win) is an input file to Wannier90 itself. This
    file is needed so that PythTB can read in the unit cell vectors.

    To correctly create the second and the third file (*prefix*\_hr.dat and
    *prefix*\_centres.dat) one needs to include the following flags in the win
    file::

       hr_plot = True
       write_xyz = True
       translate_home_cell = False

    These lines ensure that *prefix*\_hr.dat and *prefix*\_centres.dat
    are written and that the centers of the Wannier functions written
    in the *prefix*\_centres.dat file are not translated to the home
    cell.  The *prefix*\_hr.dat file contains the onsite and hopping
    terms.

    The final two files (*prefix*\_band.kpt and *prefix*\_band.dat)
    are optional.  Please see documentation of function
    :func:`pythtb.w90.w90_bands_consistency` for more detail.

    So far we tested only Wannier90 version 2.0.1.

    .. warning:: For the time being PythTB is not optimized to be used
      with very large tight-binding models.  Therefore it is not
      advisable to use the interface to Wannier90 with large
      first-principles calculations that contain many k-points and/or
      electron bands.  One way to reduce the computational cost is to
      wannierize with Wannier90 only the bands of interest (for
      example, bands near the Fermi level).

    Units used throught this interface with Wannier90 are
    electron-volts (eV) and Angstroms.

    .. warning:: User needs to make sure that the Wannier functions
      computed using Wannier90 code are well localized.  Otherwise the
      tight-binding model might not interpolate well the band
      structure.  To ensure that the Wannier functions are well
      localized it is often enough to check that the total spread at
      the beginning of the minimization procedure (first total spread
      printed in .wout file) is not more than 20% larger than the
      total spread at the end of the minimization procedure.  If those
      spreads differ by much more than 20% user needs to specify
      better initial projection functions.

      In addition, please note that the interpolation is valid only
      within the frozen energy window of the disentanglement
      procedure.

    .. warning:: So far PythTB assumes that the position operator is
      diagonal in the tight-binding basis.  This is discussed in the
      :download:`notes on tight-binding formalism
      <misc/pythtb-formalism.pdf>` in Eq. 2.7.,
      :math:`\langle\phi_{{\bf R} i} \vert {\bf r} \vert \phi_{{\bf
      R}' j} \rangle = ({\bf R} + {\bf t}_j) \delta_{{\bf R} {\bf R}'}
      \delta_{ij}`.  However, this relation does not hold for Wannier
      functions!  Therefore, if you use tight-binding model derived
      from this class in computing Berry-like objects that involve
      position operator such as Berry phase or Berry flux, you would
      not get the same result as if you computed those objects
      directly from the first-principles code!  Nevertheless, this
      approximation does not affect other properties such as band
      structure dispersion.

    For the testing purposes user can download the following
    :download:`wannier90 output example
    <misc/wannier90_example.tar.gz>` and use the following
    :ref:`script <w90_quick>` to test the functionality of the interface to
    PythTB. Run the following command in unix terminal to decompress
    the tarball::

        tar -zxf wannier90_example.tar.gz

    and then run the following :ref:`script <w90_quick>` in the same
    folder.

    :param path: Relative path to the folder that contains Wannier90
       files.  These are *prefix*.win, *prefix*\_hr.dat,
       *prefix*\_centres.dat and optionally *prefix*\_band.kpt and
       *prefix*\_band.dat.

    :param prefix: This is the prefix used by Wannier90 code.
        Typically the input to the Wannier90 code is name *prefix*.win.

    Initially this function will read in the entire Wannier90 output.
    To create :class:`pythtb.tb_model` object user needs to call
    :func:`pythtb.w90.model`.

    Example usage::

      # reads Wannier90 from folder called *example_a*
      # it assumes that that folder contains files "silicon.win" and so on
      silicon=w90("example_a", "silicon")

    """

    def __init__(self,path,prefix):
        # store path and prefix
        self.path=path
        self.prefix=prefix

        # read in lattice_vectors
        f=open(self.path+"/"+self.prefix+".win","r")
        ln=f.readlines()
        f.close()
        # get lattice vector
        self.lat=np.zeros((3,3),dtype=float)
        found=False
        for i in range(len(ln)):
            sp=ln[i].split()
            if len(sp)>=2:
                if sp[0].lower()=="begin" and sp[1].lower()=="unit_cell_cart":
                    # get units right
                    if ln[i+1].strip().lower()=="bohr":
                        pref=0.5291772108
                        skip=1
                    elif ln[i+1].strip().lower() in ["ang","angstrom"]:
                        pref=1.0
                        skip=1
                    else:
                        pref=1.0
                        skip=0
                    # now get vectors
                    for j in range(3):
                        sp=ln[i+skip+1+j].split()
                        for k in range(3):
                            self.lat[j,k]=float(sp[k])*pref
                    found=True
                    break
        if found==False:
            raise Exception( \
                    "Unable to find unit_cell_cart block in the .win file.")

        self.kgrid = None
        self.symbols = []
        self.atomic_positions = []
        read_position = 0
        for i,line in enumerate(ln):
            if "mp_grid" in line:
                line = line.split()
                self.kgrid = [int(x) for x in line[2:5]]
            elif "begin" in line and "atoms_cart" in line:
                read_position = 1
            elif "end" in line and "atoms_cart" in line:
                read_position = -1
            elif read_position > 0:
                if "bohr" in line.lower():
                    pref=0.5291772108
                elif "ang" in line.lower():
                    pref=1.0
                else:
                    line = line.split()
                    _symbol = line[0].split("_")[0]
                    symbol = _symbol[0:1].upper()
                    if len(_symbol) > 1:
                        symbol += _symbol[1:].lower()
                    self.symbols.append(symbol)
                    self.atomic_positions.append(
                            [float(x)*pref for x in line[1:4]])
            elif read_position < 0 and self.kgrid is not None:
                break

        if self.kgrid is None:
            raise Exception("Unable to find mp_grid!")

        # convert to scaled atomic position
        self.atomic_positions = np.asarray(self.atomic_positions).dot(\
                np.linalg.inv(self.lat))

        # read in hamiltonian matrix, in eV
        f=open(self.path+"/"+self.prefix+"_hr.dat","r")
        ln=f.readlines()
        f.close()
        #
        # get number of wannier functions
        self.num_wan=int(ln[1])
        # get number of Wigner-Seitz points
        num_ws=int(ln[2])
        ln = ln[3:]
        # get degenereacies of Wigner-Seitz points
        deg_ws=[]
        for j,ln1 in enumerate(ln):
            deg_ws.extend(map(int, ln1.split()))
            if len(deg_ws)==num_ws:
                ln = ln[j+1:]
                break
            if len(deg_ws)>num_ws:
                raise Exception("Too many degeneracies for WS points!")
        deg_ws = np.array(deg_ws,dtype=int)
        # now read in matrix elements
        # Convention used in w90 is to write out:
        # R1, R2, R3, i, j, ham_r(i,j,R)
        # where ham_r(i,j,R) corresponds to matrix element < i | H | j+R >
        Rvec_list = []
        Hmat_list = []
        for j,ln1 in enumerate(ln):
            ln1 = ln1.split()
            vecR = np.asarray(map(int, ln1[:3]))
            if j == 0 or not np.allclose(vecR, Rvec_list[-1]):
                Rvec_list.append(vecR)
                Hmat_list.append([])
            ia1, ia2 = map(int, ln1[3:5])
            val = float(ln1[5]) + 1.0j*float(ln1[6])
            Hmat_list[-1].append([ia1-1, ia2-1, val])
        if len(deg_ws) != len(Rvec_list):
            raise ValueError(" len(deg_ws) = {} vs len(Rvec_list) = {}". \
                    format(len(deg_ws), len(Rvec_list)))
        if len(deg_ws) != len(Hmat_list):
            raise ValueError(" len(deg_ws) = {} vs len(Hmat_list) = {}". \
                    format(len(deg_ws), len(Hmat_list)))
        self.Hmat_list = Hmat_list
        self.deg_ws = deg_ws
        self.Rvec_list = Rvec_list
        # read in wannier centers
        f=open(self.path+"/"+self.prefix+"_centres.xyz","r")
        ln=f.readlines()
        f.close()
        # Wannier centers in Cartesian, Angstroms
        xyz_cen=[]
        for i in range(2,2+self.num_wan):
            sp=ln[i].split()
            if sp[0]=="X":
                tmp=[]
                for j in range(3):
                    tmp.append(float(sp[j+1]))
                xyz_cen.append(tmp)
            else:
                raise Exception("Inconsistency in the centres file.")
        self.xyz_cen=np.array(xyz_cen,dtype=float)
        # get orbital positions in reduced coordinates
        self.red_cen = _cart_to_red((self.lat[0], self.lat[1], self.lat[2]), \
                self.xyz_cen)


    def model(self):
        """
        This function returns :class:`pythtb.tb_model` object that can
        be used to interpolate the band structure at arbitrary
        k-point, analyze the wavefunction character, etc.
        """
        # make the model object
        return tb_model(self.lat,self.red_cen,self.deg_ws,self.Rvec_list, \
                self.Hmat_list)


def _cart_to_red(tmp,cart):
    "Convert cartesian vectors cart to reduced coordinates of a1,a2,a3 vectors"
    (a1,a2,a3)=tmp
    # matrix with lattice vectors
    cnv=np.array([a1,a2,a3])
    # transpose a matrix
    cnv=cnv.T
    # invert a matrix
    cnv=np.linalg.inv(cnv)
    # reduced coordinates
    red=np.zeros_like(cart,dtype=float)
    for i in range(0,len(cart)):
        red[i]=np.dot(cnv,cart[i])
    return red

def _red_to_cart(tmp,red):
    "Convert reduced to cartesian vectors."
    (a1,a2,a3)=tmp
    # cartesian coordinates
    cart=np.zeros_like(red,dtype=float)
    for i in range(0,len(cart)):
        cart[i,:]=a1*red[i][0]+a2*red[i][1]+a3*red[i][2]
    return cart
