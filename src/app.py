""""Research application aimed at studying uncontrolled manifold and optimal feedback control paradigms."""

import io
import pickle
import time
from pathlib import Path
from hashlib import md5
from uuid import uuid4
import base64
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.utils import platform
from kivy.core.window import Window
from kivy.metrics import Metrics
from kivy.lang import global_idmap

from plyer import uniqueid
from plyer import storagepath
from plyer import email

import requests
import numpy as np

from .i18n import _, change_language_to, current_language
from .config import WEBSERVER
from .settings import Settings, SettingsContainer
from .settingsjson import LANGUAGE_CODE, LANGUAGE_SECTION, settings_general_json, settings_circle_task_json

from .widgets import UCMManager, SimplePopup

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

# i18n
global_idmap['_'] = _

# Go fullscreen. # FixMe: On android status bar still re-appears.
Window.borderless = True
Window.fullscreen = 'auto'


class UncontrolledManifoldApp(App):
    manager = ObjectProperty(None, allownone=True)
    upload_btn_enabled = BooleanProperty(True)

    def get_application_config(self, defaultpath='%(appdir)s/%(appname)s.ini'):
        """ Override path to application configuration. """
        if platform == 'win':
            return super(UncontrolledManifoldApp, self).get_application_config('~/.%(appname)s.ini')  # User directory.
        else:
            return super(UncontrolledManifoldApp, self).get_application_config()  # Use default.
    
    def build_config(self, config):
        """ This method is called before the application is initialized to construct the ConfigParser object.
        The configuration will be automatically saved in the file returned by get_application_config().
        """
        
        config.setdefaults(LANGUAGE_SECTION, {LANGUAGE_CODE: current_language()})
        config.setdefaults('General', {'task': 'Circle Task'})
        config.setdefaults('DataCollection', {
            'is_local_storage_enabled': 0,
            'is_upload_enabled': 1,
            'webserver': WEBSERVER,
            'is_email_enabled': 0,
            'email_recipient': '',
        })
        config.setdefaults('UserData', {'unique_id': self.create_user_identifier()})
        config.setdefaults('CircleTask', {
            'n_trials': 20,
            'n_blocks': 3,
            'constrained_block': 2,
            'warm_up_time': 1.0,
            'trial_duration': 3.0,
            'cool_down_time': 0.5})
    
    def build_settings(self, settings):
        """ Populate settings panel. """
        settings.add_json_panel('General',
                                self.config,
                                data=settings_general_json)
        settings.add_json_panel('Circle Task Settings',
                                self.config,
                                data=settings_circle_task_json)
    
    def update_language_from_config(self):
        """Set the current language of the application from the configuration.
        """
        config_language = self.config.get(LANGUAGE_SECTION, LANGUAGE_CODE)
        change_language_to(config_language)
    
    def display_settings(self, settings):
        """ Display the settings panel. """
        manager = self.manager
        if not manager.has_screen('Settings'):
            s = Screen(name='Settings')
            s.add_widget(settings)
            manager.add_widget(s)
        manager.current = 'Settings'
    
    def close_settings(self, *args):
        """ Always gets called on escape regardless of current screen. """
        if self.manager.current == 'Settings':
            self.manager.go_home()
            # Hack, since after this manager.key_input is executed and screen is 'home' by then.
            self.manager.n_home_esc -= 1
    
    def on_config_change(self, config, section, key, value):
        """ Fired when the section's key-value pair of a ConfigParser changes. """
        if section == 'Localization' and key == 'language':
            self.switch_language(value)
        if section == 'UserData' and key == 'configchangebuttons':
            if value == 'btn_new_uuid':
                self.settings.user = self.create_user_identifier()
                # Update User Label.
                user_label = self.settings.get_settings_widget('General', 'unique_id')
                # We need the parent SettingString object of the label.
                setting_string = user_label.parent.parent.parent
                setting_string.value = self.settings.user
    
    def switch_language(self, lang='en'):
        """ Change displayed translation. """
        change_language_to(lang)
    
    def build(self):
        """ Initializes the application; it will be called only once.
        If this method returns a widget (tree), it will be used as the root widget and added to the window.
        """
        # Settings.
        self.settings_cls = Settings
        self.use_kivy_settings = False
        self.settings = SettingsContainer()
        self.update_language_from_config()
        self.write_permit = True  # Set to true as default for platforms other than android.
        self.internet_permit = True
        
        # Containers for data.
        self.data = list()
        self.data_email = list()
        
        # GUI.
        root = UCMManager()
        self.manager = root
        return root
    
    def create_device_identifier(self, **kwargs):
        """ Returns an identifier for the hardware. """
        uid = uniqueid.get_uid().encode()
        hashed = md5(uid).hexdigest()
        # Shorten and lose information.
        ident = hashed[::4]
        return ident
    
    def create_user_identifier(self, **kwargs):
        """ Return unique identifier for user. """
        uuid = uuid4().hex
        return uuid
    
    def reset_data_collection(self):
        self.data.clear()
        self.data_email.clear()
        # Start new data collection with device information.
        self.collect_device_data()
        
    def get_device_data(self):
        """ Acquire properties of the device in use. """
        inch2cm = 2.54
        screen_x, screen_y = get_screensize()
        
        device_properties = dict()
        device_properties['device'] = self.create_device_identifier()
        device_properties['screen_x'] = screen_x
        device_properties['screen_y'] = screen_y
        device_properties['dpi'] = Metrics.dpi
        device_properties['density'] = Metrics.density
        device_properties['aspect_ratio'] = screen_x / screen_y
        device_properties['size_x'] = screen_x / Metrics.dpi * inch2cm
        device_properties['size_y'] = screen_y / Metrics.dpi * inch2cm
        device_properties['platform'] = platform
        return device_properties
        
    def collect_device_data(self):
        """ Add properties of device to data collection. """
        props = self.get_device_data()
        columns = props.keys()
        
        meta_data = dict()
        meta_data['table'] = 'device'
        meta_data['device'] = self.create_device_identifier()
        meta_data['time'] = time.time()
        
        if self.settings.is_upload_enabled or self.settings.is_local_storage_enabled:
            # Data for storage and upload.
            data = np.array([props[k] for k in columns]).reshape((1, len(columns)))
            header = ','.join(columns)
            meta_data['data'] = self.data2bytes(data, header=header, fmt='%s')
            self.data.append(meta_data)
        
        if self.settings.is_email_enabled:
            # Data for e-mail.
            meta_data_email = meta_data.copy()
            meta_data_email['data'] = pickle.dumps(props)
            self.data_email.append(meta_data_email)
    
    def get_user_data(self):
        """ Create a dataset to identify current user. """
        d = dict()
        d['table'] = 'user'
        d['time'] = time.time()
        header = 'id,device'
        data = np.array([self.settings.user, self.create_device_identifier()])
        d['data'] = self.data2bytes(data.reshape((1, len(data))), header=header, fmt='%s')
        return d
        
    def ask_internet_permission(self, timeout=5):
        """Necessary on android to post data to the server.
        Yet, no prompt appears, nor a setting in the app's permissions...
        """
        if platform == 'android':
            self.internet_permit = check_permission(Permission.INTERNET)
            if not self.internet_permit:
                request_permissions([Permission.INTERNET])
        
            # Wait a bit until user granted permission.
            t0 = time.time()
            while time.time() - t0 < timeout and not self.internet_permit:
                self.internet_permit = check_permission(Permission.INTERNET)
                time.sleep(0.5)
                
    def ask_write_permission(self, timeout=5):
        """ Necessary on Android to write to the file system. """
        if platform == 'android':
            self.write_permit = check_permission(Permission.WRITE_EXTERNAL_STORAGE)
            if not self.write_permit:
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
            
            # Wait a bit until user granted permission.
            t0 = time.time()
            while time.time() - t0 < timeout and not self.write_permit:
                self.write_permit = check_permission(Permission.WRITE_EXTERNAL_STORAGE)
                time.sleep(0.5)
    
    def get_storage_path(self):
        """ Return writable path.
        If it does not exist on android, make directory.
        """
        if platform == 'android':
            # dest = Path(storagepath.get_documents_dir())
            dest = Path(storagepath.get_external_storage_dir()) / App.get_running_app().name
            # We may need to ask permission to write to the external storage. Permission could have been revoked.
            self.ask_write_permission()
            
            if not dest.exists() and self.write_permit:
                # Make sure the path exists.
                dest.mkdir(parents=True, exist_ok=True)
        else:
            app = App.get_running_app()
            dest = Path(app.user_data_dir)
            # dest = dest.resolve()  # Resolve any symlinks.
        return dest
    
    def create_subfolder(self, subpath):
        """ Create a user folder inside storage_path.
        
        :param subpath: Path relative to get_storage_path()'s return value.
        :type subpath: Union[str,pathlib.Path]
        """
        storage_path = self.get_storage_path()
        destination = storage_path / subpath
        if not destination.exists() and self.write_permit:
            destination.mkdir(parents=True, exist_ok=True)  # Assume this works and we have permissions.

    def compile_filename(self, meta_data):
        """ Returns file name based on provided meta data.
        Uses current time if meta data is incomplete.
        """
        # Different filenames for different types of tables.
        try:
            if meta_data['table'] == 'device':
                file_name = f"device-{meta_data['device']}.csv"
            elif meta_data['table'] == 'user':
                file_name = f"user.csv"
            elif meta_data['table'] == 'session':
                file_name = f"session-{meta_data['time_iso']}.csv"
            elif meta_data['table'] == 'trials':
                file_name = f"trials-{meta_data['time_iso']}-Block_{meta_data['block']}.csv"
            else:
                # Fall back to current time when table unknown.
                file_name = f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")}.csv'
        except KeyError:
            file_name = f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")}.csv'
            
        return file_name

    def write_file(self, path, content):
        """ Save content to path.
        
        :param path: Path to file.
        :type path: pathlib.Path
        :param content: Content to write to file.
        :type content: Union[bytes,str]
        
        :return: Whether writing to file was successful.
        :rtype: bool
        """
        if self.write_permit:
            if isinstance(content, bytes):
                path.write_bytes(content)
                return True
            elif isinstance(content, str):
                path.write_text(content)
                return True
            else:
                self.show_feedback(_("Error!"),
                                   _("Unable to write to file:\n{}\nUnknown data format.").format(path.name))
        return False
        
    def write_data_to_files(self):
        """ Writes content of data to disk. """
        storage = self.get_storage_path()
        for d in self.data:
            try:
                if d['table'] in ['session', 'trials']:
                    sub_folder = Path(d['task'].replace(" ", "_")) / d['user']
                    self.create_subfolder(sub_folder)
                    dir_path = storage / sub_folder
                else:
                    dir_path = storage
            except KeyError:
                self.show_feedback(_("Error!"), _("KeyError in Meta Data."))
                continue
            
            file_name = self.compile_filename(d)
            file_path = dir_path / file_name
            try:
                self.write_file(file_path, d['data'])
            except KeyError:
                self.show_feedback(_("Error!"), _("Data missing.\nFailed to write\n{}.").format(file_name))
    
    def data2bytes(self, data, header=None, fmt="%.5f"):
        """ Takes numpy array and returns it as bytes. """
        bio = io.BytesIO()
        if header:
            #header = header.encode('utf-8')
            np.savetxt(bio, data, delimiter=',', fmt=fmt, encoding='utf-8', header=header, comments='')
        else:
            np.savetxt(bio, data, delimiter=',', fmt=fmt, encoding='utf-8')
            
        b = bio.getvalue()
        return b
    
    def get_dash_post(self, data_collection):
        """ Build a json string to post to a dash update component.

        :return: post request json string.
        """
        file_names = list()
        last_modified = list()
        data = list()
        
        # When writing data to files, we create a folder with the user's identifier.
        # We need to add user identification to the post as well.
        user_data = self.get_user_data()
        data_collection.insert(1, user_data)  # After device data, before session.
        
        for d in data_collection:
            # Build fake file name.
            name = self.compile_filename(d)
            file_names.append(name)
            try:
                last_modified.append(d['time'])
                data_b64 = base64.b64encode(d['data'])
            except KeyError:
                self.show_feedback(_("Error!"), _("KeyError in Meta Data."))
                continue
                
            data.append(data_b64)
        
        post_data = {'output': 'output-data-upload.children',
                     'changedPropIds': ['upload-data.contents'],
                     'inputs': [{'id': 'upload-data',
                                 'property': 'contents',
                                 'value': [f'data:application/octet-stream;base64,{d.decode()}' for d in data]}],
                     'state': [{'id': 'upload-data',
                                'property': 'filename',
                                'value': file_names},
                               {'id': 'upload-data',
                                'property': 'last_modified',
                                'value': last_modified}]}
        
        return post_data
    
    def get_upload_route(self):
        if platform == 'android':
            self.ask_internet_permission(2)
    
        # Upload address depends on current task. One dash application per task.
        if self.settings.task == 'Circle Task':
            upload_route = '/circletask/_dash-update-component'
        # Map other tasks to their respective dash-app here.
        else:
            upload_route = ''
        server_uri = self.settings.server_uri.strip('/') + upload_route
        return server_uri
    
    def get_response(self, server, data):
        """ Upload collected data to server. """
        # ToDo: upload error handling.
        try:
            response = requests.post(server, json=data)
            returned_txt = response.text
        except:
            returned_txt = 'There was an error processing this file.'
        return returned_txt
    
    def get_uploaded_status(self, response):
        if 'There was an error processing this file.' not in response:
            return True
        else:
            return False
        
    def get_upload_feedback(self, upload_status):
        if upload_status is True:
            feedback_title = _("Success!")
            feedback_txt = _("Upload successful!")
        else:
            feedback_title = _("Error!")
            feedback_txt = _("Upload failed.\nSomething went wrong.")
        return feedback_title, feedback_txt
    
    def upload_data(self):
        """ Upload collected data to server. """
        res = self.get_response(self.get_upload_route(), self.get_dash_post(self.data))
        status = self.get_uploaded_status(res)
        if status is True:
            self.upload_btn_enabled = False

        # Feedback after uploading.
        self.show_feedback(*self.get_upload_feedback(status))
    
    def show_feedback(self, title, msg):
        pop = SimplePopup(title=title)
        pop.msg = msg
        pop.open()
    
    def send_email(self):
        """ Send the data via e-mail. """
        recipient = self.settings.email_recipient
        subject = 'New UCM Data Set'
        disclaimer = _("Disclaimer:\n"
                       "By submitting this e-mail you agree to the data processing and evaluation for the purpose of "
                       "this scientific investigation.\nThe data below will be copied and saved from the received "
                       "e-mail. The email itself will be deleted within 3 days to separate the sender address from the "
                       "data for the purpose of anonymisation.\n If you wish to revoke your consent to data processing "
                       "and storage, please send an e-mail to the address specified in the address line and provide "
                       "your identification code [b]{}[/b] so that I can assign and delete your record.\n"
                       "If you deleted this email from your [i]Sent[/i] folder, you can look up your unique ID in "
                       "the App Settings window.").format(self.settings.user) + "\n\n"
        
        text = "### Data ###\n\n"
        for d in self.data_email:
            text += "\n".join(k + ": " + str(v) for k, v in d.items())
            text += "\n\n"
        
        create_chooser = True
        email.send(recipient=recipient, subject=subject, text=disclaimer + text, create_chooser=create_chooser)
    
    # ToDo pause App.on_pause(), App.on_resume()
    def on_pause(self):
        # Here you can save data if needed
        return True
    
    def on_resume(self):
        # Here you can check if any data needs replacing (usually nothing)
        pass
