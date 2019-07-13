"""
Substantial portions of ScreenWebView class copyright (c) 2016 suchyDev (MIT License)
with code by Micheal Hines.

MIT License

Copyright (c) 2019 Olaf Haag

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
# """Research app to study uncontrolled manifold and optimal feedback control paradigms."""

import io
import json
import pickle
import datetime
import time
from pathlib import Path
from hashlib import md5
from uuid import uuid4
import base64

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.properties import ConfigParserProperty
from kivy.animation import Animation
from kivy.clock import Clock, mainthread
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from kivy.lang import global_idmap

from plyer import vibrator
from plyer import uniqueid
from plyer import storagepath
from plyer import notification
from plyer import email

from settingsjson import settings_circle_task_json
from i18n import _, list_languages, change_language_to, current_language, language_code_to_translation
from i18n.settings import Settings

import requests
import numpy as np

from config import WEBSERVER

if platform == 'android':
    from android.permissions import request_permissions, check_permission, Permission
    from android.runnable import run_on_ui_thread
    from jnius import autoclass

    WebView = autoclass('android.webkit.WebView')
    CookieManager = autoclass('android.webkit.CookieManager')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
else:
    def run_on_ui_thread(func):
        """ dummy wrapper for desktop compatibility """
        return func
    
if platform == 'win':
    import subprocess

# i18n
LANGUAGE_CODE = "language"
LANGUAGE_SECTION = "Localization"
global_idmap['_'] = _


class ScreenHome(Screen):
    """ Display that gives general information. """
    # As a workaround for internationalization to work set actual message in on_pre_enter().
    home_msg = StringProperty(_('Initiating...'))
    
    def on_pre_enter(self, *args):
        App.get_running_app().settings.reset_current()
        self.home_msg = _('Welcome!')  # ToDo: General Information
        
    def on_leave(self, *args):
        """ Reset data collection each time a new task is started. """
        app = App.get_running_app()
        app.data_upload.clear()
        app.data_email.clear()


class ScreenOutro(Screen):
    """ Display at the end of a session. """
    settings = ObjectProperty()
    outro_msg = StringProperty(_("Initiating..."))
    
    def on_pre_enter(self, *args):
        self.outro_msg = _('[color=ff00ff][b]Thank you[/b][/color] for participating!') + "\n\n"  # Workaround for i18n.
        if self.settings.is_local_storage_enabled:
            dest = App.get_running_app().get_data_path()
            self.outro_msg += _("Files were {}saved to [i]{}[/i].").format('' if dest.exists() else _('[b]not[/b]')
                                                                           + ' ', dest)
        else:
            self.outro_msg += _("Results were [b]not[/b] locally stored as files.\n"
                                "You can enable this in the settings.")
            
        app = App.get_running_app()
        app.upload_btn_enabled = self.settings.is_upload_enabled


class ScreenWebView(Screen):
    """ Currently out of order. Crashes on create_webview!
    Shall display the analysed data after a session for individual feedback.
    """
    view_cached = None
    webview = None
    wvc = None
    webview_lock = False  # simple lock to avoid launching two webviews.
    url = StringProperty(WEBSERVER)
    
    def __init__(self, **kwargs):
        super(ScreenWebView, self).__init__(**kwargs)
        self.register_event_type('on_quit_screen')
        
    def on_enter(self, *args):
        super(ScreenWebView, self).on_enter(*args)
        
        self.url = App.get_running_app().settings.server_uri
        
        if platform == 'android':
            # On android create webview for website.
            self.ids['info_label'].text = _("Please wait\nAttaching WebView")
            self.webview_lock = True
            Clock.schedule_once(self.create_webview, 0)  # Call after the next frame.
        else:
            # On desktop just launch web browser.
            self.ids['info_label'].text = _("Please wait\nLaunching browser")
            import webbrowser
            webbrowser.open_new(self.url)
            
            # Only if we would want to manually upload data files.
            # if platform == 'win':
            #    subprocess.Popen(r'explorer "{}"'.format(App.get_running_app().get_data_path()))

    @run_on_ui_thread
    def key_back_handler(self, *args):
        if self.webview:
            Clock.schedule_once(self.detach_webview, 0)  # Call after the next frame.
    
    @mainthread
    def quit_screen(self, *args):
        self.dispatch('on_quit_screen')

    def on_quit_screen(self, *args):
        pass
    
    @run_on_ui_thread
    def create_webview(self, *args):  # FixMe: Crash - no attribute f2
        if self.view_cached is None:
            self.view_cached = activity.currentFocus
        self.webview = WebView(activity)

        cookie_manager = CookieManager.getInstance()
        cookie_manager.removeAllCookie()

        settings = self.webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setUseWideViewPort(True)  # enables viewport html meta tags
        settings.setLoadWithOverviewMode(True)  # uses viewport
        settings.setSupportZoom(True)  # enables zoom
        settings.setBuiltInZoomControls(True)  # enables zoom controls
        settings.setSavePassword(False)
        settings.setSaveFormData(False)

        self.wvc = WebViewClient()
        self.webview.setWebViewClient(self.wvc)
        activity.setContentView(self.webview)
        self.webview.loadUrl(self.url)
        self.webview_lock = False
        
    @run_on_ui_thread
    def detach_webview(self, *args):
        if not self.webview_lock:
            if self.webview:
                self.webview.loadUrl("about:blank")
                self.webview.clearHistory()  # refer to android webview api
                self.webview.clearCache(True)
                self.webview.clearFormData()
                self.webview.freeMemory()
                # self.webview.pauseTimers()
                activity.setContentView(self.view_cached)
            Clock.schedule_once(self.quit_screen, 0)  # Call after the next frame.
            
            
class ScreenInstructCircleTask(Screen):
    """ Display that tells the user what to in next task. """
    settings = ObjectProperty()
    instruction_msg = StringProperty(_("Initiating..."))

    def __init__(self, **kwargs):
        super(ScreenInstructCircleTask, self).__init__(**kwargs)
        self.df_unconstraint_msg = _("Initiating...")
        self.df_constraint_msg = _("Initiating...")
        
    def on_pre_enter(self, *args):
        self.settings.next_block()
        self.update_messages()
        self.set_instruction_msg()
    
    def update_messages(self):
        n_trials_msg = _("There are a total of {} trials in this block.").format(self.settings.circle_task.n_trials)
        n_tasks = int(self.settings.circle_task.constraint) + 1
        # ToDo: ngettext for plurals
        task_suffix = self.settings.circle_task.constraint * _("s")
        n_tasks_msg = _("You have {} task{} in this block.").format(n_tasks, task_suffix) + "\n\n"
        time_limit_msg = _("A trial ends when the outer [color=ff00ff]purple ring[/color] reaches 100% (circle closes)"
                           " and the countdown reaches 0.\nShortly thereafter you will be prompted to get ready for "
                           "the next trial.") + "\n\n"
        task1_msg = _("Use the [b]2 sliders[/b] to match the size of the [b]white disk[/b] to the "
                      "[color=008000]green ring[/color].") + "\n\n"
        task2_msg = _("Concurrently bring the [color=3f84f2]blue arch[/color] to the [color=3f84f2]blue disc[/color] "
                      "by using one of the sliders. It will be the same slider during the block.") + "\n\n"
        self.df_unconstraint_msg = n_tasks_msg + task1_msg + time_limit_msg + n_trials_msg
        self.df_constraint_msg = n_tasks_msg + task1_msg + task2_msg + time_limit_msg + n_trials_msg
            
    def set_instruction_msg(self):
        """ Change displayed text on instruction screen. """
        if self.settings.circle_task.constraint:
            self.instruction_msg = self.df_constraint_msg
        else:
            self.instruction_msg = self.df_unconstraint_msg
            

class ScreenCircleTask(Screen):
    """ This class handles all the logic for the circle size matching task. """
    settings = ObjectProperty()
    progress = StringProperty(_("Trial: ") + "0/0")
    is_constrained = BooleanProperty(False)  # Workaround, since self.settings.constraint doesn't seem to exist at init.
    
    def __init__(self, **kwargs):
        super(ScreenCircleTask, self).__init__(**kwargs)
        # Procedure related.
        self.register_event_type('on_task_stopped')
        self.schedule = None
        # Control related.
        self.target2_switch = False  # Which slider is controlling the second target.
        self.df1_touch = None
        self.df2_touch = None
        # Feedback related.
        self.sound_start = None
        self.sound_stop = None
        # Data collection related.
        self.data = None  # For numerical data.
        self.meta_data = dict()  # For context of numerical data acquisition, e.g. treatment/condition.
    
    def on_kv_post(self, base_widget):
        """ Bind events. """
        self.count_down.bind(on_count_down_finished=lambda obj: self.trial_finished())
        self.ids.df1.bind(on_grab=self.slider_grab)
        self.ids.df2.bind(on_grab=self.slider_grab)
    
    def on_pre_enter(self, *args):
        """ Setup this run of the task and initiate start. """
        self.is_constrained = self.settings.circle_task.constraint
        # df that is constrained is randomly chosen.
        self.target2_switch = np.random.choice([True, False])
        # Set visual indicator for which df is constrained.
        self.ids.df2.value_track = self.is_constrained and self.target2_switch
        self.ids.df1.value_track = self.is_constrained and not self.target2_switch
        
        self.data = np.zeros((self.settings.circle_task.n_trials, 2))
        # FixMe: Not loading sound files on Windows. (Unable to find a loader)
        self.sound_start = SoundLoader.load('res/start.ogg')
        self.sound_stop = SoundLoader.load('res/stop.ogg')
        self.count_down.start_count = self.settings.circle_task.trial_duration
        self.count_down.set_label(_("PREPARE"))
        self.start_task()
    
    # FixMe: only last touch ungrabbed, ungrab all lingering touches!
    def slider_grab(self, instance, touch):
        """ Set reference to touch event for sliders. """
        if instance == self.ids.df1:
            self.df1_touch = touch
        elif instance == self.ids.df2:
            self.df2_touch = touch
    
    def disable_sliders(self):
        self.ids.df2.disabled = True
        self.ids.df1.disabled = True
        # Release slider grabs, if any.
        if self.df1_touch:
            self.df1_touch.ungrab(self.ids.df1)
            self.df1_touch = None
        if self.df2_touch:
            self.df2_touch.ungrab(self.ids.df2)
            self.df2_touch = None
    
    def enable_sliders(self):
        self.ids.df2.disabled = False
        self.ids.df1.disabled = False
    
    def reset_sliders(self):
        """ Set sliders to initial position. """
        self.ids.df1.value = self.ids.df1.max * 0.1
        self.ids.df2.value = self.ids.df2.max * 0.1
    
    def get_progress(self):
        """ Return a string for the number of trials out of total that are already done. """
        progress = _("Trial: ") + f"{self.settings.current_trial}/{self.settings.circle_task.n_trials}"
        return progress
        
    def start_task(self):
        """ Start the time interval for the repetition of trials. """
        self.disable_sliders()
        # Repeatedly start trials each inter-trial-interval.
        iti = self.settings.circle_task.warm_up + self.settings.circle_task.trial_duration\
              + self.settings.circle_task.cool_down
        self.progress = self.get_progress()
        self.schedule = Clock.schedule_interval(self.get_ready, iti)
    
    def get_ready(self, *args):
        """ Prepare the next trial or stop if the total amount of trials are reached. """
        if self.settings.current_trial == self.settings.circle_task.n_trials:
            self.stop_task()
        else:
            self.settings.current_trial += 1
            self.progress = self.get_progress()
            self.reset_sliders()
            self.count_down.set_label(_("GET READY"))
            Clock.schedule_once(lambda dt: self.start_trial(), self.settings.circle_task.warm_up)
    
    def vibrate(self, t=0.1):
        # FixMe: bug in plyer vibrate - argument mismatch
        # try:
        #     if vibrator.exists():
        #         vibrator.vibrate(time=t)
        # except (NotImplementedError, ModuleNotFoundError):
        #     pass
        pass

    def start_trial(self):
        """ Start the trial. """
        if self.sound_start:
            self.sound_start.play()
        self.enable_sliders()
        self.vibrate()
        self.count_down.start()
    
    def trial_finished(self):
        """ Callback for when a trial ends. Collect data. """
        if self.sound_stop:
            self.sound_stop.play()
        self.disable_sliders()
        self.count_down.set_label(_("FINISHED"))
        self.vibrate()
        # Record data for current trial.
        self.data[self.settings.current_trial-1, :] = (self.ids.df1.value_normalized, self.ids.df2.value_normalized)
    
    def stop_task(self, interrupt=False):
        """ Stop time interval that starts new trials.
        When the task wasn't cancelled start data processing.
        """
        # Unschedule trials.
        if self.schedule:
            self.schedule.cancel()
            self.schedule = None
        self.reset_sliders()
        self.release_audio()
        if not interrupt:
            # Scale normalized data to 0-100.
            self.data *= 100
            self.collect_meta_data()
            
            if self.settings.is_local_storage_enabled:
                self.write_data()
            if self.settings.is_upload_enabled:
                self.collect_data_upload()
            if self.settings.is_email_enabled:
                self.collect_data_email()
                
            was_last_block = self.settings.current_block == self.settings.circle_task.n_blocks
            self.dispatch('on_task_stopped', was_last_block)
        
    def on_task_stopped(self, was_last_block=False):
        pass
        
    def release_audio(self):
        """ Unload audio sources from memory. """
        for sound in [self.sound_start, self.sound_stop]:
            if sound:
                sound.stop()
                sound.unload()
                sound = None
    
    def collect_meta_data(self):
        """ Collect information about context of data acquisition. """
        constrained_df = 'constrained_df2' if self.target2_switch else 'constrained_df1'

        self.meta_data['device'] = App.get_running_app().create_device_identifier()
        self.meta_data['user'] = self.settings.user
        self.meta_data['task'] = 'CT'  # Short for Circle Task.
        self.meta_data['block'] = self.settings.current_block
        self.meta_data['type'] = constrained_df if self.is_constrained else "unconstrained"
        self.meta_data['time_iso'] = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.meta_data['time'] = time.time()
        self.meta_data['columns'] = ['df1', 'df2']
        self.meta_data['hash'] = md5(self.data).hexdigest()
    
    # ToDo: save screen size/resolution, initial circle/ring size, slider size and slider value to file
    def collect_data_upload(self):
        """ Add data to be uploaded to a server. """
        d = self.meta_data.copy()
        d['data'] = self.data
        app = App.get_running_app()
        app.data_upload.append(d)
    
    def collect_data_email(self):
        """ Add data to be sent via e-mail. """
        d = self.meta_data.copy()
        d['data'] = pickle.dumps(self.data)
        
        app = App.get_running_app()
        app.data_email.append(d)
        
    def write_data(self):
        """ Save endpoint values in app.user_data_dir with unique file name. """
        app = App.get_running_app()
        file_name = app.compile_filename(self.meta_data)
        dest_path = app.get_data_path()
        if self.data is not None and app.write_permit:
            np.savetxt(dest_path / file_name, self.data, fmt='%10.5f', delimiter=',',
                       header=','.join(self.meta_data['columns']), comments='')


class ScaleSlider(Slider):
    def __init__(self, **kwargs):
        self.register_event_type('on_grab')
        super(ScaleSlider, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_grab', touch)
        return super(ScaleSlider, self).on_touch_down(touch)
    
    def on_grab(self, touch):
        pass
        
        
class CountDownLbl(Label):
    start_count = NumericProperty(3)  # Initial duration, replaced with CircleGame.trial_duration by ScreenCircleTask class.
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super(CountDownLbl, self).__init__(**kwargs)
        self.register_event_type('on_count_down_finished')
        self.anim = None

    def start(self):
        self.angle = 0
        Animation.cancel_all(self)
        self.anim = Animation(angle=360,  duration=self.start_count)
        self.anim.bind(on_complete=lambda animation, obj: self.finished())
        self.anim.start(self)
    
    def finished(self):
        self.dispatch('on_count_down_finished')
        
    def on_count_down_finished(self):
        pass
        
    def set_label(self, msg):
        self.text = msg


class UCMManager(ScreenManager):
    settings = ObjectProperty()
    
    def __init__(self, **kwargs):
        super(UCMManager, self).__init__(**kwargs)
        self.n_home_esc = 0  # Counter on how many times the back button was pressed on home screen.
        self.task_instructions = {'Circle Task': 'Instructions CT'}
        
    def on_kv_post(self, base_widget):
        Window.bind(on_keyboard=self.key_input)
        self.get_screen('Circle Task').bind(on_task_stopped=lambda obj, last: self.task_finished(last))
        #self.get_screen('Webview').bind(on_quit_screen=lambda obj: self.go_home())

    def on_current(self, instance, value):
        """ When switching screens reset counter on back button presses on home screen. """
        screen = self.get_screen(value)
        if screen != self.current_screen:
            self.n_home_esc = 0
        super(UCMManager, self).on_current(instance, value)
    
    def key_input(self, window, key, scancode, codepoint, modifier):
        """ Handle escape key / back button presses. """
        if key == 27:
            if self.current == 'Home':
                # When on home screen we want to be able to quit the app after 2 presses.
                self.n_home_esc += 1
                if self.n_home_esc == 1:
                    notification.notify(message=_("Press again to quit."), toast=True)
                if self.n_home_esc > 1:
                    self.quit()
            elif self.current == 'Settings':
                # Never gets called, screen already changed to 'Home' through app.close_settings() on esc.
                App.get_running_app().close_settings()
            # If we are in a task, stop that task.
            elif self.current in ['Circle Task']:
                self.get_screen(self.current).stop_task(interrupt=True)
                self.go_home()
            elif self.current == 'Webview':
                self.get_screen('Webview').key_back_handler()
                self.go_home()
            else:
                self.go_home()
            return True  # override the default behaviour
        else:  # the key now does nothing
            return False
            
    def go_home(self):
        self.transition.direction = 'down'
        self.current = 'Home'
        
    def task_finished(self, was_last_block=False):
        # Outro after last block.
        if was_last_block:
            self.current = 'Outro'
        else:
            self.transition.direction = 'down'
            self.current = self.task_instructions[self.settings.task]
    
    def quit(self, *args):
        App.get_running_app().stop()
    
    
class SettingsContainer(Widget):
    """ For now put all the settings for each task in here for simplicity.
        When (or if) more tasks get implemented and the need arises to separate them, come up with a better,
        modular solution.
    """
    # General properties.
    #language = ConfigParserProperty('en', 'Localization', 'language', 'app', val_type=str)
    task = ConfigParserProperty('Circle Task', 'General', 'task', 'app', val_type=str)
    user = ConfigParserProperty('test', 'UserData', 'unique_id', 'app', val_type=str)
    # Data Collection.
    is_local_storage_enabled = ConfigParserProperty('0', 'DataCollection', 'is_local_storage_enabled', 'app',
                                                    val_type=int)  # Converts string to int.
    is_upload_enabled = ConfigParserProperty('1', 'DataCollection', 'is_upload_enabled', 'app', val_type=int)
    server_uri = ConfigParserProperty(WEBSERVER, 'DataCollection', 'webserver', 'app', val_type=str)
    is_email_enabled = ConfigParserProperty('0', 'DataCollection', 'is_email_enabled', 'app', val_type=int)
    email_recipient = ConfigParserProperty('', 'DataCollection', 'email_recipient', 'app', val_type=str)
    
    # Properties that change over the course of all tasks and are not set by config.
    current_trial = NumericProperty(0)
    current_block = NumericProperty(0)
    
    def get_settings_widget(self, panel_name, key):
        """ Helper function to get a widget from a SettingsPanel that contains a config value. """
        app = App.get_running_app()
        panels = app._app_settings.interface.content.panels
        gen_panel = [k for k, v in panels.items() if v.title == panel_name][0]
        widgets = panels[gen_panel].children
        for w in widgets:
            try:
                if w.key == key:
                    return w.children[0].children[0].children[0]
            except AttributeError:
                pass
        return None
        
    def on_is_local_storage_enabled(self, instance, value):
        """ We need to ask for write permission before trying to write, otherwise we lose data.
        There's no callback for permissions granted yet.
        """
        if value:
            app = App.get_running_app()
            app.ask_write_permission(5)
            if not app.write_permit:
                self.is_local_storage_enabled = 0
                # Hack to change the visual switch after value was set. ConfigParserProperty doesn't work here. (1.11.0)
                switch = self.get_settings_widget('General', 'is_local_storage_enabled')
                if switch:
                    switch.active = self.is_local_storage_enabled
    
    # Circle Task properties.
    class CircleTask(Widget):
        n_trials = ConfigParserProperty('20', 'CircleTask', 'n_trials', 'app', val_type=int,
                                        verify=lambda x: x > 0, errorvalue=20)
        n_blocks = ConfigParserProperty('3', 'CircleTask', 'n_blocks', 'app', val_type=int,
                                        verify=lambda x: x > 0, errorvalue=3)
        constrained_block = ConfigParserProperty('3', 'CircleTask', 'constrained_block', 'app', val_type=int)
        warm_up = ConfigParserProperty('1.0', 'CircleTask', 'warm_up_time', 'app', val_type=float,
                                       verify=lambda x: x > 0.0, errorvalue=1.0)
        trial_duration = ConfigParserProperty('1.0', 'CircleTask', 'trial_duration', 'app', val_type=float,
                                              verify=lambda x: x > 0.0, errorvalue=1.0)
        cool_down = ConfigParserProperty('0.5', 'CircleTask', 'cool_down_time', 'app', val_type=float,
                                         verify=lambda x: x > 0.0, errorvalue=0.5)
        
        def __init__(self, **kwargs):
            super(SettingsContainer.CircleTask, self).__init__(**kwargs)
            self.constraint = False
        
        def set_constraint_setting(self, current_block):
            self.constraint = current_block == self.constrained_block
    
    def __init__(self, **kwargs):
        super(SettingsContainer, self).__init__(**kwargs)
        self.circle_task = self.CircleTask()
        self.reset_current()
    
    def reset_current(self):
        self.current_block = 0
        self.current_trial = 0
    
    def next_block(self):
        self.current_trial = 0
        self.current_block += 1
    
    def on_current_trial(self, instance, value):
        """ Bound to change in current trial. """
        pass
    
    def on_current_block(self, instance, value):
        """ Bound to change in current block property. """
        if self.task == 'Circle Task':
            self.circle_task.set_constraint_setting(value)


class UncontrolledManifoldApp(App):
    manager = ObjectProperty(None, allownone=True)
    upload_btn_enabled = BooleanProperty(True)
    
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
                                data=self.general_settings_json)
        settings.add_json_panel('Circle Task Settings',
                                self.config,
                                data=settings_circle_task_json)

    @property
    def general_settings_json(self):
        """The settings specification as JSON string.
        :rtype: str
        :return: a JSON string
        """
        settings = [
            {'type': 'optionmapping',
             'title': _("Language"),
             'desc': _("Display language for user instructions."),
             'section': LANGUAGE_SECTION,
             'key': LANGUAGE_CODE,
             'options': {code: language_code_to_translation(code)
                         for code in list_languages()}},
            {'type': 'title',
             'title': 'User Data'},
            {'type': 'string',
             'title': 'Unique Identifier',
             'desc': 'Anonymous identifier for the current user.',
             'section': 'UserData',
             'key': 'unique_id'},
            {'type': 'title',
             'title': 'Task'},
            {'type': 'options',
             'title': _('Current Task'),
             'desc': 'Which task should be run.',
             'section': 'General',
             'key': 'task',
             'options': ['Circle Task']},
            {'type': 'title',
             'title': 'Data Collection'},
            {'type': 'bool',
             'title': _('Local Storage'),
             'desc': _('Save data locally on device.'),
             'section': 'DataCollection',
             'key': 'is_local_storage_enabled'},
            {'type': 'bool',
             'title': _('Upload Data'),
             'desc': _('Send collected data to server.'),
             'section': 'DataCollection',
             'key': 'is_upload_enabled'},
            {'type': 'string',
             'title': _('Upload Server'),
             'desc': _('Target server address to upload data to.'),
             'section': 'DataCollection',
             'key': 'webserver'},
            {'type': 'bool',
             'title': _('Send E-Mail'),
             'desc': _('Offer to send data via e-mail.'),
             'section': 'DataCollection',
             'key': 'is_email_enabled'},
            {'type': 'string',
             'title': _('E-Mail Recipient'),
             'desc': _('E-mail address to send data to.'),
             'section': 'DataCollection',
             'key': 'email_recipient'},
        ]
        return json.dumps(settings)

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
            #dest = Path(storagepath.get_documents_dir())
            dest = Path(storagepath.get_external_storage_dir()) / App.get_running_app().name
            # We may need to ask permission to write to the external storage. Permission could have been revoked.
            self.ask_write_permission()
            
            if not dest.exists() and self.write_permit:
                # Make sure the path exists.
                dest.mkdir(parents=True, exist_ok=True)
        else:
            app = App.get_running_app()
            dest = Path(app.user_data_dir)
            #dest = dest.resolve()  # Resolve any symlinks.
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

    def upload_data(self):
        """ Upload collected data to server. """
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
    
        # ToDo: error handling after uploading.
        try:
            response = requests.post(self.settings.server_url, json=post_data)
            r_txt = response.text
        except:
            r_txt = 'There was an error processing this file.'
        if 'There was an error processing this file.' not in r_txt:
            self.upload_btn_enabled = False
        else:
            pass
    
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
    
    
if __name__ in ('__main__', '__android__'):
    UncontrolledManifoldApp().run()
