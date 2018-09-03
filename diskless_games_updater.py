import logging
from subprocess import Popen
from win32 import win32gui
from win32 import win32process
from win32con import SW_MINIMIZE
from time import sleep
from psutil import process_iter
from sys import stdout
from os import system

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

launchers = [
{'exe': "DRIVE:/PATH/TO/Battle.net/Battle.net Launcher.exe", 'kill': "Battle.net.exe", 'hide': "Blizzard Battle.net", 'hide_wait': 20, 'timeout': 7200, 'rounds': 2, 'copy': ["ROBOCOPY %programdata%\Battle.net \"DRIVE:\PATH\TO\Blizzard Data\Battle.net\" /MIR /FFT"]},
{'exe': "DRIVE:/PATH/TO/Epic Games/Launcher/Engine/Binaries/Win64/EpicGamesLauncher.exe", 'kill': "EpicGamesLauncher.exe", 'hide': "Epic Games", 'hide_wait': 20, 'timeout': 7200, 'rounds': 2, 'copy': ["ROBOCOPY %userprofile%\AppData\Local\EpicGamesLauncher \"DRIVE:\PATH\TO\Epic Data\EpicGamesLauncher\" /MIR /FFT", "ROBOCOPY %programdata%\Epic \"DRIVE:\PATH\TO\Epic Data\Epic\" /MIR /FFT"]},
]

def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor

def minimize_window(pid, pid_text=None):
	def callback(hwnd, hwnds):
		if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
			if pid_text is not None:
				text = win32gui.GetWindowText(hwnd)
				if text.find(pid_text) >= 0:
					hwnds.append(hwnd)
			else:
				_, found_pid = win32process.GetWindowThreadProcessId(hwnd)
				if found_pid == pid:
					hwnds.append(hwnd)
		return True

	hwnds = []
	win32gui.EnumWindows(callback, hwnds)
	if len(hwnds) > 0:
		win32gui.ShowWindow(hwnds[0], SW_MINIMIZE)
		return True
	else:
		return False

def kill_by_name(name):
	killed = False
	for proc in process_iter():
		if proc.name() == name:
			proc.kill()
			killed = True
	return killed

for launcher in launchers:
	for round in range(launcher['rounds']):
		logger.info("Launching " + launcher['exe'])
		launcher_proc = Popen([launcher['exe']])

		if 'hide' in launcher:
			logger.info("Waiting {} seconds then minimizing...".format(launcher['hide_wait']))

			tries = 0
			while 1:
				sleep(launcher['hide_wait'])

				if minimize_window(0, launcher['hide']):
					break

				tries += 1
				if tries == 3:
					kill_by_name(launcher['kill'])
					logger.error("Failed to minimize launcher, skipping")
					break
			if tries == 3:
				break

		logger.info("Waiting {} seconds before killing launcher".format(launcher['timeout']))
		tmp = launcher['timeout']
		spinner = spinning_cursor()
		while tmp != 0:
			if 'hide' in launcher and (tmp % 60) == 0:
				minimize_window(0, launcher['hide'])

			stdout.write(next(spinner))
			stdout.flush()
			sleep(1)
			stdout.write('\b')
			tmp -= 1

		if kill_by_name(launcher['kill']):
			logger.info("Killed launcher...")
		else:
			logger.error("Failed to kill launcher") #todo: what now?
		
		if round == 1 and 'copy' in launcher:
			for cmd in launcher['copy']:
				system(cmd)

logger.info("All launched... Quitting")

