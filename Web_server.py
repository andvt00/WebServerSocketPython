import socket
 
address = ('0.0.0.0',10968)
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind(address)
s.listen(1)
print('Serving on localhost:'+str(address[1]))
while True:
   connection,address = s.accept()
   request = connection.recv(1024).decode('utf-8')
   print(request)
   string_list = request.split(' ')     # Split request from spaces
   method = string_list[0]
   try:
      name_file=''
      if method=='GET':
         if string_list[1] == '/index.html':
            name_file = string_list[1][1:]
         if string_list[1] == '/files.html':
            name_file = string_list[1][1:]
         if string_list[1] == '/info.html':
            name_file = string_list[1][1:]
         print(name_file)
         file = open(name_file,'rb')
         response = file.read()
         file.close()
         header = 'HTTP/1.1 200 OK\n'
         mimetype = 'text/html'
         header += 'Content-Type: '+str(mimetype)+'\n\n'
      if method == 'POST':
         check = False
         for sl in string_list:
            check = check or 'uname=admin&psw=admin' in sl
         if check:
            header = 'HTTP/1.1 301 Moved Permanently\nLocation: /info.html\nConnection: Keep-Alive\nContent-length: 0\n\n'
   except Exception as e:
      header = 'HTTP/1.1 404 Not Found\n\n'
      response = '<html><body><center><h3>Error 404: File not found</h3><p>Python HTTP Server</p></center></body></html>'.encode('utf-8')
   final_response = header.encode('utf-8')
   final_response += response
   connection.send(final_response)
   connection.close()
