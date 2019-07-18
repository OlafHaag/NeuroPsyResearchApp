import pickle
import datetime
import time
from hashlib import md5

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.core.audio import SoundLoader
from kivy.clock import Clock

import numpy as np

from ..i18n import _


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
        iti = self.settings.circle_task.warm_up + self.settings.circle_task.trial_duration \
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
        self.data[self.settings.current_trial - 1, :] = (self.ids.df1.value_normalized, self.ids.df2.value_normalized)
    
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
            
            if self.settings.is_local_storage_enabled or self.settings.is_upload_enabled:
                self.collect_data()
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
        constrained_df = 'df2' if self.target2_switch else 'df1'
        
        self.meta_data['table'] = 'trials'
        self.meta_data['device'] = App.get_running_app().create_device_identifier()
        self.meta_data['user'] = self.settings.user
        self.meta_data['task'] = self.settings.task
        self.meta_data['block'] = self.settings.current_block
        self.meta_data['treatment'] = constrained_df if self.is_constrained else ''
        self.meta_data['time_iso'] = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        self.meta_data['time'] = time.time()
        self.meta_data['hash'] = md5(self.data).hexdigest()
        self.meta_data['columns'] = ['df1', 'df2']
    
    # ToDo: put task settings in session CSV.
    def collect_data(self):
        """ Add data to be written or uploaded to app data member. """
        app = App.get_running_app()
        header = ','.join(self.meta_data['columns'])
        data_b = app.data2bytes(self.data, header=header)
        d = self.meta_data.copy()
        d['data'] = data_b
        app.data.append(d)
    
    def collect_data_email(self):
        """ Add data to be sent via e-mail. """
        d = self.meta_data.copy()
        d['data'] = pickle.dumps(self.data)
        
        app = App.get_running_app()
        app.data_email.append(d)
