# SimpleSoC

These Python scripts enable a simplified analysis of the state of charge of different types of energy storage:

- [SOC_bat_1_LT](/SoC_bat_1_LT.py)
  
  Consists of scripts for a short-term storage option (stationary battery) and a long-term storage option (hydrogen).
  
  Charging strategy 1: the battery is charged when the PV generation is higher than the building load and discharged when the building load exceeds PV generation. 
- [SOC_bat_2](/SoC_bat_2.py)

  Consists of a script for a short-term storage option (stationary battery).

  Charging strategy 2: The battery is used for reducing peak grid exports on very sunny days to mitigate grid congestion without complete curtailment. On days where the peak PV generation exceeds a defined threshold, the battery is held at a constant state of charge between defined morning hours, after which and on all other days the battery is charged and discharged as in the case of strategy 1. 

- [SOC_bat_3](/SoC_bat_3.py)

  Consists of a script for a short-term storage option (stationary battery).

  Charging strategy 3: 3.	The same approach is used on very sunny days as in strategy 2, with the addition that the charging rate is limited to a lower defined threshold than with strategies 1 and 2. This would increase the time it takes for the battery to become fully charged, and the potential for peak export reduction could be decreased.

- [SOC_EV](/SoC_EV.py)

  Consists of a script for a short-term storage option (electric vehicle (EV) battery).

  The EVs are only charged at home and when the PV generation exceeds the building load. Grid-imported energy is used for charging the EVs if there is not enough energy for the next trip after returning home. 
