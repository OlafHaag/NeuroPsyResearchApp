""""Research application aimed at studying uncontrolled manifold and optimal feedback control paradigms."""

import io
import time
from pathlib import Path
from hashlib import md5
from uuid import uuid4
import base64

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.utils import platform
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
    pass

# i18n
global_idmap['_'] = _


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
        """ Configure initial settings. """
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
        change_language_to(lang)
    
    def build(self):
        self.settings_cls = Settings
        self.use_kivy_settings = False
        self.settings = SettingsContainer()
        self.update_language_from_config()
        self.write_permit = True  # Set to true as default for platforms other than android.
        root = UCMManager()
        self.manager = root
        self.data_upload = list()
        self.data_email = list()
        return root
    
    @staticmethod
    def create_device_identifier(**kwargs):
        """ Returns an identifier for the hardware. """
        uid = uniqueid.get_uid().encode()
        hashed = md5(uid).hexdigest()
        # Shorten and lose information.
        ident = hashed[::4]
        return ident
    
    @staticmethod
    def create_user_identifier(**kwargs):
        """ Return unique identifier for user. """
        uuid = uuid4().hex
        return uuid
    
    def ask_write_permission(self, timeout=5):
        if platform == 'android':
            self.write_permit = check_permission(Permission.WRITE_EXTERNAL_STORAGE)
            if not self.write_permit:
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
            
            # Wait a bit until user granted permission.
            t0 = time.time()
            while time.time() - t0 < timeout and not self.write_permit:
                self.write_permit = check_permission(Permission.WRITE_EXTERNAL_STORAGE)
                time.sleep(0.5)
    
    def get_data_path(self):
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
    
    def data2bytes(self, data):
        """ Takes numpy array and returns it as bytes. """
        bio = io.BytesIO()
        np.savetxt(bio, data, delimiter=',', fmt="%.5f", encoding='utf-8')
        b = bio.getvalue()
        return b
    
    def compile_filename(self, meta_data):
        # ToDo: different filenames for different types of tables.
        file_name = f"{meta_data['user']}-{meta_data['task']}-Block{meta_data['block']}-{meta_data['type']}-{meta_data['time_iso']}.csv"
        return file_name
    
    def get_dash_post(self):
        """ Build a json string to post to a dash update component.

        :return: post request json string.
        """
        file_names = list()
        last_modified = list()
        data = list()
        
        for d in self.data_upload:
            # Build fake file name.
            file_names.append(self.compile_filename(d))
            last_modified.append(d['time'])
            # Convert data to base64.
            header = (','.join(d['columns']) + '\n').encode('utf-8')
            data_bytes = self.data2bytes(d['data'])
            data_b64 = base64.b64encode(header + data_bytes)
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
    
    def upload_data(self):
        """ Upload collected data to server. """
        
        # Upload address depends on current task. One dash application per task.
        if self.settings.task == 'Circle Task':
            upload_route = '/circletask/_dash-update-component'
        # Map other tasks to their respective dash-app here.
        else:
            upload_route = ''
        server_uri = self.settings.server_uri.strip('/') + upload_route
        
        post_data = self.get_dash_post()
        
        # ToDo: upload error handling.
        try:
            response = requests.post(server_uri, json=post_data)
            returned_txt = response.text
        except:
            returned_txt = 'There was an error processing this file.'
        
        if 'There was an error processing this file.' not in returned_txt:
            feedback_title = _("Success!")
            feedback_txt = _("Upload successful!")
            self.upload_btn_enabled = False
        else:
            feedback_title = _("Error!")
            feedback_txt = _("Upload failed.\nSomething went wrong.")
        
        # Feedback after uploading.
        self.show_feedback(feedback_title, feedback_txt)
    
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
                       "the App Settings window. It is based on your hardware but does not contain any identifiable "
                       "information about it or about yourself.").format(self.settings.user) + "\n\n"
        
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
