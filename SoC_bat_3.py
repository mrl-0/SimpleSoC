# -*- coding: utf-8 -*-

import pandas as pd

step = 0.25  # define timestep (h) (0.25: 15-min timestep)

demand =  0  # define hourly energy demand (kWh)
PV_gen =  0  # define PV generation (kWh)
time =    0  # datettime index


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

discharge_lim = bat_max*0.5     # battery charging/discharging rate (kW) on days that are not sunny
charge_lim = discharge_lim
charge_lim_s = 1                # battery charging/discharging rate (kW) on very sunny days
charge_lim_vs = 0.7             # battery charging/discharging rate (kW) on sunny days

hours = time.dt.hour

sunny_day = PV_gen.resample('D').max()
for i in range(0,len(sunny_day)):
    if sunny_day.iloc[i] >= 3 and sunny_day.iloc[i] < 3.9:          # specify min and max thresholds (kw) for a sunny day
        sunny_day.iloc[i] = 1
    else:
        sunny_day.iloc[i] = 0
sunny_day_rule = sunny_day.resample('15T').ffill()

very_sunny_day = PV_gen.resample('D').max()                         # specify min and max thresholds (kW) for a sunny day
for i in range(0,len(very_sunny_day)):
    if very_sunny_day.iloc[i] >= 3.9:
        very_sunny_day.iloc[i] = 1
    else:
        very_sunny_day.iloc[i] = 0
very_sunny_day_rule = very_sunny_day.resample('15T').ffill()


time_rule = pd.Series(data=0,index=time.index)
for i in range(0,len(time)):
    if hours.iloc[i] >= 7 and hours.iloc[i] < 10:
        time_rule.iloc[i] = 1
    else:
        time_rule.iloc[i] = 0

def pv_bat(bat_max):
        
        SoC = pd.Series(data=0,index=demand.index)
        from_bat = pd.Series(data=0,index=demand.index)
        to_bat = pd.Series(data=0,index=demand.index)
        from_grid_wb = pd.Series(data=0,index=demand.index)
        to_grid_wb = pd.Series(data=0,index=demand.index)

        SoC.iloc[0] = bat_initial
        
        for i in range(1,len(time)):
            
            if sunny_day_rule.iloc[i] > 0 and time_rule.iloc[i] > 0 and b_step.iloc[i] > 0: 
                
                SoC.iloc[i] = SoC.iloc[i-1]
                
            elif sunny_day_rule.iloc[i] > 0 and time_rule.iloc[i] <= 0 and b_step.iloc[i] > 0:
            
                if b_step.iloc[i] <= -abs(discharge_lim*step):
                    if SoC.iloc[i-1]+(b_step.iloc[i]) <= bat_min:
                        if b_step.iloc[i] <= -abs(discharge_lim*step) and SoC.iloc[i-1]+(-abs(discharge_lim*step)) > bat_min:
                            SoC.iloc[i] = SoC.iloc[i-1]+(-abs(discharge_lim*step))
                        else:
                            SoC.iloc[i] = bat_min
                    else:
                        SoC.iloc[i] = SoC.iloc[i-1]+(-abs(discharge_lim*step))    
                
                elif b_step.iloc[i] >= abs(charge_lim_s*step):
                    if SoC.iloc[i-1]+(b_step.iloc[i]) >= bat_max:
                        if b_step.iloc[i] >= abs(charge_lim_s*step) and SoC.iloc[i-1]+(abs(charge_lim_s*step)) < bat_max:
                            SoC.iloc[i] = SoC.iloc[i-1]+(abs(charge_lim_s*step))
                        else:
                            SoC.iloc[i] = bat_max
                    else:
                        SoC.iloc[i] = SoC.iloc[i-1]+(abs(charge_lim_s*step))
                                    
                elif b_step.iloc[i] < abs(charge_lim_s*step) and b_step.iloc[i] > -abs(discharge_lim*step):
                    if SoC.iloc[i-1]+(b_step.iloc[i]) >= bat_max:
                        SoC.iloc[i] = bat_max
                    elif SoC.iloc[i-1]+(b_step.iloc[i]) <= bat_min:
                        SoC.iloc[i] = bat_min
                    else:
                        SoC.iloc[i] = SoC.iloc[i-1]+(b_step.iloc[i])
            
            
            elif very_sunny_day_rule.iloc[i] > 0 and time_rule.iloc[i] > 0 and b_step.iloc[i] > 0: 
                
                SoC.iloc[i] = SoC.iloc[i-1]
                
            elif very_sunny_day_rule.iloc[i] > 0 and time_rule.iloc[i] <= 0 and b_step.iloc[i] > 0:
            
                if b_step.iloc[i]<= -abs(discharge_lim*step):
                    if SoC.iloc[i-1]+(b_step.iloc[i]) <= bat_min:
                        if b_step.iloc[i] <= -abs(discharge_lim*step) and SoC.iloc[i-1]+(-abs(discharge_lim*step)) > bat_min:
                            SoC.iloc[i] = SoC.iloc[i-1]+(-abs(discharge_lim*step))
                        else:
                            SoC.iloc[i] = bat_min
                    else:
                        SoC.iloc[i] = SoC.iloc[i-1]+(-abs(discharge_lim*step))    
                
                elif b_step.iloc[i] >= abs(charge_lim_vs*step):
                    if SoC.iloc[i-1]+(b_step.iloc[i]) >= bat_max:
                        if b_step.iloc[i] >= abs(charge_lim_vs*step) and SoC.iloc[i-1]+(abs(charge_lim_vs*step)) < bat_max:
                            SoC.iloc[i] = SoC.iloc[i-1]+(abs(charge_lim_vs*step))
                        else:
                            SoC.iloc[i] = bat_max
                    else:
                        SoC.iloc[i] = SoC.iloc[i-1]+(abs(charge_lim_vs*step))
                                    
                elif b_step.iloc[i] < abs(charge_lim_vs*step) and b_step.iloc[i] > -abs(discharge_lim*step):
                    if SoC.iloc[i-1]+(b_step.iloc[i]) >= bat_max:
                        SoC.iloc[i] = bat_max
                    elif SoC.iloc[i-1]+(b_step.iloc[i]) <= bat_min:
                        SoC.iloc[i] = bat_min
                    else:
                        SoC.iloc[i] = SoC.iloc[i-1]+(b_step.iloc[i])
                
            else:

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

