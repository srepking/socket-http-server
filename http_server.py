import socket
import sys
import traceback
import logging
import os
import mimetypes

mimetypes.add_type("image/jpeg", '.jpeg')
mimetypes.add_type("image/jpeg", '.jpg')

logging.basicConfig(level=logging.INFO)

def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
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
        b"Content-Type: " + mimetype,
        b"",
        body,
    ])

def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""

    return b"\r\n".join([
        b"HTTP/1.1 405 Method Not Allowed",
        b"",
        b"You can't do that on this server!"
    ])


def response_not_found():
    """Returns a 404 Not Found response"""

    return b"HTTP/1.1 404 Not Found"


def parse_request(request):
    """
    Given the content of an HTTP request, returns the path of that request.

    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.
    """

    method, path, version = request.split("\r\n")[0].split(" ")

    if method != "GET":
        raise NotImplementedError
    return path


def response_path(path):
    """
    This method should return appropriate content and a mime type.

    If the requested path is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the path is a file, it should return the contents of that file
    and its correct mimetype.

    If the path does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        response_path('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        response_path('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        response_path('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        response_path('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """


    head = os.path.split(path)[0]
    tail = os.path.split(path)[1]
    logging.debug("the head is: {}".format(head))
    logging.debug("the tail is: {}".format(tail))
    file_path = os.path.join('webroot'+head, tail)
    logging.debug("the file_path is: {}".format(file_path))
    if os.path.isfile(file_path) is True:
        logging.debug("File is found")
        with open(file_path, "rb") as f:
            content = f.read()
            tail = os.path.split(path)[1]
            print('File_name: {}'.format(tail))
            mime_type = mimetypes.guess_type(tail)[0].encode()
            print(mime_type)
            return content, mime_type

    elif os.path.isdir(file_path):
        logging.debug("Directory is found")
        mime_type = b"text/plain"
        file_list = os.listdir(file_path) #list of files
        file_string = ','.join(file_list) #string of files
        content = file_string.encode() #encoded string
        logging.debug("Contents in Directory: {}".format(content))
        return content, mime_type

    else:
        logging.debug("Nothing is found")
        raise NameError
    

def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)

                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')

                    if '\r\n\r\n' in request:
                        break

                print("Request received:\n{}\n\n".format(request))

                try:
                    # Use parse_request to retrieve the path from the request.
                    path = parse_request(request)
                    # Use response_path to retrieve the content and the mimetype,
                    # based on the request path.
                    content, mime_type = response_path(path)
                    response = response_ok(
                        body=content,
                        mimetype=mime_type)

                # If parse_request raised a NotImplementedError, then let
                # response be a method_not_allowed response.
                except NotImplementedError:
                    response = response_method_not_allowed()

                # If response_path raised a NameError, then let response
                # be a not_found response. Else,use the content and
                # mimetype from response_path to build a response_ok.
                except NameError:
                    response = response_not_found()

                conn.sendall(response)
            except:
                traceback.print_exc()
            finally:
                conn.close() 

    except KeyboardInterrupt:
        sock.close()
        return
    except:
        traceback.print_exc()


if __name__ == '__main__':
    server()
    sys.exit(0)


