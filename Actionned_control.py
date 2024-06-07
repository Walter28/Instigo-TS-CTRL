import traci
import traci.constants as tc
import time
import os
import sys
from pathlib import Path
import sumolib
import csv
import pandas as pd
from typing import Callable, Optional, Tuple, Union, List

# Fonction pour détecter le nombre de véhicules dans une voie
def detect_vehicle_count(detector_ids: List[str]):
    lane_1 = traci.lanearea.getLastStepVehicleNumber(detector_ids[0])
    lane_2 = traci.lanearea.getLastStepVehicleNumber(detector_ids[1])
    lane_3 = traci.lanearea.getLastStepVehicleNumber(detector_ids[2])
    lane_4 = traci.lanearea.getLastStepVehicleNumber(detector_ids[3])
    
    phase_veh_num = lane_1 + lane_2 + lane_3 + lane_4
    
    # return True if phase_veh_num > 0 else False
    return phase_veh_num

def new_veh_detection(lanes: List[str], phase_index, simulation_time):
    if phase_index == 0:
        detection = False
        add_G_time = 0      
        for lane in lanes:
            veh_list = traci.lanearea.getLastStepVehicleIDs(lane)  # Get list of vehicles on lane
            for veh in veh_list:
                # print("___________ SIMU TIME : ", simulation_time)
                if veh not in phase1_seen_vehicles:  # Check if vehicle has not been seen before
                    phase1_seen_vehicles.add(veh)  # Add vehicle to set of seen vehicles
                    detection = True
                    
                    if(simulation_time < 1):
                        # add_G_time = psg_time
                        pass
                    else:
                        add_G_time += psg_time
                else :
                    detection = False
        return detection, add_G_time
    if phase_index == 2:
        detection = False
        add_G_time = 0 
        for lane in lanes:
            veh_list = traci.lanearea.getLastStepVehicleIDs(lane)  # Get list of vehicles on lane
            for veh in veh_list:
                # print("___________ SIMU TIME : ", simulation_time)
                if veh not in phase2_seen_vehicles:  # Check if vehicle has not been seen before
                    phase2_seen_vehicles.add(veh)  # Add vehicle to set of seen vehicles
                    detection = True
                    
                    if(simulation_time < 1):
                        # add_G_time = psg_time
                        pass
                    else:
                        add_G_time += psg_time
                else :
                    detection = False
        return detection, add_G_time

# # Paramètres
# G_max = 42  # Maximum green time
# G_min = 3   # Minimum green time
# p = 3       # Passage time
# Y = 3       # Yellow time

Green_1_time = 0
Green_2_time = 0

Green_1 = 1 # vert pour la phase 1
Yellow_1 = 0 # yellow pour la phase 1
Green_2 = 0 # vert pour la phase 2
Yellow_2 = 0 # yellow pour la phase 1

#NEW VARS
G_max = 42
G_min = 5
psg_time = 5
Y = 3
phase1_time = 0
phase2_time = 0
phase1_G_time = G_min
phase2_G_time = G_min
phase1_nb_veh_old = 0
phase2_nb_veh_old = 0
phase1_seen_vehicles = set()
phase2_seen_vehicles = set()

# Variables globales pour stocker les informations collectées
vehicle_info = {}  # Structure: {vehicle_id: {"waitTime": value, "co2Emission": value, "fuelConsumption": value}}
metrics = []
sim_step = 0
seen_vehicles = set()
halted_vehicles = set()
total_co2_emission = 0.0  # Initialize total CO2 emission to 0
total_waiting_time = 0.0  # Initialize total waiting time to 0
total_fuel_consumption = 0.0  # Initialize total fuel consumption to 0
max_steps = 3600

# Configuration
sumoBinary = sumolib.checkBinary('sumo-gui')
sumoCmd = [sumoBinary, "-c", "network_trainning/single-intersection-actionned.sumocfg"]
# sumoCmd = [sumoBinary, "-c", "network/osm.sumocfg"]

# Main function
def main():
    # global Green_1
    # global Green_2
    # global Green_1_time
    # global Green_2_time
    # global Yellow_1
    # global Yellow_2
    # global G_max
    # global G_min
    # global p
    # global Y
    
    #new vars
    global G_max
    global G_min
    global psg_time
    global Y
    global phase1_time
    global phase2_time
    global phase1_G_time
    global phase2_G_time
    global phase1_nb_veh_old
    global phase2_nb_veh_old
    global phase1_seen_vehicles
    global phase2_seen_vehicles
    global sim_step
    global max_steps
    
    traci.start(sumoCmd)
    
    # Initialisation des variables
    # phase_duration = 0
    # current_phase = 0
    # current_green_time = 0
    # phase = 0
    # green_max = 30
    # min_green = 5
    # green_time = 0
    # no_vehicle_time = 0

    # phase_start_time = traci.simulation.getTime()
    
    # Boucle principale de simulation
    # Boucle principale de simulation
    # while traci.simulation.getMinExpectedNumber() > 0:
        # traci.simulationStep()
    step = 0
    # while traci.simulation.getMinExpectedNumber() > 0:
    while step < max_steps:
        sim_step = traci.simulation.getTime()
        # print("$$$$$$$$$$$$$$$$$$ SIMU TIME : ", step)
        phase1_G_time = G_min
        phase1_time = traci.simulation.getTime()
        # phase1_seen_vehicles = detect_vehicle_count(["e2_0", "e2_1", "e2_2", "e2_4"])
        
        traci.trafficlight.setPhase("t", 0)
        traci.trafficlight.setPhaseDuration("t", G_max)
        while traci.simulation.getTime() - phase1_time <= G_max:
            sim_step = traci.simulation.getTime()
            traci.simulationStep()
            step += 1
            _compute_info()
            phase1_time_experimental = traci.simulation.getTime() - phase1_time
            print("phase 1 green time  : ", phase1_G_time)
            print("++++ phase 1 time : ", phase1_time_experimental)
            
            phase1_veh_detection, add_G_time = new_veh_detection(["e2_0", "e2_1", "e2_2", "e2_4"], 0, phase1_time_experimental)
            if phase1_G_time > 0:
                phase1_G_time -= 1
                
                if(phase1_veh_detection): #means there is new vehicule detected
                    phase1_G_time += add_G_time
                    # phase1_nb_veh_old = phase1_nb_veh_new
                    
                # print("nb veh old : ", phase1_nb_veh_old)
                # print("nb veh new : ", phase1_nb_veh_new)
                
            # print("phase 1 green time  : ", phase1_G_time)
                
            if phase1_G_time == 0:
                break
            
            
            
        ##################################################################################################
        #                                                                                                #
        #   here we switch the phase(passing by the yellow phase) : consider the first one is finished   #              #
        #                                                                                                #
        ##################################################################################################
        traci.trafficlight.setPhase("t", 1)
        traci.trafficlight.setPhaseDuration("t", Y)
        yellow_time = traci.simulation.getTime()
        while traci.simulation.getTime() - yellow_time < Y:
            sim_step = traci.simulation.getTime()
            traci.simulationStep()
            step += 1
            _compute_info()
            print("")
            print("YELLOW : ",Y)
            print("")
            
            
            
        
        #######################################################
        #                                                     #
        #   Here we switch to the second phase                #
        #                                                     #
        #######################################################
        phase2_G_time = G_min
        phase2_time = traci.simulation.getTime()
        # phase2_nb_veh_old = detect_vehicle_count(["e2_3", "e2_5", "e2_6", "e2_7"])
        
        traci.trafficlight.setPhase("t", 2)
        traci.trafficlight.setPhaseDuration("t", G_max)
        while traci.simulation.getTime() - phase2_time <= G_max:
            sim_step = traci.simulation.getTime()
            traci.simulationStep()
            step += 1
            _compute_info()
            phase2_time_experimental = traci.simulation.getTime() - phase2_time
            print("phase 2 green time  : ", phase2_G_time)
            print("++++ phase 2 time : ", phase2_time_experimental)
            
            # phase2_nb_veh_new = detect_vehicle_count(["e2_3", "e2_5", "e2_6", "e2_7"])
            phase2_veh_detection, add_G_time = new_veh_detection(["e2_3", "e2_5", "e2_6", "e2_7"], 2, phase2_time_experimental)
            if phase2_G_time > 0:
                phase2_G_time -= 1
                
                if(phase2_veh_detection): #means there is new vehicule detected
                    phase2_G_time += add_G_time
                    # phase2_nb_veh_old = phase2_nb_veh_new
                     
                # print("nb veh old : ", phase2_nb_veh_old)
                # print("nb veh new : ", phase2_nb_veh_new)
                
            # print("phase 2 green time  : ", phase2_G_time)
                
            if phase2_G_time == 0:
                break
            
        ##################################################################################################
        #                                                                                                #
        #   here we switch the phase(passing by the yellow phase) : consider the second one is finished   #              #
        #                                                                                                #
        ##################################################################################################
        traci.trafficlight.setPhase("t", 3)
        traci.trafficlight.setPhaseDuration("t", Y)
        yellow_time = traci.simulation.getTime()
        while traci.simulation.getTime() - yellow_time < Y:
            sim_step = traci.simulation.getTime()
            traci.simulationStep()
            step += 1
            _compute_info()
            print("")
            print("YELLOW : ",Y)
            print("")
            
          
        
        
        
        
        
        
        
        

        # # Détecter les véhicules avec le capteur de boucle d'induction
        # if phase == 0:
        #     induction_loop_vehicles = detect_vehicle_count(["e2_0", "e2_1", "e2_2", "e2_4"]) #phase1_veh_exit
        # else:
        #     induction_loop_vehicles = detect_vehicle_count(["e2_3", "e2_5", "e2_6", "e2_7"]) #phase2_veh_exit

        # # Contrôler le feu de signalisation en fonction de la demande
        # if induction_loop_vehicles == 0:
        #     no_vehicle_time = 0
        #     if green_time < min_green:
        #         traci.trafficlight.setPhaseDuration("t", min_green - green_time)
        #         green_time = min_green
        #     else:
        #         green_time += 1
        #         if green_time > green_max:
        #             phase = (phase + 1) % 2  # Changer de phase
        #             traci.trafficlight.setPhase("t", phase)
        #             green_time = 0
        # else:
        #     no_vehicle_time += 1
        #     if no_vehicle_time > 3:
        #         phase = (phase + 1) % 2  # Changer de phase
        #         traci.trafficlight.setPhase("t", phase)
        #         green_time = 0
        #         no_vehicle_time = 0
        

    # Arrêter SUMO à la fin de la simulation
    traci.close()
    
    save_csv("outputs_actionned/ACTIONNED_control_17h-18h.csv", 0)
    

def get_vehicle_metrics_on_lanes(lanes: List[str]) -> Tuple[float, float, float]:
        """Calculates the total CO2 emission, total waiting time, and total fuel consumption of vehicles on specified lanes.
        
        Args:
            lanes (List[str]): List of lane IDs.
        
        Returns:
            Tuple[float, float, float]: Total CO2 emission, total waiting time, and total fuel consumption of vehicles on specified lanes.
        """
        co2_emission = 0.0  # Initialize total CO2 emission to 0
        waiting_time = 0.0  # Initialize total waiting time to 0
        fuel_consumption = 0.0  # Initialize total fuel consumption to 0
        
        global total_co2_emission
        global total_waiting_time
        global total_fuel_consumption
        global seen_vehicles
        global halted_vehicles
        
        for lane in lanes:
            veh_list = traci.lane.getLastStepVehicleIDs(lane)  # Get list of vehicles on lane
            for veh in veh_list:
                if veh not in seen_vehicles:  # Check if vehicle has not been seen before
                    co2 = traci.vehicle.getCO2Emission(veh)  # Get CO2 emission of vehicle
                    time = traci.vehicle.getAccumulatedWaitingTime(veh)  # Get waiting time of vehicle
                    fuel = traci.vehicle.getFuelConsumption(veh)  # Get fuel consumption of vehicle
                    
                    co2_emission += co2 # Add CO2 emission to total
                    waiting_time += time  # Add waiting time to total
                    fuel_consumption += fuel  # Add fuel consumption to total
                    seen_vehicles.add(veh)  # Add vehicle to set of seen vehicles
                    
            # Get the list of vehicles halted on this lane
            halted_vehicle_count = traci.lane.getLastStepHaltingNumber(lane)      
            # Get the list of vehicle IDs on this lane
            vehicle_ids = traci.lane.getLastStepVehicleIDs(lane)            
            # Filter out only the halted vehicles
            for vehicle_id in vehicle_ids:
                if traci.vehicle.getSpeed(vehicle_id) < 0.1:  # vehicle is halted
                    halted_vehicles.add(vehicle_id)
                    
        total_fuel_consumption += fuel_consumption
        total_co2_emission += co2_emission
        total_waiting_time += waiting_time
        
        return total_co2_emission, total_waiting_time, total_fuel_consumption
    
def _get_agent_info():
    global total_co2_emission
    global total_waiting_time
    global total_fuel_consumption
    global seen_vehicles

    lane_temp = ["n_t_0", "n_t_1", "s_t_0", "s_t_1","w_t_0", "w_t_1", "e_t_0", "e_t_1"]
    co2, time, fuel = get_vehicle_metrics_on_lanes(lane_temp)
    
    info = {}
    
    info["agent_total_vehicles_passed"] = [len(seen_vehicles)]
    info["agent_total_stopped"] = [len(halted_vehicles)]
    info["agent_total_fuel_consumption"] = [total_fuel_consumption]
    info["agent_co2_emission"] = [total_co2_emission]
    info["agent_accumulated_waiting_time"] = [total_waiting_time]
    return info
    
def _compute_info():
    global sim_step
    global metrics
    
    info = {"step": sim_step}
    info.update(_get_agent_info())
    metrics.append(info.copy())
    return info

def save_csv(out_csv_name, episode):
    """Save metrics of the simulation to a .csv file.

    Args:
        out_csv_name (str): Path to the output .csv file. E.g.: "results/my_results
        episode (int): Episode number to be appended to the output file name.
    """
    global metrics
    if out_csv_name is not None:
        df = pd.DataFrame(metrics)
        Path(Path(out_csv_name).parent).mkdir(parents=True, exist_ok=True)
        df.to_csv(out_csv_name + f"_conn{0}_ep{episode}" + ".csv", index=False)

if __name__ == "__main__":
    main()
