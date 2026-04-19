import subprocess
import time

p_ftp_server = subprocess.Popen(["python", "backend/honeypots/ftp_server.py", "2121"])
time.sleep(1)

with open('ftp_commands.txt', 'w') as f:
    f.write('open 127.0.0.1 2121\nquit\n')

print("Running Windows ftp.exe")
client = subprocess.run(["ftp", "-s:ftp_commands.txt"], capture_output=True, text=True)
print("FTP OUT:", client.stdout)
print("FTP ERR:", client.stderr)

p_ftp_server.terminate()
