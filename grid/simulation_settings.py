import os
def init_gui_settings(sumo_home):
	return {
		"width": "750",
		"height": "1080",
		"sumo_binary": os.path.join(sumo_home, 'bin/sumo'),
		"sumo_gui": os.path.join(sumo_home, 'bin/sumo-gui'),
		"global_zoom": 100,
		"global_offset": 100,
		"route_correction_num_steps": 10
	}
def init_simulation_settings(simulation_settings):
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