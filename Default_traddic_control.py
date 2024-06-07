import os
import sys
from pathlib import Path
import traci
import sumolib
import csv
import pandas as pd
from typing import Callable, Optional, Tuple, Union, List

# Configuration
sumoBinary = sumolib.checkBinary('sumo-gui')
sumoCmd = [sumoBinary, "-c", "network_trainning/single-intersection-real-scenario.sumocfg"]
# sumoCmd = [sumoBinary, "-c", "network/osm.sumocfg"]

# Variables globales pour stocker les informations collectées
vehicle_info = {}  # Structure: {vehicle_id: {"waitTime": value, "co2Emission": value, "fuelConsumption": value}}
metrics = []
sim_step = 0
seen_vehicles = set()
total_stopped = 0 # Initialize the total stop to 0
total_co2_emission = 0.0  # Initialize total CO2 emission to 0
total_waiting_time = 0.0  # Initialize total waiting time to 0
total_fuel_consumption = 0.0  # Initialize total fuel consumption to 0
halted_vehicles = set()
max_steps = 3600

def run_simulation():
    global sim_step
    traci.start(sumoCmd)
    step = 0
    # while traci.simulation.getMinExpectedNumber() > 0:
    while step < max_steps:
        sim_step = traci.simulation.getTime()
        traci.simulationStep()
        _compute_info()
        step += 1
    traci.close()

    save_csv("outputs_pretimed/default_control_17h-18h.csv", 0)
    
def get_total_queued(in_lanes) -> int:
        """Returns the total number of vehicles halting in the intersection."""
        return sum(traci.lane.getLastStepHaltingNumber(lane) for lane in in_lanes)
    
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
    global total_stopped
    global total_fuel_consumption
    global seen_vehicles

    lane_temp = ["n_t_0", "n_t_1", "s_t_0", "s_t_1","w_t_0", "w_t_1", "e_t_0", "e_t_1"]
    co2, time, fuel = get_vehicle_metrics_on_lanes(lane_temp)  
    stopped = [get_total_queued(lane_temp)]
    # total_stopped += sum(stopped)
    
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
            
    
    
    
    
    
    

# def collect_vehicle_info():
#     for veh_id in traci.vehicle.getIDList():
#         if veh_id not in vehicle_info:
#             vehicle_info[veh_id] = {"waitTime": 0, "co2Emission": 0, "fuelConsumption": 0}
        
#         # Mise à jour des informations pour chaque véhicule
#         vehicle_info[veh_id]["waitTime"] += traci.vehicle.getAccumulatedWaitingTime(veh_id)
#         vehicle_info[veh_id]["co2Emission"] += traci.vehicle.getCO2Emission(veh_id)
#         vehicle_info[veh_id]["fuelConsumption"] += traci.vehicle.getFuelConsumption(veh_id)

# def save_additional_info_csv():
#     with open('additional_info.csv', 'w', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow(["VehicleID", "WaitTime", "CO2Emission", "FuelConsumption"])
        
#         for veh_id, info in vehicle_info.items():
#             writer.writerow([veh_id, info["waitTime"], info["co2Emission"], info["fuelConsumption"]])
    
#     # Totalise et imprime des informations agrégées
#     total_vehicles = len(vehicle_info)
#     total_wait_time = sum(info["waitTime"] for info in vehicle_info.values())
#     total_co2_emission = sum(info["co2Emission"] for info in vehicle_info.values())
#     total_fuel_consumption = sum(info["fuelConsumption"] for info in vehicle_info.values())
    
#     print(f"Total Vehicles: {total_vehicles}, Total Wait Time: {total_wait_time}, Total CO2 Emission: {total_co2_emission}, Total Fuel Consumption: {total_fuel_consumption}")

if __name__ == "__main__":
    run_simulation()
