import sys
import pdb
from operator import itemgetter

def hexListToNum (hex):
	value = 0
	for i, byte in enumerate(hex):
		value += byte * (256**i)
	return value

def parseDir(offset, table, diskLetter, cluster_size, sector_size):
	disk = open("\\\\.\\" + diskLetter + ":", "rb+")
	print(offset)
	disk.seek(offset)
	disk.read(0x20)
	files = []
	while True:
		record = disk.read(0x20)
		print(record)
		#print("------------------------------")
		filestatus = record[0]
		flags = record[0x0B]
		isDir = flags & 0x10 == 0x10
		#print(filestatus)
		if filestatus == 0:
			break;
		elif filestatus == 229 or filestatus == 255 or filestatus == 46: 
			#print("deleted file, skipping")
			continue
		else: 
			filename = ""
			#print(record)
			if filestatus == 5:
				filename = b'\xe5'.decode() + record[1:8].decode()
			else: 
				filename = record[:8].decode()
			extension = ""
			extensionBytes = record[8:11]
			if extensionBytes == b'\xFF\xFF\xFF':
				extension = ""
			else:
				extension = extensionBytes.decode()
			#print(filename + "." + extension)
			next_cluster = hexListToNum(record[0x1a:0x1c])
			#print(next_cluster)
			clusters = []
			while next_cluster != 0:
				clusters.append(next_cluster)
				table_entry = table[next_cluster]
				if (table_entry == b'\xFF\xFF'):
					next_cluster = 0
				else:
					#print(table_entry)
					next_cluster = hexListToNum(table_entry)
			files.append({"name": filename + "." + extension, "clusters": clusters})
			#if isDir and filename != "SYSTEM~1" and filename != "$RECYCLE":
			#	print("running dir")
			#	print(clusters[0])
			#	print(parseDir((clusters[0] * cluster_size + 504) * sector_size, table, diskLetter, cluster_size, sector_size))
			if isDir and filename != "SYSTEM~1" and filename != "$RECYCLE":
				print("running dir")
				print(clusters[0])
				print(cluster_size)
				print(sector_size)
				files += parseDir(((clusters[0] - 1) * cluster_size + 504) * sector_size, table, diskLetter, cluster_size, sector_size)
	print(files)
	return files

def parseFAT(diskLetter):
	disk = open("\\\\.\\" + diskLetter + ':', "rb+")

	#Check filesystem type
	fsName = disk.read(12)[3:11].decode()
	#print(fsName)
	if (not fsName == "MSDOS5.0"):
		print("file system is not FAT")
		sys.exit(0)


	#Bytes per sector
	disk.seek(0x0B)
	sector_size = hexListToNum(disk.read(2))

	#Sectors per cluster
	cluster_size = hexListToNum(disk.read(1))

	#File Table Start in bytes
	table_start = hexListToNum(disk.read(2)) * sector_size

	fats_amount = hexListToNum(disk.read(1))
	disk.seek(0x16)

	#FATs size (in bytes)
	fat_size = hexListToNum(disk.read(2)) * sector_size

	class file:
		length = 0
		offset = 0
		name = ""
		def __init__(length, offset, name):
			self.length = length
			self.offset = offset
			self.name = name

	table = []
	disk.seek(table_start)
	while True:
		record = disk.read(2)
		if (record == b'\x00\x00'):
			break
		else:
			table.append(record)

	files = parseDir(table_start + fats_amount * fat_size, table, diskLetter, cluster_size, sector_size)
	segments = []
	for file in files:
		lastCluster = None
		currentSegment = []
		for i, cluster in enumerate(file["clusters"]):
			if lastCluster != None and (cluster - lastCluster != 1):
				print(currentSegment)
				segments.append({"name": file["name"], "offset": currentSegment[0], "length": len(currentSegment)})
				currentSegment = []
			currentSegment.append(cluster)
			if i + 1 == len(file["clusters"]):
				print(currentSegment)
				segments.append({"name": file["name"], "offset": currentSegment[0], "length": len(currentSegment)})
			lastCluster = cluster

	gruns = sorted(segments, key = itemgetter("offset"))

	segments = []
	currentEnd = 0
	for run in gruns:
		if (currentEnd < run["offset"]):
			segments.append({'offset': currentEnd, "length": run["offset"] - currentEnd, "name": "Unallocated Segment"})
		segments.append(run)
		currentEnd = run["offset"] + run["length"]

	return segments