#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 17:14:02 2020

@author: Jens
"""

import numpy as np
from dyn_prog import kron_indices

class Basin():
    def __init__(self, vol, num_states, content, height, name=None, power_plant=None):
        self.name = name
        self.vol = vol
        self.num_states = num_states
        self.content = content
        self.height = height
        self.power_plant = power_plant
        
    def index(self):
        if self.power_plant is None:
            return None
        else:
            return self.power_plant.basin_index(self)
        
    def __repr__(self):
        if self.name is None:
            name = f'basin_{self.index()}'
        return f"Basin('{name}', {self.vol}, {self.num_states})"
    
    
class Outflow(Basin):
    def __init__(self, height, name='Outflow'):
        super().__init__(vol=1, num_states=2, content=0, height=height, name=name)
        
        
class Action():
    def __init__(self, turbine, flow_rate):
        self.turbine = turbine
        self.flow_rate = flow_rate
        
    def turbine_prod(self):
        return self.turbine.power(self.flow_rate)
        
    def __repr__(self):
        return f"Action({self.turbine}, {self.flow_rate})"
    
    
class ProductAction():
    def __init__(self, actions, power_plant=None):
        self.actions = tuple(actions)
        self.power_plant = power_plant
        
    def turbine_prod(self):
        return [action.turbine_prod() for action in self.actions]
    
    def basin_flow_rates(self):
        basins = self.power_plant.basins
        basin_flow_rates = len(basins)*[0]
        for action in self.actions:
            outflow_ind = action.turbine.upper_basin.index()
            if outflow_ind is not None:
                basin_flow_rates[outflow_ind] += action.flow_rate
            inflow_ind = action.turbine.lower_basin.index()
            if inflow_ind is not None:
                basin_flow_rates[inflow_ind] -= action.flow_rate
                
        return basin_flow_rates
        
    def __repr__(self):
        return f"ProductAction({self.actions})"
    
    
class ActionCollection():
    def __init__(self, actions):
        self.actions = actions
        
    def turbine_prod(self):
        return [action.turbine_prod() for action in self.actions]
    
    def basin_flow_rates(self):
        return [action.basin_flow_rates() for action in self.actions]
    
    def __repr__(self):
        return f"ActionCollection({self.actions})"
        
        
class Turbine():
    def __init__(self, name, nu, flow_rates, upper_basin, lower_basin):
        self.name = name
        self.nu = nu
        self.flow_rates = flow_rates
        self.upper_basin = upper_basin
        self.lower_basin = lower_basin
        
    def actions(self):
        return [Action(self, flow_rate=flow_rate) for flow_rate in self.flow_rates]
    
    def head(self):
        return self.upper_basin.height - self.lower_basin.height
    
    def power(self, flow_rate):
        return self.nu*(1000*9.81)*self.head()*flow_rate
    
    def __repr__(self):
        return f"Turbine('{self.name}')"
    
    
class PlantModel():
    def __init__(self, basins=None, turbines=None):
        self._basins = []
        self._basin_index = {}
        self.add_basins(basins)      
        self.turbines = turbines
        
    @property
    def basins(self):
        return self._basins
    
    def add_basins(self, basins):
        for basin in basins:
            basin.power_plant = self
            self._basins.append(basin)
            self._basin_index[basin] = len(self._basins)-1
        
    def basin_index(self, basin):
        return self._basin_index[basin]
        
    def basin_volumes(self):
        return np.array([basin.vol for basin in self.basins])
    
    def basin_num_states(self):
        return np.array([basin.num_states for basin in self.basins])
    
    def basin_contents(self):
        return np.array([basin.content for basin in self.basins])
    
    def basin_names(self):
        return np.array([basin.names for basin in self.basins])
    
    def num_states(self):
        return np.prod(self.basin_num_states())
    
    def turbine_actions(self):
        actions = list()
        for turbine in self.turbines:
            actions.append(turbine.actions())
        return actions
    
    def actions(self):
        turbine_actions = self.turbine_actions()
        num_actions = [len(a) for a in turbine_actions]
        combinations = kron_indices(num_actions, range(len(num_actions)))
        product_actions = []
        for comb in combinations:
            group = []
            for k in range(len(comb)):
                group.append(turbine_actions[k][comb[k]])
            product_actions.append(ProductAction(group, self))
        return ActionCollection(product_actions)
            

class Underlyings():
    def __init__(self, price_curve, inflows):
        self.price_curve = price_curve
        self.inflows = inflows    