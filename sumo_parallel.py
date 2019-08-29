# -*- coding: utf-8 -*-

import os
import sys
from Simulation import Simulation
from diff2edgefiles import diffEdgeFiles, plotEdgeFile
from sumo_parallel_tools import get_sumo_home, colormaps


sumo_home = get_sumo_home()
import traci


def scenario_name():
	try:
		return sys.argv[1]
	except IndexError:
		return "grid"


# ------------------------------------------------------- Import simulation settings based on parameter






def getSimulationSettings(name):
	_temp = __import__(name, globals(), locals(), [], 0)
	simulation_settings = _temp.simulation_settings
	os.chdir(name)
	return simulation_settings
def startParallelSimulations(simulation_settings):
	simulation_settings_common = simulation_settings.both_settings(sumo_home)
	simulation_settings_final = simulation_settings.each_simulation_settings(simulation_settings_common)
	simulations = [Simulation(simulation_settings_final[0], traci), Simulation(simulation_settings_final[1], traci)]
	return simulations, simulation_settings_common

def printSimulationsStats(simulations):
	output_table = [
		['----------', '--------', '----------', '----------'],  # 1
		['', 'SIM1', 'SIM2', 'DIFF'],  # 5
		['WAITING', '%.2f' % simulations[0].averageWaitingTime, '%.2f' % simulations[1].averageWaitingTime,
		 '%.2f' % (simulations[0].averageWaitingTime - simulations[1].averageWaitingTime)],  # 6
		['ROUTE', '%.2f' % simulations[0].measureRoutes[0]['waitingtime'],
		 '%.2f' % simulations[1].measureRoutes[0]['waitingtime'],
		 '%.2f' % (simulations[0].measureRoutes[0]['waitingtime'] - simulations[1].measureRoutes[0][
			 'waitingtime'])],  # 7
		['TRIPFILE_STATS', '--------', '----------', '----------'],
		['AVG_DURATION', simulations[0].total_duration, simulations[1].total_duration,
		 simulations[0].total_duration - simulations[1].total_duration],
		['AVG_T_LOSS', '%.2f' % simulations[0].average_timeloss, '%.2f' % simulations[1].average_timeloss,
		 '%.2f' % (simulations[0].average_timeloss - simulations[1].average_timeloss)],  # 8
		['AVG_REL_DURATION', '%.2f' % simulations[0].average_relative_timeloss,
		 '%.2f' % simulations[1].average_relative_timeloss,
		 '%.2f' % (simulations[0].average_relative_timeloss - simulations[1].average_relative_timeloss)],

		[],  # 9
		['TIMERS', '--------', '----------', '----------']  # 10
	]
	for row in output_table:
		print(row)
def diffParallelSimulationResults(simulations,output_filename):
	filenames = [i.edgeDumpFilename for i in simulations]
	diffEdgeFiles(filenames[0],filenames[1],output_filename)

def simulations_run(simulations):
	step = 1
	simulation_on = True
	global_zoom = 100
	global_offset = (10, 10)
	while step < 1000 and simulation_on:
		for simulation in simulations:
			simulation.setActive()
			traci.simulationStep()
			# --------------------------------------------------------------- ADD VEHICLES
			for deployRoute in simulation.deployRoutes:
				if step % deployRoute['period'] == 0:
					simulation.add_vehicle(deployRoute['from'], deployRoute['to'])
			# --------------------------------------------------------------- CLOSED_LANES
			simulation.scanLanes()
			# --------------------------------------------------------------- GUI SYNC
			global_zoom, global_offset = simulation.sync_guis(global_zoom, global_offset)
			# ---------------------------------------------------------------

			if step % simulation.route_correction_num_steps == 0:
				# --------------------------------------------------------------- tripinfo xml
				simulation.getTripinfo()
				# --------------------------------------------------------------- subscribe to currently loaded vehicles
				simulation.getLoadedVehicles()
				simulation.subscribeLoadedVehicles()
				# --------------------------------------------------------------- vehicle iteration
				simulation.scanVehicles()
				# --------------------------------------------------------------- meassure time for defined routes
				simulation.getRouteTime()
		if step % 10 == 0:
			# --------------------------------------------------------------- print all data
			print("STEP: " + str(step))
			printSimulationsStats(simulations)
		# --------------------------------------------------------------- Print timers

		# ---------------------------------------------------------------
		step += 1
	for simulation in simulations:
		simulation.setActive()
		traci.close()
def main():


	simulation_settings = getSimulationSettings(scenario_name())
	simulations, simulation_settings_common = startParallelSimulations(simulation_settings)



	for simulation in simulations:
		simulation.start()
		simulation.initStaticObjects()
		pass
	simulations_run(simulations)
	edgedifFilename = "log/edgeDiff.xml"
	diffParallelSimulationResults(simulations, edgedifFilename)
	netfile = simulation_settings_common["netfile"]
	for metric in simulation_settings_common["plot_net_dump"]['metrics']:
		plotEdgeFile(edgedifFilename, netfile,os.path.join('visualizations',metric+ ".png"), metric, colormaps['basic'])
if __name__ == '__main__':
	main()
