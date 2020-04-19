#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 17:14:02 2020

@author: Jens
"""

import numpy as np
import scipy.sparse as sparse


def transition_prob(V, num_states, q):
    if q == 0:
        return ([1.0, ], [0, ])
    else:
        dV = V/(num_states-1)
        k_0 = int(q/dV)
        p_0 = 1 - (np.abs(q) % dV)/dV
        k_1 = int(k_0 + np.sign(q))
        p_1 = (np.abs(q) % dV)/dV
        return ([p_0, p_1], [k_0, k_1])


def transition_matrix(V, num_states, q):
    L_combined = np.ones((1,1))
    for k in np.arange(V.shape[0]):
        # state with index 0 represents empty basin
        pp, kk = transition_prob(V[k], num_states[k], q[k])
        L = np.zeros((num_states[k],num_states[k]))
        for ppp, kkk in zip(pp,kk):
            if kkk >=0:
                L[np.arange(0,num_states[k]-kkk), np.arange(kkk,num_states[k])] = ppp
            else:
                L[np.arange(abs(kkk),num_states[k]), np.arange(0,num_states[k]-abs(kkk))] = ppp
        L_combined = np.kron(L_combined, L)
    return L_combined


def kron_index(num_states, position):
    index = np.ones(1, dtype='int64')
    
    for k, num in enumerate(num_states):
        if k == position:
            index = np.kron(index, np.arange(num))
        else:
            index = np.kron(index, np.ones(num, dtype='int64'))
            
    return index


def kron_indices(num_states, positions):
    indices = list()
    
    for position in positions:
        indices.append(kron_index(num_states, position))
        
    return np.stack(indices, axis=1)


def kron_basis_map(num_states):
    num_states = np.int64(np.round(num_states))
    return np.flip(np.cumprod(np.flip(num_states)))//num_states


def backward_induction(n_steps, volume, num_states, turbine_actions, basin_actions,
                       inflow, hpfc, water_value_end, penalty):
    num_states_tot = np.prod(num_states)
    
    # initialize boundary condition (valuation of states at the end of optimization)
    value = np.zeros((num_states_tot, ))
    for k in np.arange(num_states.shape[0]):
        value += water_value_end*volume[k]*np.linspace(0,1, num_states[k])[kron_index(num_states, k)]
    
    # allocate momory
    rewards_to_evaluate = np.zeros((turbine_actions.shape[0], num_states_tot))
    action_grid = np.zeros((n_steps, num_states_tot), dtype=np.int64)
    value_grid = np.zeros((n_steps,num_states_tot))
    
    # loop backwords through time (backward induction)
    for k in np.arange(n_steps):
        hpfc_now = hpfc[(n_steps-1)-k]
        inflow_now = inflow[(n_steps-1)-k, :]
        
        # loop through all actions and every state
        for act_index, (turbine_action, basin_action) in enumerate(zip(turbine_actions, basin_actions)):
            L = transition_matrix(volume, num_states, basin_action-inflow_now)
            # print(k, act_index , '\n', L.todense()[:,0])
            immediate_reward = np.sum(turbine_action*hpfc_now)
            future_reward = L.T.dot(value) 
            # TODO: Normalize penalty
            penatly_reward = penalty*(1-np.sum(L, axis=0))
            rewards_to_evaluate[act_index, :] = future_reward + immediate_reward - penatly_reward

        # find index of optimal action for each state
        optimal_action_index = np.argmax(rewards_to_evaluate, axis=0)
        
        # value of each state is given by the reward of the optimal action
        value = rewards_to_evaluate[optimal_action_index, np.arange(num_states_tot)]
        
        # fill action and value grids
        action_grid[(n_steps-1)-k, :] = optimal_action_index
        value_grid[(n_steps-1)-k, :] = value
    
    return action_grid, value_grid


def forward_propagation(n_steps, volume, num_states, basins_contents, turbine_actions, basin_actions,
                        inflow, action_grid):
    basin_actions_taken = np.zeros((n_steps, basin_actions.shape[1]))
    turbine_actions_taken = np.zeros((n_steps, turbine_actions.shape[1]))
    
    vol = np.zeros((n_steps+1, volume.shape[0]))
    vol[0,:] = basins_contents
    state_finder = kron_basis_map(num_states)
    
    for k in np.arange(n_steps):
        state_index = np.dot(state_finder, np.int64(np.round((num_states-1)*vol[k, :]/volume)))
        basin_actions_taken[k] = basin_actions[action_grid[k, state_index]]
        turbine_actions_taken[k] = turbine_actions[action_grid[k, state_index]]
        vol[k+1, :] = vol[k,:] - basin_actions_taken[k, :] + inflow[k, :]
        
    return turbine_actions_taken, basin_actions_taken, vol


