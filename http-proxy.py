# -*- coding: utf-8 -*- 
# @ filename: http-proxy.py
# @ author: 陈介平
# @ student number: PB14209115 
# @ date: 2016.12.31 
# @ function: 实现代理功能 

import socketserver
import socket
import threading
import os


class MyThread(threading.Thread):
	def __init__(self, request, dest_host, dest_port, data):
		# 初始化函数
		threading.Thread.__init__(self)
		self.request = request
		self.dest_host = dest_host
		self.dest_port = dest_port
		self.data = data

	def run(self):
		# 创建一个socket连接 (SOCK_STREAM means a TCP socket)
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			# 连接到服务器
			sock.connect((self.dest_host, self.dest_port))
			# 发送数据
			sock.sendall(self.data)
			# 从服务器获取数据
			while True:
				received = sock.recv(1024)
				if len(received) > 0:
					self.request.sendall(received)
				else:
					break


class MyHTTPSThread(threading.Thread):
	def __init__(self, request, dest_host, dest_port, sock):
		# 初始化函数
		threading.Thread.__init__(self)
		self.request = request
		self.sock = sock
		self.dest_host = dest_host
		self.dest_port = dest_port

	def run(self):
		# 连接到服务器
		print("connect to", self.dest_host, self.dest_port)
		self.sock.connect((self.dest_host, self.dest_port))
		print("connect", self.dest_host, "completed")
		# 发送数据
		self.request.sendall(b"HTTP/1.1 200 Connection Established\n\n")
		print(self.dest_host, "send completed")
		# 从服务器端获取数据
		while True:
			received = self.sock.recv(1024)
			if len(received) > 0:
				print("receive:", received)
				self.request.sendall(received)


class MyTCPHandler(socketserver.BaseRequestHandler):
	def handle(self):
		self.isHttps = False
		while True:
			self.data = self.request.recv(1024)
			if self.isHttps:
				self.sock.sendall(self.data)
			else:
				lines = self.data.split(b"\n")

				# 分离请求行，把请求方法、请求的url等信息分开存储到对应的数组项中
				first_line = lines[0]
				first_arr = first_line.split()
				method = first_arr[0]
				# 打印请求的方式
				print(method)
				if method == b"CONNECT":
					# 处理"CONNECT"请求
					self.isHttps = True
					dest_tuple = first_arr[1].split(b":")
					dest_host = dest_tuple[0].decode("utf-8")
					dest_port = int(dest_tuple[1].decode("utf-8"))
					self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					MyHTTPSThread(self.request, dest_host, dest_port, self.sock).start()
				else:
					# 获取完整的请求url
					absolute_url = first_arr[1]
					# 限制对域名含'csdn.net'的网页的访问
					limit = absolute_url.find(b'csdn.net')
					if limit > 0:
						print('The request url is limited!')
						os._exit()
					if absolute_url.startswith(b"http://"):
						# 处理HTTP请求
						first_arr[1] = absolute_url[absolute_url.find(b'/', 7):]
					elif absolute_url.startswith(b"https://"):
						# 处理HTTPS请求
						first_arr[1] = absolute_url[absolute_url.find(b'/', 8):]
					lines[0] = b" ".join(first_arr)

					for index, line in enumerate(lines):
						if line.startswith(b"Proxy-Connection"):
							lines[index] = line.replace(b"Proxy-Connection", b"Connection")
						if line.startswith(b"Host"):
							tmp_arr = line.split()[1].split(b":")
							dest_host = tmp_arr[0].decode("utf-8")
							if len(tmp_arr) > 1:
								dest_port = int(tmp_arr[1].decode("utf-8"))
							else:
								dest_port = 80
					self.data = b"\n".join(lines)
					thread = MyThread(self.request, dest_host, dest_port, self.data)
					thread.start()



if __name__ == "__main__":
	# 在cmd命令行中用netstat查询，发现本机端口号8888空闲，可以使用
	HOST, PORT = "localhost", 8888
	# 创建服务器，把本地端口号8888开放由作服务器端口号使用
	server = socketserver.ThreadingTCPServer((HOST, PORT), MyTCPHandler)
	# 运行服务器端，直至按下Ctrl+C键结束程序
	server.serve_forever()
