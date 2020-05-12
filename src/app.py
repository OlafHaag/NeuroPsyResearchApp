""""Research application aimed at studying uncontrolled manifold and optimal feedback control paradigms."""

import pickle
import json
import time
from pathlib import Path
import base64

from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.utils import platform
from kivy.lang import global_idmap
from kivy.clock import Clock

from plyer import storagepath
from plyer import email

import requests
import numpy as np

from .utility import (create_device_identifier,
                      create_user_identifier,
                      get_device_data,
                      compile_filename,
                      ask_permission,
                      data2bytes,
                      switch_language
                      )
from .i18n import _, DEFAULT_LANGUAGE
from .config import WEBSERVER
from .settings import SettingsContainer
from .widgets import BaseScreen, SettingsWithTabbedPanels
from .settingsjson import LANGUAGE_CODE, LANGUAGE_SECTION, settings_general_json, settings_circle_task_json


if platform == 'android':
    from android.permissions import Permission

# i18n
global_idmap['_'] = _

# Go fullscreen. # FixMe: On android status bar still re-appears.
#Window.borderless = True
#Window.fullscreen = 'auto'


class Root(Screen):
    """ Root widget, child of Window. """
    pass


class UncontrolledManifoldApp(MDApp):
    manager = ObjectProperty(None, allownone=True)
    
    def build(self):
        """ Initializes the application; it will be called only once.
        If this method returns a widget (tree), it will be used as the root widget and added to the window.
        """
        # Theme.
        self.icon = 'res/icons/mipmap-mdpi/ucmicon.png'
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"
        # Settings.
        self.settings_cls = SettingsWithTabbedPanels
        self.use_kivy_settings = False
        self.settings = SettingsContainer()
        self.update_language_from_config()
        self.write_permit = True  # Set to true as default for platforms other than android.
        self.internet_permit = True
        
        # Containers for data.
        self.data = list()
        self.data_email = list()
        
        # GUI.
        root = Root()
        self.manager = root.ids.mgr
        return root
    
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
        # setdefault doesn't work here for single keys. Can't find section if no config yet. NoSectionError
        config.setdefaults(LANGUAGE_SECTION, {LANGUAGE_CODE: DEFAULT_LANGUAGE})
        config.setdefaults('General', {'is_first_run': 1,
                                       'current_user': create_user_identifier(),
                                       'task': 'Circle Task'})
        config.setdefaults('DataCollection',
                           {
                               'is_local_storage_enabled': 0,
                               'is_upload_enabled': 1,
                               'webserver': WEBSERVER,
                               'is_email_enabled': 0,
                               'email_recipient': '',
                           })
        config.setdefaults('CircleTask',
                           {
                               'n_trials': 20,
                               'n_blocks': 3,
                               'constrained_block': 2,
                               'warm_up_time': 1.0,
                               'trial_duration': 3.0,
                               'cool_down_time': 0.5,
                           })
        # To set aliases for user ids we need to schedule it next frame, we can't retrieve current_user yet.
        Clock.schedule_once(lambda dt: self.set_configdefaults_user(config), 1)
    
    def set_configdefaults_user(self, config):
        """ Set default alias for first user. """
        # We allow multiple users on the same device.
        user_id = config.get('General', 'current_user')
        config.setdefaults('UserData', {user_id: 'Standard'})

    def build_settings(self, settings):
        """ Populate settings panel. """
        settings.add_json_panel('General',
                                self.config,
                                data=settings_general_json)
        settings.add_json_panel('Circle Task',
                                self.config,
                                data=settings_circle_task_json)
    
    def display_settings(self, settings):
        """ Display the settings panel. """
        manager = self.manager
        if not manager.has_screen('Settings'):
            s = BaseScreen(name='Settings', navbar_enabled=True)
            s.add_widget(settings)
            manager.add_widget(s)
        manager.current = 'Settings'
    
    def close_settings(self, *args):
        """ Always gets called on escape regardless of current screen. """
        if self.manager.current == 'Settings':
            self.manager.go_home()  # FixMe: When entered from outro screen, return to outro screen.
            # Hack, since after this manager.key_input is executed and screen is 'home' by then.
            self.manager.n_home_esc -= 1
    
    def on_config_change(self, config, section, key, value):
        """ Fired when the section's key-value pair of a ConfigParser changes. """
        if section == 'Localization' and key == 'language':
            switch_language(value)

    def update_language_from_config(self):
        """Set the current language of the application from the configuration.
        """
        config_language = self.config.get(LANGUAGE_SECTION, LANGUAGE_CODE)
        switch_language(lang=config_language)

    def reset_data_collection(self):
        self.data.clear()
        self.data_email.clear()
        # Start new data collection with device information.
        self.collect_device_data()

    def collect_device_data(self):
        """ Add properties of device to data collection. """
        props = get_device_data()
        columns = props.keys()
        
        meta_data = dict()
        meta_data['table'] = 'device'
        meta_data['id'] = create_device_identifier()
        meta_data['time'] = time.time()
        
        if self.settings.is_upload_enabled or self.settings.is_local_storage_enabled:
            # Data for storage and upload.
            data = np.array([props[k] for k in columns]).reshape((1, len(columns)))
            header = ','.join(columns)
            meta_data['data'] = data2bytes(data, header=header, fmt='%s')
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
        header = 'id,device_id'
        data = np.array([self.settings.current_user, create_device_identifier()])
        d['data'] = data2bytes(data.reshape((1, len(data))), header=header, fmt='%s')
        return d

    def get_storage_path(self):
        """ Return writable path.
        If it does not exist on android, make directory.
        """
        if platform == 'android':
            # dest = Path(storagepath.get_documents_dir())
            dest = Path(storagepath.get_external_storage_dir()) / MDApp.get_running_app().name  # ToDo: Isn't that self.name?!
            # We may need to ask permission to write to the external storage. Permission could have been revoked.
            self.write_permit = ask_permission(Permission.WRITE_EXTERNAL_STORAGE)
            
            if not dest.exists() and self.write_permit:
                # Make sure the path exists.
                dest.mkdir(parents=True, exist_ok=True)
        else:
            app = MDApp.get_running_app()  # ToDo: Isn't that self?!
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
                self.manager.dispatch('on_error',
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
                self.manager.dispatch('on_error',
                                      _("KeyError in Meta Data."))
                continue
            
            file_name = compile_filename(d)
            file_path = dir_path / file_name
            try:
                self.write_file(file_path, d['data'])
            except KeyError:
                self.manager.dispatch('on_error',
                                      _("Data missing.\nFailed to write\n{}.").format(file_name))

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
            name = compile_filename(d)
            file_names.append(name)
            try:
                last_modified.append(d['time'])
                data_b64 = base64.b64encode(d['data'])
            except KeyError:
                self.manager.dispatch('on_error',
                                      _("KeyError in Meta Data."))
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
        """ Generate the destination URI dependent on the current task.
        
        :return: Destination URI for data upload.
        :rtype: str
        """
        if platform == 'android':
            self.internet_permit = ask_permission(Permission.INTERNET, timeout=2)
        
        # Upload address depends on current task. One dash application per task.
        if self.settings.current_task == 'Circle Task':
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
        except (requests.exceptions.InvalidSchema, requests.exceptions.ConnectionError):
            returned_txt = _("ERROR: Server not reachable:") + f"\n{server}"
        except Exception:
            returned_txt = _("ERROR: There was an error processing the upload.")
        return returned_txt
    
    def parse_response(self, response):
        """
        
        :param response: JSON formatted string.
        :type response: str
        :return:
        :rtype: str
        """
        try:
            res_json = json.loads(response)
        except json.decoder.JSONDecodeError:
            # If it's not JSON and not the usual error message length, something else went wrong.
            if len(response) > 150:
                return _("ERROR: There was an unexpected error during upload.")
            return response
        try:
            msg = res_json['response']['props']['children'][0]['props']['children']
        except (KeyError, IndexError):
            msg = _("Not the usual error response.")
        return msg
    
    def get_uploaded_status(self, response):
        """ Determine success of upload.
        
        :param response: Message received from server.
        :type response: str
        :return: Was the upload successful?
        :rtype: bool
        """
        try:
            if response.startswith('ERROR:') or 'Error' in response:
                return False
        except AttributeError:
            pass
        return True
    
    def upload_data(self):
        """ Upload collected data to server. """
        res = self.get_response(self.get_upload_route(), self.get_dash_post(self.data))
        res_msg = self.parse_response(res)
        status = self.get_uploaded_status(res_msg)
        # Let the manager decide what to do on screen when data was uploaded.
        self.manager.dispatch('on_upload_response', status, res_msg)
    
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
                       "the App Settings window.").format(self.settings.current_user) + "\n\n"
        
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
