import sys
import os.path
import socket



def send_chunk():
    size = os.path.getsize(sys.argv[1])
    bs = int(sys.argv[2])

    tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_client.connect(('127.0.0.1', 8000))
    
    tcp_client.sendall(b'POST /chunk http/1.1\r\nHost:127.0.0.1:8000\r\nAccept:*/*\r\nConnection:close\r\nTransfer-Encoding:chunked\r\nUser-Agent:Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36\r\n\r\n')
    
    with open(sys.argv[1], 'rb') as f:
        print('send file size', size)
        while size > 0:
            if size > bs:
                tcp_client.sendall("%X\r\n" % bs)
                tcp_client.sendall(f.read(bs) + b'\r\n')
                size -= bs
            else:
                tcp_client.sendall("%X\r\n" % size)
                tcp_client.sendall(f.read(size) + b'\r\n')
                break
            
    tcp_client.sendall(b'0\r\n\r\n')
    print('recv response', tcp_client.recv(8192))
    tcp_client.close()


if __name__ == '__main__':
    send_chunk()
