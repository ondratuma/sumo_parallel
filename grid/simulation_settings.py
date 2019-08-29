import os

def both_settings(sumo_home):
	return {
		"width": "750",
		"height": "1080",
		"sumo_binary": os.path.join(sumo_home, 'bin/sumo'),
		"sumo_gui": os.path.join(sumo_home, 'bin/sumo-gui'),
		"edgedump" : "log/log.edgedata.xml",
		"netfile" : "grid.net.xml",
		"plot_net_dump" : {
			"metrics" : [
				"density",
				"overlapTraveltime",
				'occupancy',
				'waitingTime'
			]
		},
		"global_zoom": 100,
		"global_offset": 100,
		"route_correction_num_steps": 10,
		'measure_routes': [
			{
				"from": "gneE0",
				"to": "gneE2",
				"current_expected_time": 0
			}
		],
		"deploy_routes": [
			{
				'from': "gneE0",
				'to': "gneE2",
				'period': 1
			}
		]
	}

def each_simulation_settings(simulation_settings):
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
			"edgedump": "log/sim1log.edgedata.xml",
			"netfile": simulation_settings['netfile'],
			"deploy_routes": simulation_settings["deploy_routes"],
			"measure_routes": simulation_settings["measure_routes"],
			'data': {
				'tripinfo': "log/sim1log.trip.xml"
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
			"edgedump": "log/sim2log.edgedata.xml",
			"netfile": simulation_settings['netfile'],
			"deploy_routes": simulation_settings["deploy_routes"],
			"measure_routes": simulation_settings["measure_routes"],
			'data': {
				'tripinfo': "log/sim2log.trip.xml",


			}

		}
	]
