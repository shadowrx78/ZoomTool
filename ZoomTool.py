#! python3
# -*- coding: utf-8 -*-

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
# from tkinter import font
from tkinter.messagebox import showerror
# from tkinter.colorchooser import askcolor
import os, re
import time

import json
import math
from ctypes import windll
from collections import OrderedDict
from PIL import Image, ImageTk, ImageGrab

import sys
from sys import platform
import traceback

from concurrent.futures import ThreadPoolExecutor, wait

import win32api         # package pywin32
import win32con
import win32gui_struct
try:
    import winxpgui as win32gui
except ImportError:
    import win32gui









class SysTrayIcon(object):
    '''TODO'''
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]

    FIRST_ID = 1023

    def __init__(self,
                 icon,
                 hover_text,
                 menu_options,
                 on_quit=None,
                 on_ldouble_click=None,
                 default_menu_index=None,
                 window_class_name=None,
                 quit_text='Quit',):

        self.icon = icon
        self.hover_text = hover_text
        self.on_quit = on_quit
        self.on_ldouble_click = on_ldouble_click

        self.isDestory = False

        self.tm_id_2_menu = dict()
        self.tl_checkbox_id = set()
        self.hmenu = None

        menu_options = menu_options + ((quit_text, None, self.QUIT),)
        self._next_action_id = self.FIRST_ID
        self.menu_actions_by_id = set()
        self.menu_options = self._add_ids_to_menu_options(list(menu_options))
        self.menu_actions_by_id = dict(self.menu_actions_by_id)
        del self._next_action_id


        self.default_menu_index = (default_menu_index or 0)
        self.window_class_name = window_class_name or "SysTrayIconPy"

        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
                       win32con.WM_DESTROY: self.on_destroy,
                       win32con.WM_COMMAND: self.command,
                       win32con.WM_USER+20 : self.notify,}
        # Register the Window class.
        window_class = win32gui.WNDCLASS()
        hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
        window_class.lpszClassName = self.window_class_name
        window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        window_class.hbrBackground = win32con.COLOR_WINDOW
        window_class.lpfnWndProc = message_map # could also specify a wndproc.
        classAtom = win32gui.RegisterClass(window_class)
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(classAtom,
                                          self.window_class_name,
                                          style,
                                          0,
                                          0,
                                          win32con.CW_USEDEFAULT,
                                          win32con.CW_USEDEFAULT,
                                          0,
                                          0,
                                          hinst,
                                          None)
        win32gui.UpdateWindow(self.hwnd)
        self.notify_id = None
        self.refresh_icon()

        # win32gui.PumpMessages()

    def unpack_menu_option(self, menu_option):
        result = dict()
        result['option_text'] = menu_option[0]
        result['option_icon'] = menu_option[1]
        result['option_action'] = menu_option[2]
        result['option_fState'] = menu_option[3] if len(menu_option) >= 4 else None
        return result

    def _add_ids_to_menu_options(self, menu_options):
        result = []
        for menu_option in menu_options:
            # option_text, option_icon, option_action, option_fState = menu_option
            menu_option_unpack = self.unpack_menu_option(menu_option)
            option_action = menu_option_unpack['option_action']
            # print(menu_option_unpack)

            if callable(option_action) or option_action in self.SPECIAL_ACTIONS:
                self.menu_actions_by_id.add((self._next_action_id, option_action))
                # result.append(menu_option + (self._next_action_id,))
                if menu_option_unpack['option_fState'] != None:
                    self.tl_checkbox_id.add(self._next_action_id)
                menu_option_unpack['option_id'] = self._next_action_id
                result.append(menu_option_unpack)
            elif non_string_iterable(option_action):
                # result.append((option_text,
                #                option_icon,
                #                self._add_ids_to_menu_options(option_action),
                #                self._next_action_id))
                menu_option_unpack['option_action'] = self._add_ids_to_menu_options(option_action)
                menu_option_unpack['option_id'] = self._next_action_id
                result.append(menu_option_unpack)
            else:
                print('Unknown item', option_text, option_icon, option_action)
            self._next_action_id += 1
        return result

    def refresh_icon(self):
        # Try and find a custom icon
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(self.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst,
                                       self.icon,
                                       win32con.IMAGE_ICON,
                                       0,
                                       0,
                                       icon_flags)
        else:
            print("Can't find icon file - using default.")
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if self.notify_id: message = win32gui.NIM_MODIFY
        else: message = win32gui.NIM_ADD
        self.notify_id = (self.hwnd,
                          0,
                          win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                          win32con.WM_USER+20,
                          hicon,
                          self.hover_text)
        win32gui.Shell_NotifyIcon(message, self.notify_id)

    def restart(self, hwnd, msg, wparam, lparam):
        self.notify_id = None
        self.refresh_icon()

    def on_destroy(self, hwnd, msg, wparam, lparam):
        if self.on_quit: self.on_quit(self)
        # nid = (self.hwnd, 0)
        # win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        # win32gui.PostQuitMessage(0) # Terminate the app.
        self.destroy()

    def destroy(self):
        if not self or self.isDestory:
            return
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0) # Terminate the app.
        self.isDestory = True

    def notify(self, hwnd, msg, wparam, lparam):
        if lparam==win32con.WM_LBUTTONDBLCLK:
            if self.on_ldouble_click:
                self.on_ldouble_click(self)
            else:
                self.execute_menu_option(self.default_menu_index + self.FIRST_ID)
        elif lparam==win32con.WM_RBUTTONUP:
            self.show_menu()
        elif lparam==win32con.WM_LBUTTONUP:
            pass
        return True

    def show_menu(self):
        menu = self.hmenu
        # if not menu:
        if True:
            menu = win32gui.CreatePopupMenu()
            self.create_menu(menu, self.menu_options)
            #win32gui.SetMenuDefaultItem(menu, 1000, 0)
            self.hmenu = menu

        pos = win32gui.GetCursorPos()
        # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                self.hwnd,
                                None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def create_menu(self, menu, menu_options):
        # for option_text, option_icon, option_action, option_id, option_fState in menu_options[::-1]:
        for menu_option_unpack in menu_options[::-1]:
            option_text = menu_option_unpack['option_text']
            option_icon = menu_option_unpack['option_icon']
            option_action = menu_option_unpack['option_action']
            option_id = menu_option_unpack['option_id']
            option_fState_blist = menu_option_unpack['option_fState']
            option_fState = None
            if option_fState_blist:
                option_fState = win32con.MFS_CHECKED if option_fState_blist[0] else win32con.MFS_UNCHECKED

            self.tm_id_2_menu[option_id] = menu

            if option_icon:
                option_icon = self.prep_menu_icon(option_icon)

            if option_id in self.menu_actions_by_id:                
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                wID=option_id,
                                                                fState=option_fState)
                win32gui.InsertMenuItem(menu, 0, 1, item)
            else:
                submenu = win32gui.CreatePopupMenu()
                self.create_menu(submenu, option_action)
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                hSubMenu=submenu)
                win32gui.InsertMenuItem(menu, 0, 1, item)

    def prep_menu_icon(self, icon):
        # First load the icon.
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

        hdcBitmap = win32gui.CreateCompatibleDC(0)
        hdcScreen = win32gui.GetDC(0)
        hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
        hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
        # Fill the background.
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
        win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
        # unclear if brush needs to be feed.  Best clue I can find is:
        # "GetSysColorBrush returns a cached brush instead of allocating a new
        # one." - implies no DeleteObject
        # draw the icon
        win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        win32gui.SelectObject(hdcBitmap, hbmOld)
        win32gui.DeleteDC(hdcBitmap)

        return hbm.Detach()

    def command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        self.execute_menu_option(id)

    def execute_menu_option(self, id):
        menu_action = self.menu_actions_by_id[id]      
        if menu_action == self.QUIT:
            win32gui.DestroyWindow(self.hwnd)
        else:
            if id in self.tl_checkbox_id:
                menu = self.tm_id_2_menu[id]
                state = win32gui.GetMenuState(menu, id, win32con.MF_BYCOMMAND)
                is_check = False
                if state != -1 and not (state & win32con.MF_CHECKED):
                    is_check = True
                check_flags = win32con.MFS_CHECKED if is_check else win32con.MFS_UNCHECKED
                rc = win32gui.CheckMenuItem(
                    menu, id, win32con.MF_BYCOMMAND | check_flags
                )

                # new_state = win32gui.GetMenuState(menu, id, win32con.MF_BYCOMMAND)
                # if new_state & win32con.MF_CHECKED != check_flags:
                #     raise RuntimeError("The new item didn't get the new checked state!")
                menu_action(self, is_check)
            else:
                menu_action(self)

def non_string_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return not isinstance(obj, str)



# 报错弹框
# You would normally put that on the App class
def showError(self, *args):
    tlErr = traceback.format_exception(*args)
    errStr = ''
    for i in range(0,len(tlErr)):
        errStr += tlErr[i]
    print(errStr, end='')
    messageboxShowerror('错误', errStr)

# # but this works too
Tk.report_callback_exception = showError


# 报错弹框过滤
def messageboxShowerror(title, errStr):
    tlSkipTagStr = [
        'WinError 1223',        #操作已被用户取消
    ]
    isSkip = False
    for skipTagStr in tlSkipTagStr:
        if re.search(r'%s' % skipTagStr, errStr):
            isSkip = True
            break

    # print('isSkip:%s' % isSkip)
    if not isSkip:
        messagebox.showerror('错误', errStr)



# 打包成exe后内部资源路径要改下
EXE_SOURSE_BASE_PATH = None
try:
    EXE_SOURSE_BASE_PATH = sys._MEIPASS
except Exception as e:
    EXE_SOURSE_BASE_PATH = '.'

ICO_PATH = os.path.join(EXE_SOURSE_BASE_PATH, 'icon\icon.ico')



# 默认抓图范围 x,y,w,h
DEFAULT_CATCH_RECT = [800, 400, 300, 100]
# 默认倍率
DEFAULT_RATE = 140
# 默认最小倍率
DEFAULT_MIN_RATE = 20
# 默认最大倍率
DEFAULT_MAX_RATE = 1000
# 默认透明度
DEFAULT_ALPHA = 100
DEFAULT_MIN_ALPHA = 30
DEFAULT_MAX_ALPHA = 100
# 刷新间隔
UPDATE_MS = 16

NOW_CONFIG = None
NOW_LOCK_BLIST = [False]

CONFIG_JSON_PATH = './zoomToolConfig.json'


# 删除文件和文件夹
def delete_file_folder(src):
    '''delete files and folders'''
    if os.path.isfile(src):
        try:
            os.remove(src)
        except:
            print(u"不存在文件:%s" % src)
    elif os.path.isdir(src):
        for item in os.listdir(src):
            itemsrc=os.path.join(src,item)
            delete_file_folder(itemsrc)
        try:
            os.rmdir(src)
        except:
            pass


# 读取json到list
def loadJsonToList(path, ignoreLog=False, isOrdered=True):
    if not os.path.isfile(path):
        if not ignoreLog:
            print("不存在文件:%s" % path)
        return False

    _config = open(path,'r',encoding='UTF-8')
    try:
        fileContent = _config.read()
    finally:
        _config.close()
    config_List = None
    try:
        if isOrdered:
            config_List = json.loads(fileContent, object_pairs_hook=OrderedDict)
        else:
            config_List = json.loads(fileContent)
    except json.JSONDecodeError:
        # raise e
        pass
    return config_List


# 将list写入json
def dumpJsonFromList(path, config_List, indent=None, sort_keys=False, print_dump_path=True):
    if not config_List or not path:
        return False

    with open(path,"wb") as _config:
        content = json.dumps(config_List, ensure_ascii=False, indent=indent, sort_keys=sort_keys)
        try:
            _config.write(content.encode('utf-8'))
        finally:
            _config.close()
        if print_dump_path:
            print("写入json:%s" % path)
        return True
    return False


def tkCenter(win, resetSize=False, anchorPos={'x':0.5, 'y':0.5}):
    """
    centers a tkinter window
    :param win: the main window or Toplevel window to center
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = round(win.winfo_screenwidth() * anchorPos['x']) - win_width // 2
    y = round(win.winfo_screenheight() * anchorPos['y']) - win_height // 2
    # py3_common.Logging.error(width, height, x, y)
    if resetSize:
        win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    else:
        win.geometry('+{}+{}'.format(x, y))
    win.deiconify()


# 读设置
def loadConfigData():
    data = None
    if os.path.isfile(CONFIG_JSON_PATH):
        data = loadJsonToList(CONFIG_JSON_PATH)
    else:
        data = dict()
        data['catchRect'] = DEFAULT_CATCH_RECT
        data['rate'] = DEFAULT_RATE
        data['minRate'] = DEFAULT_MIN_RATE
        data['maxRate'] = DEFAULT_MAX_RATE
        data['alpha'] = DEFAULT_ALPHA
    global NOW_CONFIG
    NOW_CONFIG = data

# 写设置
def saveConfigData():
    if os.path.isfile(CONFIG_JSON_PATH):
        delete_file_folder(CONFIG_JSON_PATH)
    dumpJsonFromList(CONFIG_JSON_PATH, NOW_CONFIG, indent=2)



class MyToplevel(Toplevel):
    def __init__(self, rootWindow, mainView, **kwargs):
        super().__init__(rootWindow, **kwargs)
        self.rootWindow = rootWindow
        self.mainView = mainView
        self.initView()

    def initView(self):
        self.tkPosX = 0
        self.tkPosY = 0
        self.addCommonEvent()

    def addCommonEvent(self):
        # 鼠标中键拖动窗口
        self.bind('<Button-3>', self.onMouseButton3Click)
        self.bind('<B3-Motion>', self.onMouseButton3Motion)

        # 覆盖关闭按钮功能
        self.protocol("WM_DELETE_WINDOW", self.closeView)

    # 鼠标中键
    def onMouseButton3Click(self, event):
        self.tkPosX, self.tkPosY = event.x, event.y

    # 鼠标中键拖动
    def onMouseButton3Motion(self, event):
        newX = (event.x - self.tkPosX) + self.winfo_x()
        newY = (event.y - self.tkPosY) + self.winfo_y()
        self.geometry('+%d+%d' % (newX, newY))

    # 关闭界面
    def closeView(self):
        self.destroy()
        


# 设置界面
class SettingView(MyToplevel):
    def __init__(self, rootWindow, mainView, **kwargs):
        super().__init__(rootWindow, mainView, **kwargs)

    def initView(self):
        super().initView()
        self.resizable(width=False, height=False)
        self.title("设置")
        self.columnconfigure(0,weight=1)

        # 透明度
        frameTemp = Frame(self)
        frameTemp.grid(row=0, column=0, sticky='nsew')
        frameAlphaTitle = Frame(frameTemp)
        frameAlphaTitle.grid(row=0, column=0, sticky='nsew')
        labelAlphaTitle = Label(frameAlphaTitle, text='透明度：', anchor='w')
        labelAlphaTitle.grid(row=0, column=0, sticky='w')
        labelAlpha = Label(frameAlphaTitle, text=NOW_CONFIG['alpha'], anchor='w')
        labelAlpha.grid(row=0, column=1, sticky='w')
        self.labelAlpha = labelAlpha
        self.scaleAlphaVar = IntVar()
        self.scaleAlphaVar.set(NOW_CONFIG['alpha'])
        # showvalue=0隐藏数字
        scaleAlpha = Scale(frameTemp, from_=DEFAULT_MIN_ALPHA, to=DEFAULT_MAX_ALPHA, length=300, orient="horizontal", variable=self.scaleAlphaVar, command=lambda e:self.onScaleAlphaChange(), showvalue=0)
        scaleAlpha.grid(row=1, column=0, sticky='e')

        # 放大倍率
        frameZoomTitle = Frame(frameTemp)
        frameZoomTitle.grid(row=2, column=0, sticky='nsew')
        labelZoomTitle = Label(frameZoomTitle, text='放大倍率（%d%%~%d%%）：' % (NOW_CONFIG['minRate'], NOW_CONFIG['maxRate']), anchor='w')
        labelZoomTitle.grid(row=0, column=0, sticky='w')
        labelZoom = Label(frameZoomTitle, text='%d%%' % NOW_CONFIG['rate'], anchor='w')
        labelZoom.grid(row=0, column=1, sticky='w')
        self.labelZoom = labelZoom
        self.scaleZoomVar = IntVar()
        self.scaleZoomVar.set(NOW_CONFIG['rate'])
        # showvalue=0隐藏数字
        scaleZoom = Scale(frameTemp, from_=NOW_CONFIG['minRate'], to=NOW_CONFIG['maxRate'], length=300, orient="horizontal", variable=self.scaleZoomVar, command=lambda e:self.onScaleZoomChange(), showvalue=0)
        scaleZoom.grid(row=3, column=0, sticky='e')

        # 覆盖关闭按钮功能
        self.protocol("WM_DELETE_WINDOW", self.closeView)

    def onScaleAlphaChange(self):
        NOW_CONFIG['alpha'] = self.scaleAlphaVar.get()
        self.labelAlpha.configure(text=NOW_CONFIG['alpha'])
        self.mainView.refreshAlpha()

    def onScaleZoomChange(self):
        NOW_CONFIG['rate'] = self.scaleZoomVar.get()
        self.labelZoom.configure(text='%d%%' % NOW_CONFIG['rate'])
        self.mainView.refreshRootSize()

    def closeView(self):
        super().closeView()
        saveConfigData()



# 选范围界面
class RectView(MyToplevel):
    def __init__(self, rootWindow, mainView, **kwargs):
        super().__init__(rootWindow, mainView, **kwargs)

    def initView(self):
        super().initView()
        self.title("选择放大区域（按住右键拖动）")
        self.attributes('-alpha', 60/100.0)

        x, y, w, h = tuple(NOW_CONFIG['catchRect'])
        self.update_idletasks()
        frmW, frmH = self.winfo_rootx() - self.winfo_x(), self.winfo_rooty() - self.winfo_y()
        self.geometry('%dx%d+%d+%d' % (w, h-frmH, x-frmW, y))
        self.deiconify()

        # 置顶
        self.wm_attributes('-topmost',1)

        self.oldRect = list(NOW_CONFIG['catchRect'])

        self.bind('<Configure>', self.onViewConfigure)

    def onViewConfigure(self, event):
        rootX, rootY = self.winfo_rootx(), self.winfo_rooty()
        frmW, frmH = rootX - event.x, rootY - event.y
        x, y, w, h = rootX, event.y, event.width, event.height + frmH
        ox, oy, ow, oh = tuple(self.oldRect)
        NOW_CONFIG['catchRect'] = [x, y, w, h]
        if x != ox or y != oy or w != ow or h != oh:
            self.mainView.refreshRootSize()

    def closeView(self):
        saveConfigData()
        self.destroy()



# 放大镜界面
class MainGui(Frame):
    def __init__(self, rootWindow, **kwargs):
        super().__init__(rootWindow, borderwidth=0, **kwargs)
        self.rootWindow = rootWindow
        self.initWindow()
        
    def initWindow(self):
        loadConfigData()
        programName = 'ZoomTool'
        self.rootWindow.title(programName)
        self.rootWindow.iconbitmap(ICO_PATH)
        # self.rootWindow.wm_attributes('-topmost',1)       #置顶
        self.rootWindow.resizable(0,0)      # 禁用最大化按钮

        self.rootWindow.rowconfigure(0,weight=1)
        self.rootWindow.columnconfigure(0,weight=1)

        self.emptyMBar = Menu(self.rootWindow)

        canvas = Canvas(self.rootWindow)  #创建画布
        canvas.grid(row=0, column=0, sticky='nsew')
        self.canvas = canvas

        self.refreshRootSize()
        self.refreshAlpha()

        # 图像
        self.grabImg = None

        self.tkPosX = 0
        self.tkPosY = 0
        self.rootWindow.update_idletasks()
        self.frmW = self.rootWindow.winfo_rootx() - self.rootWindow.winfo_x()
        self.frmH = self.rootWindow.winfo_rooty() - self.rootWindow.winfo_y()
        self.isHideTitleBar = False
        self.rect = None
        self.isEnter = False

        NOW_LOCK_BLIST[0] = False

        self.executor = ThreadPoolExecutor(max_workers=1)   #线程池

        self.rectView = None
        self.settingView = None

        # 鼠标中键拖动窗口
        self.rootWindow.bind('<Button-3>', self.onMouseButton3Click)
        self.rootWindow.bind('<B3-Motion>', self.onMouseButton3Motion)
        # self.rootWindow.bind('<F11>', lambda e:self.switchHideTitleBar())
        self.rootWindow.bind('<F12>', lambda e:self.lockMain())
        self.rootWindow.bind('<Enter>', self.onEnter)
        self.rootWindow.bind('<Motion>', self.onEnter)

        # 覆盖关闭按钮功能
        self.rootWindow.protocol("WM_DELETE_WINDOW", self.closeRootWindow)

        # 通知栏图标
        menuOptions = (
            ('锁定（F12）', None, self.onSysTrayLock, NOW_LOCK_BLIST),
            ('选择范围', None, self.onSysTrayShowRectView),
            ('设置', None, self.onSysTraySetting),
            )
        self.sysTrayIcon = SysTrayIcon(ICO_PATH,
            programName,
            menuOptions,
            on_quit=self.onSysTrayExit,
            quit_text='退出',
            on_ldouble_click=self.onSysTrayLDoubleClick,
            window_class_name=programName,
            )

        # 刷新
        self.updateView()

    # 切换无边框
    def switchHideTitleBar(self):
        self.isHideTitleBar = not self.isHideTitleBar

        def setAppwindow(root):
            GWL_EXSTYLE=-20
            WS_EX_APPWINDOW=0x00040000
            WS_EX_TOOLWINDOW=0x00000080

            hwnd = windll.user32.GetParent(root.winfo_id())
            style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
            style = style & ~WS_EX_TOOLWINDOW
            style = style | WS_EX_APPWINDOW
            res = windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
            # re-assert the new window style
            root.wm_withdraw()
            root.after(1, lambda :root.wm_deiconify())
            root.after(1, lambda :root.focus_force())

        ox, oy = self.rootWindow.winfo_x(), self.rootWindow.winfo_y()
        nx, ny = (ox + self.frmW) if self.isHideTitleBar else (ox - self.frmW), (oy + self.frmH) if self.isHideTitleBar else (oy - self.frmH)
        self.rootWindow.overrideredirect(self.isHideTitleBar)
        if self.isHideTitleBar:
            self.rootWindow.after(1, lambda :setAppwindow(self.rootWindow))
        self.rootWindow.after(1, lambda :self.rootWindow.geometry('+%d+%d' % (nx, ny)))

    def lockMain(self):
        NOW_LOCK_BLIST[0] = not NOW_LOCK_BLIST[0]
        if NOW_LOCK_BLIST[0]:
            root = self.rootWindow
            self.rect = [root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()]

            # 关闭选范围界面
            if self.rectView:
                try:
                    self.rectView.closeView()
                except Exception as e:
                    pass
                self.rectView = None
            # 关闭设置界面
            if self.settingView:
                try:
                    self.settingView.closeView()
                except Exception as e:
                    pass
                self.settingView = None
        else:
            self.rootWindow.attributes('-alpha', NOW_CONFIG['alpha']*0.01)
            self.rootWindow.wm_attributes('-topmost',0)
        self.switchHideTitleBar()

    # 获取放大后大小
    def _getRootSize(self):
        cx, cy, cw, ch = tuple(NOW_CONFIG['catchRect'])
        rate = NOW_CONFIG['rate']
        w, h = math.floor(cw*rate*0.01), math.floor(ch*rate*0.01)
        return (w, h)

    # 刷新大小
    def refreshRootSize(self):
        self.rootWindow.geometry('%dx%d' % self._getRootSize())

    # 刷新透明度
    def refreshAlpha(self):
        self.rootWindow.attributes('-alpha', NOW_CONFIG['alpha']*0.01)

    # 刷新图像
    def updateView(self):
        cx, cy, cw, ch = tuple(NOW_CONFIG['catchRect'])
        w, h = self._getRootSize()
        root = self.rootWindow
        img = ImageGrab.grab((cx, cy, cx+cw, cy+ch))
        imgTemp = img.resize((w, h))
        self.grabImg = ImageTk.PhotoImage(image=imgTemp)  #全屏抓取
        self.canvas.create_image(math.floor(w*0.5), math.floor(h*0.5), image=self.grabImg)

        if NOW_LOCK_BLIST[0] and self.isEnter and self.rect:
            mx, my = win32api.GetCursorPos()
            rx, ry, rw, rh = tuple(self.rect)
            shiftX, shiftY = 10, 10
            if mx < rx-shiftX or mx > rx+rw+shiftX or my < ry-shiftY or my > ry+rh+shiftY:
                self.isEnter = False
                self.rootWindow.attributes('-alpha', NOW_CONFIG['alpha']*0.01)
                self.rootWindow.wm_attributes('-topmost',1)

        self.after(func=self.updateView, ms=UPDATE_MS)

    # 鼠标中键
    def onMouseButton3Click(self, event):
        self.tkPosX, self.tkPosY = event.x, event.y

    # 鼠标中键拖动
    def onMouseButton3Motion(self, event):
        newX = (event.x - self.tkPosX) + self.rootWindow.winfo_x()
        newY = (event.y - self.tkPosY) + self.rootWindow.winfo_y()
        self.rootWindow.geometry('+%d+%d' % (newX, newY))

    def showRectView(self):
        if NOW_LOCK_BLIST[0]:
            self.lockMain()

        if self.rectView:
            try:
                self.rectView.closeView()
            except Exception as e:
                # raise e
                pass
            self.rectView = None

        view = RectView(self.rootWindow, self)
        self.rectView = view
        view.after(1, lambda: view.focus_force())

    def showSettingView(self):
        if NOW_LOCK_BLIST[0]:
            self.lockMain()

        if self.settingView:
            try:
                self.settingView.closeView()
            except Exception as e:
                pass
            self.settingView = None

        view = SettingView(self.rootWindow, self)
        self.settingView = view
        view.after(1, lambda: view.focus_force())
        tkCenter(view)

    def onEnter(self, event):
        # print('onEnter')
        if NOW_LOCK_BLIST[0]:
            self.rootWindow.attributes('-alpha', 0.0)
            self.isEnter = True

    # -----------------通知栏小图标-----------------
    def sysTrayThreadHelper(self, sysTrayIcon=None):
        time.sleep(0.01)
        return sysTrayIcon

    def onSysTrayCallback(self, command, sysTrayIcon=None):
        if not self:
            return
        thread = self.executor.submit(self.sysTrayThreadHelper, sysTrayIcon)
        thread.add_done_callback(lambda s: command(s))

    # 双击小图标
    def onSysTrayLDoubleClick(self, sysTrayIcon=None):
        def helper(s=None):
            self.rootWindow.wm_deiconify()  #最小化了要重新弹出界面
            self.rootWindow.focus_force()   #设置焦点
        self.onSysTrayCallback(helper, sysTrayIcon)

    # 锁定
    def onSysTrayLock(self, sysTrayIcon=None, isCheck=False):
        def helper(s=None):
            self.lockMain()
        self.onSysTrayCallback(helper, sysTrayIcon)

    # 选择范围
    def onSysTrayShowRectView(self, sysTrayIcon=None):
        def helper(s=None):
            self.showRectView()
        self.onSysTrayCallback(helper, sysTrayIcon)

    # 设置
    def onSysTraySetting(self, sysTrayIcon=None):
        def helper(s=None):
            self.showSettingView()
        self.onSysTrayCallback(helper, sysTrayIcon)

    # 退出
    def onSysTrayExit(self, sysTrayIcon=None):
        self.closeRootWindow()

    # 关闭界面
    def closeRootWindow(self):
        # self.rootWindow.destroy()
        # saveConfigData()
        if self.sysTrayIcon != None:
            self.sysTrayIcon.destroy()
        # 杀进程
        os._exit(0)









def gui_start():
    rootWindow = Tk()

    # screenW = rootWindow.winfo_screenwidth()
    # screenH = rootWindow.winfo_screenheight()
    # print(screenW, screenH)

    mainGui = MainGui(rootWindow)
    rootWindow.mainloop()

    os._exit(0)

gui_start()