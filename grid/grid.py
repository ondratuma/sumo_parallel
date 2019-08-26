# -*- coding: utf-8 -*-

import os, sys, time
import random
from xml.dom import minidom
from curseXcel import Table
import unicodedata



current_milli_time = lambda: int(round(time.time() * 1000))
def do_open(filename):
	if not os.path.exists(os.path.dirname(filename)):
		try:
			os.makedirs(os.path.dirname(filename))
		except OSError as exc: # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise
	open(filename,'w').close()
	return open(filename,'r+')


if 'SUMO_HOME' in os.environ:
	tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
	sys.path.append(tools)
else:   
	sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
	#,"--device.rerouting.period","10","-l","plog2.txt","--device.rerouting.output","p-rerouting.txt","--device.rerouting.synchronize","--device.rerouting.threads","4"

#initiate traci

simulation_settings = {
	'width' : "750",
	"height" : "1080",
	"sumo_binary" : os.path.join(os.environ['SUMO_HOME'],'bin/sumo'),
	"sumo_gui" : os.path.join(os.environ['SUMO_HOME'],'bin/sumo-gui'),
	"coloring_mode" : 1,				#1 occupancy	#2 waiting time
	"global_zoom" : 100,
	"global_offset" : 100,
	"route_correction_num_steps" : 10
}									
simulations = [
	{
		'name' : 'sim1',
		
		'settings' : [
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
		'data' : {
			'tripinfo' : do_open("log/sim1log.trip.xml"),
			'total_timeloss' : 0,
			'average_timeloss' : 0,
			'num_lines' : 0,
			'zoom' : 0,
			'offset' : (0,0),
			'lanes' : [],
			'average_waiting_time' : 0,
			'total_waiting_time' : 0,
			'vehicles' : [],
			'timeloss' : 0,
			'avg_timeloss' : 0,
			'routes' :[
				{
					"from" : "gneE0",
					"to" : "gneE2",
					"current_expected_time" : 0
				}
			]
			
		}
	},
	{
		'name' : 'sim2',
		
		'settings' : [
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
		'data' : {
			'tripinfo' : do_open("log/sim2log.trip.xml"),
			'total_timeloss' : 0,
			'average_timeloss' : 0,
			'num_lines' : 0,
			'zoom' : 0,
			'offset' : (0,0),
			'lanes' : [],
			'average_waiting_time' : 0,
			'total_waiting_time' : 0,
			'timeloss' : 0,
			'avg_timeloss' : 0,
			'vehicles' : [],
			'routes' : [
				{
					"from" : "gneE0",
					"to" : "gneE2",
					"current_expected_time" : 0
				}
			]
				
			
		}
		
	}
]
lane_colors = {
	'closed' : '7',
}

step = 1




for simulation in simulations:
	traci.start(simulation['settings'],label=simulation['name']) 
	lanes_ids = traci.lane.getIDList()
	edges_ids = traci.edge.getIDList()
	traci.gui.setZoom('View #0',simulation_settings['global_zoom'])

	for lane_id in lanes_ids:
		traci.lane.subscribe(lane_id,{
			int("0x34",0), 	# allowed vehicle classes 
			int("0x12",0), 	# last step vehicle ids
			int("0x13",0),	# last step occupancy
			int("0x7a",0),	# last step waiting time
			int("0x5a",0),	# last step travel time
			int("0x41",0),	# vmax
			})

	for edge_id in edges_ids:
		traci.edge.subscribe(edge_id,{
			int("0x1b",0),	# street name
			int("0x5a",0),	# travel time
			int("0x13",0),	# occupancy
			int("0x7a",0)	# waiting time
			})




#manully adding vehicles
last_vehicle_id = 0
default_start_edge = "gneE0"
default_end_edge = "gneE2"
reversed_start = "gneE3"
reversed_end = "gneE1"

def add_vehicle(id,start,stop):
	id = str(id)
	veh_id = "".join(("veh_",id))
	rou_id = "".join(("rou_",id))
	route = traci.simulation.findRoute(start,stop,vType="type1")
	traci.route.add(rou_id,route.edges)
	traci.vehicle.add(veh_id,rou_id,"type1")
################################################################## Global timers
def timer_init (simulations):
	global timers
	for simulation in simulations:
		timers[simulation['name']] = {}
def timer_start (name,simulation_name):
	global timers
	timers[simulation_name][name] = []
	timers[simulation_name][name].append(current_milli_time())
def timer_end (name,simulation_name):
	global timers
	timers[simulation_name][name].append(current_milli_time())
################################################################## Parse xml tripinfo from open file
def parse_xml_tripinfo(xml_file):
	num_lines = 0
	total_timeloss = 0
	try:
		lines = list()
		for line in lines:
			if "<tripinfo id=" in line:
				num_lines += 1
				xml_string = "<tripinfos>"
				xml_string = "/n".join((xml_string,line))
				xml_string = "/n".join((xml_string,"</tripinfos>"))	
				open_data = minidom.parseString(xml_string)
				
				intervals_open = open_data.getElementsByTagName('tripinfo')	
				total_timeloss += float(intervals_open[0].getAttribute('timeLoss'))
		
	except Exception as e: 
		print(e)
	finally: 
		return total_timeloss, num_lines
################################################################## Subscribe to vehicles
def sub_veh_ids(veh_ids):
	for vehicle_id in vehicle_ids:
		if vehicle_id not in set(simulation['data']['vehicles']):
			traci.vehicle.subscribe(vehicle_id,{
				int("0x87",0), 	# acumulated waiting time 
				int("0x45",0),	# color
				int("0x54",0),	# edges
				int("0x69",0),	# route index 
				int("0xbd",0),	# line
				int("0x92",0),	# is route valid
				})
################################################################## color lanes				
def act_closed_lanes(lanes):	
	closed_lanes = []		
	for lane in lanes:
		if 'authority' in lanes[lane][52]:
			traci.lane.setParameter(lane,"color","100")
			closed_lanes.append(lane)
		else:
			traci.lane.setParameter(lane,"color",str(
				170* lanes[lane][19] 
				))
	return closed_lanes

################################################################## Compare actual / local / global gui settings and act upon
def sync_guis(current_zoom,current_offset):
	global simulation
	if current_offset != simulation['data']['offset']:
		if current_offset != simulation_settings['global_offset']:
			simulation_settings['global_offset'] = current_offset
			simulation['data']['offset'] = current_offset
	else:
		if current_offset != simulation_settings['global_offset']:
			traci.gui.setOffset('View #0',simulation_settings['global_offset'][0],simulation_settings['global_offset'][1])
			simulation['data']['offset'] = simulation_settings['global_offset']

	if current_zoom != simulation['data']['zoom']:
		if current_zoom != simulation_settings['global_zoom']:
			simulation_settings['global_zoom'] = current_zoom
			simulation['data']['zoom'] = current_zoom
	else:
		if current_zoom != simulation_settings['global_zoom']:
			traci.gui.setZoom('View #0',simulation_settings['global_zoom'])
			simulation['data']['zoom'] = simulation_settings['global_zoom']

################################################################## iterate over list of vehicles and act upon
def act_vehicles(vehicles):
	for vehicle in vehicles:
		simulation['data']['total_waiting_time'] += vehicles[vehicle][135]	
		is_invalid = not vehicles[vehicle][146]
		vehicle_color = vehicles[vehicle][69]
		if not is_invalid and vehicle_color != (255,255,0,255):
			traci.vehicle.setColor(vehicle,(255,255,0,255))
		if is_invalid:
			if vehicle_color != (255,0,0,255):
				traci.vehicle.setColor(vehicle,(255,0,0,255))	
			route = vehicles[vehicle][84]
			route_index = vehicles[vehicle][105]

			current_edge = route[route_index]
			current_line = vehicles[vehicle][189]
			if current_line == '':
				current_line = 0
			if str(current_edge) + "_" + str(current_line) in closed_lanes:
				pass
			else:
				try: 
					new_route = traci.simulation.findRoute(current_edge,route[len(route)-1],vType="type1")
					traci.vehicle.setRoute(vehicle,new_route.edges)
				except:
					traci.vehicle.setColor(vehicle,(1,1,1,255))
					print("Vehicle stuck")
import curses

################################################################## Output formatiing settings
screen = curses.initscr()
table = Table(screen, 30, 4, 10, 40, 20, col_names=True, spacing=None)	
output_table = [
	['STEP','','TIME',''],									# 0
	['----------','--------','----------','----------'],	# 1
	[],														# 2
	[],														# 3
	[],														# 4
	['','SIM1','SIM2','DIFF'],								# 5
	['WAITING'],											# 6
	['ROUTE'],												# 7
	['T_LOSS'],												# 8
	[],														# 9
	['TIMERS','--------','----------','----------']			# 10
]
timers_row = 11

def init_table(input_table):
	for row_index, row in enumerate(input_table):
		for col_index, cell in enumerate(row):
			if cell:
				table.set_cell(row_index,col_index,cell)
traci.simulation.subscribe(
	{
		int("0x72",0), # ids of loaded vehicles in last time step
		int("0x7a",0)  # ids of arrived vehicles in last time step
	})
simulation_on = True
timers = {}
init_table(output_table)
timer_init(simulations)



while step < 1000 and simulation_on:	
	timer_start('step',simulation['name'])
	for simulation in simulations:
		timer_start('sim',simulation['name'])
		traci.switch(simulation['name'])	
		traci.simulationStep()
		if step % 1 == 0:
			################################################################## ADD VEHICLES
			timer_start('add_veh',simulation['name'])
			add_vehicle(last_vehicle_id,default_start_edge,default_end_edge)
			last_vehicle_id += 1 
			add_vehicle(last_vehicle_id,reversed_start,reversed_end)
			last_vehicle_id += 1 
			timer_end('add_veh',simulation['name'])
			################################################################## CLOSED_LANES
			timer_start('lane_coloring',simulation['name'])
			lanes = traci.lane.getAllSubscriptionResults()
			closed_lanes = act_closed_lanes(lanes)
			timer_end('lane_coloring',simulation['name'])			
			################################################################## GUI SYNC
			timer_start('gui',simulation['name'])
			sync_guis(traci.gui.getZoom(),traci.gui.getOffset())		
			timer_end('gui',simulation['name'])
			################################################################## 

			if step % simulation_settings['route_correction_num_steps'] == 0: 
				timer_start('e_10',simulation['name'])

				################################################################## tripinfo xml 
				timer_start('tripinfo',simulation['name'])
				total_timeloss, num_lines = parse_xml_tripinfo(simulation['data']['tripinfo'])
				simulation['data']['total_timeloss'] += total_timeloss
				simulation['data']['num_lines'] += num_lines
				try:
					simulation['data']['average_timeloss'] = simulation['data']['total_timeloss'] / simulation['data']['num_lines']	
				except:
					pass
				timer_end('tripinfo',simulation['name'])
				################################################################## get vehicle ids
				timer_start('veh_init',simulation['name'])
				vehicle_ids = traci.vehicle.getIDList()
				sub_veh_ids(vehicle_ids)
				timer_end('veh_init',simulation['name'])


				################################################################## vehicle iteration
				timer_start('veh_run',simulation['name'])
				simulation['data']['total_waiting_time'] = 0
				simulation['data']['average_waiting_time'] = 0
				simulation['data']['vehicles'] = traci.vehicle.getAllSubscriptionResults()
				vehicles = simulation['data']['vehicles']
				act_vehicles(vehicles)
				timer_end('veh_run',simulation['name'])				
				################################################################## meassure time for defined routes
				timer_start('routes',simulation['name'])
				simulation['data']['average_waiting_time'] = simulation['data']['total_waiting_time'] / len(vehicles)
				for route in simulation['data']['routes']:
					route['waitingtime'] = 0	
					measure_route = traci.simulation.findRoute(route['from'],route['to'],vType="type1")
					route['waitingtime'] = measure_route.travelTime
					edges = traci.edge.getAllSubscriptionResults()
					for edge in measure_route.edges:
						waitingtime = edges[edge][122]
						route['waitingtime'] += waitingtime
				timer_end('routes',simulation['name'])
				timer_end('e_10',simulation['name'])
		timer_end('sim',simulation['name'])

		
	if step % 10 == 0:
		################################################################## print all data
		timer_start('printing',simulation['name'])
		waiting_difference = simulations[0]['data']['average_waiting_time'] - simulations[1]['data']['average_waiting_time']
		route_1_difference = simulations[0]['data']['routes'][0]['waitingtime'] - simulations[1]['data']['routes'][0]['waitingtime']
		avg_timeloss_diff = simulations[0]['data']['average_timeloss'] - simulations[1]['data']['average_timeloss']


		table.set_cell(6,1,str("%.2f" % simulations[0]['data']['average_waiting_time']))
		table.set_cell(6,2,str("%.2f" % simulations[1]['data']['average_waiting_time']))
		table.set_cell(6,3,str("%.2f" % waiting_difference))

		table.set_cell(7,1,str("%.2f" % simulations[0]['data']['routes'][0]['waitingtime']))
		table.set_cell(7,2,str("%.2f" % simulations[1]['data']['routes'][0]['waitingtime']))
		table.set_cell(7,3,str("%.2f" % route_1_difference))

		table.set_cell(8,1,str("%.2f" % simulations[0]['data']['average_timeloss']))
		table.set_cell(8,2,str("%.2f" % simulations[1]['data']['average_timeloss']))		
		table.set_cell(8,3,str("%.2f" % avg_timeloss_diff))		

		table.set_cell(3,0,"zoom")
		table.set_cell(3,1,"%.2f" % simulations[0]['data']['zoom'])
		table.set_cell(3,2,"%.2f" % simulations[1]['data']['zoom'])

		table.set_cell(4,0,'offset')
		table.set_cell(4,1,str("%.0f" % simulations[0]['data']['offset'][0]) + ":" + str("%.0f" % simulations[0]['data']['offset'][1]))
		table.set_cell(4,2,str("%.0f" % simulations[1]['data']['offset'][0]) + ":" +  str("%.0f" % simulations[1]['data']['offset'][1]))
		timer_end('printing',simulation['name'])
		timer_end('step',simulation['name'])
		################################################################## Print timers
		for key, simulation in enumerate(simulations):
			timers_row = 11
			for timer in timers[simulation['name']]:
				table.set_cell(timers_row,0,timer)
				table.set_cell(timers_row,key + 1,timers[simulation['name']][timer][1] - timers[simulation['name']][timer][0])
				timers_row += 1	
		table.set_cell(0,1,str(step))
		##################################################################
	
	

	

	table.refresh()
	step += 1
for simulation in simulations:
	traci.switch(simulation['name'])
	traci.close(False)


