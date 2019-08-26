from xml.dom import minidom
import unicodedata
open_data = minidom.parse('edgedata-open.xml')
closed_data = minidom.parse('edgedata-closed.xml')
intervals_open = open_data.getElementsByTagName('interval')
intervals_closed = closed_data.getElementsByTagName('interval')
intervals = zip(intervals_open,intervals_closed)

output = doc = minidom.Document()
meandata = output.createElement('book')
for interval_open,interval_closed in intervals:
    output_string = ""
    if interval_open.attributes['id'].value == interval_closed.attributes['id'].value:
        edges_open = interval_open.getElementsByTagName("edge")
        edges_closed = interval_closed.getElementsByTagName("edge")
        edges = zip(edges_open,edges_closed)
        for edge_open,edge_closed in edges:
            if edge_open.attributes["id"].value == edge_closed.attributes["id"].value:
                attributes_open = edge_open.attributes.items()
                attributes_closed = edge_closed.attributes.items()
                output_attributes = []

                for attribute_open in attributes_open:
                    try:
                        att_name = unicodedata.normalize('NFKD', attribute_open[0]).encode('ascii','ignore')
                        if att_name != 'id':
                            open_att_value = attribute_open[1]
                            closed_att_value = edge_closed.attributes[att_name].value
                            final_value = str(float(open_att_value) - float(closed_att_value))
                            output_attribute = (att_name,final_value)
                            print (output_attribute)
                    except:
                        pass
                for attribute_closed in attributes_closed:
                    try:
                        att_name = unicodedata.normalize('NFKD', attribute_closed[0]).encode('ascii','ignore')
                        #print(edge_open.attributes[att_name].value)
                    except:
                        print("fuck")
                
                
            else:
                print("fuck")  