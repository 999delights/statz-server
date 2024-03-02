from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

# Define the authorizer for the FTP server
authorizer = DummyAuthorizer()
authorizer.add_user("andrei", "andrei", "C:\\Users\\andre\\AppData\\Local\\Programs\\FTP", perm="elradfmw")

# Define the FTP handler
handler = FTPHandler
handler.authorizer = authorizer

# Create the FTP server
server = FTPServer(("192.168.1.85", 2121), handler)

# Start the FTP server
server.serve_forever()
