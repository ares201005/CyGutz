!******************************************************************************
! Copyright c 2013, The Ames Laboratory, Iowa State University, and Rutgers
! University*.  All rights reserved.
!
! This software was authored by Yongxin Yao, Nicola Lanata*, Gabriel Kotliar*,
! Cai-Zhuang Wang, and Kai-Ming Ho, at The Ames Laboratory and
! Rutgers University and was supported by the U.S.
! Department of Energy (DOE), Office of Science,
! Basic Energy Sciences, Materials Science and Engineering Division.
! The Ames Laboratory is operated by Iowa State University for DOE
! under U.S. Government contract DE-AC02-07CH11358.
! The U.S. Government has the rights to use, reproduce, and
! distribute this software.
! NEITHER THE GOVERNMENT, THE AMES LABORATORY, IOWA STATE UNIVERSITY,
! NOR RUTGERS UNIVERSITY MAKES ANY WARRANTY,
! EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.
! If software is modified to produce derivative works,
! such modified software should be clearly marked,
! so as to not confuse it with the version available from
! The Ames Laboratory and Rutgers University.
!
! Additionally, redistribution and use in source and binary forms,
! with or without modification,
! are permitted provided that the following conditions are met:
!
!     Redistribution of source code must retain the above copyright notice,
!     this list of conditions, and the following disclaimer.
!
!     Redistribution in binary form must reproduce the above copyright notice,
!     this list of conditions, and the following disclaimer
!     in the documentation and/or other materials provided with distribution.
!
!     Neither the name of The Ames Laboratory, Iowa State University,
!     Rutgers University, the U.S. Government, nor the names of
!     its contributors may be used to endorse or promote products derived
!     from this software without specific prior written permission.
!
! THIS SOFTWARE IS PROVIDED BY THE AMES LABORATORY, IOWA STATE UNIVERSITY,
! RUTGERS UNIVERSITY, AND CONTRIBUTORS "AS IS"
! AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
! THE IMPLIED WARRANTIES OF MERCHANTABILITY
! AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
! IN NO EVENT SHALL THE GOVERNMENT, THE AMES LABORATORY,
! IOWA STATE UNIVERSITY, RUTGERS UNIVERSITY, OR CONTRIBUTORS BE LIABLE
! FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
! EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
! PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
! LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
! HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
! WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
! OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
! EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
!******************************************************************************

module gspci
    ! sparse-matrix based CI, with impurity-bath basis.
    use gprec
    use gprimme
    use sparse
    use gutil
    use ghdf5_base
    use gtime
    implicit none

    type gspci_mem
        integer::norb,norb2,nstates=0,nval_bot,nval_top,norb_mott=0, &
                &nelect_mott=0,imp, &
                &sjz=1 ! sjz=0: use sz; sjz=1: use jz.
        type(dcoo_matrix),pointer::mcoo(:,:),nvcoo(:,:),npcoo(:,:)
        integer,pointer::bs(:),ibs(:),idx(:),bs_l(:),ibs_l(:),idx_l(:), &
                &iorb_mott(:)=>null(),m_struct(:,:), &
                &mem_binom(:,:)
        type(ivector),allocatable::i_phi(:)
        real(q),pointer::bs_sz(:)=>null(),bs_sz_l(:)=>null(), &
                &sz_orb(:)=>null()
        complex(q),pointer::h1e(:,:),daalpha(:,:),lambdac(:,:), &
                &v2e(:,:,:,:),dm(:,:),v(:), &
                &svec(:,:,:)=>null(),lvec(:,:,:)=>null(), &
                &jvec(:,:,:)=>null(),jn(:,:)=>null()
        type(zcsr_matrix)::ucsr
        real(q)::lambda_j2=.0_q,etot
    end type gspci_mem

    type(gspci_mem)::dmem
    private
    public::gspci_mem,dmem,gspci_gh5exe,setup_hdns_spci,av1_gspci

    contains


    subroutine gspci_gh5exe()
    integer j,ierr,nv,idx
    character*32 str
    real(q) etot,de
    complex(q) zes
    logical lexist
    character(255) cmd


    call get_command(cmd)
    idx=index(cmd,'-i ')
    if(idx>0)then
        read(cmd(idx+2:),*)dmem%imp
    else
        ! By default, work with the 1st impurity
        dmem%imp=1
    endif
    write(0,'(" solving impurity ", i2)')dmem%imp
    idx=index(cmd,'-sz ')
    if(idx>0)then
        dmem%sjz=0
        write(0,'(" with Sz contraints. ")')
    else
        write(0,'(" with Jz contraints. ")')
    endif
   
    call gh5_init()
    call gh5_open_r('EMBED_HAMIL_'//trim(int_to_str(dmem%imp))//'.h5',f_id)
    call gh5_read(dmem%norb,'/na2',f_id)
    call gh5_read(dmem%nval_bot,'/nval_bot',f_id)
    call gh5_read(dmem%nval_top,'/nval_top',f_id)
    allocate(dmem%m_struct(dmem%norb,dmem%norb))
    call gh5_read(dmem%m_struct,dmem%norb,dmem%norb,'/sigma_struct',f_id)
    dmem%norb2=dmem%norb*2
    allocate(dmem%h1e(dmem%norb,dmem%norb), &
            &dmem%daalpha(dmem%norb,dmem%norb), &
            &dmem%lambdac(dmem%norb,dmem%norb), &
            &dmem%v2e(dmem%norb,dmem%norb,dmem%norb,dmem%norb), &
            &dmem%dm(dmem%norb2,dmem%norb2))
    call gh5_read(dmem%h1e,dmem%norb,dmem%norb,'/H1E',f_id)
    call gh5_read(dmem%daalpha,dmem%norb,dmem%norb,'/D',f_id)
    call gh5_read(dmem%lambdac,dmem%norb,dmem%norb,'/LAMBDA',f_id)
    call gh5_read(dmem%v2e,dmem%norb,dmem%norb,dmem%norb,dmem%norb,'/V2E',f_id)
    call gh5_read(dmem%norb_mott,'/norb_mott',f_id)
    if(dmem%norb_mott>0)then
        call gh5_read(dmem%nelect_mott,'/nelect_mott',f_id)
        allocate(dmem%iorb_mott(dmem%norb_mott))
        call gh5_read(dmem%iorb_mott,dmem%norb_mott,'/iorb_mott',f_id)
    endif
    call gh5_close(f_id)

    ! get jz or sz for the spin-orbitals
    call gh5_open_r('GPARAM.h5',f_id)
    allocate(dmem%svec(dmem%norb,dmem%norb,1))
    call gh5_read(dmem%svec(:,:,1),dmem%norb,dmem%norb,'/IMPURITY_'// &
            &trim(int_to_str(dmem%imp))//'/SZ',f_id)
    allocate(dmem%lvec(dmem%norb,dmem%norb,1))
    call gh5_read(dmem%lvec(:,:,1),dmem%norb,dmem%norb,'/IMPURITY_'// &
            &trim(int_to_str(dmem%imp))//'/LZ',f_id)
    call gh5_close(f_id)

    allocate(dmem%sz_orb(dmem%norb))
    do j=1,dmem%norb
        dmem%sz_orb(j)=dmem%svec(j,j,1)
        if(dmem%sjz==1)then
            dmem%sz_orb(j)=dmem%sz_orb(j)+dmem%lvec(j,j,1)
        endif
    enddo

    call init_gspci_mem()

    ! Check previous solution vector
    inquire(file='EMBED_HAMIL_RES_'//trim(int_to_str(dmem%imp))//'.h5', &
            &exist=lexist)
    if(lexist)then
        call gh5_open_r('EMBED_HAMIL_RES_'//trim(int_to_str(dmem%imp)) &
                &//'.h5',f_id)
        call gh5_read(nv,'/dimv',f_id)
        if(nv==dmem%nstates)then
            allocate(dmem%v(nv))
            call gh5_read(dmem%v,nv,'/evec',f_id)
        else
            write(0,'(" existing solution vec does not match in dimension,")')
            write(0,'(" choose random vector to initialize!")')
        endif
        call gh5_close(f_id)
    endif

    call calc_save_rho_cp_blks(dmem%imp)

    return

    end subroutine gspci_gh5exe


    subroutine init_gspci_mem()
    
    allocate(dmem%mem_binom(dmem%norb,0:dmem%norb))
    call set_binoms(dmem%norb,dmem%mem_binom)
    call set_fock_state_indices(dmem%norb,dmem%mem_binom,dmem%idx,dmem%bs, &
            &dmem%ibs,dmem%bs_sz,dmem%sz_orb)
    call set_full_fock_states_l_spci()
    call set_mncoo_spci()
    call calc_ucsr_spci()
    return

    end subroutine init_gspci_mem


    subroutine setup_hdns_spci(a,n)
    integer,intent(in)::n
    complex(q),intent(out)::a(n,n)

    call setup_hdns_spci_dlh(a,n)
    return

    end subroutine setup_hdns_spci


    subroutine av1_gspci(v1,v2)
    complex(q),intent(in)::v1(*)
    complex(q),intent(out)::v2(*)

    call av1_gspci_dlh(v1,v2)
    return

    end subroutine av1_gspci   


end module gspci
