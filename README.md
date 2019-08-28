# sumo_parallel
sumo_parallel is a small script with the intention to **compare sumo simulations on the fly** mainly for demonstration
 purposes. 
###requirements
- python3
- 
### run
to run the grid scenario
```
python3 sumo_parallel.py grid
```
## Install sumo
https://sumo.dlr.de/wiki/Installing
https://sumo.dlr.de/wiki/Installing/Linux_Build#Building_the_SUMO_binaries_with_cmake_.28recommended.29

####DEFINE SUMO_HOME !!!

#####on linux
get the install directory
```buildoutcfg
which sumo
```

set sumo_home
```buildoutcfg
export SUMO_HOME="your/install/directory"
```
#####on windows
https://sumo.dlr.de/wiki/Basics/Basic_Computer_Skills#Windows

## Create scenario
to create own scenario, duplicate the grid subfolder and rename it to your scenario name. Set all simulation settings 
in the subfolder.
### Map generation

####Download map data
http://download.geofabrik.de/

####Generate boundaries 
boundaries easy generate		https://boundingbox.klokantech.com/
- Prague 
```top=50.149717 left=14.315076 bottom=50.020224 right=14.547125```
- Prague 1
```top=50.094109 left=14.411357 bottom=50.076919 right=14.435836```
####Crop map based on boundaries
https://wiki.openstreetmap.org/wiki/Osmosis
```
osmosis/bin/osmosis --read-xml mapfile.osm.pbf --bounding-box top=50.149717 left=14.315076  bottom=50.020224 right=14.547125 --write-xml file="output.osm"
```
## Final visualization
plot net dump
```
python $SUMO_HOME/tools/visualization/plot_net_dump.py -i edgedata.xml,edgedata.xml -n grid.net.xml --output net.png
```
mlp dump
```
python $SUMO_HOME/tools/visualization/mpl_dump_onNet.py --show -n grid.net.xml -d edgedata.xml
```

