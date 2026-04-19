import subprocess
import time

print("Starting SSH server...")
server_proc = subprocess.Popen(
    ["python", "backend/honeypots/ssh_server.py", "2222"], 
    stdout=subprocess.PIPE, 
    stderr=subprocess.STDOUT, 
    text=True
)
time.sleep(2)

print("Connecting with ssh CLI...")
client_proc = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-p", "2222", "root@127.0.0.1", "ls"], 
    capture_output=True, 
    text=True
)
print("SSH CLI OUT:", client_proc.stdout)
print("SSH CLI ERR:", client_proc.stderr)

server_proc.terminate()
stdout, _ = server_proc.communicate()
print("SERVER OUT:\n", stdout)
