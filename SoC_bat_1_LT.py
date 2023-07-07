# -*- coding: utf-8 -*-

import pandas as pd

step = 0.25  # define timestep (h) (0.25: 15-min timestep)

demand =    # define hourly energy demand (kWh)
PV_gen =    # define hourly PV generation (kWh)


def pv():
    
    from_grid = pd.Series(data=0,index=demand.index)
    to_grid = pd.Series(data=0,index=demand.index)
    balance = pd.Series(data=0,index=demand.index)  
    
    for i in range(1,len(demand)):
        balance.iloc[i] = PV_gen.iloc[i] - demand.iloc[i]
        
        if balance.iloc[i] < 0:
            from_grid.iloc[i] = abs(balance.iloc[i])
        else:
            from_grid.iloc[i] = 0
            
        if balance.iloc[i] > 0:
            to_grid.iloc[i] = abs(balance.iloc[i])
        else:
            to_grid.iloc[i] = 0

    return balance, from_grid, to_grid
balance, from_grid, to_grid = pv()



# Short-term capacity & charging
# ---------------------------

b_step = balance*step

bat_max = 11.5     # useable capacity (kWh)
bat_min = 0.001
bat_initial = bat_min

discharge_lim = bat_max*0.5     # battery charging/discharging rate (kW)
charge_lim = discharge_lim

def pv_bat(bat_max):
        
        SoC = pd.Series(data=0,index=demand.index)
        from_bat = pd.Series(data=0,index=demand.index)
        to_bat = pd.Series(data=0,index=demand.index)
        from_grid_wb = pd.Series(data=0,index=demand.index)
        to_grid_wb = pd.Series(data=0,index=demand.index)

        SoC.iloc[0] = bat_initial
        
        for i in range(1,len(demand)):
            
            if b_step.iloc[i] <= -abs(discharge_lim*step):
                if SoC.iloc[i-1]+(b_step.iloc[i]) <= bat_min:
                    if b_step.iloc[i] <= -abs(discharge_lim*step) and SoC.iloc[i-1]+(-abs(discharge_lim*step)) > bat_min:
                        SoC.iloc[i] = SoC.iloc[i-1]+(-abs(discharge_lim*step))
                    else:
                        SoC.iloc[i] = bat_min
                else:
                    SoC.iloc[i] = SoC.iloc[i-1]+(-abs(discharge_lim*step))    
            
            elif b_step.iloc[i] >= abs(charge_lim*step):
                if SoC.iloc[i-1]+(b_step.iloc[i]) >= bat_max:
                    if b_step.iloc[i] >= abs(charge_lim*step) and SoC.iloc[i-1]+(abs(charge_lim*step)) < bat_max:
                        SoC.iloc[i] = SoC.iloc[i-1]+(abs(charge_lim*step))
                    else:
                        SoC.iloc[i] = bat_max
                else:
                    SoC.iloc[i] = SoC.iloc[i-1]+(abs(charge_lim*step))
                                
            elif b_step.iloc[i] < abs(charge_lim*step) and b_step.iloc[i] > -abs(discharge_lim*step):
                if SoC.iloc[i-1]+(b_step.iloc[i]) >= bat_max:
                    SoC.iloc[i] = bat_max
                elif SoC.iloc[i-1]+(b_step.iloc[i]) <= bat_min:
                    SoC.iloc[i] = bat_min
                else:
                    SoC.iloc[i] = SoC.iloc[i-1]+(b_step.iloc[i])
            
            if SoC.iloc[i]-SoC.iloc[i-1] < 0:
                from_bat.iloc[i] = (SoC.iloc[i]-SoC.iloc[i-1])/step
            else:
                from_bat.iloc[i] = 0
    
            if SoC.iloc[i]-SoC.iloc[i-1] > 0:
                to_bat.iloc[i] = (SoC.iloc[i]-SoC.iloc[i-1])/step
            else:
                to_bat.iloc[i] = 0
                
            if balance.iloc[i] < -abs(from_bat.iloc[i]):  
                from_grid_wb.iloc[i] = abs(balance.iloc[i])-abs(from_bat.iloc[i])  
            else:
                from_grid_wb.iloc[i] = 0
           
            if balance.iloc[i] > abs(to_bat.iloc[i]):
               to_grid_wb.iloc[i] = abs(balance.iloc[i])-abs(to_bat.iloc[i])
            else:
               to_grid_wb.iloc[i] = 0
        
        return SoC, from_bat, to_bat, from_grid_wb, to_grid_wb
        
SoC, from_bat, to_bat, from_grid_wb, to_grid_wb = pv_bat(bat_max)



# Long-term capacity & charging
# ---------------------------

H_max = 9000        # useable capacity of hydrogen storage (kWh)
H_min = 0.001
H_initial = H_min

discharge_lim_H = H_max*0.25
charge_lim_H = discharge_lim_H
n_conversion = 0.42                 # conversion efficiency in case of hydrogen storage


def pv_bat_LT(bat_max,H_max):
        
        SoC = pd.Series(data=0,index=demand.index)
        SoC_long = pd.Series(data=0,index=demand.index)
        from_bat = pd.Series(data=0,index=demand.index)
        to_bat = pd.Series(data=0,index=demand.index)
        from_LT = pd.Series(data=0,index=demand.index)
        to_LT = pd.Series(data=0,index=demand.index)
        from_grid_wb_LT = pd.Series(data=0,index=demand.index)
        to_grid_wb_LT = pd.Series(data=0,index=demand.index)
        
        SoC.iloc[0] = bat_initial
        SoC_long.iloc[0] = H_initial
        
        discharge_lim = bat_max*0.5
        charge_lim = discharge_lim
        
        for i in range(1,len(demand)):
            
            if b_step.iloc[i] <= -abs(discharge_lim*step):
                if SoC.iloc[i-1]+(b_step.iloc[i]) <= bat_min:
                    if b_step.iloc[i] <= -abs(discharge_lim*step) and SoC.iloc[i-1]+(-abs(discharge_lim*step)) > bat_min:
                        SoC.iloc[i] = SoC.iloc[i-1]+(-abs(discharge_lim*step))
                    else:
                        SoC.iloc[i] = bat_min
                else:
                    SoC.iloc[i] = SoC.iloc[i-1]+(-abs(discharge_lim*step))    
            
            elif b_step.iloc[i] >= abs(charge_lim*step):
                if SoC.iloc[i-1]+(b_step.iloc[i]) >= bat_max:
                    if b_step.iloc[i] >= abs(charge_lim*step) and SoC.iloc[i-1]+(abs(charge_lim*step)) < bat_max:
                        SoC.iloc[i] = SoC.iloc[i-1]+(abs(charge_lim*step))
                    else:
                        SoC.iloc[i] = bat_max
                else:
                    SoC.iloc[i] = SoC.iloc[i-1]+(abs(charge_lim*step))
                                
            elif b_step.iloc[i] < abs(charge_lim*step) and b_step.iloc[i] > -abs(discharge_lim*step):
                if SoC.iloc[i-1]+(b_step.iloc[i]) >= bat_max:
                    SoC.iloc[i] = bat_max
                elif SoC.iloc[i-1]+(b_step.iloc[i]) <= bat_min:
                    SoC.iloc[i] = bat_min
                else:
                    SoC.iloc[i] = SoC.iloc[i-1]+(b_step.iloc[i])
            
            if SoC.iloc[i]-SoC.iloc[i-1] < 0:
                from_bat.iloc[i] = (SoC.iloc[i]-SoC.iloc[i-1])/step
            else:
                from_bat.iloc[i] = 0
    
            if SoC.iloc[i]-SoC.iloc[i-1] > 0:
                to_bat.iloc[i] = (SoC.iloc[i]-SoC.iloc[i-1])/step
            else:
                to_bat.iloc[i] = 0
               
            
            # HYDROGEN STORAGE
            
            if SoC.iloc[i] >= bat_max:
                if SoC_long.iloc[i-1]+(b_step.iloc[i]*n_conversion) >= H_max:
                    SoC_long.iloc[i] = H_max
                else:
                    SoC_long.iloc[i] = SoC_long.iloc[i-1]+(b_step.iloc[i]*n_conversion)
            elif SoC.iloc[i] <= bat_min:
                if SoC_long.iloc[i-1]+(b_step.iloc[i]) <= H_min:
                    SoC_long.iloc[i] = H_min
                else:
                    SoC_long.iloc[i] = SoC_long.iloc[i-1]+(b_step.iloc[i])
            elif SoC.iloc[i] < bat_max and SoC.iloc[i] > bat_min:
                SoC_long.iloc[i] = SoC_long.iloc[i-1]           
 
            if SoC_long.iloc[i]-SoC_long.iloc[i-1] <= 0:
                from_LT.iloc[i] = (SoC_long.iloc[i]-SoC_long.iloc[i-1])/step
            else:
                from_LT.iloc[i] = 0
    
            if SoC_long.iloc[i]-SoC_long.iloc[i-1] >= 0:
                to_LT.iloc[i] = (SoC_long.iloc[i]-SoC_long.iloc[i-1])/step
            else:
                to_LT.iloc[i] = 0
 
    
            if balance.iloc[i] < 0:  
                 from_grid_wb_LT.iloc[i] = balance.iloc[i]-from_bat.iloc[i]-from_LT.iloc[i]  
            else:
                 from_grid_wb_LT.iloc[i] = 0
            
            if balance.iloc[i] > 0:
                to_grid_wb_LT.iloc[i] = balance.iloc[i]-to_bat.iloc[i]-to_LT.iloc[i]
            else:
                to_grid_wb_LT.iloc[i] = 0
                
        
        return SoC, SoC_long, from_bat, to_bat, from_LT, to_LT, from_grid_wb_LT, to_grid_wb_LT
        
SoC, SoC_long, from_bat, to_bat, from_LT, to_LT, from_grid_wb_LT, to_grid_wb_LT = pv_bat_LT(bat_max,H_max)
