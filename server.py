import sys
import socket
import time
import thread
import threading
import Queue
import json

###########################################################################
############################# Configuration ###############################
###########################################################################

# Reading settings from configuration.json file
with open('configuration.json') as json_data_file:
	data = json.load(json_data_file)

host = (data["server"]["host"])
port = int((data["server"]["port"]))
clientHeartbeatPort = int((data["client"]["port"]))

##########################################################################
########################## Time Interval #################################
##########################################################################
# Time interval between sending each heartbeat
global hbtimeouttime
try:
	hbtimeouttime = int(raw_input('Please enter the time interval between each heartbeat, default is set to 10 \n'))
	if hbtimeouttime < 0:
		hbtimeouttime = 10
except:
	hbtimeouttime = 10
print 'Time interval between heartbeats: ' + str(hbtimeouttime)


# number of heartbeats to send before disconnecting
global nofheartbeat
try:
	nofheartbeat = int(raw_input('Please enter the number of heartbeats to send before disconnecting, default is set to 3 \n'))
	if nofheartbeat < 0:
		nofheartbeat = 3
except:
	nofheartbeat = 3
print 'Number of heartbeats: ' +str(nofheartbeat)


# how many seconds before sending the heartbeat
global timeouttime
hbprotocoltime = hbtimeouttime * nofheartbeat

try:
	timeouttime = int(raw_input('Please enter how many seconds to wait if no data is exchanged before starting heartbeat protocol \n Warning: This should be longer than the toatal time of the heartbeat protocol, if not appplication will use the toltal time of the heartbeat protocol \n'))

	if timeouttime <= hbprotocoltime:
		timeouttime = hbprotocoltime + 10

except:
		timeouttime = hbprotocoltime + 10
print 'Timeout time set to: ' + str(timeouttime)

###################################################################################
############################# Testing Configuration ###############################
###################################################################################

#blocking incoiming traffic for testing purpose, set to True for porduction
global replying
replying = True


###########################################################################
############################ Binding Socket ###############################
###########################################################################
# bindging the main socket
serversocket = socket.socket()
serversocket.bind((host,port))
print 'Socket has been created and bind to port: '+str(port)
serversocket.listen(10)
print 'Socket is now listening'

###########################################################################
############################## Threads ####################################
###########################################################################

# defining the heartbeat thread
def heartbeatthread(addr,conn,starthb,alive):
	n=0 
	
	# connecting to client's heartbeat socket
	heartbeatsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	heartbeatsocket.connect((addr[0],clientHeartbeatPort))
	heartbeatsocket.settimeout(hbtimeouttime)
	while True:
		#get start heartbeat value:
			#1: Start heart beat protocol
			#2: End conncetion without heart beat
			#3: Stop and wait for the start heartbeat value to be changed
		run = starthb.get()
		if run == 2:
                                heartbeatsocket.shutdown(socket.SHUT_RDWR)
                                heartbeatsocket.close()
                                print 'Connection with ' + addr[0] + ':' + '8000 has been diconnected by client'
                                starthb.put(0)
                                break
		if run == 1:
			while n < nofheartbeat:
				n = n +1
				heatbeatmessage = b'heartbeat'
				heartbeatsocket.sendall(b'heartbeat')
				print 'HeartBeat Control Message: Sending heart beat, time: ' + str(n)
				try:	
					data = heartbeatsocket.recv(1024)
					print ('HeartBeat Control Message: Recieved', repr(data),' connection is alive')
					alive.put(1)
					n = 0
					starthb.put(0)
					break
				except:
					continue

			if n >= nofheartbeat:
				heartbeatsocket.sendall(b'End Connection')
				heartbeatsocket.shutdown(socket.SHUT_RDWR)
				heartbeatsocket.close()
    				print 'Connection with ' + addr[0] + ':' + '8000 has been closed'
				starthb.put(0)
				alive.put(0)
				break

			
# define client connection thread)
def clientthread(conn,addr):
	starthb = Queue.Queue()
	alive = Queue.Queue()
	starthb.put(0)
	alive.put(1)
	# start thread2 - the heart beat thread
	t2 = threading.Thread(target = heartbeatthread,args=(addr,conn,starthb,alive))
	t2.start()

# Keep reading from client connection
	while True:
		# Check if the connection is still alive
		try:
			checkalive = alive.get_nowait()
		except: 
			pass
		# Close the connection if the Checklive value is 0
		if checkalive == 0:
			conn.sendall(b'End Connection')
                        conn.close()
                        print 'Connection with ' + addr[0] + ':' + str(addr[1]) + ' has been closed'
			break
		
		# if hasn't recieved data from client after designed time, start the heartbeat
		try:
			conn.settimeout(timeouttime)
	        	# Read message from client
	        	data = conn.recv(1024)
			reply = 'Echoing...' + data
			# Close the socket if client is disconnected
			if not data:
                        	print 'Connection with ' + addr[0] + ':' + str(addr[1]) + ' has been terminated by client'
                        	conn.close()
				starthb.put(2)
				break
			try:
                        	print data
	            		conn.sendall(reply)
			except:
				pass
			continue
		# start the heartbeat protocl, since x seconds has past
		except socket.timeout:
                        print 'has not received data for the past: ' +str(timeouttime) + ' seconds, from: ' + addr[0] + ':' + str(addr[1])
                        starthb.put(1)
			continue
		
#		if not data:
#			print 'Connection with ' + addr[0] + ':' + str(addr[1]) + ' has been terminated by client'
#			break
#			conn.close()
		
############################################################################################################################
############################################# Main Thread ##################################################################
############################################################################################################################


#main thread, keep waiting and start a new client thread when there is incoming connections from clients      
while True:
        conn, addr = serversocket.accept()
        print 'Connected with ' + addr[0] + ':' + str(addr[1])
        thread.start_new_thread(clientthread,(conn,addr))

