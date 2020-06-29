import os
import socket
import threading
import time
import math
import sys
import mimetypes
from urllib.parse import unquote

HOST = 'localhost'
PORT = 80
sr = 'ServerRoot'
accessInfo = False
def response_ok(body=b"This is a minimal response", mimetype=b"text/plain", length=0, name='Noname'):
    return b"\r\n".join([
        b"HTTP/1.1 200 OK",
        b"accept-ranges: bytes",
        b"Content-Disposition: inline; filename=" + name,
        b"content-length: " + str(length).encode('utf-8'),
        b"Content-Type: " + mimetype,
        b"",
        body,
    ])

def convert_size(size_bytes):
   if size_bytes == 0:
      return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 1)
   return "%s%s" % (s, size_name[i])

def getDomain():
    return 'http://'+HOST+':'+str(PORT)+'/'
#Path_directory Ex: /files/
def directory_files(path_directory):
    name_directory = path_directory[1:]  # files/.../
    files = os.listdir(name_directory)
    parent_directory = name_directory[:name_directory.rfind('/')]
    result = '<html><head><meta charset="utf-8"/><title>' + name_directory + '</title></head><body><h2>' + name_directory +'</h2><table><tbody><tr><th valign="top"></th>'
    result += '<th><a href="' + name_directory + '">Name</a></th>'
    result += '<th><a href="' + name_directory + '">Last modified</a></th>'
    result += '<th><a href="' + name_directory + '">Size</a></th>'
    result += '<th><a href="' + name_directory + '">Description</a></th></tr>'
    result += '<tr><th colspan="5"><hr></th></tr><tr><td valign="top"><img src="' + getDomain() + 'back.gif" alt="[PARENTDIR]"></td>'
    result += '<td><a href="' + getDomain() + parent_directory + '"' + 'target=_top' + '>Parent Directory</a></td><td>&nbsp;</td><td align="right">  - </td><td>&nbsp;</td></tr>'
    for f in files:
      path_file = name_directory + '/' + f    # files/a.txt
      print(path_file)
      times = time.strftime('%Y-%m-%d %H:%M', time.gmtime(os.path.getmtime(name_directory + '/' + f)))
      sizes = convert_size(os.path.getsize(name_directory + '/' + f))
      result += '<tr><td valign="top"><img src="' + getDomain() + 'compressed.gif" alt="[   ]"></td><td><a href="' + getDomain() + path_file + '">' + f + '</a>  </td><td align="right">'
      result += str(times) + '</td><td align="right">'
      result += str(sizes) + '</td><td>&nbsp;</td></tr>'
    result += '<tr><th colspan="5"><hr></th></tr></tbody></table><iframe id="nr-ext-rsicon" style="position: absolute; display: none; width: 50px; height: 50px; z-index: 2147483647; border-style: none; background: transparent"></iframe></form></body></html>'
    return result

def download_file(path_file): # path_file: /files/a.txt or /files/abc
    path_file = unquote(path_file)[1:]
    print(path_file)
    if os.path.isdir(path_file):
        content = directory_files('/' + path_file)
        mime_type = 'text/plain'
        return content.encode('utf-8'), mime_type.encode('utf-8'), path_file, 0, 1
    if os.path.isfile(path_file):
        if "text" not in mimetypes.guess_type(path_file)[0]:
            with open(path_file, 'rb') as fd:
                content = fd.read()
            fd.close()
            mime_type = mimetypes.guess_type(path_file)[0]
            length = os.path.getsize(path_file)
            val = path_file.split('/')
            name_file = '' + val[-1]
            return content, mime_type.encode('utf8'), name_file.encode('utf-8'), length, 0
        else:
            with open(path_file, 'r') as fd:
                content = fd.readlines()
            fd.close()
            content1 = ' '.join(content)
            mime_type = mimetypes.guess_type(path_file)[0]
            length = os.path.getsize(path_file)
            val = path_file.split('/')
            name_file = '' + val[-1]
            return content1.encode('utf-8'), mime_type.encode('utf8'), name_file.encode('utf-8'), length, 0
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
    if not data:
        conn.close()
        return
    print("Recieved Request:\n")
    print(data)
    parsed_fields = {}
    parsed_fields = parse_header(data)
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
          sock = ("HTTP/1.1 200 OK\r\n\r\n").encode('utf-8')
          sock += directory_files('/files').encode('utf-8')
          conn.sendall(sock)
          conn.close()
          return
        elif parsed_fields['Path'].find("/files") == 0: # Path: /files/a.txt ro /files/abc
          path_file = (parsed_fields['Path'])
          try:
            body, mimetype, name_file, leng, isdir = download_file(path_file)
          except NameError:
            conn.close()
            return
          else: 
            if isdir:
              sock = ("HTTP/1.1 200 OK\r\n\r\n").encode('utf-8')
              sock += body
            else:
              sock = response_ok(body=body, mimetype=mimetype, length=leng, name=name_file)
          conn.sendall(sock)
          conn.close()
          return
        req_file = sr + parsed_fields['Path']
    if (os.path.isfile(req_file)):
        response_header = ("HTTP/1.1 200 OK\r\n\r\n")
    else:
        reDirect('/404.html',conn)
        print('reDirect')
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
