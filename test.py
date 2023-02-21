import subprocess


x = subprocess.check_output(['silly'], shell=True).decode()
print(x)