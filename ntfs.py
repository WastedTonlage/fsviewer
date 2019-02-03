import pdb
from operator import itemgetter
import time

def hexListToNum (hex):
	value = 0
	for i, byte in enumerate(hex):
		value += byte * (256**i)
	return value

def hexStrip(hex):
	lastFound = 0
	for i, byte in enumerate(hex):
		if byte != 0:
			lastFound = i+1
	return hex[:lastFound]


def parseNTFS(disk):
	class file:
		name = ""
		segments = []

		def __init__ (self):
			segments = []


	disk = open("\\\\.\\" + disk + ':', "rb+")

	#Check filesystem type
	if (not disk.read(10)[3:7].decode() == "NTFS"):
		#print("file system is not NTFS")
		sys.exit(0)

	#Read sector length in bytes
	disk.seek(0x0B)
	seclength = hexListToNum(disk.read(2))

	#Read cluster length in sectors
	clusterlength = hexListToNum(disk.read(1))

	#Read MFT location
	disk.seek(0x30)
	mftloc = hexListToNum(disk.read(8))

	#navigate to mft
	disk.seek(mftloc * clusterlength * seclength)

	files = []

	empty = 0
	while True:
		##print("starting new record")
		fileInstance = file()
		fileInstance.segments = []
		record = disk.read(1024)
		sig = record[:4]
		if (sig == b'BAAD'):
			continue;
		elif (not sig == b'FILE'):
			empty += 1
			if empty > 10:
				break;
			continue;

		#Parse attributes
		nextAtt = hexListToNum(record[0x14:0x16])
		currentAtt = 0
		while True:
			##print("starting new attribute")
			attType = record[nextAtt:nextAtt+4]
			currentAtt = nextAtt
			nextAtt = currentAtt + hexListToNum(record[currentAtt+4:currentAtt+8])
			
			isResident = True
			if (record[currentAtt + 8] == 1):
				isResident = False
			
			namelength = record[currentAtt + 9]

			headerlength = 2 * namelength
			if (isResident):
				headerlength += 0x18
			else:
				headerlength += 0x40

			if (attType == b'\xff\xff\xff\xff'):
				break;
			if (attType == b'\x30\x00\x00\x00'):
				#print("-----------------------------------------------------------")
				#print("name:" + hexStrip(record[currentAtt+0x5A:nextAtt:2]).decode())
				fileInstance.name = hexStrip(record[currentAtt+0x5A:nextAtt:2]).decode()
			elif (attType == b'\x80\x00\x00\x00'):
				#print("data:" + str(record[currentAtt+headerlength:nextAtt]))
				#print("Resident: " + str(isResident))
				if (not isResident):
					runNum = 0
					runs = hexStrip(record[currentAtt+headerlength:nextAtt])
					nextIndex = 0
					if (runs != b''):
						while True:
							##print("Run: " + str(runNum))
							runNum += 1
							offsetBytes = int((runs[nextIndex] & 0xF0) / 0x10)
							lengthBytes = runs[nextIndex] & 0x0F
							##print("Offset: " + str(hexListToNum(runs[nextIndex + lengthBytes + 1: nextIndex + lengthBytes + offsetBytes + 1])))
							##print("Length: " + str(hexListToNum(runs[nextIndex + 1: nextIndex + lengthBytes + 1])))
							##print({"length": hexListToNum(runs[nextIndex + 1: nextIndex + lengthBytes + 1]), "offset": hexListToNum(runs[nextIndex + lengthBytes + 1: nextIndex + lengthBytes + offsetBytes + 1])})
							fileInstance.segments.append({"length": hexListToNum(runs[nextIndex + 1: nextIndex + lengthBytes + 1]), "offset": hexListToNum(runs[nextIndex + lengthBytes + 1: nextIndex + lengthBytes + offsetBytes + 1])})
							nextIndex = nextIndex + lengthBytes + offsetBytes + 1
							if nextIndex >= len(runs):
								break;
		
		files.append(fileInstance)

	##print(files)
	#pdb.set_trace()
	gruns = []
	for file in files:
		for run in file.segments:
			if (run["offset"] != 0 or file.name == "$Boot"):
				gruns.append({'offset': run["offset"], 'length': run["length"], 'name': file.name})

	gruns = sorted(gruns, key=itemgetter("offset"))

	currentEnd = 0
	segments = []
	for run in gruns:
		if (currentEnd < run["offset"]):
			segments.append({'offset': currentEnd, "length": run["offset"] - currentEnd, "name": "Unallocated Segment"})
		segments.append(run)
		currentEnd = run["offset"] + run["length"]
	return segments