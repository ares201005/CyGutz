      SUBROUTINE SPHBES(N,X,FJ)                                         
      IMPLICIT REAL*8 (A-H,O-Z)
      DIMENSION FJ(*)                                                   
      DATA XLIM/0.1D0/,HF/0.5D0/,ZERO/0.0D0/,ONE/1.0D0/,TWO/2.0D0/, &
      TNHF/10.5D0/,     &
           FFT/15.0D0/,T25/1.0D25/,TN25/1.0D-25/,TN50/1.0D-50/          
!***********************************************************************
!***  VERSION III-UPPER LIMIT OBTAINED FROM THE EXPRESSIONS OF          
!***             CORBATO AND URETSKY USING A LIMIT OF E SUB M OF        
!***             2**-30 WHICH IS APPROXIMATELY 1.E-9                    
!***            SUMMATION PROPERTY USED TO NORMALIZE RESULTS.           
!***  ADDITIONAL FACTOR ADDED TO STARTING VALUE                         
!***  N IS THE MAXIMUM L TO BE CALCULATED                               
!***  X IS THE ARGUMENT                                                 
!***  FJ IS THE ARRAY THAT THE SPHERICAL BESSEL FUNCTIONS ARE TO BE     
!***  PLACED IN.                                                        
!*****  MODIFIED TO NOT REQUIRE THE WORKING SPACE.                      
!*****        29 MAY,1968                                               
!***********************************************************************
      IF(N.GE.0) GOTO 7                                                 
    1 PRINT 2                                                           
    2 FORMAT (33H1 ERROR, N SHOULD NOT BE NEGATIVE  )                   
      GO TO 99                                                          
  7   IF (X.GE.ZERO)  GO TO 10                                          
    8 PRINT 9                                                           
    9 FORMAT (33H1 ERROR, X SHOULD NOT BE NEGATIVE  )                   
      GO TO 99                                                          
  10  IF (X.GT.XLIM) GO TO 25                                           
      HFXSQ=HF*X*X                                                      
      XL=ONE                                                            
      TWM=ONE                                                           
      M=0                                                               
  11  M=M+1                                                             
      TA=XL                                                             
      TWM=TWM+TWO                                                       
      XL=XL/TWM                                                         
      TA=TA-XL*HFXSQ                                                    
      XLP=XL/(TWM+TWO)                                                  
      FJ(M)=TA+HF*XLP*HFXSQ*HFXSQ                                        
      XL=XL*X                                                           
      IF (M.LE.N)  GO TO 11                                             
   15 RETURN                                                            
  25  CUFAC=4.2D0                                                       
      IF (X.LT.(N-2)) CUFAC=TNHF/(N+HF-X)                               
      NS=N+5+X*CUFAC                                                    
!*******************  ADD ADDITIONAL FACTOR  ***************************
      NS=NS + (FFT/(ONE+SQRT(X)))                                       
!***********************************************************************
  30  CONTINUE                                                          
 313  FFO=ZERO                                                          
      FFN=TN25                                                          
      M=NS-1                                                            
      XI=ONE/X                                                          
      FM=(M+M)+ONE                                                      
      SDR=FM*TN50                                                       
 314  FFP=FM*XI*FFN-FFO                                                 
      IF (ABS(FFP).LT.T25) GO TO 315                                    
      SDR=SDR*TN50                                                      
      FFP=FFP*TN25                                                      
      FFN=FFN*TN25                                                      
 315  SDR=SDR + (FM-TWO)*FFP*FFP                                        
      FFO=FFN                                                           
      FFN=FFP                                                           
      IF (M.LE.N) GO TO 316                                             
      M=M-1                                                             
      FM=FM-TWO                                                         
      GO TO 314                                                         
 316  FJ(M)=FFN                                                         
      FJ(M+1)=FFO                                                       
      GO TO 33                                                          
  32  FJ(M)=FM*XI*FJ(M+1)-FJ(M+2)                                       
      IF(ABS(FJ(M)).GE.T25) GO TO 56                                    
      SDR=SDR + (FM-TWO)*FJ(M)*FJ(M)                                    
      IF (M.LE.1) GO TO 34                                              
   33 M = M-1                                                           
      FM=FM-TWO                                                         
      GO TO 32                                                          
 34   SER=ONE/SQRT(SDR)                                                 
   39 MM = N+1                                                          
      DO 40 M=1,MM                                                      
      FJ(M)=FJ(M)*SER                                                   
  40  CONTINUE                                                          
      GO TO 98                                                          
   56 JJ= M+1                                                           
      NS=N+1                                                            
      DO 57 J = JJ,NS                                                   
      FJ(J)=FJ(J)*TN25                                                  
  57  CONTINUE                                                          
      SDR=SDR*TN50                                                      
      GO TO 32                                                          
   99 CALL OUTERR('SPHBES','look in output.')
      STOP 'SPHBES - Error'
   98 RETURN                                                            
      END                                                               
