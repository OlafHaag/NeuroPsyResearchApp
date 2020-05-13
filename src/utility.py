import time
from hashlib import md5
from uuid import uuid4

from kivy import platform
from kivy.core.window import Window

from plyer import uniqueid

from .i18n import change_language_to

if platform == 'android':
    from android.permissions import request_permissions, check_permission

if platform == 'win':
    def get_screensize():
        import ctypes
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        return screensize
else:
    def get_screensize():
        return Window.width, Window.height
    
    
def switch_language(lang='en'):
    """ Change displayed translation. """
    try:
        change_language_to(lang)
    except ReferenceError:
        # I spent hours trying to fix it. Now I just don't care anymore.
        print(f"WARNING: Couldn't translate everything. Possible weakref popups that don't exist anymore.")


def create_device_identifier(**kwargs):
    """ Returns an identifier for the hardware. """
    uid = uniqueid.get_uid().encode()
    hashed = md5(uid).hexdigest()
    # Shorten and lose information.
    ident = hashed[::4]
    return ident


def create_user_identifier(**kwargs):
    """ Return unique identifier for user. """
    uuid = uuid4().hex
    return uuid


def ask_permission(permission, timeout=5):
    """ Necessary on Android to request permission for certain actions. """
    if platform == 'android':
        got_permission = check_permission(permission)
        if not got_permission:
            request_permissions([permission])
        
        # Wait a bit until user granted permission.
        t0 = time.time()
        while time.time() - t0 < timeout and not got_permission:
            got_permission = check_permission(permission)
            time.sleep(0.5)
        return got_permission
    # For any other platform assume given permission.
    return True
