import io
import time
from datetime import datetime
from hashlib import md5
from uuid import uuid4

import numpy as np
from kivy import platform
from kivy.metrics import Metrics
from kivy.core.window import Window

from plyer import uniqueid

from .config import time_fmt
from .i18n import change_language_to

if platform == 'android':
    from android.permissions import request_permissions, check_permission, Permission

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
    
    
# ToDo: Put everything data related into some kind of DataManager class.

def compile_filename(meta_data):
    """ Returns file name based on provided meta data.
    Uses current time if meta data is incomplete.
    """
    # Different filenames for different types of tables.
    try:
        if meta_data['table'] == 'device':
            file_name = f"device-{meta_data['id']}.csv"
        elif meta_data['table'] == 'user':
            file_name = f"user.csv"
        elif meta_data['table'] == 'session':
            file_name = f"session-{meta_data['time_iso']}.csv"
        elif meta_data['table'] == 'trials':
            file_name = f"trials-{meta_data['time_iso']}-Block_{meta_data['block']}.csv"
        else:
            # Fall back to current time when table unknown.
            file_name = f'{datetime.now().strftime(time_fmt)}.csv'
    except KeyError:
        file_name = f'{datetime.now().strftime(time_fmt)}.csv'
    
    return file_name


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


def get_device_data():
    """ Acquire properties of the device in use. """
    inch2cm = 2.54
    screen_x, screen_y = get_screensize()
    
    device_properties = dict()
    device_properties['id'] = create_device_identifier()
    device_properties['screen_x'] = screen_x
    device_properties['screen_y'] = screen_y
    device_properties['dpi'] = Metrics.dpi
    device_properties['density'] = Metrics.density
    device_properties['aspect_ratio'] = screen_x / screen_y
    device_properties['size_x'] = screen_x / Metrics.dpi * inch2cm
    device_properties['size_y'] = screen_y / Metrics.dpi * inch2cm
    device_properties['platform'] = platform
    return device_properties


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


def data2bytes(data, header=None, fmt="%.5f"):
    """ Takes numpy array and returns it as bytes. """
    bio = io.BytesIO()
    if header:
        #header = header.encode('utf-8')
        np.savetxt(bio, data, delimiter=',', fmt=fmt, encoding='utf-8', header=header, comments='')
    else:
        np.savetxt(bio, data, delimiter=',', fmt=fmt, encoding='utf-8')
    
    b = bio.getvalue()
    return b
