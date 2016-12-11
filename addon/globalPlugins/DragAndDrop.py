# DragAndDrop version 1.0dev (december 2016)
# NVDA addon for drag an drop objects
# Author Javi Dominguez <fjavids@gmail.com>
# License GNU GPL

import globalPluginHandler
import addonHandler
import appModuleHandler
import scriptHandler
import appModules
import api
import ui
import controlTypes
import speech
import win32api
import winUser
from time import sleep
from threading import Timer
import tones
import globalVars

addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	scriptCategory = _("Drag and drop")
	
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		if globalVars.appArgs.secure:
			return
		self.objectToDrag = None
		self.dragFromPosition = None
		self.toggling = False
		self.kbTimeout = None

	def script_mouseCursorInfo(self, gesture):
		if scriptHandler.getLastScriptRepeatCount() == 1:
			if not self.objectToDrag:
				ui.message(_("without selection for drag and drop"))
				return
			speech.speakObject(self.objectToDrag, reason=controlTypes.REASON_MOUSE)
			ui.message(_(" marked for drag and drop"))
			x, y = self.dragFromPosition
			if api.getDesktopObject().objectFromPoint(x,y) != self.objectToDrag:
				ui.message(_("(inaccessible from here)"))
			return
		fg = api.getForegroundObject()
		x, y = win32api.GetCursorPos()
		ui.message(_("Mouse cursor is on %d, %d above ") % (x, y))
		mouse = api.getDesktopObject().objectFromPoint(x,y)
		speech.speakObject(mouse, reason=controlTypes.REASON_MOUSE)
		if fg.appModule.appModuleName != mouse.appModule.appModuleName:
			ui.message(_("(outside of the active window)"))
		if winUser.getKeyState(winUser.VK_LBUTTON)&32768:
			ui.message (_("Left button locked"))
		if winUser.getKeyState(winUser.VK_RBUTTON)&32768:
			ui.message (_("Right button locked"))
	# Translators: Message presented in input help mode.
	script_mouseCursorInfo.__doc__ = _("Reports on the position of the mouse cursor and the object to which it points. Twice, reports on the marked object for drag and drop.")

	def script_selectObjectToDrag (self, gesture):
		if self.objectToDrag:
			ui.message(_("selection cancelled"))
			self.objectToDrag = None
		else:
			obj = api.getNavigatorObject()
			self.objectToDrag = obj
			# Mark the center of the object
			x = obj.location[0]+obj.location[2]/2
			y = obj.location[1]+obj.location[3]/2
			# If the marked position points to a different object, mark the top corner.
			# This happens with large objects, such as windows or panels, that contain other objects.
			if api.getDesktopObject().objectFromPoint(x,y) != self.objectToDrag:
				x = obj.location[0]+1
				y = obj.location[1]+1
			self.dragFromPosition = (x, y)
			ui.message(_("%s selected to drag") % controlTypes.roleLabels[obj.role])
	# Translators: Message presented in input help mode.
	script_selectObjectToDrag.__doc__ = _("Marks the object in navigator to be dragged.")

	def script_dragAndDrop(self, gesture):
		if not self.objectToDrag:
			tones.beep(120, 100)
			ui.message(_("Nothing is selected for drag"))
			return
		if self.toggling:
			tones.beep(100,10)
			return
		ui.message(_("press space or arrows to drag and drop"))
		self.bindGestures(self.__ddGestures)
		self.toggling = True
		def cancel():
			tones.beep(100, 20)
			self.kbFinish()
		self.kbTimeout = Timer(2.0, cancel)
		self.kbTimeout.start()
	# Translators: Message presented in input help mode.
	script_dragAndDrop.__doc__ = _("Drags the selected object. Then press space, arrows or Enter to choose where to drop it. ")

	def script_dropInto(self,gesture):
		obj = api.getNavigatorObject()
		if self.objectToDrag == obj:
			self.error(_("can't move it on himself"))
			return
		if obj.location == (0, 0, 0, 0) or controlTypes.STATE_INVISIBLE in obj.states or controlTypes.STATE_OFFSCREEN in obj.states \
		or api.getDesktopObject().objectFromPoint(obj.location[0]+1, obj.location[1]+1) != obj:
			self.error(_("Can't drop here"))
			return
		x = obj.location[0]+obj.location[2]/2
		y = obj.location[1]+obj.location[3]/2
		if api.getDesktopObject().objectFromPoint(x,y) != obj:
			x = obj.location[0]+1
			y = obj.location[1]+1
		self.dragAndDrop(x, y)

	def script_dropAbove(self, gesture):
		obj = api.getNavigatorObject()
		if obj.location == (0, 0, 0, 0) or controlTypes.STATE_INVISIBLE in obj.states or controlTypes.STATE_OFFSCREEN in obj.states \
		or api.getDesktopObject().objectFromPoint(obj.location[0]+1, obj.location[1]+1) != obj:
			self.error(_("Can't drop here"))
			return
		x = obj.location[0]+obj.location[2]/2
		y = obj.location[1]-1
		self.dragAndDrop(x, y)

	def script_dropBelow(self, gesture):
		obj = api.getNavigatorObject()
		if obj.location == (0, 0, 0, 0) or controlTypes.STATE_INVISIBLE in obj.states or controlTypes.STATE_OFFSCREEN in obj.states \
		or api.getDesktopObject().objectFromPoint(obj.location[0]+1, obj.location[1]+1) != obj:
			self.error(_("Can't drop here"))
			return
		x = obj.location[0]+obj.location[2]/2
		y = obj.location[1]+obj.location[3]+1
		self.dragAndDrop(x, y)

	def script_dropRight(self, gesture):
		obj = api.getNavigatorObject()
		if obj.location == (0, 0, 0, 0) or controlTypes.STATE_INVISIBLE in obj.states or controlTypes.STATE_OFFSCREEN in obj.states \
		or api.getDesktopObject().objectFromPoint(obj.location[0]+1, obj.location[1]+1) != obj:
			self.error(_("Can't drop here"))
			return
		x = obj.location[0]+obj.location[2]+1
		y = obj.location[1]+obj.location[3]/2
		self.dragAndDrop(x, y)

	def script_dropLeft(self, gesture):
		obj = api.getNavigatorObject()
		if obj.location == (0, 0, 0, 0) or controlTypes.STATE_INVISIBLE in obj.states or controlTypes.STATE_OFFSCREEN in obj.states \
		or api.getDesktopObject().objectFromPoint(obj.location[0]+1, obj.location[1]+1) != obj:
			self.error(_("Can't drop here"))
			return
		x = obj.location[0]-1
		y = obj.location[1]+obj.location[3]/2
		self.dragAndDrop(x, y)

	def script_dropInMousePosition(self, gesture):
		x, y = win32api.GetCursorPos()
		self.dragAndDrop(x, y)

	def dragAndDrop(self, drop_x, drop_y):
		self.kbFinish()
		x, y = self.dragFromPosition
		if api.getDesktopObject().objectFromPoint(x,y) != self.objectToDrag:
			self.error(_("Cannot find the object marked."))
			return
		win32api.SetCursorPos((x, y))
		if winUser.getKeyState(winUser.VK_LBUTTON)&32768:
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,1,None,None)
		ui.message(_("click in %d, %d") % win32api.GetCursorPos())
		sleep(1.0)
		ui.message(_("dragging"))
		sleep(0.5)
		win32api.SetCursorPos((drop_x, drop_y))
		obj = api.getDesktopObject().objectFromPoint(drop_x,drop_y) 
		ui.message(_("moved to %d, %d") % win32api.GetCursorPos())
		sleep(0.5)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		sleep(1.0)
		x, y = self.dragFromPosition
		if api.getDesktopObject().objectFromPoint(x,y) != self.objectToDrag:
			ui.message(_("dropped on "))
			speech.speakObject(obj, reason=controlTypes.REASON_MOUSE)
		else:
			self.error(_("can't drop here"))
		self.objectToDrag = None

	def error(self, message):
		tones.beep(120, 100)
		ui.message(message)
		self.kbFinish()

	def kbFinish(self):
		if self.toggling :
			self.toggling = False
			self.clearGestureBindings()
			self.bindGestures(self.__gestures)
		if self.kbTimeout:
			self.kbTimeout.cancel()

	__gestures = {
	"kb(desktop):NVDA+numpad9": "mouseCursorInfo",
	"kb(laptop):NVDA+Control+,": "mouseCursorInfo",
	"kb:NVDA+,": "selectObjectToDrag",
	"kb(desktop):NVDA+.": "dragAndDrop",
	"kb(laptop):NVDA+Shift+,": "dragAndDrop"
	} 

	__ddGestures = {
	"kb:space": "dropInto",
	"kb:Enter": "dropInMousePosition",
	"kb:downArrow": "dropBelow",
	"kb:upArrow": "dropAbove",
	"kb:rightArrow": "dropRight",
	"kb:leftArrow": "dropLeft"
	}
	