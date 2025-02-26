      subroutine inouh (dp,dq,dr,dq1,dfl,dv,z,test,nstop)        

!                                                                       
! valeurs initiales pour l integration vers l exrerieur                 
! dp grande composante    dq petite composante    dr bloc des points    
! dq1 pente a l origine de dp ou dq    dfl puissance du premier terme   
! du developpement limite   dv potentiel au premier point               
! z numero atomique    test test de precision                           
! noyau de dimensions finies si nuc non nul                             
! nstop controle la convergence du developpement limite                 
! **********************************************************************'
      USE param
      implicit real*8 (a-h,o-z)

      common /ps1/ dep(5),deq(5),dd,dvc,dsal,dk,dm1                        
      save   /ps1/

!                                                                       
! dep,deq derivees de dp et dq   dd=energie/dvc    dvc vitesse de la    
! lumiere en u.a.   dsal=2.*dvc   dk nombre quantique kappa             
! dm=pas exponentiel/720.                                               
! **********************************************************************
      common/trois/ dpno(4,30),dqno(4,30)                               
      dimension dp(nrad),dq(nrad),dr(nrad) 

      nuc = 0
      do i=1,10                                                       
        dp(i)=0.                                                          
        dq(i)=0.
      enddo                                                          

      if (nuc.le.0) then
        dval=z/dvc                                                        
        deva1=-dval                                                       
        deva2=dv/dvc+dval/dr(1)-dd                                        
        deva3=0.                                                          
        if (dk.le.0) then
          dbe=(dk-dfl)/dval                                                 
        else
          dbe=dval/(dk+dfl)                                                 
        endif
        dq(10)=dq1                                                        
        dp(10)=dbe*dq1
      else
        dval=dv+z*(3.-dr(1)*dr(1)/(dr(nuc)*dr(nuc)))/(dr(nuc)+dr(nuc))    
        deva1=0.                                                          
        deva2=(dval-3.*z/(dr(nuc)+dr(nuc)))/dvc-dd                        
        deva3=z/(dr(nuc)*dr(nuc)*dr(nuc)*dsal)                            
        if (dk.le.0.d0) then
          dp(10)=dq1                                                        
        else
          dq(10)=dq1                                                        
        endif
      endif
      do i=1,5                                                       
        dp(i)=dp(10)                                                      
        dq(i)=dq(10)                                                      
        dep(i)=dp(i)*dfl                                                  
        deq(i)=dq(i)*dfl                                                  
      enddo
      m=1                                                               
 41   dm=m+dfl                                                          
      dsum=dm*dm-dk*dk+deva1*deva1                                      
      dqr=(dsal-deva2)*dq(m+9)-deva3*dq(m+7)                            
      dpr=deva2*dp(m+9)+deva3*dp(m+7)                                   
      dval=((dm-dk)*dqr-deva1*dpr)/dsum                                 
      dsum=((dm+dk)*dpr+deva1*dqr)/dsum                                 
      j=-1                                                              
      do i=1,5                                                       
        dpr=dr(i)**m                                                      
        dqr=dsum*dpr                                                      
        dpr=dval*dpr                                                      
        if (m.ne.1) then
          if (abs(dpr/dp(i)).le.test.and.abs(dqr/dq(i)).le.test) j=1        
        endif
        dp(i)=dp(i)+dpr                                                   
        dq(i)=dq(i)+dqr                                                   
        dep(i)=dep(i)+dpr*dm                                              
        deq(i)=deq(i)+dqr*dm                                              
      enddo
      if (j.ne.1) then
        dp(m+10)=dval                                                     
        dq(m+10)=dsum                                                     
        m=m+1                                                             
        if (m.gt.20) then
          nstop=45        
        else
          goto 41
        endif
      endif                                                  
      return                                                            
      end                                                               
