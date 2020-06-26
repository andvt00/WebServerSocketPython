import os
import socket
import threading
import time
import math
import sys
import mimetypes
HOST = '0.0.0.0'
PORT = 8080
sr = 'ServerRoot'
accessInfo = False
def response_ok(body=b"This is a minimal response", mimetype=b"text/plain", length=0):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->
        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """

    return b"\r\n".join([
        b"HTTP/1.1 200 OK",
        b"accept-ranges: bytes",
        b"Content-Disposition: inline; filename=picture.png",
        b"content-length: " + str(length).encode('utf-8'),
        b"Content-Type: " + mimetype,
        b"",
        body,
    ])

def response_not_found():
    """Returns a 404 Not Found response"""

    return b"\r\n".join([
        b"HTTP/1.1 404 Not Found",
        b"",
        b"The server can not find the requested URL",
    ])

def convert_size(size_bytes):
   if size_bytes == 0:
      return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 1)
   return "%s%s" % (s, size_name[i])

def directory_files(path_directory):
    files = os.listdir(path_directory)
    result = '<html><head><meta charset="utf-8"/><title>' + path_directory + '</title></head><body><h2>' + path_directory +'</h2><table><tbody><tr><th valign="top"></th>'
    result += '<th><a href="' + path_directory + '?C=N;O=D">Name</a></th>'
    result += '<th><a href="' + path_directory + '?C=M;O=A">Last modified</a></th>'
    result += '<th><a href="' + path_directory + '?C=S;O=A">Size</a></th>'
    result += '<th><a href="' + path_directory + '?C=D;O=A">Description</a></th></tr>'
    result += '<tr><th colspan="5"><hr></th></tr><tr><td valign="top"><img src="./ServerRoot/back.gif" alt="[PARENTDIR]"></td>'
    result += '<td><a href="' + path_directory + '">Parent Directory</a></td><td>&nbsp;</td><td align="right">  - </td><td>&nbsp;</td></tr>'
    for f in files:
      path_file = path_directory + f
      times = time.strftime('%Y-%m-%d %H:%M', time.gmtime(os.path.getmtime(path_file)))
      sizes = convert_size(os.path.getsize(path_file))
      result += '<tr><td valign="top"><img src="./ServerRoot/compressed.gif" alt="[   ]"></td><td><a href="' + path_file + '">' + f + '</a>  </td><td align="right">'
      result += str(times) + '</td><td align="right">'
      result += str(sizes) + '</td><td>&nbsp;</td></tr>'
    result += '<tr><th colspan="5"><hr></th></tr></tbody></table><iframe id="nr-ext-rsicon" style="position: absolute; display: none; width: 50px; height: 50px; z-index: 2147483647; border-style: none; background: transparent"></iframe></form></body></html>'
    return result

def download_file(path_file):
  path_file = '.' + path_file
  print('Path:' + path_file)
  # if file requested is a directory list the files in the directory
  # and append a '/' to any files listed that are directories
  if os.path.isdir(os.path.join(path_file)):
    content = directory_files(path_file + '/')
    mime_type = 'text/plain'
    return content.encode('utf-8'), mime_type.encode('utf-8'), 0, 1

  # if file requested is a file list the contents of the file
  if os.path.isfile(path_file):
    print('Hello')
    print(mimetypes.guess_type(path_file)[0])
    if "text" not in mimetypes.guess_type(path_file)[0]:  
      #print('file_path = ', file_path)
      print(path_file)
      with open(path_file, 'rb') as fd:
        content = fd.read()
        fd.close()
        #print(content)
      mime_type = mimetypes.guess_type(path_file)[0]
      print(mime_type)
      length = os.path.getsize(path_file)
      return str(content).encode('utf8'), mime_type.encode('utf8'), length, 0
    else:
      with open(path_file, 'r') as fd:
        content = fd.readlines()
      print("content = ", content)
      content1 = ' '.join(content)
      mime_type = mimetypes.guess_type(path_file)[0]
      length = os.path.getsize(path_file)
      return content1.encode('utf8'), mime_type.encode('utf8'), length, 0
    # If file can not be found
  else:
    raise NameError
def parse_header(data):
    h_lines = data.split('\r\n')
    h_words = h_lines[0].split(' ')
    d_words = {}
    l = [h_lines.index(i) for i in h_lines if 'Cookie' in i]
    if (len(l) != 0):
        cookie_value = h_lines[l[0]].split(' ')[1].split('=')[1]
        d_words['Cookie'] = cookie_value
    else:
        d_words['Cookie'] = "DELETED"
    l = [h_lines.index(i) for i in h_lines if 'Content-Length' in i]
    if (len(l) != 0):
        c_length = h_lines[l[0]].split(' ')[1]
        d_words['Content-Length'] = c_length
    else:
        d_words['Content-Length'] = "0"
    d_words['Method'] = h_words[0]
    d_words['Path'] = h_words[1]
    d_words['Version'] = h_words[2][5:8]
    h_lines_len = len(h_lines)
    d_words['Data'] = h_lines[h_lines_len-1]
    if(d_words['Data'].split('&')[0].split('=')[0] == "_method"):
        d_words['Method'] = d_words['Data'].split('&')[0].split('=')[1]
    return d_words
      
def reDirect(url, conn):
    response_header = 'HTTP/1.1 301 Moved Permanently\nLocation: '+ url + '\nConnection: Keep-Alive\nContent-length: 0\n\n'
    conn.sendall(response_header.encode('utf-8'))
    conn.close()

def openSR(url, conn): #Send file on ServerRoot folder
    response = ("HTTP/1.1 200 OK\r\n\r\n").encode('utf-8')
    f = open(sr + url,"rb")
    response_body = f.read()         
    f.close()
    response += response_body
    conn.sendall(response)
    conn.close()
    
def ConnHandler(conn, addr):
    data = conn.recv(1024).decode('utf-8')
    print("Recieved Request:\n")
    print(data)
    if not data:
        conn.close()
        return
    parsed_fields = {}
    parsed_fields = parse_header(data)
    print(parsed_fields)
    req_file = ''
    global accessInfo
    if parsed_fields['Method'] == 'POST':
        if parsed_fields['Path'] == '/info.html' and parsed_fields['Data'] == 'uname=admin&psw=admin':
            accessInfo = True
            reDirect('/info.html', conn)
            return
    if parsed_fields['Method'] == 'GET':
        if len(parsed_fields['Path'])==1:
            reDirect('/index.html', conn)
            return
        elif parsed_fields['Path'] == '/info.html':
            if accessInfo:
                openSR('/info.html', conn)
            else:
                reDirect('/404.html', conn)
            return
        elif parsed_fields['Path'] == '/files.html':
          print('hello')
          sock = ("HTTP/1.1 200 OK\r\n\r\n").encode('utf-8')
          sock += directory_files(sr + '/files/').encode('utf-8')
          conn.sendall(sock)
          conn.close()
          return
        elif parsed_fields['Path'].find("/ServerRoot/files/") == 0:
          path_file = (parsed_fields['Path'])
          try:
            body, mimetype, leng, isdir = download_file(path_file)
            print('Hi')
            # print("body ", body, file=sys.stderr)
          except NameError:
            reDirect('/404.html', conn)
            return
          else:
            if isdir:
              sock = ("HTTP/1.1 200 OK\r\n\r\n").encode('utf-8')
              sock += body
              conn.sendall(sock)
              conn.close()
            else:
              sock = response_ok(body=body, mimetype=mimetype, length=leng)
              #print(sock)
              # conn.sendall('HTTP/1.1 200 OK\r\n'.encode())
              # conn.sendall(("Content-Type: image/jpeg\r\n").encode())
              # conn.sendall("Accept-Ranges: bytes\r\n\r\n".encode())
              # conn.sendall(body)
              conn.sendall(sock)
              conn.close()
          return
        req_file = sr + parsed_fields['Path']
    if (os.path.isfile(req_file)):
        response_header = ("HTTP/1.1 200 OK\r\n\r\n")
    else:
        reDirect('/404.html',conn)
        return
    file_content = open(req_file,"rb")
    response_body = file_content.read()
    sock = response_header.encode('utf-8')
    sock += response_body
    conn.sendall(sock)
    file_content.close()
    conn.close()
#main
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    print('Error while creating socket')
    sys.exit()
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
try:
    s.bind((HOST,PORT))
except socket.error:
    print("Error while binding host")
    sys.exit()
print("Socket bind successful")
print('Serving on http://'+HOST+':'+str(PORT))
s.listen(3)
print("Socket is now listening, ready for connections")
while True:
   conn,addr = s.accept()
   print("Connected to: " + str(addr[0]) + ":" + str(addr[1]) + "\n")
   ConnThread = threading.Thread(target=ConnHandler, args=(conn, addr))
   ConnThread.start()
conn.close()
s.close()
