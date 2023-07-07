# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from datetime import datetime

step = 0.25  # define timestep (h) (0.25: 15-min timestep)

time =      # datettime index
demand =    # define hourly energy demand (kWh)
PV_gen =    # define hourly PV generation (kWh)
people = demand['People']   # define hourly occupancy (for example based on internal gains due to occupancy); 0=away, 1=at home
EV_home = pd.Series(np.where(people > 0, 1, 0),index=demand.index)


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

b_step = balance*step

# EV battery capacity & charging
# ---------------------------

# max 40 kWh, min 15.6 kWh 

EVbat_max = 40     
EVbat_min1 = 15.6
EVbat_min2 = 10
EVbat_initial = EVbat_min1
EVbat_nc = EVbat_max - EVbat_min1

charge_lim_EV = 3.7
discharge_lim_EV = charge_lim_EV

EV_home.iloc[0] = 1

def pv_EVbat(EVbat_max):
    
        EV_home_day_temp = EV_home.resample('D').sum()
        for i in range(0,len(EV_home_day_temp)):
            if EV_home_day_temp.iloc[i] < 96:
                EV_home_day_temp.iloc[i] = 0
            else:
                EV_home_day_temp.iloc[i] = 1
                
        EV_home_day = EV_home_day_temp.resample('15T').ffill()

        hours = time.dt.hour
        g2v = pd.Series(data=0,index=demand.index)

        for i in range(0,len(g2v)):
            if hours.iloc[i] >= 12 and EV_home.iloc[i] > 0:
                g2v.iloc[i] = charge_lim_EV*step
            elif hours.iloc[i] < 6 and EV_home.iloc[i] > 0:
                g2v.iloc[i] = charge_lim_EV*step
            else:
                g2v.iloc[i] = 0
        
        SoC_EV = pd.Series(data=0,index=demand.index)
        SoC_EV_temp = pd.Series(data=0,index=demand.index)
        from_EVbat = pd.Series(data=0,index=demand.index)
        PV_to_EVbat = pd.Series(data=0,index=demand.index)
        from_grid_EV = pd.Series(data=0,index=demand.index)
        from_grid_total = pd.Series(data=0,index=demand.index)
        to_grid_EV = pd.Series(data=0,index=demand.index)

        SoC_EV.iloc[0] = EVbat_initial
        
        g2v_charging = pd.Series(data=0,index=demand.index)
        
        for i in range(1,len(demand)):
                            
            if EV_home.iloc[i] > 0  and EV_home.iloc[i-1] > 0 and EV_home_day.iloc[i] > 0:
            
                    if b_step.iloc[i] <= -abs(discharge_lim_EV*step):  
                        if SoC_EV.iloc[i-1]+(b_step.iloc[i]) <= EVbat_min1:
                            if b_step.iloc[i] <= -abs(discharge_lim_EV*step) and SoC_EV.iloc[i-1]+(-abs(discharge_lim_EV*step)) > EVbat_min1:
                                SoC_EV.iloc[i] = SoC_EV.iloc[i-1]+(-abs(discharge_lim_EV*step))
                            else:
                                SoC_EV.iloc[i] = EVbat_min1
                        else:
                            SoC_EV.iloc[i] = SoC_EV.iloc[i-1]+(-abs(discharge_lim_EV*step))
                                              
                    elif b_step.iloc[i] >= abs(charge_lim_EV*step):
                        if SoC_EV.iloc[i-1]+(b_step.iloc[i]) >= EVbat_max:
                            SoC_EV.iloc[i] = EVbat_max
                        else:
                            SoC_EV.iloc[i] = SoC_EV.iloc[i-1]+(abs(charge_lim_EV*step))
                    
                    elif b_step.iloc[i] < abs(charge_lim_EV*step) and b_step.iloc[i] > -abs(discharge_lim_EV*step):
                        if SoC_EV.iloc[i-1]+(b_step.iloc[i]) >= EVbat_max:
                            SoC_EV.iloc[i] = EVbat_max
                        elif SoC_EV.iloc[i-1]+(b_step.iloc[i]) <= EVbat_min1:
                            SoC_EV.iloc[i] = EVbat_min1
                        else:
                            SoC_EV.iloc[i] = SoC_EV.iloc[i-1]+(b_step.iloc[i])
                            
            elif EV_home.iloc[i] > 0  and EV_home.iloc[i-1] > 0 and (EV_home_day.iloc[i] <= 0 or EV_home_day.iloc[i-48] <= 0):
            
                if b_step.iloc[i] > 0:
                        if b_step.iloc[i] >= abs(charge_lim_EV*step):   
                            SoC_EV.iloc[i] = SoC_EV.iloc[i-1]+(abs(charge_lim_EV*step))
                        elif b_step.iloc[i] < abs(charge_lim_EV*step):
                            SoC_EV.iloc[i] = SoC_EV.iloc[i-1]+(b_step.iloc[i])
                if b_step.iloc[i] <= 0:
                        if SoC_EV.iloc[i-1] >= 0.5*EVbat_max:
                            if b_step.iloc[i] <= -abs(discharge_lim_EV*step):
                                SoC_EV.iloc[i] = SoC_EV.iloc[i-1]+(-abs(discharge_lim_EV*step))
                            elif b_step.iloc[i] < abs(charge_lim_EV*step) and b_step.iloc[i] > -abs(discharge_lim_EV*step):
                                SoC_EV.iloc[i] = SoC_EV.iloc[i-1]+(b_step.iloc[i])
                        if SoC_EV.iloc[i-1] < 0.5*EVbat_max:    
                            if SoC_EV.iloc[i-1] + g2v.iloc[i] <= EVbat_min1:
                                SoC_EV.iloc[i] = SoC_EV.iloc[i-1] + g2v.iloc[i]
                                g2v_charging.iloc[i] = g2v.iloc[i]/step
                            else:
                                SoC_EV.iloc[i] = SoC_EV.iloc[i-1]

            elif EV_home.iloc[i] <= 0 and EV_home.iloc[i-1] > 0:
                SoC_EV.iloc[i] = 0
                SoC_EV_temp.iloc[i] = SoC_EV.iloc[i-1]

            elif EV_home.iloc[i] <= 0 and EV_home.iloc[i-1] <= 0:     
                SoC_EV.iloc[i] = 0
                SoC_EV_temp.iloc[i] = SoC_EV_temp.iloc[i-1]

            elif EV_home.iloc[i] > 0 and EV_home.iloc[i-1] <= 0:            
                SoC_EV_temp.iloc[i] = SoC_EV_temp.iloc[i-1]
                SoC_EV.iloc[i] = SoC_EV_temp.iloc[i] - 5.6

            
            if SoC_EV.iloc[i]-SoC_EV.iloc[i-1] <= 0 and EV_home.iloc[i] > 0 and EV_home.iloc[i-1] > 0:
                from_EVbat.iloc[i] = (SoC_EV.iloc[i]-SoC_EV.iloc[i-1])/step
            else:
                from_EVbat.iloc[i] = 0
    
            if SoC_EV.iloc[i]-SoC_EV.iloc[i-1] >= 0 and balance.iloc[i] > 0 and EV_home.iloc[i] > 0 and EV_home.iloc[i-1] > 0:
                PV_to_EVbat.iloc[i] = (SoC_EV.iloc[i]-SoC_EV.iloc[i-1])/step
            else:
                PV_to_EVbat.iloc[i] = 0
                
            if balance.iloc[i] < -abs(from_EVbat.iloc[i]):  
                from_grid_EV.iloc[i] = abs(balance.iloc[i])-abs(from_EVbat.iloc[i])   
            else:
                from_grid_EV.iloc[i] = 0
           
            if balance.iloc[i] > abs(PV_to_EVbat.iloc[i]):
               to_grid_EV.iloc[i] = abs(balance.iloc[i])-abs(PV_to_EVbat.iloc[i])
            else:
               to_grid_EV.iloc[i] = 0
               
        from_grid_total = abs(from_grid_EV) + abs(g2v_charging)
        
        return SoC_EV, from_EVbat, g2v_charging, PV_to_EVbat, from_grid_EV, from_grid_total, to_grid_EV, SoC_EV_temp
        
SoC_EV, from_EVbat, g2v_charging, PV_to_EVbat, from_grid_EV, from_grid_total, to_grid_EV, SoC_EV_temp = pv_EVbat(EVbat_max)