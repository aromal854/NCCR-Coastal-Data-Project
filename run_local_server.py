from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import os

# 1. Setup a fake username and password
authorizer = DummyAuthorizer()

# 2. Point the server specifically to the Server_Room folder
server_directory = os.path.join(os.getcwd(), "Server_Room") 
authorizer.add_user("nccr_admin", "password123", server_directory, perm="elradfmw")

# 3. Setup the handler
handler = FTPHandler
handler.authorizer = authorizer

# 4. Start the server on your local IP (127.0.0.1) on port 2121
address = ("127.0.0.1", 2121)
server = FTPServer(address, handler)

print("🟢 Local FTP Server Running! Waiting for connections from the Dashboard...")
server.serve_forever()