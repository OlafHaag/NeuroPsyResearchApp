from datetime import datetime
import time
from hashlib import md5

from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.core.audio import SoundLoader
from kivy.clock import Clock

from kivymd.uix.behaviors import BackgroundColorBehavior

import numpy as np
import plyer

from . import BaseScreen, DifficultyRatingPopup
from ..i18n import _
from ..utility import time_fmt, create_device_identifier


class ScreenCircleTask(BackgroundColorBehavior, BaseScreen):
    """ This class handles all the logic for the circle size matching task. """
    settings = ObjectProperty()
    progress = StringProperty(_("Trial: ") + "0/0")
    # Workaround, since self.settings.circle_task.constraint doesn't seem to exist at init.
    is_constrained = BooleanProperty(False)
    constraint = NumericProperty(0)  # 0 = no constraint, 1 = single constraint, 2 = both constrained
    target2_switch = BooleanProperty(False)  # Which slider is controlling the second target.
    is_practice = BooleanProperty(True)
    
    def __init__(self, **kwargs):
        # Procedure related.
        self.register_event_type('on_task_stopped')
        self.schedule = None
        self.max_trials = 0
        self.max_blocks = 0
        # Control related.
        self.df1_touch = None
        self.df2_touch = None
        # Save defaults in order to check if sliders have been used at all. Set in on_kv_post.
        self.df1_default = 0.0
        self.df2_default = 0.0
        # Feedback related.
        self.sound_start = None
        self.sound_stop = None
        # Data collection related.
        self.clear_times()
        self.data = None  # For numerical data.
        self.meta_data = dict()  # For context of numerical data acquisition, e.g. treatment/condition.
        self.session_data = list()  # For description of a block if numerical data.
        super(ScreenCircleTask, self).__init__(**kwargs)
    
    def on_kv_post(self, base_widget):
        """ Bind events. """
        self.count_down.bind(on_count_down_finished=lambda instance: self.trial_finished())
        # Release slider when we leave handle position too much.
        # We don't want extra degrees of freedom that we don't measure.
        self.ids.df1.bind(on_grab=self.slider_grab,
                          on_ungrab=self.slider_ungrab,
                          on_leave=self.slider_ungrab)
        self.ids.df2.bind(on_grab=self.slider_grab,
                          on_ungrab=self.slider_ungrab,
                          on_leave=self.slider_ungrab)
        # Save starting positions of sliders.
        self.df1_default = self.ids.df1.value_normalized
        self.df2_default = self.ids.df2.value_normalized
    
    def set_slider_colors(self, slider, status=False):
        """ Set the slider's handle and track colors depending on status and target_switch.
        
        :param slider: Slider instance.
        :param status: True if colored, False if not.
        """
        if status:
            if slider is self.ids.df1:
                color = [0.25, 0.52, 0.95, 1]
            else:
                color = [0.95, 0.52, 0.25, 1]
        else:
            color = [1, 1, 1, 1]
        slider.value_track = status
        slider.value_track_color = color
        slider.children[0].color = color
    
    def on_pre_enter(self, *args):
        """ Setup this run of the task and initiate start. """
        # Do we do practice trials?
        self.is_practice = bool(self.settings.circle_task.practice_block)
        if self.is_practice:
            self.max_trials = self.settings.circle_task.n_practice_trials
        else:
            self.max_trials = self.settings.circle_task.n_trials
        self.is_constrained = self.settings.circle_task.constraint
        self.constraint = int(self.settings.circle_task.constraint_type)
        # df that is constrained is randomly chosen.
        self.target2_switch = np.random.choice([True, False])
        # Set visual indicator for which df is constrained.
        if self.is_constrained:
            df1_colored = (self.constraint == 2) or not self.target2_switch
            df2_colored = (self.constraint == 2) or self.target2_switch
        else:
            df1_colored = df2_colored = False
        self.set_slider_colors(self.ids.df1, df1_colored)
        self.set_slider_colors(self.ids.df2, df2_colored)
        # Remind to use sliders.
        self.ids.df1_warning.opacity = 1.0
        self.ids.df2_warning.opacity = 1.0

        # Initiate data container for this block.
        if self.is_practice:
            n_trials = self.settings.circle_task.n_practice_trials
        else:
            n_trials = self.settings.circle_task.n_trials
        self.data = np.zeros((n_trials, 6))  # Data for df1, df2, df1_grab, df1_release, df2_grab, df2_release
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
            self.df1_grab_dt = self.df1_touch.time_start - self.onset
            self.ids.df1_warning.opacity = 0.0
        elif instance == self.ids.df2 and not self.ids.df2.disabled:
            self.df2_touch = touch
            self.df2_grab_dt = self.df2_touch.time_start - self.onset
            self.ids.df2_warning.opacity = 0.0
    
    def slider_ungrab(self, instance, touch):
        """ Disable sliders when they're let go. """
        if touch.time_end == -1:
            t = time.time()
        else:
            t = touch.time_end
        if (instance == self.ids.df1) and touch is self.df1_touch:
            self.ids.df1.disabled = True
            self.df1_touch.ungrab(self.ids.df1)
            self.df1_release_dt = t - self.onset
            self.df1_touch = None
        elif (instance == self.ids.df2) and touch is self.df2_touch:
            self.ids.df2.disabled = True
            self.df2_touch.ungrab(self.ids.df2)
            self.df2_release_dt = t - self.onset
            self.df2_touch = None
    
    def disable_sliders(self):
        """ Disable sliders regardless of whether they have touch or not. """
        self.ids.df2.disabled = True
        self.ids.df1.disabled = True
        t = time.time()
        # Release slider grabs, if any.
        if self.df1_touch:
            self.df1_touch.ungrab(self.ids.df1)
            self.df1_release_dt = t - self.onset
            self.df1_touch = None
        if self.df2_touch:
            self.df2_touch.ungrab(self.ids.df2)
            self.df2_release_dt = t - self.onset
            self.df2_touch = None
    
    def enable_sliders(self):
        self.ids.df2.disabled = False
        self.ids.df1.disabled = False
    
    def reset_sliders(self):
        """ Set sliders to initial position. """
        self.ids.df1.value = self.ids.df1.max * 0.1
        self.ids.df2.value = self.ids.df2.max * 0.1
        # Reset slider grab times.
        self.clear_times()
    
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
        if self.settings.is_vibrate_enabled:
            try:
                if plyer.vibrator.exists():
                    plyer.vibrator.vibrate(time=t)
            except (NotImplementedError, ModuleNotFoundError):
                pass
    
    def clear_times(self):
        self.onset = np.NaN
        self.df1_grab_dt = np.NaN
        self.df1_release_dt = np.NaN
        self.df2_grab_dt = np.NaN
        self.df2_release_dt = np.NaN
        
    def start_trial(self):
        """ Start the trial. """
        if self.sound_start:
            self.sound_start.play()
        self.enable_sliders()
        self.vibrate()
        self.count_down.start()
        self.onset = time.time()
    
    def trial_finished(self):
        """ Callback for when a trial ends. Collect data. """
        if self.sound_stop:
            self.sound_stop.play()
        self.disable_sliders()
        self.count_down.set_label(_("FINISHED"))
        # Record data for current trial.
        try:
            self.data[self.settings.current_trial - 1, :] = (self.ids.df1.value_normalized,
                                                             self.ids.df2.value_normalized,
                                                             self.df1_grab_dt, self.df1_release_dt,
                                                             self.df2_grab_dt, self.df2_release_dt)
            self.check_slider_use()
        except TypeError:
            # Trial was aborted and data set to None by self.clea_data().
            pass
        self.clear_times()
        
    def check_slider_use(self):
        """ Checks if the slider values are still at their defaults and displays warning where appropriate."""
        if np.isnan(self.data[self.settings.current_trial - 1, [2, 3]]).all():
            self.ids.df1_warning.opacity = 1.0
        else:
            self.ids.df1_warning.opacity = 0.0
        if np.isnan(self.data[self.settings.current_trial - 1, [4, 5]]).all():
            self.ids.df2_warning.opacity = 1.0
        else:
            self.ids.df2_warning.opacity = 0.0
        if np.isnan(self.data[self.settings.current_trial - 1, 2:]).any() \
                or np.greater_equal(*self.data[self.settings.current_trial - 1, [2, 5]]) \
                or np.greater_equal(*self.data[self.settings.current_trial - 1, [4, 3]]):
            self.ids.concurrency_warning.opacity = 1.0
        else:
            self.ids.concurrency_warning.opacity = 0.0
    
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
        if interrupt:
            self.clear_data()
            return
        
        # Check if task was properly done, i.e. sliders were not used at all.
        if (np.isnan(self.data[:, 2]).all()) or (np.isnan(self.data[:, 4]).all()):
            self.clear_data()
            # Feedback and reset/abort.
            msg = _("Please read instructions again carefully and perform task accordingly.\nAborting Session...")
            self.manager.dispatch('on_warning', text=msg)
            # These are not the data you're looking for...
            app = App.get_running_app()
            app.data_mgr.is_invalid = True
            # Abort session. Was last block.
            self.dispatch('on_task_stopped', True)
            return
        
        rating_popup = DifficultyRatingPopup()
        rating_popup.bind(on_confirm=lambda instance, rating: self.save_rating(rating),
                          on_dismiss=lambda instance: self.pre_task_stopped())
        rating_popup.open()
    
    def pre_task_stopped(self):
        """ """
        was_last_block = self.settings.current_block == (self.settings.circle_task.n_blocks
                                                         + bool(self.settings.circle_task.n_practice_trials) * 2)
        # Only add data of session if we're not practicing anymore.
        if not self.is_practice:
            self.data_collection()
        else:
            if self.meta_data['rating'] > 3:
                msg = _("If the task was too difficult for you, go back and start over to practice some more.\n"
                        "You can also increase the number of practice trials in the settings, if you really need to.")
                self.manager.dispatch('on_info', title=_("Info"), text=msg)
        if was_last_block:
            self.add_session_data_to_manager()
        self.dispatch('on_task_stopped', was_last_block)
        
    def on_task_stopped(self, was_last_block=False):
        """ Gets called AFTER all bindings on this are through.
        Therefore, data collection must happen before this.
        """
        if was_last_block:
            self.clear_data()
    
    def release_audio(self):
        """ Unload audio sources from memory. """
        if self.sound_start:
            self.sound_start.stop()
            self.sound_start.unload()
            self.sound_start = None
        if self.sound_stop:
            self.sound_stop.stop()
            self.sound_stop.unload()
            self.sound_stop = None
    
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
    
    def save_rating(self, rating):
        """ Save difficulty rating to meta-data. """
        self.meta_data['rating'] = rating  # This is not really meta data, but it's the best place to put it.
    
    def data_collection(self):
        """ Gather all the data for current block. """
        # Scale normalized data to 0-100.
        self.data[:, :2] = self.data[:, :2] * 100
        # When writing we save as %.5f. For hashing this must match.
        self.data = np.around(self.data, decimals=5)
        self.collect_meta_data()
        self.add_block_to_session()
        self.add_data_to_manager()
    
    def collect_meta_data(self):
        """ Collect information about context of data acquisition. """
        if self.is_constrained and (self.constraint == 1):
            constrained_df = 'df2' if self.target2_switch else 'df1'
        elif self.is_constrained and (self.constraint == 2):
            constrained_df = 'df1|df2'  # Can't use comma as it is the separator in CSV (comma separated values).
        else:
            constrained_df = ''
        
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
        self.meta_data['treatment'] = constrained_df
        self.meta_data['time_iso'] = self.get_current_time_iso(time_fmt)
        self.meta_data['time'] = time.time()
        self.meta_data['hash'] = md5(self.data).hexdigest()
        self.meta_data['columns'] = ['df1', 'df2', 'df1_grab', 'df1_release', 'df2_grab', 'df2_release']
    
    def add_data_to_manager(self):
        """ Add data to be written or uploaded to data manager. """
        app = App.get_running_app()
        app.data_mgr.add_data(self.meta_data['columns'], self.data, self.meta_data.copy())
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
                self.settings.circle_task.cool_down,
                self.meta_data['rating']]
        self.session_data.append(data)
    
    def add_session_data_to_manager(self):
        """ Send session data to data manager. """
        data = np.array(self.session_data)
        meta_data = dict()
        meta_data['table'] = 'session'
        meta_data['time'] = time.time()
        meta_data['time_iso'] = self.get_current_time_iso(time_fmt)
        meta_data['task'] = self.settings.current_task
        meta_data['user'] = self.settings.current_user
        columns = ['task', 'time', 'time_iso', 'block', 'treatment', 'hash', 'warm_up', 'trial_duration', 'cool_down',
                   'rating']
        app = App.get_running_app()
        app.data_mgr.add_data(columns, data, meta_data)
        app.data_mgr.add_data_email([columns] + self.session_data, meta_data.copy())
    
    def clear_data(self):
        """ Clear data for the next session. """
        self.session_data.clear()
        self.meta_data.clear()
        self.data = None
