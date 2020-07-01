# Built-in imports
import base64
from datetime import datetime
import io
import json
from pathlib import Path
import pickle
import shutil
import time
from typing import List

# Third party imports
from kivy.app import App
from kivy.metrics import Metrics
from kivy.properties import BooleanProperty
from kivy.uix.widget import Widget
from kivy.utils import platform
import numpy as np
import plyer
import requests

# Own module imports
from .i18n import _
from .utility import (time_fmt,
                      create_device_identifier,
                      get_screensize,
                      ask_permission,
                      Permission,
                      )
# Conditional imports
if platform == 'android':
    from jnius import autoclass


class DataManager(Widget):  # Inherit from Widget so we can dispatch events.
    """ Manager for data collection and saving or sending them. """
    is_data_saved = BooleanProperty(False)  # Did we save the current data?
    is_data_sent = BooleanProperty(False)  # Did we sent the current data?
    
    def __init__(self, **kwargs):
        super(DataManager, self).__init__(**kwargs)
        self.app = App.get_running_app()
        # Containers for data.
        self._data = list()  # type: List[dict]
        self._data_email = list()
        self.is_invalid = False
        # For which user to collect data. Set after given consent.
        self._user_id = ''
        # Events to listen to.
        self.app.settings.bind(on_user_removed=lambda instance, user_id: self._remove_user_folders(user_id))
        # Events to fire.
        self.register_event_type('on_data_processing_failed')
        self.register_event_type('on_data_upload')

    def _data2bytes(self, data, header=None, fmt="%.5f"):
        """ Takes numpy array and returns it as bytes. """
        with io.BytesIO() as bio:
            if header:
                # header = header.encode('utf-8')
                np.savetxt(bio, data, delimiter=',', fmt=fmt, encoding='utf-8', header=header, comments='')
            else:
                np.savetxt(bio, data, delimiter=',', fmt=fmt, encoding='utf-8')
        
            b = bio.getvalue()
        return b

    # ## Data Collection ## #
    def clear_data_collection(self):
        """ Clear data. """
        self._data.clear()
        self._data_email.clear()
        self.is_invalid = False
        self.is_data_sent = False
        self.is_data_saved = False
    
    def new_data_collection(self, user_id):
        """ Start new collection. """
        self._user_id = user_id
        # Start new data collection with device information.
        self._collect_device_data()
    
    def _collect_device_data(self):
        """ Add properties of device to data collection. """
        props = self.get_device_data()
        columns = props.keys()
    
        meta_data = dict()
        meta_data['table'] = 'device'
        meta_data['id'] = create_device_identifier()
        meta_data['time'] = time.time()
    
        # Data for storage and upload.
        data = np.array([props[k] for k in columns]).reshape((1, len(columns)))
        self.add_data(columns, data, meta_data, fmt='%s')
    
        # Data for e-mail.
        meta_data_email = meta_data.copy()
        self.add_data_email(props, meta_data_email)
    
    def get_device_data(self):
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
    
    def add_user_data(self, age="", gender="", gaming_experience=-1):
        """ Create a dataset to identify the user when uploading to server.
        
        :param age: Age-group of user.
        :type age: str
        :param gender: code for user's gender identification.
        :type gender: str
        :param gaming_experience: How much does the user play mobile games?
        :type: int
        """
        meta_data = dict()
        meta_data['table'] = 'user'
        meta_data['user'] = self._user_id
        meta_data['task'] = self.app.settings.current_task
        meta_data['time'] = time.time()
        columns = ['id', 'device_id', 'age_group', 'gender', 'gaming_exp']
        if gaming_experience < 0:
            gaming_experience = ""  # This will translate to null in dataframe when read from csv.
        data = np.array([self._user_id, create_device_identifier(), age, gender, gaming_experience])
        data = data.reshape((1, len(columns)))
        
        self.add_data(columns, data, meta_data, fmt='%s')
        # Data for e-mail.
        self.add_data_email([columns] + [data], meta_data.copy())
        
    def add_data(self, columns, data, meta_data, fmt='%s'):
        """ Adds a data set to current collection.
        
        :param columns:
        :type columns: list[str]
        :param data: numpy.ndarray
        :param meta_data: Descriptors of data, e.g. table, time.
        :type meta_data: dict
        :param fmt: Format to use for data.
        :type fmt: str
        :return: None
        """
        header = ','.join(columns)
        meta_data['data'] = self._data2bytes(data, header=header, fmt=fmt)
        self._data.append(meta_data)

    def add_data_email(self, data, meta_data):
        meta_data['data'] = pickle.dumps(data)
        self._data_email.append(meta_data)
    
    # ## Data Local Storage ## #
    def get_storage_path(self):
        """ Return path we want to save data to.
        This returns an app specific path in external storage that we don't need special permission to use and that gets
        removed with app uninstall.
        """
        if platform == 'android':
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            # This should work even if there's no external storage.
            dest = activity.getExternalFilesDir(None).getAbsolutePath()
            dest = Path(dest)
            # Alternative storage paths that would need permission management.
            # dest = Path(plyer.storagepath.get_external_storage_dir()) / self.app.name
            # dest = Path(plyer.storagepath.get_documents_dir()) / self.app.name
        else:
            dest = Path(self.app.user_data_dir)
            # dest = dest.resolve()  # Resolve any symlinks.
        return dest

    def _create_subfolder(self, subpath):
        """ Create a user folder inside storage_path.

        :param subpath: Path relative to get_storage_path()'s return value.
        :type subpath: Union[str,pathlib.Path]
        """
        storage_path = self.get_storage_path()
        destination = storage_path / subpath
        if not destination.exists():
            destination.mkdir(parents=True, exist_ok=True)  # Assume this works and we have permissions.
        
    def _remove_user_folders(self, user_id):
        """ Removes all of user's locally stored data. """
        storage_path = self.get_storage_path()
        # Look for all sub-folders of user in all studies.
        user_folders = storage_path.rglob(user_id)
        for folder in user_folders:
            shutil.rmtree(folder, ignore_errors=True)

    def compile_filename(self, meta_data):
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

    def write_file(self, path, content):
        """ Save content to path.

        :param path: Path to file.
        :type path: pathlib.Path
        :param content: Content to write to file.
        :type content: Union[bytes,str]

        :return: Whether writing to file was successful.
        :rtype: bool
        """
        if isinstance(content, bytes):
            path.write_bytes(content)
            return True
        elif isinstance(content, str):
            path.write_text(content)
            return True
        else:
            self.dispatch('on_data_processing_failed',
                          _("Unable to write to file:\n{}\nUnknown data format.").format(path.name))
        return False

    def write_data_to_files(self):
        """ Writes content of data to disk. """
        success = True
        storage = self.get_storage_path()
        for d in self._data:
            try:
                if d['table'] in ['session', 'trials', 'user']:
                    sub_folder = Path(d['task'].replace(" ", "_")) / d['user']
                    self._create_subfolder(sub_folder)
                    dir_path = storage / sub_folder
                else:
                    dir_path = storage
            except KeyError:
                success = False
                self.dispatch('on_data_processing_failed', _("KeyError in Meta Data."))
                continue
        
            file_name = self.compile_filename(d)
            file_path = dir_path / file_name
            # Because external storage resides on a physical volume that the user might be able to remove,
            # verify that the volume is accessible before trying to write app-specific data to external storage.
            try:
                success = self.write_file(file_path, d['data'])
            except KeyError:
                success = False
                self.dispatch('on_data_processing_failed', _("Data missing.\nFailed to write\n{}.").format(file_name))
        self.is_data_saved = success

    # ## Data Upload ## #
    def _get_dash_post(self):
        """ Build a json string from collected data to post to a dash update component.

        :return: post request json string.
        """
        file_names = list()
        last_modified = list()
        data = list()
    
        for d in self._data:
            # Build fake file name.
            name = self.compile_filename(d)
            file_names.append(name)
            try:
                last_modified.append(d['time'])
                data_b64 = base64.b64encode(d['data'])
            except KeyError:
                self.dispatch('on_data_processing_failed', _("KeyError in Meta Data."))
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
    
    def _get_response(self, server, data):
        """ Upload collected data to server. """
        try:
            response = requests.post(server, json=data)
            returned_txt = response.text
        except (requests.exceptions.InvalidSchema, requests.exceptions.ConnectionError):
            returned_txt = _("ERROR: Server not reachable:") + f"\n{server}"
        except Exception:
            returned_txt = _("ERROR: There was an error processing the upload.")
        return returned_txt

    def _parse_response(self, response):
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
        msg = ""
        try:
            msg = res_json['response']['output-data-upload']['children'][0]['props']['children']
        except (KeyError, IndexError):
            pass
        
        try:
            msg = res_json['response']['props']['children'][0]['props']['children']
        except (KeyError, IndexError):
            pass
        msg = msg or _("ERROR: There was an unexpected error during upload.")
        return msg

    def _get_uploaded_status(self, response):
        """ Determine success of upload.

        :param response: Message received from server.
        :type response: str
        :return: Was the upload successful?
        :rtype: bool
        """
        try:
            if response.lower().startswith('error')  \
                or response.lower().startswith(_('ERROR').lower()) \
                    or _('ERROR').lower() in response.lower():
                return False
        except AttributeError:
            pass
        return True
    
    def upload_data(self, route):
        """ Upload collected data to server. """
        # Since ask_permission first checks for permission and, if present, doesn't trigger the callback, this does
        # not result in an endless loop.
        permission = ask_permission(Permission.INTERNET, callback=self._on_internet_permission_request)
        if permission:
            res = self._get_response(route, self._get_dash_post())
            res_msg = self._parse_response(res)
            status = self._get_uploaded_status(res_msg)
            self.is_data_sent = status
            # Inform any listeners about the result.
            self.dispatch('on_data_upload', status, res_msg)

    def _on_internet_permission_request(self, permissions, grant_results):
        """ Callback receiving results of permission request.
        :type permissions: List[str]
        :type grant_results: List[bool]
        """
        try:
            idx = permissions.index(Permission.INTERNET)
            # Check if internet permission was granted.
            permission_granted = grant_results[idx]
        except ValueError:
            # Request was interrupted and we didn't get request result.
            permission_granted = False
        # Act on permission request result.
        if permission_granted:
            self.upload_data(self.app.get_upload_route())
        else:
            # Toast with info on failed permit
            plyer.notification.notify(message=_("Permission to access Internet denied."), toast=True)
    
    def send_email(self, recipient):
        """ Send the data via e-mail. """
        
        subject = f"New {self.app.get_application_name()} Data Set"
        disclaimer = _("Disclaimer:\n"
                       "By submitting this e-mail you agree to the data processing and evaluation for the purpose of "
                       "this scientific investigation and any other purpose that an interested third party might have."
                       "\n"
                       "The research data below will be copied from the received e-mail and will be made publicly "
                       "available on the Internet under a CC-BY-SA license, as stated in the privacy policy you gave "
                       "your consent to before participating in the study. The e-mail itself will be deleted within "
                       "10 days from our e-mail service to separate the sender's address from the research data "
                       "for the purpose of anonymization. The research data itself does not contain personal "
                       "or sensitive information that could be used to identify you.\n")
    
        text = "\n\n### Data ###\n\n"
        for d in self._data_email:
            text += "\n".join(k + ": " + str(v) for k, v in d.items())
            text += "\n\n"
    
        create_chooser = True
        plyer.email.send(recipient=recipient, subject=subject, text=disclaimer + text, create_chooser=create_chooser)

    # ## Events ## #
    def on_is_data_saved(self, instance, value):
        pass
    
    def on_is_data_sent(self, instance, value):
        pass

    def on_data_processing_failed(self, *args):
        pass

    def on_data_upload(self, *args):
        pass
