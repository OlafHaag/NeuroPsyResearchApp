# Built-in imports
import base64
from datetime import datetime
import io
import json
from pathlib import Path
import pickle
import time

# Third party imports
from kivy.app import App
from kivy.metrics import Metrics
from kivy.properties import BooleanProperty
from kivy.uix.widget import Widget
from kivy.utils import platform
import numpy as np
from plyer import storagepath
from plyer import email
import requests

# Own module imports
from .config import time_fmt
from .i18n import _
from .utility import (create_device_identifier,
                      get_screensize,
                      ask_permission,
                      )

# Conditional imports
if platform == 'android':
    from android.permissions import Permission


class DataManager(Widget):  # Inherit from Widget so we can dispatch events.
    """ Manager for data collection and saving or sending them. """
    data_saved = BooleanProperty(False)  # Did we save the current data?
    data_sent = BooleanProperty(False)  # Did we sent the current data?
    
    def __init__(self, **kwargs):
        super(DataManager, self).__init__(**kwargs)
        self.app = App.get_running_app()
        # Android permissions.
        self.write_permit = True  # Set to true as default for platforms other than android.
        self.internet_permit = True
        # Containers for data.
        self._data = list()  # type: list[dict]
        self._data_email = list()
        # For which user to collect data. Set after given consent.
        self._user_id = ''
        # Events to fire.
        self.register_event_type('on_data_processing_failed')
        self.register_event_type('on_data_upload')

    def _data2bytes(self, data, header=None, fmt="%.5f"):
        """ Takes numpy array and returns it as bytes. """
        bio = io.BytesIO()
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
        self.data_sent = False
        self.data_saved = False
    
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
        """ Return writable path.
        If it does not exist on android, make directory.
        """
        if platform == 'android':
            # dest = Path(storagepath.get_documents_dir())
            dest = Path(storagepath.get_external_storage_dir()) / self.app.name
            # We may need to ask permission to write to the external storage. Permission could have been revoked.
            self.write_permit = ask_permission(Permission.WRITE_EXTERNAL_STORAGE)
        
            if not dest.exists() and self.write_permit:
                # Make sure the path exists.
                dest.mkdir(parents=True, exist_ok=True)
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
        if not destination.exists() and self.write_permit:
            destination.mkdir(parents=True, exist_ok=True)  # Assume this works and we have permissions.

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
        if self.write_permit:
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
                if d['table'] in ['session', 'trials']:
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
            try:
                success = self.write_file(file_path, d['data'])
            except KeyError:
                success = False
                self.dispatch('on_data_processing_failed', _("Data missing.\nFailed to write\n{}.").format(file_name))
        self.data_saved = success

    # ## Data Upload ## #
    def _get_user_data(self, user_id):
        """ Create a dataset to identify the user when uploading to server. """
        d = dict()
        d['table'] = 'user'
        d['time'] = time.time()
        header = 'id,device_id'
        data = np.array([user_id, create_device_identifier()])
        d['data'] = self._data2bytes(data.reshape((1, len(data))), header=header, fmt='%s')
        return d

    def _get_dash_post(self, data_collection):
        """ Build a json string to post to a dash update component.

        :return: post request json string.
        """
        file_names = list()
        last_modified = list()
        data = list()
    
        # When writing data to files, we create a folder with the user's identifier.
        # We need to add user identification to the post as well.
        user_data = self._get_user_data(self._user_id)
        data_collection.insert(1, user_data)  # After device data, before session.
    
        for d in data_collection:
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
        # ToDo: upload error handling.
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
        try:
            msg = res_json['response']['props']['children'][0]['props']['children']
        except (KeyError, IndexError):
            msg = _("Not the usual error response.")
        return msg

    def _get_uploaded_status(self, response):
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
    
    def upload_data(self, route):
        """ Upload collected data to server. """
        res = self._get_response(route, self._get_dash_post(self._data))
        res_msg = self._parse_response(res)
        status = self._get_uploaded_status(res_msg)
        self.data_sent = status
        # Inform any listeners about the result.
        self.dispatch('on_data_upload', status, res_msg)

    def send_email(self, recipient):
        """ Send the data via e-mail. """
        
        subject = f"New {self.app.get_application_name()} Data Set"
        disclaimer = _("Disclaimer:\n"
                       "By submitting this e-mail you agree to the data processing and evaluation for the purpose of "
                       "this scientific investigation and any other purpose that an interested party might have.\n"
                       "The data below will be copied and saved from the received e-mail and will be made publicly "
                       "available on the internet under a CC-BY-SA license as stated in the consent you gave before "
                       "participating in the study. The email itself will be deleted within 3 days to separate "
                       "the sender address from the data for the purpose of anonymisation.\n")
    
        text = "### Data ###\n\n"
        for d in self._data_email:
            text += "\n".join(k + ": " + str(v) for k, v in d.items())
            text += "\n\n"
    
        create_chooser = True
        email.send(recipient=recipient, subject=subject, text=disclaimer + text, create_chooser=create_chooser)

    # ## Events ## #
    def on_data_saved(self, instance, value):
        pass
    
    def on_data_sent(self, instance, value):
        pass

    def on_data_processing_failed(self, *args):
        pass

    def on_data_upload(self, *args):
        pass
