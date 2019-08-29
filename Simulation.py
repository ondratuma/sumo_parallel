from sumo_parallel_tools import do_open
from xml.dom import minidom


class Simulation:
	def __init__(self, settings, traci):
		self.traci = traci
		self.settings = settings
		self.start_command = settings['settings']
		self.tripinfoFilename = settings['data']['tripinfo']
		self.tripinfoFile = do_open(self.tripinfoFilename)
		self.edgeDumpFilename = settings['edgedump']
		self.netfile = settings['netfile']
		self.simulationName = settings['name']
		self.measureRoutes = settings['measure_routes']
		self.deployRoutes = settings['deploy_routes']
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
		self.route_correction_num_steps = 10
	def start(self):
		self.traci.start(self.start_command, label=self.simulationName)
		self.lanes_ids = self.traci.lane.getIDList()
		self.edges_ids = self.traci.edge.getIDList()

	def initStaticObjects(self):
		for lane_id in self.lanes_ids:
			self.traci.lane.subscribe(lane_id, {
				int("0x34", 0),  # allowed vehicle classes
				int("0x12", 0),  # last step vehicle ids
				int("0x13", 0),  # last step occupancy
				int("0x7a", 0),  # last step waiting time
				int("0x5a", 0),  # last step travel time
				int("0x41", 0),  # vmax
			})

		for edge_id in self.edges_ids:
			self.traci.edge.subscribe(edge_id, {
				int("0x1b", 0),  # street name
				int("0x5a", 0),  # travel time
				int("0x13", 0),  # occupancy
				int("0x7a", 0)  # waiting time
			})
		self.traci.simulation.subscribe(
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
		self.lanes = self.traci.lane.getAllSubscriptionResults()
		self.closed_lanes = []
		for lane in self.lanes:
			if 'authority' in self.lanes[lane][52]:
				self.traci.lane.setParameter(lane, "color", "100")
				self.closed_lanes.append(lane)
			else:
				self.traci.lane.setParameter(lane, "color", str(
					170 * self.lanes[lane][19]
				))

	def add_vehicle(self, start, stop):
		id = str(self.last_vehicle_id)
		veh_id = "".join(("veh_", id))
		rou_id = "".join(("rou_", id))
		route = self.traci.simulation.findRoute(start, stop, vType="type1")
		self.traci.route.add(rou_id, route.edges)
		self.traci.vehicle.add(veh_id, rou_id, "type1")
		self.last_vehicle_id += 1

	def getLoadedVehicles(self):
		self.loaded_vehicles_ids = self.traci.vehicle.getIDList()
		return self.loaded_vehicles_ids

	def subscribeLoadedVehicles(self):
		for vehicle_id in self.loaded_vehicles_ids:
			if vehicle_id not in set(self.subscribed_vehicles_ids):
				self.traci.vehicle.subscribe(vehicle_id, [
					int("0x87", 0),  # accumulated waiting time
					int("0x45", 0),  # color
					int("0x54", 0),  # edges
					int("0x69", 0),  # route index
					int("0xbd", 0),  # line
					int("0x92", 0),  # is route valid
				])
				self.subscribed_vehicles_ids.append(vehicle_id)

	def scanVehicles(self):
		self.vehicles = self.traci.vehicle.getAllSubscriptionResults()
		for vehicle in self.vehicles:
			self.totalWaitingTime += self.vehicles[vehicle][135]
			is_invalid = not self.vehicles[vehicle][146]
			vehicle_color = self.vehicles[vehicle][69]
			if not is_invalid and vehicle_color != (255, 255, 0, 255):
				self.traci.vehicle.setColor(vehicle, (255, 255, 0, 255))
			if is_invalid:
				if vehicle_color != (255, 0, 0, 255):
					self.traci.vehicle.setColor(vehicle, (255, 0, 0, 255))
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
						new_route = self.traci.simulation.findRoute(current_edge, route[len(route) - 1], vType="type1")
						self.traci.vehicle.setRoute(vehicle, new_route.edges)
					except self.traci.exceptions.traciException:
						self.traci.vehicle.setColor(vehicle, (1, 1, 1, 255))
						print("Vehicle stuck")
		self.averageWaitingTime = self.totalWaitingTime / len(self.vehicles)

	def getRouteTime(self):
		for route in self.measureRoutes:
			route['waitingtime'] = 0
			measure_route = self.traci.simulation.findRoute(route['from'], route['to'], vType="type1")
			route['waitingtime'] = measure_route.travelTime
			edges = self.traci.edge.getAllSubscriptionResults()
			for edge in measure_route.edges:
				waitingtime = edges[edge][122]
				route['waitingtime'] += waitingtime

	def setActive(self):
		self.traci.switch(self.simulationName)

	def sync_guis(self, global_zoom, global_offset):
		current_zoom = self.traci.gui.getZoom()
		current_offset = self.traci.gui.getOffset()
		if current_offset != self.offset:
			if current_offset != global_offset:
				global_offset = current_offset
				self.offset = current_offset
		else:
			if current_offset != global_offset:
				self.traci.gui.setOffset('View #0', global_offset[0],
				                    global_offset[1])
				self.offset = global_offset

		if current_zoom != self.zoom:
			if current_zoom != global_zoom:
				global_zoom = current_zoom
				self.zoom = current_zoom
		else:
			if current_zoom != global_zoom:
				self.traci.gui.setZoom('View #0', global_zoom)
				self.zoom = global_zoom
		return global_zoom, global_offset
