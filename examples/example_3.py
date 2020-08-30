#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 20:42:16 2020

@author: Jens
"""


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from hydropt.model import Basin, Outflow, Turbine, PowerPlant
from hydropt.action import ActionStanding, ActionPowerMin, ActionPowerMax
from hydropt.scenarios import Scenario, Underlyings
from hydropt.constraints import TurbineConstraint

basins = [Basin(name='basin_1', 
                volume=75e6, 
                num_states=201, 
                init_volume=60e6, 
                levels=(1700, 1792)),
          ]

outflow = Outflow(outflow_level=1090)

turbines = [Turbine('turbine_1', 
                    max_power = 45e6,
                    base_load =  1e6,
                    efficiency=0.8, 
                    upper_basin=basins[0], 
                    lower_basin=outflow),
            Turbine('turbine_2', 
                    max_power = 45e6,
                    base_load =  1e6,
                    efficiency=0.8,
                    upper_basin=basins[0], 
                    lower_basin=outflow)
            ]

actions = [ActionStanding(turbines[0]), 
           ActionPowerMin(turbines[0]),
           ActionPowerMax(turbines[0]),
           ActionStanding(turbines[1]), 
           ActionPowerMin(turbines[1]),
           ActionPowerMax(turbines[1])
           ]

power_plant = PowerPlant(basins, turbines, actions)    

constraints = [TurbineConstraint(turbines[0], '2019-02-24T00', '2019-02-27T00',
                                     name='test_0', power_max=0),
               ]

market_data = pd.read_csv('../data/spot_prices_2019.csv', 
                          sep=';', 
                          index_col=0,
                          parse_dates=True)

n_steps = len(market_data)

time = market_data.index[0:n_steps].to_numpy().astype('datetime64[h]')
spot = market_data.iloc[0:n_steps,2].to_numpy()

inflow_rate = 2.5*np.ones((n_steps,1))

underlyings = Underlyings(time, spot, inflow_rate)
scenario = Scenario(power_plant, underlyings, name='base')

scenario_sdl = Scenario(power_plant, underlyings, constraints, name='SDL')

scenario.run()
scenario_sdl.run()

#%%
print(scenario.valuation(),
      scenario_sdl.valuation(),
      scenario.valuation()-scenario_sdl.valuation())

#%%
plt.figure(2)
plt.clf()
plt.plot(time,spot, marker='.', label='hpfc')
plt.plot(time,10*inflow_rate, marker='.', label='inflow')
plt.plot(time,scenario.turbine_actions_/1e6, marker='.', label='action')
plt.plot(time,scenario.volume_[1:]/1e6, marker='.', label='vol')
plt.legend()
plt.show()

plt.figure(3)
plt.clf()
plt.plot(time,spot, marker='.', label='hpfc')
plt.plot(time,10*inflow_rate, marker='.', label='inflow')
plt.plot(time,scenario_sdl.turbine_actions_/1e6, marker='.', label='action')
plt.plot(time,scenario_sdl.volume_[1:]/1e6, marker='.', label='vol')
plt.legend()
plt.show()

plt.figure(4)
plt.clf()
plt.plot(time,spot, marker='.', label='hpfc')
plt.plot(time,
         np.sum(scenario_sdl.turbine_actions_/1e6, 1)-np.sum(scenario.turbine_actions_/1e6, 1), 
         marker='.', label='action delta')
plt.legend()
plt.show()



