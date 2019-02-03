import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QScrollArea, QMenu
from PyQt5.QtCore import Qt as QtGeneral
from operator import itemgetter
import pdb
from pprint import pprint
import copy
import ntfs
import fat
import time

app = QApplication(sys.argv)

CELL_WIDTH = 20
CELL_HEIGHT = 40

class fileBtn():
	name = ""
	length = 0
	def __init__(self, name, length, sequence):
		self.name = name
		self.length = length
		self.sequence = sequence


def calcLength (name, buttons):
	length = 0
	for button in buttons:
		if (button.fileRep.name == name):
			length += button.fileRep.length
	return length

class hoverPushBtn (QPushButton):
	fileRep = fileBtn("No Name", 0, None)
	
	def __init__(self, parent, fileRep):
		super().__init__(parent)
		self.setMouseTracking(True)
		self.fileRep = fileRep


	def enterEvent(self, event):
		self.setStyleSheet("background-color: lightblue;")
		if self.fileRep.name != "Unallocated Segment":
			for button in windowI.buttons:
				if (button.fileRep.name == self.fileRep.name):
					button.setStyleSheet("background-color: lightblue;")
		else:
			for button in windowI.buttons:
				if button.fileRep.sequence == self.fileRep.sequence:
					button.setStyleSheet("background-color: lightblue;")		
			
	def leaveEvent (self, event):
		self.setStyleSheet("")
		if self.fileRep.name != "Unallocated Segment":
			for button in windowI.buttons:
				if (button.fileRep.name == self.fileRep.name):
					button.setStyleSheet("")
		else:
			for button in windowI.buttons:
				if button.fileRep.sequence == self.fileRep.sequence:
					button.setStyleSheet("")

	def contextMenuEvent(self, event):
		#print("running context menu")
		menu = QMenu(self)
		startAction = menu.addAction("Scroll to Start")
		testAction2 = menu.addAction("Scroll to End")
		action = menu.exec_(self.mapToGlobal(event.pos()))
		if (action == startAction):
			scrollBar = self.parentWidget().parentWidget().parentWidget().verticalScrollBar() 
			scrollBar.setValue((self.fileRep.sequence["offset"] / 60) * CELL_HEIGHT)
		elif (action  == testAction2):
			scrollBar = self.parentWidget().parentWidget().parentWidget().verticalScrollBar() 
			scrollBar.setValue(((self.fileRep.sequence["offset"] + self.fileRep.sequence["length"]) / 60) * CELL_HEIGHT)
		

class window (QWidget):
	def __init__(self, x_size, y_size):
		super().__init__()

		self.x_size = x_size
		self.y_size = y_size
		self.buttons = []
		self.initUI()

	def initUI(self):
		self.setGeometry(100, 100, self.x_size * CELL_WIDTH, self.y_size * CELL_HEIGHT)
		self.setWindowTitle("File allocation viewer")
		
		self.scrollA = QScrollArea(self)
		self.scrollwidget = QWidget()
		self.scrollwidget.resize(self.x_size * CELL_WIDTH, self.y_size * CELL_HEIGHT * 100)
		self.scrollA.resize(self.x_size * CELL_WIDTH, self.y_size * CELL_HEIGHT)
		#self.scrollA.setWidgetResizable(True)
		self.scrollA.setWidget(self.scrollwidget)
		self.render()
		self.show()

	def render(self):
		for button in self.buttons:
			button.setParent(None)
			button.deleteLater()
		self.buttons = []
		dictSegments = {}
		if sys.argv[1] == "NTFS":
			dictSegments = ntfs.parseNTFS(sys.argv[2])
		elif sys.argv[1] == "FAT":
			dictSegments = fat.parseFAT(sys.argv[2])
		else: 
			print("No file system selected")
		#print(dictSegments)
		segments = []
		for segment in dictSegments:
			segments.append(fileBtn(segment["name"], segment["length"], segment))
		currentX = 0
		currentY = 0
		tempSegments = copy.deepcopy(segments)
		#print(tempSegments)
		for i, segment in enumerate(tempSegments):
			#print(segment.name)
			#print("segment.length: " + str(segment.length))
			#print("x_size: " + str(self.x_size))
			#print("current x: " + str(currentX))
			#print("---------------------------------")
			if (segment.length <= self.x_size - currentX):
				#print(segment)
				btn = hoverPushBtn(self.scrollwidget, segment)
				btn.setText(segment.name)
				btn.resize(segment.length * CELL_WIDTH, CELL_HEIGHT)
				btn.move(currentX * CELL_WIDTH, currentY * CELL_HEIGHT)
				self.buttons.append(btn)
				currentX += segment.length
				if (currentX == self.x_size):
					currentY += 1
					currentX = 0
			else:
				tempSegments.insert(i + 1, fileBtn(segment.name, self.x_size - currentX, segment.sequence))
				tempSegments.insert(i + 2, fileBtn(segment.name, segment.length - (self.x_size - currentX), segment.sequence))
			#print(buttons)
		self.scrollwidget.resize(self.x_size * CELL_WIDTH, (currentY + 1) * CELL_HEIGHT)
		for btn in self.buttons:
			#print(btn.height())
			if (btn.fileRep.name == "Unallocated Segment"):
				btn.setToolTip("Unallocated Segment\nThis area has not been allocated yet\nSequence Length: " + str(btn.fileRep.sequence["length"]) + "\nSequence Offset: " + str(btn.fileRep.sequence["offset"]))
			else:	
				btn.setToolTip("Name: " + btn.fileRep.name  + "\nFile Length: " + str(calcLength(btn.fileRep.name, self.buttons)) + "\nSequence Length: " + str(btn.fileRep.sequence["length"])  + "\nSequence Offset: " + str(btn.fileRep.sequence["offset"]))
		#print(self.scrollwidget.children()[0].x())
		#print(self.scrollwidget.children()[0].y())
		#print(self.scrollwidget.children()[0].height())
		#print(self.scrollwidget.children()[0].width())
		#print(len(self.buttons))
		
		#For some reason the buttons are automatically hidden with every rerender except the initial
		# -- Black Magic Dont Remove --
		children = self.findChildren(QWidget)
		for child in children:
			child.show()

	def keyPressEvent(self, event):
		#print(event.key())
		if event.key() == QtGeneral.Key_F5:
			scrollBar = self.scrollA.verticalScrollBar() 
			scrolled = scrollBar.value()
			self.render()
			scrollBar.setValue(scrolled)


windowI = window(60, 20)
app.exec_()