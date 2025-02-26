      REAL*8 FUNCTION T3J (J1,J2,J3,M1,M2,M3)                           
! calculation of 3-j symbols according to formula (1.5) of
! M. Rottenberg et al.: the 3-j and 6-j symbols
! The Technology Press MIT, Cambridge- Massachsetts, 1959
! programmed and checked by P.Novak May, 1999 (novakp@fzu.cz)
!                                                                       
!     ARRAY FCT MUST BE DECLARED AND FILLED GLOBALLY WITH               
!     J-FACTORIAL IN THE 2J+1 POSITION                                  
!     LARGEST  FACTORIAL NEEDED IS JA+JB+JC+1                           
!     FUNCTION NOTRI(J,K,L) RETURNS 1 IF K,L,J FORM A TRIANGLE,-1 IF NOT
      IMPLICIT REAL*8 (A-H,O-Z)
      COMMON/FACT/FCT(0:100),nfac   

      nfac=20
      call fac()
! check the conditions
      t3j=0.
      IF((M1+M2+M3).NE.0) then                                          
      return
      endif
      IF(NOTRI(J1,J2,J3).LT.0)then
      return
      endif
! calculation of prefactor
      L1=j1+j2-j3
      L2=j1-j2+j3
      L3=-j1+j2+j3
      L4=j1+m1
      L5=j1-m1
      L6=j2+m2
      L7=j2-m2
      L8=j3+m3
      L9=j3-m3
      Lb= j1+j2+j3+1
      if(lb.gt.nfac)then
      write(0,*)' Not enough factorials',lb,' is minimum - stop'
      stop
      endif
      a1=fct(j1+j2-j3)
      a2=fct(j1-j2+j3)
      a3=fct(-j1+j2+j3)
      a4=fct(j1+m1)
      a5=fct(j1-m1)
      a6=fct(j2+m2)
      a7=fct(j2-m2)
      a8=fct(j3+m3)
      a9=fct(j3-m3)
      b= fct(j1+j2+j3+1)
      J=J1-J2-M3                                              
      sgJ=(-1)**(J)                                              
      C=sgJ*SQRT(a1*a2*a3*a4*a5*a6*a7*a8*a9/b)
! lower and upper limit of the sum over k
      K0=J1+J2-J3                                                       
      K1=J1-M1                                                          
      K2=J2+M2                                                          
      L1=J2-J3-M1                                                       
      L2=J1-J3+M2                                                       
      KMAX=MIN0(K1,K2,K0)                                             
      KMIN=MAX0(0,L1,L2)                                             
! sum over k starts here
      T3J=0.                                                            
      DO 10 K=KMIN,KMAX                                               
      L1=k
      L2=j1+j2-j3-k
      L3=j1-m1-k
      L4=j2+m2-k
      L5=j3-j2+m1+k
      L6=j3-j1-m2+k
      a1=fct(k)
      a2=fct(j1+j2-j3-k)
      a3=fct(j1-m1-k)
      a4=fct(j2+m2-k)
      a5=fct(j3-j2+m1+k)
      a6=fct(j3-j1-m2+k)
      sgk=(-1)**k
      T3J=T3J+sgk/(a1*a2*a3*a4*a5*a6)        
   10 CONTINUE                                                          
! end of the sum
      T3J=C*T3J                                              
      t32=t3j**2
      return
      END                                                               
! *********************************************************************
      function notri(j1,j2,j3)
!     check the triangular rule
      notri=1
      if((j1+j2-j3).lt.0)notri=-1
      if((j1-j2+j3).lt.0)notri=-1
      if((-j1+j2+j3).lt.0)notri=-1
      return
      end
! ********************************************************************
       subroutine fac
       implicit real*8(a-h,o-z)
       common/fact/fct(0:100),nfac
      fct(0)=1.
      f=0.
      do i=1,nfac
      f=f+1.
      fct(i)=fct(i-1)*f
      enddo
      return
      end
