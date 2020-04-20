#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 16:13:07 2020

@author: Jens
"""

import numpy as np
import matplotlib.pyplot as plt

from dynprog.model import Basin, BasinLevels, Outflow, Turbine, Plant
from dynprog.scenarios import Scenario, ScenarioOptimizer, Underlyings



# TODO: height --> rename as level_range
basins = [Basin(name='basin_1', vol=81, num_states=21, content=10, height=BasinLevels(2000,2120)),
          Basin(name='basin_2', vol=31, num_states=11, content=10, height=BasinLevels(1200,1250))]

outflow = Outflow(height=600)

turbines = [Turbine('turbine_1', nu=0.8, flow_rates=[0, 5], 
                    upper_basin=basins[0], lower_basin=basins[1]),
            Turbine('turbine_2a', nu=0.8, flow_rates=[0, 2], 
                    upper_basin=basins[1], lower_basin=outflow),
            Turbine('turbine_2b', nu=0.7, flow_rates=[0, 2], 
                    upper_basin=basins[1], lower_basin=outflow)]

plant = Plant(basins, turbines)    

n_steps = 24*7
hpfc = 10*(np.sin(2*np.pi*2*np.arange(n_steps)/n_steps) + 1)
inflow = 0.8*np.ones((n_steps,2))

underlyings = Underlyings(hpfc, inflow, 3600)
scenario = Scenario(plant, underlyings, name='base')

optimizer = ScenarioOptimizer(scenario)
optimizer.run()

plt.figure(1)
plt.clf()
plt.plot(hpfc, marker='.', label='hpfc')
plt.plot(10*inflow, marker='.', label='inflow')
plt.plot(optimizer.turbine_actions/1000000, marker='.', label='action')
plt.plot(np.arange(n_steps+1)-1,optimizer.volume, marker='.', label='vol')
plt.legend()
plt.show()