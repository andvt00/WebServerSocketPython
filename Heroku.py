import os
import socket
import threading
import time
import math
import sys
import mimetypes
from urllib.parse import unquote

HOST = '0.0.0.0'
PORT = int(os.environ['PORT'])
sr = 'ServerRoot'
nameApp = 'socket-hcmus'
accessInfo = False
def response_ok(body=b"This is a minimal response", mimetype=b"text/plain", length=0, name='Noname'):
    return b"\r\n".join([
        b"HTTP/1.1 200 OK",
        b"accept-ranges: bytes",
        b"Content-Disposition: inline; filename=" + name,
        #b"content-length: " + str(length).encode('utf-8'),
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
    return 'http://' + nameApp + '.herokuapp.com/'

def getFolderSize(folder):
    total_size = os.path.getsize(folder)
    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getFolderSize(itempath)
    return total_size

def getSize(path):
    if os.path.isdir(path):
        return getFolderSize(path)
    return(os.path.getsize(path))
    
#Path_directory Ex: /files/
def directory_files(path_directory):
    name_directory = path_directory[1:]  # files/.../
    # Bien sort
    sortable, next_sort = False, 'O=D'
    if "Sort=1" in path_directory:
        sortable = True
        name_directory = path_directory[1:-16]
    files = os.listdir(name_directory)
    # Create list of tuple to sort
    f_val = [(f, os.path.getmtime(name_directory+'/' + f), getSize(name_directory + '/'+f), f) for f in files]
    pos = name_directory.rfind('/')
    parent_directory = ''
    if pos != -1:
        parent_directory = name_directory[:name_directory.rfind('/')]
    if sortable:
        require = path_directory[(len(path_directory)-7):].split(';') # C=*;O=*
        type_sort, trend_sort = require[0], require[1]
        if trend_sort == next_sort:
            next_sort = 'O:I'
        list_type = ['N', 'M', 'S', 'D']
        for i in range(len(list_type)):
            if list_type[i] == type_sort[2]:
                if trend_sort[2] == 'D':
                    f_val.sort(key = lambda x:x[i], reverse = True)
                else:
                    f_val.sort(key = lambda x:x[i])
    result = '<html><head><meta charset="utf-8"/><title>' + name_directory + '</title></head><body><h2>' + name_directory +'</h2><table><tbody><tr><th valign="top"></th>'
    result += '<th><a href="' + getDomain() + name_directory + '/?Sort=1;C=N;' + next_sort + '">Name</a></th>'
    result += '<th><a href="' + getDomain() + name_directory + '/?Sort=1;C=M;' + next_sort + '">Last modified</a></th>'
    result += '<th><a href="' + getDomain() + name_directory + '/?Sort=1;C=S;' + next_sort + '">Size</a></th>'
    result += '<th><a href="' + getDomain() + name_directory + '/?Sort=1;C=D;' + next_sort + '">Description</a></th></tr>'
    result += '<tr><th colspan="5"><hr></th></tr><tr><td valign="top"><img src="' + getDomain() + 'back.gif" alt="[PARENTDIR]"></td>'
    result += '<td><a href="' + getDomain() + parent_directory + '">Parent Directory</a></td><td>&nbsp;</td><td align="right">   </td><td>&nbsp;</td></tr>'
    
    for i in range(len(f_val)):
      path_file = name_directory + '/' + f_val[i][0]  # files/a.txt
      icon = 'file.gif'
      if (os.path.isdir(path_file)):
      	icon = 'folder.gif'
      times = time.strftime('%Y-%m-%d %H:%M', time.gmtime(f_val[i][1]))
      sizes = convert_size(f_val[i][2])
      result += '<tr><td valign="top"><img src="' + getDomain() + icon + '" alt="[   ]"></td><td><a href="' + getDomain() + path_file + '">' + f_val[i][0] + '</a>  </td><td align="right">'
      result += str(times) + '</td><td align="right">'
      result += str(sizes) + '</td><td>&nbsp;</td></tr>'
    result += '<tr><th colspan="5"><hr></th></tr></tbody></table><iframe id="nr-ext-rsicon" style="position: absolute; display: none; width: 50px; height: 50px; z-index: 2147483647; border-style: none; background: transparent"></iframe></form></body></html>'
    return result

def download_file(path_file): # path_file: /files/a.txt or /files/abc
    path_file = unquote(path_file)[1:]
    print(path_file)
    if os.path.isdir(path_file) or "Sort=1" in path_file:
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

def openSR(url, conn): #Send file on ServerRoot folder
    response = ("HTTP/1.1 200 OK\r\n\r\n").encode('utf-8')
    f = open(sr + url,"rb")
    response_body = f.read()         
    f.close()
    response += response_body
    conn.sendall(response)
    conn.close()

def reDirect(url, conn):
    response_header = 'HTTP/1.1 301 Permanently\r\nLocation: ' + getDomain() + url + '\r\nContent-length: 0\r\nConnection: close\r\n\r\n'
    conn.sendall(response_header.encode('utf-8'))
    conn.close()
    
def ConnHandler(conn, addr):
    data = conn.recv(4096)
    cl = int(parse_header(data.decode('utf-8'))['Content-Length'])
    if (data.find(b'\r\n\r\n')+4==len(data)) and cl > 0:
        data+=conn.recv(int(parse_header(data.decode('utf-8'))['Content-Length']))
    if not data:
        conn.close()
        return
    print("Recieved Request:\n")
    print(data)
    parsed_fields = {}
    parsed_fields = parse_header(data.decode('utf-8'))
    print(parsed_fields)
    req_file = ''
    global accessInfo
    if parsed_fields['Method'] == 'POST':
        if parsed_fields['Data'] == 'uname=admin&psw=admin':
            accessInfo = True
            reDirect('info.html', conn)
        else:
            accessInfo = False
            reDirect('404.html', conn)
        return
    if parsed_fields['Method'] == 'GET':
        if len(parsed_fields['Path'])==1:
            reDirect('index.html', conn)
            return
        elif parsed_fields['Path'] == '/info.html':
            if not accessInfo:
                reDirect('404.html', conn)
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
        reDirect('404.html',conn)
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
except socket.error as e:
    print("Error while binding host:")
    print(e)
    sys.exit()
print("Socket bind successful")
print('Serving on http://'+HOST+':'+str(PORT))
s.listen(10)
print("Socket is now listening, ready for connections")
while True:
   conn,addr = s.accept()
   print("Connected to: " + str(addr[0]) + ":" + str(addr[1]) + "\n")
   ConnThread = threading.Thread(target=ConnHandler, args=(conn, addr))
   ConnThread.start()
conn.close()
s.close()
