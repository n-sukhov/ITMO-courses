[Transient Analysis]
{
   Npanes: 1
   {
      traces: 1 {524290,0,"V(vout2)"}
      X: ('m',1,0,0.0004,0.004)
      Y[0]: (' ',0,-16,2,2)
      Y[1]: ('m',4,1e+308,2e-07,-1e+308)
      Volts: (' ',0,0,1,-16,2,2)
      Log: 0 0 0
      GridStyle: 1
      PltMag: 1
      PltPhi: 1 0
   }
}
[DC transfer characteristic]
{
   Npanes: 1
   {
      traces: 1 {524290,0,"V(vout1)"}
      X: (' ',1,-16.5,3,16.5)
      Y[0]: (' ',0,-2,2,16)
      Y[1]: ('_',0,1e+308,0,-1e+308)
      Volts: (' ',0,0,0,-2,2,16)
      Log: 0 0 0
      GridStyle: 1
   }
}
