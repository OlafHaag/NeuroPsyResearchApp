"""
Research app to study uncontrolled manifold and optimal feedback control paradigms.
"""

from pathlib import Path
from datetime import datetime
from hashlib import md5

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingsWithSpinner
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.properties import ConfigParserProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.utils import platform

from plyer import vibrator
from plyer import uniqueid
from plyer import storagepath
from plyer import notification

import numpy as np

from settingsjson import settings_json

if platform == 'android':
    from android.permissions import request_permissions, check_permission, Permission


class ScreenHome(Screen):
    """ Display that gives general information. """
    home_msg = StringProperty('[color=ff00ff][b]Hello![/b][/color]')  # Todo: General Information
    
    def on_pre_enter(self, *args):
        App.get_running_app().settings.reset_current()


class ScreenOutro(Screen):
    """ Display that gives general information. """
    outro_msg = StringProperty('[color=ff00ff][b]Thank you[/b][/color] for participating!\n')  # Todo: Outro Information
    
    def on_pre_enter(self, *args):
        dest = App.get_running_app().get_data_path()
        self.outro_msg += "\nFiles were {1}saved to {0}".format(dest, "" if dest.exists() else "[b]not[/b] ")


class ScreenInstruct(Screen):
    """ Display that tells the user what to in next task. """
    settings = ObjectProperty()
    instruction_msg = StringProperty('Instructions')

    def __init__(self, **kwargs):
        super(ScreenInstruct, self).__init__(**kwargs)
        self.df_unconstraint_msg = 'Initiating...'
        self.df_constraint_msg = 'Initiating...'
        
    def on_pre_enter(self, *args):
        self.update_messages()
        self.set_instruction_msg()
    
    def update_messages(self):
        n_trials_msg = f"There are a total of {self.settings.n_trials} trials in this block."
        n_tasks = int(self.settings.constraint) + 1
        task_suffix = self.settings.constraint * 's'
        n_tasks_msg = f"You have {n_tasks} task{task_suffix} in this block.\n\n"
        time_limit_msg = "A trial ends when the outer [color=ff00ff]purple ring[/color] reaches 100% (circle closes)"\
                         " and the countdown reaches 0.\n Shortly thereafter you will be prompted to get ready for "\
                         "the next trial.\n\n"
        task1_msg = "Use the [b]2 sliders[/b] to match the size of the [b]white disk[/b] to the " \
                    "[color=008000]green ring[/color].\n\n"
        task2_msg = "Concurrently bring the [color=3f84f2]blue arch[/color] to the [color=3f84f2]blue disc[/color] " \
                    f"by using one of the sliders. It will be the same slider during the block.\n\n"
        self.df_unconstraint_msg = n_tasks_msg + task1_msg + time_limit_msg + n_trials_msg
        self.df_constraint_msg = n_tasks_msg + task1_msg + task2_msg + time_limit_msg + n_trials_msg
            
    def set_instruction_msg(self):
        """ Change displayed text on instruction screen. """
        if self.settings.constraint:
            self.instruction_msg = self.df_constraint_msg
        else:
            self.instruction_msg = self.df_unconstraint_msg
            

class ScreenCircleTask(Screen):
    """ This class handles all the logic for the circle size matching task. """
    settings = ObjectProperty()
    progress = StringProperty("Trial: 0/0")
    is_constrained = BooleanProperty(False)  # Workaround, since self.settings.constraint doesn't seem to exist at init.
    
    def __init__(self, **kwargs):
        super(ScreenCircleTask, self).__init__(**kwargs)
        self.target2_switch = False
        self.register_event_type('on_task_stopped')
        self.schedule = None
        self.df1_touch = None
        self.df2_touch = None
        self.sound_start = None
        self.sound_stop = None
        self.data = None
    
    def on_kv_post(self, base_widget):
        self.count_down.bind(on_count_down_finished=lambda obj: self.trial_finished())
        self.ids.df1.bind(on_grab=self.slider_grab)
        self.ids.df2.bind(on_grab=self.slider_grab)
        # todo: save screen size/resolution, initial circle/ring size, slider size and slider value to file
    
    def on_pre_enter(self, *args):
        self.is_constrained = self.settings.constraint
        # df that is constrained is randomly chosen.
        self.target2_switch = np.random.choice([True, False])
        self.data = np.zeros((self.settings.n_trials, 2))
        # FixMe: Not loading sound files on Windows. (Unable to find a loader)
        self.sound_start = SoundLoader.load('res/start.ogg')
        self.sound_stop = SoundLoader.load('res/stop.ogg')
        self.count_down.start_count = self.settings.trial_duration
        self.count_down.set_label("PREPARE")
        self.start_task()
    
    # FixMe: only last touch ungrabbed, ungrab all lingering touches!
    def slider_grab(self, instance, touch):
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
        self.ids.df1.value = self.ids.df1.max * 0.1
        self.ids.df2.value = self.ids.df2.max * 0.1
    
    def start_task(self):
        self.disable_sliders()
        # Repeatedly start trials each inter-trial-interval.
        iti = self.settings.warm_up + self.settings.trial_duration + self.settings.cool_down
        self.schedule = Clock.schedule_interval(self.get_ready, iti)
        self.progress = "Trial {}/{}".format(self.settings.current_trial, self.settings.n_trials)
    
    def get_ready(self, *args):
        if self.settings.current_trial == self.settings.n_trials:
            self.stop_task()
        else:
            self.settings.current_trial += 1
            self.progress = "Trial {}/{}".format(self.settings.current_trial, self.settings.n_trials)
            self.reset_sliders()
            self.count_down.set_label("GET READY")
            Clock.schedule_once(lambda dt: self.start_trial(), self.settings.warm_up)
    
    def vibrate(self, t=0.1):
        # FixMe: bug in plyer vibrate - argument mismatch
        # try:
        #     if vibrator.exists():
        #         vibrator.vibrate(time=t)
        # except (NotImplementedError, ModuleNotFoundError):
        #     pass
        pass

    def start_trial(self):
        if self.sound_start:
            self.sound_start.play()
        self.enable_sliders()
        self.vibrate()
        self.count_down.start()
    
    def trial_finished(self):
        if self.sound_stop:
            self.sound_stop.play()
        self.disable_sliders()
        self.count_down.set_label("FINISHED")
        self.vibrate()
        self.data[self.settings.current_trial-1, :] = (self.ids.df1.value_normalized, self.ids.df2.value_normalized)
    
    def stop_task(self, interrupt=False):
        # Unschedule trials.
        if self.schedule:
            self.schedule.cancel()
            self.schedule = None
        self.reset_sliders()
        self.release_audio()
        if not interrupt:
            self.write_data()
            self.dispatch("on_task_stopped")
        
    def on_task_stopped(self):
        pass
        
    def release_audio(self):
        for sound in [self.sound_start, self.sound_stop]:
            if sound:
                sound.stop()
                sound.unload()
                sound = None
    
    def write_data(self):
        # Save endpoint values in app.user_data_dir with unique file name.
        t = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        constrained_df = "cosntrained_df2" if self.target2_switch else "constrained_df1"
        file_name = "{id}-CT-Block{block}-{type}-{time}.csv".format(id=self.settings.user,
                                                                    block=self.settings.current_block,
                                                                    type=constrained_df if self.settings.constraint else "unconstraint",
                                                                    time=t)
        app = App.get_running_app()
        dest = app.get_data_path()
        if self.data is not None and app.write_permit:
            np.savetxt(dest / file_name, self.data*100, fmt='%10.5f', delimiter=",", header="df1,df2", comments='')


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
        
    def on_kv_post(self, base_widget):
        Window.bind(on_keyboard=self.key_input)
        self.get_screen('Circle Task').bind(on_task_stopped=lambda obj: self.task_finished())

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
                    notification.notify(message="Press again to quit.", toast=True)
                if self.n_home_esc > 1:
                    self.quit()
            elif self.current == 'Settings':
                # Never gets called, screen already changed to 'Home' through app.close_settings() on esc.
                App.get_running_app().close_settings()
            elif self.current == 'Circle Task':
                self.get_screen('Circle Task').stop_task(interrupt=True)
                self.go_home()
            else:
                self.go_home()
            return True  # override the default behaviour
        else:  # the key now does nothing
            return False
        
    def go_home(self):
        self.transition.direction = 'down'
        self.current = 'Home'
        
    def task_finished(self):
        self.settings.next_block()
        self.settings.set_constraint_setting()
        # Outro after last block.
        if self.settings.current_block > self.settings.n_blocks:
            self.current = 'Outro'
        else:
            self.transition.direction = 'down'
            self.current = 'Instructions'
    
    def quit(self, *args):
        App.get_running_app().stop()
    
    
class SettingsContainer(Widget):
    user = ConfigParserProperty('0', 'UserData', 'unique_id', 'app', val_type=str)
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
        super(SettingsContainer, self).__init__(**kwargs)
        self.reset_current()
    
    def reset_current(self):
        self.current_block = 1
        self.current_trial = 0
        self.set_constraint_setting()
    
    def next_block(self):
        self.current_trial = 0
        self.current_block += 1
    
    def set_constraint_setting(self):
        self.constraint = self.current_block == self.constrained_block
        

class UncontrolledManifoldApp(App):
    manager = ObjectProperty(None, allownone=True)

    def build_config(self, config):
        """ Configure initial settings. """
        config.setdefaults('UserData', {'unique_id': self.create_identifier()})
        config.setdefaults('CircleTask', {
            'n_trials': 20,
            'n_blocks': 3,
            'constrained_block': 2,
            'warm_up_time': 1.0,
            'trial_duration': 3.0,
            'cool_down_time': 0.5})

    def build_settings(self, settings):
        settings.add_json_panel('Circle Task Settings',
                                self.config,
                                data=settings_json)

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
        pass
        
    def build(self):
        self.settings_cls = SettingsWithSpinner
        self.use_kivy_settings = False
        self.settings = SettingsContainer()
        self.write_permit = True
        root = UCMManager()
        self.manager = root
        return root

    @staticmethod
    def create_identifier(**kwargs):
        """ Returns an identifier for the hardware. """
        uid = uniqueid.get_uid().encode()
        hashed = md5(uid).hexdigest()
        # Shorten and lose information.
        ident = hashed[::4]
        return ident

    def get_data_path(self):
        if platform == 'android':
            #dest = Path(storagepath.get_documents_dir())
            dest = Path(storagepath.get_external_storage_dir()) / App.get_running_app().name
            # We may need to ask permission to write to the external storage.
            self.write_permit = check_permission(Permission.WRITE_EXTERNAL_STORAGE)
            if not self.write_permit:
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
            
            # FixMe: wait until permission granted.
            self.write_permit = check_permission(Permission.WRITE_EXTERNAL_STORAGE)
            if not dest.exists() and self.write_permit:
                # Make sure the path exists.
                dest.mkdir(parents=True, exist_ok=True)
        else:
            app = App.get_running_app()
            dest = Path(app.user_data_dir)
            #dest = dest.resolve()  # Resolve any symlinks.
        return dest
    
    # todo pause App.on_pause(), App.on_resume()
    def on_pause(self):
        # Here you can save data if needed
        return True
    
    def on_resume(self):
        # Here you can check if any data needs replacing (usually nothing)
        pass
    
    
if __name__ in ('__main__', '__android__'):
    UncontrolledManifoldApp().run()
