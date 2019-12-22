# NVDA addon for drag an drop objects
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.
#Copyright (C) 2016-2019 Javi Dominguez <fjavids@gmail.com>

import globalPluginHandler
import addonHandler
import appModuleHandler
import scriptHandler
import appModules
import api
import ui
import controlTypes
import speech
import winUser
from time import sleep
from threading import Timer
import tones
import globalVars
import mouseHandler

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
		if scriptHandler.getLastScriptRepeatCount() == 2:
			ui.message (_("Window in %d, %d. Width %d, height %d") % api.getForegroundObject().location)
			return
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
		x, y = winUser.getCursorPos()
		ui.message(_("Mouse cursor is on %d, %d above ") % (x, y))
		mouse = api.getDesktopObject().objectFromPoint(x,y)
		speech.speakObject(mouse, reason=controlTypes.REASON_MOUSE)
		if fg.appModule.appModuleName != mouse.appModule.appModuleName:
			ui.message(_("(outside of the active window)"))
		if winUser.getKeyState(winUser.VK_LBUTTON)&32768:
			ui.message (_("Left button locked"))
		if winUser.getKeyState(winUser.VK_RBUTTON)&32768:
			ui.message (_("Right button locked"))
		ui.message(_("%s cursor") % mouseHandler.curMouseShape)
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
			x = obj.location[0]+obj.location[2]//2
			y = obj.location[1]+obj.location[3]//2
			# If the marked position points to a different object, mark the top corner.
			# This happens with large objects, such as windows or panels, that contain other objects.
			# Note: Drag and drop from here does not move the object but that it will be resized
			if api.getDesktopObject().objectFromPoint(x,y) != self.objectToDrag:
				x = obj.location[0]+1
				y = obj.location[1]+1
			self.dragFromPosition = (x, y)
			ui.message(_("%s selected to drag") % controlTypes.roleLabels[obj.role])
	# Translators: Message presented in input help mode.
	script_selectObjectToDrag.__doc__ = _("Marks the object in navigator to be dragged.")

	def script_dragAndDrop(self, gesture):
		if not self.objectToDrag:
			self.error(_("Nothing is selected for drag"))
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
		x = obj.location[0]+obj.location[2]//2
		y = obj.location[1]+obj.location[3]//2
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
		x = obj.location[0]+obj.location[2]//2
		y = obj.location[1]-1
		self.dragAndDrop(x, y)

	def script_dropBelow(self, gesture):
		obj = api.getNavigatorObject()
		if obj.location == (0, 0, 0, 0) or controlTypes.STATE_INVISIBLE in obj.states or controlTypes.STATE_OFFSCREEN in obj.states \
		or api.getDesktopObject().objectFromPoint(obj.location[0]+1, obj.location[1]+1) != obj:
			self.error(_("Can't drop here"))
			return
		x = obj.location[0]+obj.location[2]//2
		y = obj.location[1]+obj.location[3]+1
		self.dragAndDrop(x, y)

	def script_dropRight(self, gesture):
		obj = api.getNavigatorObject()
		if obj.location == (0, 0, 0, 0) or controlTypes.STATE_INVISIBLE in obj.states or controlTypes.STATE_OFFSCREEN in obj.states \
		or api.getDesktopObject().objectFromPoint(obj.location[0]+1, obj.location[1]+1) != obj:
			self.error(_("Can't drop here"))
			return
		x = obj.location[0]+obj.location[2]+1
		y = obj.location[1]+obj.location[3]//2
		self.dragAndDrop(x, y)

	def script_dropLeft(self, gesture):
		obj = api.getNavigatorObject()
		if obj.location == (0, 0, 0, 0) or controlTypes.STATE_INVISIBLE in obj.states or controlTypes.STATE_OFFSCREEN in obj.states \
		or api.getDesktopObject().objectFromPoint(obj.location[0]+1, obj.location[1]+1) != obj:
			self.error(_("Can't drop here"))
			return
		x = obj.location[0]-1
		y = obj.location[1]+obj.location[3]//2
		self.dragAndDrop(x, y)

	def script_dropInMousePosition(self, gesture):
		x, y = winUser.getCursorPos()
		self.dragAndDrop(x, y)

	def dragAndDrop(self, drop_x, drop_y):
		self.kbFinish()
		x, y = self.dragFromPosition
		if api.getDesktopObject().objectFromPoint(x,y) != self.objectToDrag:
			self.error(_("Cannot find the object marked."))
			return
		winUser.setCursorPos(x, y)
		if winUser.getKeyState(winUser.VK_LBUTTON)&32768:
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN,0,1,None,None)
		ui.message(_("click in %d, %d") % (winUser.getCursorPos()[0], winUser.getCursorPos()[1]))
		sleep(1.0)
		ui.message(_("dragging"))
		sleep(0.5)
		winUser.setCursorPos(drop_x, drop_y)
		obj = api.getDesktopObject().objectFromPoint(drop_x,drop_y) 
		ui.message(_("moved to %d, %d") % (winUser.getCursorPos()[0], winUser.getCursorPos()[1]))
		sleep(0.5)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP,0,0,None,None)
		sleep(1.0)
		x, y = self.dragFromPosition
		if api.getDesktopObject().objectFromPoint(x,y) != self.objectToDrag:
			ui.message(_("dropped on "))
			speech.speakObject(obj, reason=controlTypes.REASON_MOUSE)
		else:
			tones.beep(500, 100)
		self.objectToDrag = None

	def script_changeWindow(self, gesture):
		size = ""
		horizontal = ""
		vertical = ""
		gesture.send()
		X, Y, W, H = api.getDesktopObject().location
		desk = W*H
		x, y, w, h = api.getForegroundObject().location
		win = w*h
		rSize = win*100/desk
		# size of window
		if rSize > 90:
			size = _("maximized")
		elif rSize > 75:
			size = _("large")
		elif rSize >35:
			size = _("medium")
		elif rSize > 10:
			size = _("small")
		else:
			size = _("very small")
		# window position
		if x > (W-w-x)*0.95 and x < (W-w-x)*1.05 and y > (H-h-y)*0.95 and y < (H-h-y)*1.05:
			vertical = _("centered")
		else:
			# vertical position
			if h < H*0.75 and y < H/2+1:
				vertical = _("up")
			if y > H*0.25 and y+h > H*0.75:
				vertical = _("down")
			# horizontal position
			if w < W*0.66 and x < W/2+1:
				horizontal = _("on left")
			if x > W*0.25 and x+w >= W*0.75:
				horizontal = _("on right")
		ui.message(_("%s window, %s %s") % (size, vertical, horizontal))

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
	"kb(laptop):NVDA+Shift+,": "dragAndDrop",
	"kb:Windows+leftArrow": "changeWindow",
	"kb:Windows+rightArrow": "changeWindow",
	"kb:Windows+upArrow": "changeWindow",
	"kb:Windows+downArrow": "changeWindow"
	} 

	__ddGestures = {
	"kb:space": "dropInto",
	"kb:Enter": "dropInMousePosition",
	"kb:downArrow": "dropBelow",
	"kb:upArrow": "dropAbove",
	"kb:rightArrow": "dropRight",
	"kb:leftArrow": "dropLeft"
	}
	