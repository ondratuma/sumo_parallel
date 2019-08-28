# -*- coding: utf-8 -*-

import os
import sys
import time
from xml.dom import minidom
import unicodedata
import curses

current_milli_time = lambda: int(round(time.time() * 1000))

if 'SUMO_HOME' in os.environ:
	tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
	sys.path.append(tools)
else:
	sys.exit("please declare environment variable 'SUMO_HOME'")

import traci


# --------------------------------------------------------------- Open file or create file and directory
def do_open(filename):
	if not os.path.exists(os.path.dirname(filename)):
		try:
			os.makedirs(os.path.dirname(filename))
		except OSError as exc:  # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise
	open(filename, 'w').close()
	return open(filename, 'r+')


# --------------------------------------------------------------- Set simulation variables / global settings
def init_simulation_settings():
	return {
		'width': "750",
		"height": "1080",
		"sumo_binary": os.path.join(os.environ['SUMO_HOME'], 'bin/sumo'),
		"sumo_gui": os.path.join(os.environ['SUMO_HOME'], 'bin/sumo-gui'),
		"global_zoom": 100,
		"global_offset": 100,
		"route_correction_num_steps": 10
	}


# --------------------------------------------------------------- Simulations object used to store simulation values
def init_simulations(simulation_settings):
	return [
		{
			'name': 'sim1',
			'settings': [
				simulation_settings['sumo_gui'],
				"-c",
				"grid.sumocfg",
				"--window-size",
				simulation_settings['width'] + "," + simulation_settings['height'],
				"--window-pos",
				"0,0",
				"--start",
				"true",
				"--output-prefix",
				"sim1"
			],
			'data': {
				'tripinfo': "log/sim1log.trip.xml",
				'routes': [
					{
						"from": "gneE0",
						"to": "gneE2",
						"current_expected_time": 0
					}
				]

			}
		},
		{
			'name': 'sim2',

			'settings': [
				simulation_settings['sumo_gui'],
				"-c",
				"grid.sumocfg",
				"--window-size",
				simulation_settings['width'] + "," + simulation_settings['height'],
				"--window-pos",
				simulation_settings['width'] + ",0",
				"--start",
				"true",
				"--output-prefix",
				"sim2"
			],
			'data': {
				'tripinfo': "log/sim2log.trip.xml",
				'routes': [
					{
						"from": "gneE0",
						"to": "gneE2",
						"current_expected_time": 0
					}
				]

			}

		}
	]


last_vehicle_id = 0
default_start_edge = "gneE0"
default_end_edge = "gneE2"
reversed_start = "gneE3"
reversed_end = "gneE1"


class Timers:

	def __init__(self, simulations):
		self.timers = {}
		for simulation in simulations:
			self.timers[simulation['name']] = {}

	def start(self, name, simulation_name):
		self.timers[simulation_name][name] = []
		self.timers[simulation_name][name].append(current_milli_time())

	def end(self, name, simulation_name):
		self.timers[simulation_name][name].append(current_milli_time())


class Simulation:
	def __init__(self, settings):
		self.settings = settings
		self.start_command = settings['settings']
		self.tripinfoFile = do_open(settings['data']['tripinfo'])
		self.simulationName = settings['name']
		self.measureRoutes = settings['data']['routes']
		self.totalWaitingTime = 0
		self.averageWaitingTime = 0
		self.total_timeloss = 0
		self.total_trips = 0
		self.average_timeloss = 0
		self.loaded_vehicles_ids = []
		self.subscribed_vehicles_ids = []
		self.zoom = 100
		self.offset = (0, 0)
		self.lanes = []
		self.closed_lanes = []
		self.last_vehicle_id = 1
		self.vehicles = []
		self.lanes_ids = []
		self.edges_ids = []
		self.total_duration = 0
		self.average_duration = 0
		self.average_relative_timeloss = 0

	def start(self):
		traci.start(self.start_command, label=self.simulationName)
		self.lanes_ids = traci.lane.getIDList()
		self.edges_ids = traci.edge.getIDList()

	def initStaticObjects(self):
		for lane_id in self.lanes_ids:
			traci.lane.subscribe(lane_id, {
				int("0x34", 0),  # allowed vehicle classes
				int("0x12", 0),  # last step vehicle ids
				int("0x13", 0),  # last step occupancy
				int("0x7a", 0),  # last step waiting time
				int("0x5a", 0),  # last step travel time
				int("0x41", 0),  # vmax
			})

		for edge_id in self.edges_ids:
			traci.edge.subscribe(edge_id, {
				int("0x1b", 0),  # street name
				int("0x5a", 0),  # travel time
				int("0x13", 0),  # occupancy
				int("0x7a", 0)  # waiting time
			})
		traci.simulation.subscribe(
			{
				int("0x72", 0),  # ids of loaded vehicles in last time step
				int("0x7a", 0)  # ids of arrived vehicles in last time step
			})

	def getTripinfo(self):
		try:
			lines = list(self.tripinfoFile)
			for line in lines:
				if "<tripinfo id=" in line:
					self.total_trips += 1
					xml_string = "<tripinfos>"
					xml_string = "/n".join((xml_string, line))
					xml_string = "/n".join((xml_string, "</tripinfos>"))
					open_data = minidom.parseString(xml_string)
					intervals_open = open_data.getElementsByTagName('tripinfo')
					timeloss = float(intervals_open[0].getAttribute('timeLoss'))
					duration = float(intervals_open[0].getAttribute('duration'))
					self.total_timeloss += timeloss
					self.total_duration += duration
					relative_timeloss = timeloss / duration
					self.average_relative_timeloss = ((self.average_relative_timeloss * (
							self.total_trips - 1) + relative_timeloss) / self.total_trips)

			self.average_duration = self.total_duration / self.total_trips
			self.average_timeloss = self.total_timeloss / self.total_trips

		except Exception as e:
			# print(e)
			pass

	def scanLanes(self):
		self.lanes = traci.lane.getAllSubscriptionResults()
		self.closed_lanes = []
		for lane in self.lanes:
			if 'authority' in self.lanes[lane][52]:
				traci.lane.setParameter(lane, "color", "100")
				self.closed_lanes.append(lane)
			else:
				traci.lane.setParameter(lane, "color", str(
					170 * self.lanes[lane][19]
				))

	def add_vehicle(self, start, stop):
		id = str(self.last_vehicle_id)
		veh_id = "".join(("veh_", id))
		rou_id = "".join(("rou_", id))
		route = traci.simulation.findRoute(start, stop, vType="type1")
		traci.route.add(rou_id, route.edges)
		traci.vehicle.add(veh_id, rou_id, "type1")
		self.last_vehicle_id += 1

	def getLoadedVehicles(self):
		self.loaded_vehicles_ids = traci.vehicle.getIDList()
		return self.loaded_vehicles_ids

	def subscribeLoadedVehicles(self):
		for vehicle_id in self.loaded_vehicles_ids:
			if vehicle_id not in set(self.subscribed_vehicles_ids):
				traci.vehicle.subscribe(vehicle_id, [
					int("0x87", 0),  # accumulated waiting time
					int("0x45", 0),  # color
					int("0x54", 0),  # edges
					int("0x69", 0),  # route index
					int("0xbd", 0),  # line
					int("0x92", 0),  # is route valid
				])
				self.subscribed_vehicles_ids.append(vehicle_id)

	def scanVehicles(self):
		self.vehicles = traci.vehicle.getAllSubscriptionResults()
		for vehicle in self.vehicles:
			self.totalWaitingTime += self.vehicles[vehicle][135]
			is_invalid = not self.vehicles[vehicle][146]
			vehicle_color = self.vehicles[vehicle][69]
			if not is_invalid and vehicle_color != (255, 255, 0, 255):
				traci.vehicle.setColor(vehicle, (255, 255, 0, 255))
			if is_invalid:
				if vehicle_color != (255, 0, 0, 255):
					traci.vehicle.setColor(vehicle, (255, 0, 0, 255))
				route = self.vehicles[vehicle][84]
				route_index = self.vehicles[vehicle][105]

				current_edge = route[route_index]
				current_line = self.vehicles[vehicle][189]
				if current_line == '':
					current_line = 0
				if str(current_edge) + "_" + str(current_line) in self.closed_lanes:
					pass
				else:
					try:
						new_route = traci.simulation.findRoute(current_edge, route[len(route) - 1], vType="type1")
						traci.vehicle.setRoute(vehicle, new_route.edges)
					except traci.exceptions.TraCIException:
						traci.vehicle.setColor(vehicle, (1, 1, 1, 255))
						print("Vehicle stuck")
		self.averageWaitingTime = self.totalWaitingTime / len(self.vehicles)

	def getRouteTime(self):
		for route in self.measureRoutes:
			route['waitingtime'] = 0
			measure_route = traci.simulation.findRoute(route['from'], route['to'], vType="type1")
			route['waitingtime'] = measure_route.travelTime
			edges = traci.edge.getAllSubscriptionResults()
			for edge in measure_route.edges:
				waitingtime = edges[edge][122]
				route['waitingtime'] += waitingtime

	def setActive(self):
		traci.switch(self.simulationName)

	def sync_guis(self, global_zoom, global_offset):
		current_zoom = traci.gui.getZoom()
		current_offset = traci.gui.getOffset()
		if current_offset != self.offset:
			if current_offset != global_offset:
				global_offset = current_offset
				self.offset = current_offset
		else:
			if current_offset != global_offset:
				traci.gui.setOffset('View #0', global_offset[0],
				                    global_offset[1])
				self.offset = global_offset

		if current_zoom != self.zoom:
			if current_zoom != global_zoom:
				global_zoom = current_zoom
				self.zoom = current_zoom
		else:
			if current_zoom != global_zoom:
				traci.gui.setZoom('View #0', global_zoom)
				self.zoom = global_zoom
		return global_zoom, global_offset


def main():
	simulation_settings = init_simulation_settings()  # TODO import external settings
	simulation_init = init_simulations(simulation_settings)
	simulations = []
	simulations.append(Simulation(simulation_init[0]))
	simulations.append(Simulation(simulation_init[1]))
	global_zoom = 100
	global_offset = (10, 10)
	for simulation in simulations:
		simulation.start()
		simulation.initStaticObjects()
	timers = Timers(simulation_init)
	step = 1
	simulation_on = True
	while step < 1000 and simulation_on:
		for simulation in simulations:
			simulation.setActive()
			traci.simulationStep()
			if step % 1 == 0:
				# --------------------------------------------------------------- ADD VEHICLES
				simulation.add_vehicle(default_start_edge, default_end_edge)
				# --------------------------------------------------------------- CLOSED_LANES
				simulation.scanLanes()
				# --------------------------------------------------------------- GUI SYNC
				global_zoom, global_offset = simulation.sync_guis(global_zoom, global_offset)
				# ---------------------------------------------------------------

				if step % simulation_settings['route_correction_num_steps'] == 0:
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
