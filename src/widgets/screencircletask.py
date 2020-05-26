import pickle
from datetime import datetime
import time
from hashlib import md5

from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.core.audio import SoundLoader
from kivy.clock import Clock

from kivymd.uix.behaviors import BackgroundColorBehavior

import numpy as np

from . import BaseScreen
from ..config import time_fmt
from ..i18n import _
from ..utility import create_device_identifier, platform

if platform != 'win':
    from plyer import vibrator
else:
    vibrator = None


class ScreenCircleTask(BackgroundColorBehavior, BaseScreen):
    """ This class handles all the logic for the circle size matching task. """
    settings = ObjectProperty()
    progress = StringProperty(_("Trial: ") + "0/0")
    # Workaround, since self.settings.circle_task.constraint doesn't seem to exist at init.
    is_constrained = BooleanProperty(False)
    is_practice = BooleanProperty(True)
    
    def __init__(self, **kwargs):
        super(ScreenCircleTask, self).__init__(**kwargs)
        # Procedure related.
        self.register_event_type('on_task_stopped')
        self.schedule = None
        self.max_trials = 0
        self.max_blocks = 0
        # Control related.
        self.target2_switch = False  # Which slider is controlling the second target.
        self.df1_touch = None
        self.df2_touch = None
        # Save defaults in order to check if sliders have been used at all. Set in on_kv_post.
        self.df1_default = 0.0
        self.df2_default = 0.0
        # Feedback related.
        self.sound_start = None
        self.sound_stop = None
        # Data collection related.
        self.data = None  # For numerical data.
        self.meta_data = dict()  # For context of numerical data acquisition, e.g. treatment/condition.
        self.session_data = list()  # For description of a block if numerical data.
    
    def on_kv_post(self, base_widget):
        """ Bind events. """
        self.count_down.bind(on_count_down_finished=lambda instance: self.trial_finished())
        self.ids.df1.bind(on_grab=self.slider_grab,
                          on_ungrab=self.slider_ungrab)
        self.ids.df2.bind(on_grab=self.slider_grab,
                          on_ungrab=self.slider_ungrab)
        # Save starting positions of sliders.
        self.df1_default = self.ids.df1.value_normalized
        self.df2_default = self.ids.df2.value_normalized
    
    def set_slider_colors(self, slider, status=False):
        """ Set the slider's handle and track colors depending on status.
        
        :param slider: Slider instance.
        :param status: True if colored, False if not.
        """
        if slider.orientation == 'vertical':
            o = 'v'
        else:
            o = 'h'
        slider.value_track = status
        if status:
            slider.cursor_image = f'res/sliderhandle_{o}_on_color.png'
            slider.cursor_disabled_image = f'res/sliderhandle_{o}_off_color.png'
        else:
            slider.cursor_image = f'res/sliderhandle_{o}_on.png'
            slider.cursor_disabled_image = f'res/sliderhandle_{o}_off.png'
            
    def on_pre_enter(self, *args):
        """ Setup this run of the task and initiate start. """
        # Do we do practice trials?
        self.is_practice = bool(self.settings.circle_task.practice_block)
        if self.is_practice:
            self.max_trials = self.settings.circle_task.n_practice_trials
        else:
            self.max_trials = self.settings.circle_task.n_trials
        self.is_constrained = self.settings.circle_task.constraint
        # df that is constrained is randomly chosen.
        self.target2_switch = np.random.choice([True, False])
        # Set visual indicator for which df is constrained.
        df1_colored = self.is_constrained and not self.target2_switch
        df2_colored = self.is_constrained and self.target2_switch
        self.set_slider_colors(self.ids.df1, df1_colored)
        self.set_slider_colors(self.ids.df2, df2_colored)
        # Remind to use sliders.
        self.ids.df1_warning.opacity = 1.0
        self.ids.df2_warning.opacity = 1.0

        # Initiate data container for this block.
        self.data = np.zeros((self.settings.circle_task.n_trials, 2))
        # FixMe: Not loading sound files on Windows. (Unable to find a loader)
        if self.settings.is_sound_enabled:
            self.sound_start = SoundLoader.load('res/start.ogg')
            self.sound_stop = SoundLoader.load('res/stop.ogg')
        self.count_down.start_count = self.settings.circle_task.trial_duration
        self.count_down.set_label(_("PREPARE"))
        self.start_task()
    
    # ToDo: only last touch ungrabbed, ungrab all lingering touches. Doesn't appear to cause problems so far.
    def slider_grab(self, instance, touch):
        """ Set reference to touch event for sliders. """
        if instance == self.ids.df1 and not self.ids.df1.disabled:
            self.df1_touch = touch
            self.ids.df1_warning.opacity = 0.0
        elif instance == self.ids.df2 and not self.ids.df2.disabled:
            self.df2_touch = touch
            self.ids.df2_warning.opacity = 0.0
    
    def slider_ungrab(self, instance, touch):
        """ Disable sliders when they're let go. """
        if (instance == self.ids.df1) and self.df1_touch:
            self.ids.df1.disabled = True
            self.df1_touch.ungrab(self.ids.df1)
            self.df1_touch = None
        elif (instance == self.ids.df2) and self.df2_touch:
            self.ids.df2.disabled = True
            self.df2_touch.ungrab(self.ids.df2)
            self.df2_touch = None
        
    def disable_sliders(self):
        """ Disable sliders regardless of whether they have touch or not. """
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
        progress = _("Trial: ") + f"{self.settings.current_trial}/{self.max_trials}"
        return progress
    
    def start_task(self):
        """ Start the time interval for the repetition of trials. """
        self.disable_sliders()
        # Repeatedly start trials each inter-trial-interval.
        iti = self.settings.circle_task.warm_up + self.settings.circle_task.trial_duration \
              + self.settings.circle_task.cool_down
        self.progress = self.get_progress()
        self.schedule = Clock.schedule_interval(self.get_ready, iti)
    
    def get_ready(self, *args):
        """ Prepare the next trial or stop if the total amount of trials are reached. """
        if self.settings.current_trial == self.max_trials:
            self.stop_task()
        else:
            self.settings.current_trial += 1
            self.progress = self.get_progress()
            self.reset_sliders()
            self.count_down.set_label(_("GET READY"))
            Clock.schedule_once(lambda dt: self.start_trial(), self.settings.circle_task.warm_up)
    
    def vibrate(self, t=0.1):
        if self.settings.is_vibrate_enabled and vibrator:
            try:
                if vibrator.exists():
                    vibrator.vibrate(time=t)
            except (NotImplementedError, ModuleNotFoundError):
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
        self.check_slider_use()
        # Record data for current trial.
        self.data[self.settings.current_trial - 1, :] = (self.ids.df1.value_normalized, self.ids.df2.value_normalized)
        
    def check_slider_use(self):
        """ Checks if the slider values are still at their defaults and displays warning where appropriate."""
        if self.ids.df1.value_normalized == self.df1_default:
            self.ids.df1_warning.opacity = 1.0
        else:
            self.ids.df1_warning.opacity = 0.0
        if self.ids.df2.value_normalized == self.df2_default:
            self.ids.df2_warning.opacity = 1.0
        else:
            self.ids.df2_warning.opacity = 0.0
    
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
            # Check if task was properly done, i.e. values are not all at default.
            if (self.data[:, 0] == self.df1_default).all() and (self.data[:, 1] == self.df2_default).all():
                self.clear_data()
                # Feedback and reset/abort.
                msg = _("Please read instructions again carefully and perform task accordingly.\nAborting Session...")
                self.manager.dispatch('on_warning', text=msg)
                # These are not the data you're looking for...
                app = App.get_running_app()
                app.data_mgr.data_sent = True  # Hack to disable upload button.
                # Abort session.
                self.dispatch('on_task_stopped', True)
                return
            
            was_last_block = self.settings.current_block == (self.settings.circle_task.n_blocks
                                                             + bool(self.settings.circle_task.n_practice_trials) * 2)
            # Only add data of session if we're not practicing anymore.
            if not self.is_practice:
                self.data_collection()
                if was_last_block:
                    self.add_session_data()
                
            self.dispatch('on_task_stopped', was_last_block)
    
    def on_task_stopped(self, was_last_block=False):
        if was_last_block:
            self.clear_data()
    
    def release_audio(self):
        """ Unload audio sources from memory. """
        for sound in [self.sound_start, self.sound_stop]:
            if sound:
                sound.stop()
                sound.unload()
                sound = None
    
    def get_current_time_iso(self, fmt=None):
        """ Returns the current datetime as string.
        
        :param fmt: Format to return, e.g. "%Y-%m-%d".
        :type fmt: str|None
        :return: Current time as string.
        :rtype: str
        """
        if fmt:
            t = datetime.now().strftime(time_fmt)
        else:
            t = datetime.now().isoformat()
        return t
    
    def collect_meta_data(self):
        """ Collect information about context of data acquisition. """
        constrained_df = 'df2' if self.target2_switch else 'df1'
        
        self.meta_data['table'] = 'trials'
        self.meta_data['device'] = create_device_identifier()
        self.meta_data['user'] = self.settings.current_user
        self.meta_data['task'] = self.settings.current_task
        # Practice blocks don't count. Make them zero.
        if self.is_practice:
            self.meta_data['block'] = 0
        else:
            self.meta_data['block'] = self.settings.current_block \
                                      - (bool(self.settings.circle_task.n_practice_trials) * 2)
        self.meta_data['treatment'] = constrained_df if self.is_constrained else ''
        self.meta_data['time_iso'] = self.get_current_time_iso(time_fmt)
        self.meta_data['time'] = time.time()
        self.meta_data['hash'] = md5(self.data).hexdigest()
        self.meta_data['columns'] = ['df1', 'df2']
    
    def data_collection(self):
        # Scale normalized data to 0-100.
        self.data = np.around(self.data * 100, decimals=5)  # When writing we save as %.5f. For hashing this must match.
        self.collect_meta_data()
        self.add_block_to_session()
        if self.settings.is_local_storage_enabled or self.settings.is_upload_enabled:
            self.collect_data()
        if self.settings.is_email_enabled:
            self.collect_data_email()
    
    def collect_data(self):
        """ Add data to be written or uploaded to app data member. """
        app = App.get_running_app()
        app.data_mgr.add_data(self.meta_data['columns'], self.data, self.meta_data.copy())
    
    def collect_data_email(self):
        """ Add data to be sent via e-mail. """
        app = App.get_running_app()
        app.data_mgr.add_data_email(self.data, self.meta_data.copy())
    
    def add_block_to_session(self):
        """ Collects meta data about the current block. """
        data = [self.meta_data['task'],
                self.meta_data['time'],
                self.meta_data['time_iso'],
                self.meta_data['block'],
                self.meta_data['treatment'],
                self.meta_data['hash'],
                self.settings.circle_task.warm_up,
                self.settings.circle_task.trial_duration,
                self.settings.circle_task.cool_down]
        self.session_data.append(data)
    
    def add_session_data(self):
        data = np.array(self.session_data)
        header = 'task,time,time_iso,block,treatment,hash,warm_up,trial_duration,cool_down'
        meta_data = dict()
        meta_data['table'] = 'session'
        meta_data['time'] = time.time()
        meta_data['time_iso'] = self.get_current_time_iso(time_fmt)
        meta_data['task'] = self.settings.current_task
        meta_data['user'] = self.settings.current_user
        columns = ['task', 'time', 'time_iso', 'block', 'treatment', 'hash', 'warm_up', 'trial_duration', 'cool_down']
        app = App.get_running_app()
        if self.settings.is_local_storage_enabled or self.settings.is_upload_enabled:
            app.data_mgr.add_data(columns, data, meta_data)
        if self.settings.is_email_enabled:
            app.data_mgr.add_data_email([columns] + self.session_data, meta_data.copy())
    
    def clear_data(self):
        """ Clear data for the next session. """
        self.session_data.clear()
        self.meta_data.clear()
        self.data = None
