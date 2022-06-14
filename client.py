import sys
import socket
import time
import thread
import os
import Queue
import json
############################################################################################
######################################### Time Configuration################################
############################################################################################

# Time interval between excahnge data
global timeinterval
try:
	timeinterval=int(raw_input('Please enter the time interval between exchanging data with serverip, default set to 30 \n'))
except:
	timeinterval = 30
print 'Timeinterval set to: ' + str(timeinterval) + ' seconds'
	
# Time before triggering heartbeat
#global timebeforehb
#timebeforehb = 20









############################################################################################
######################################## Testing Configuration #############################
############################################################################################


# Time blocking the heartbeat protocol reply (Tsting Purpose)
global timeblockinghb
try:
	timeblockinghb = int(raw_input('Please enter the time blocking the heartbeat protocol. \nWarning: Not recommended, only for testing purpose. Default is set to 0 \n'))
except:
	timeblockinghb = 0
print 'Time blocking Heartbeat protocol set to: ' + str(timeblockinghb) + ' seconds'




#############################################################################################
####################################### Socket Configuration ################################
#############################################################################################
	
# Reading settings from configuration.json file
with open('configuration.json') as json_data_file:
	data = json.load(json_data_file)

HOST = (data["server"]["host"])
PORT = int((data["server"]["port"]))
Clienthost = (data["client"]["host"])
Clientport = int((data["client"]["port"]))

###################################################
##############client script########################
###################################################

#triggerhb = Queue.Queue()
#triggerhb.put(1)


########################################################
################## Threads #############################
########################################################
# client heartbeat thread
def heartbeatclientthread():
	ClientHeartbeatSocket = socket.socket()
	print 'Heartbeat socket has been created'
	ClientHeartbeatSocket.bind((Clienthost,Clientport))
	print 'Heartbeat socket has been bound'
	ClientHeartbeatSocket.listen(10)
	conn, addr = ClientHeartbeatSocket.accept()
	print 'Connected with ' + addr[0] + ':' + str(addr[1])
	while True:
		hbdata = conn.recv(1024)
		if 'End Connection' in hbdata:
			conn.close()
			print 'Connection closed by server'
			os._exit(0)
			break
		elif not hbdata:
			conn.close()
			print 'Disconnected by server'
			os.exit(0)
			break
		elif hbdata:
			print hbdata
		reply = 'Echoing...' + hbdata
		time.sleep(timeblockinghb)
        	try:
            		conn.sendall(reply)
			continue
		except:
			pass
		continue


########################################################
################## Main Thread #########################
########################################################

#Start the client heartbeat threat to monitor heartbeat
thread.start_new_thread(heartbeatclientthread,())

clientsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

clientsocket.connect((HOST, PORT))

while True:

        time.sleep(timeinterval)

        clientsocket.sendall(b'Hello, there')
	print 'data sent'		
	try:	
		data = clientsocket.recv(1024)
		
        	print('Received', repr(data))
	
	except:
		pass


#	if 'End Connection' in data:
#		clientsocket.close()
#		print 'Connection closed by server'
