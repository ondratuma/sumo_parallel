# -*- coding: utf-8 -*-

import os
import sys
from Simulation import Simulation




if 'SUMO_HOME' in os.environ:
	sumo_home = os.environ['SUMO_HOME']
	tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
	sys.path.append(tools)
else:
	sys.exit("please declare environment variable 'SUMO_HOME'")


def scenario_name():
	try:
		return sys.argv[1]
	except IndexError:
		return "grid"


# ------------------------------------------------------- Import simulation settings based on parameter
_temp = __import__(scenario_name(), globals(), locals(), [], 0)
simulation_settings = _temp.simulation_settings
os.chdir(scenario_name())

import traci


def main():

	gui_settings = simulation_settings.init_gui_settings(sumo_home)
	simulation_init = simulation_settings.init_simulation_settings(gui_settings)
	simulations = [Simulation(simulation_init[0], traci), Simulation(simulation_init[1], traci)]
	global_zoom = 100
	global_offset = (10, 10)
	for simulation in simulations:
		simulation.start()
		simulation.initStaticObjects()
	step = 1
	simulation_on = True
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

			if step % gui_settings['route_correction_num_steps'] == 0:
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
			output_table = [
				['STEP', step, 'TIME', ''],  # 0
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

		# --------------------------------------------------------------- Print timers

		# ---------------------------------------------------------------
		step += 1
	for simulation in simulations:
		simulation.setActive()
		traci.close(False)


if __name__ == '__main__':
	main()
