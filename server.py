#coding
import socket # socket
import struct # tcp-struct
import hashlib,base64 #hashmap
import threading,random #thread, random tokenID

connectionlist = {} # client list

def sendMessage(message): # server send message to all client
	global connectionlist
	for connection in connectionlist.values():
		connection.send("\x00%s\xFF" % message)

def deleteconnection(item): # server remove one connection
	global connectionlist
	del connectionlist['connection'+item]

def generate_token_2(self, key): # create tokenID by base64
	key = key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
	ser_key = hashlib.sha1(key).digest()
	return base64.b64encode(ser_key)

def generate_token(self, key1, key2, key3):
	num1 = int("".join([digit for digit in list(key1) if digit.isdigit()]))
	spaces1 = len([char for char in list(key1) if char == " "])
	num2 = int("".join([digit for digit in list(key2) if digit.isdigit()]))
	spaces2 = len([char for char in list(key2) if char == " "])
	combined = struct.pack(">II", num1/spaces1, num2/spaces2) + key3
	return hashlib.md5(combined).digest()

# websocket class based on thread
class WebSocket(threading.Thread):
	def __init__(self, conn, index, name, remote, path="/"): # init websocket
		threading.Thread.__init__(self)
		self.conn = conn
		self.index = index
		self.name = name
		self.remote = remote
		self.path = path
		self.buffer = ""

	def run(self): # http connection & so on
		print 'Socket%s Start!' % self.index
		headers = {}
		self.handshaken = False
		while True:
			if self.handshaken == False: # before http-handshake
				print 'Socket%s Start Handshaken with %s!' % (self.index, self.remote)
				self.buffer += self.conn.recv(1024) # receive 1024 bit from remote connection
				if self.buffer.find('\r\n\r\n') != -1:
					# header parse
					header, data = self.buffer.split('\r\n\r\n', 1)
					for line in header.split("\r\n")[1:]:
						key, value = line.split(": ", 1)
						headers[key] = value
					headers["Location"] = "ws://%s%s" %(headers["Host"], self.path)
					
					# data parse
					if len(data) < 8:
						data += self.conn.recv(8-len(data))
					self.buffer = data[8:]
					token = generate_token_2(self, key) # create a tokenID

					handshake = '\
					HTTP/1.1 101 Web Socket Protocol Handshake\r\n\
					Upgrade: WebSocket\r\n\
					Connection: Upgrade\r\n\
					Sec-WebSocket-Origin: %s\r\n\
					Sec-WebSocket-Location: %s\r\n\r\n\
					'%(headers['Origin'], headers['Location']) # return handshake info
					self.handshaken = True # set true
					sendMessage('Welcome, '+self.name+' !')  # welcome message
			else: # after http-handshake
				self.buffer += self.conn.recv(64) # read 64bit from client to buffer
				if self.buffer.find("\xFF")!=-1:
					s = self.buffer.split("\xFF")[0][1:]
					if s=='quit': # client send message to stop connection
						sendMessage(self.name+' Logout')
						deleteconnection(str(self.index))
						self.conn.close()
						break
					else:
						sendMessage(self.name+":"+s)
					self.buffer = "" # clear buffer per time

# create websokcet server [one server muli-thread]
class WebSocketServer(object): 
	def __init__(self):
		self.socket = None
	def begin(self):
		print 'WebSocketServer Start!' # log
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # tcp-init
		ip = "localhost"
		port = 8080
		self.socket.bind((ip,port)) # binding
		self.socket.listen(50) # max_connection

		i = 0 # counting client valume
		global connectionlist
		while True:
			connection, address = self.socket.accept()
			username = address[0]
			newSocket =WebSocket(connection,i,username,address) # create websocket connection
			newSocket.start() # start a thread
			connectionlist['connection'+str(i)]=connection # create connection per client
			i += 1 # who will be the next one?

if __name__ == "__main__":
	server = WebSocketServer()
	server.begin()
