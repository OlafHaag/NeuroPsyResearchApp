""" Defines kivy Settings classes. """
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import (NumericProperty,
                             ListProperty,
                             ConfigParserProperty,
                             )
from kivy.clock import Clock

from .utility import get_app_details


class SettingsContainer(Widget):
    """ Config settings that can be changes by user and properties for current state. """
    # General properties.
    current_user = ConfigParserProperty('Default', 'General', 'current_user', 'app', val_type=str)
    is_sound_enabled = ConfigParserProperty('1', 'General', 'sound_enabled', 'app', val_type=int)
    is_vibrate_enabled = ConfigParserProperty('1', 'General', 'vibration_enabled', 'app', val_type=int)
    # Data Collection.
    is_local_storage_enabled = ConfigParserProperty('0', 'DataCollection', 'is_local_storage_enabled', 'app',
                                                    val_type=int)  # Converts string to int.
    is_upload_enabled = ConfigParserProperty('1', 'DataCollection', 'is_upload_enabled', 'app', val_type=int)
    server_uri = ConfigParserProperty(get_app_details()['webserver'], 'DataCollection', 'webserver', 'app',
                                      val_type=str)
    is_email_enabled = ConfigParserProperty('0', 'DataCollection', 'is_email_enabled', 'app', val_type=int)
    
    # Properties that change over the course of all tasks and are not set by config.
    current_trial = NumericProperty(0)
    current_block = NumericProperty(0)
    # These only contain the values and are not bound to the config.
    # Can't use apply_property() to dynamically add ConfigParserProperty, because we can't set the key dynamically.
    # Can't save in one list with ids as mapping, because callbacks are only triggered at toplevel changes.
    user_ids = ListProperty([])
    user_aliases = ListProperty([])

    def __init__(self, **kwargs):
        super(SettingsContainer, self).__init__(**kwargs)
        # Study settings have to follow the rule of being named the lowercase study name with underscores.
        self.circle_task = SettingsCircleTask()
        self.current_task = None
        self.reset_current()
        self.register_event_type('on_user_removed')
        # Schedule user settings for nct frame. Section is not yet ready.
        Clock.schedule_once(lambda dt: self.populate_users(), 1)
    
    def populate_users(self):
        app = App.get_running_app()
        config = app.config
        for user_id in config['UserData']:
            self.user_ids.append(user_id)
            self.user_aliases.append(config.get('UserData', user_id))
    
    def edit_user(self, instance, user_id=None, user_alias=''):
        """ Edit user information. This can be a new user. """
        app = App.get_running_app()
        config = app.config
        try:
            idx = self.user_ids.index(user_id)
            self.user_aliases[idx] = user_alias
        except ValueError:
            self.user_aliases.append(user_alias)
            self.user_ids.append(user_id)
            # Add to config.
        config.set('UserData', user_id, user_alias)
        config.write()
        
    def remove_user(self, user_id):
        """ Remove a user from settings and config by its ID. """
        app = App.get_running_app()
        config = app.config
        config.remove_option(section='UserData', option=user_id)
        config.write()
        idx = self.user_ids.index(user_id)
        self.user_aliases.pop(idx)
        self.user_ids.remove(user_id)
        self.dispatch('on_user_removed', user_id)
    
    def on_user_removed(self, *args):
        """ Default dummy implementation of event callback. """
        pass
    
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
        if self.current_task == 'Circle Task':
            self.circle_task.on_new_block(value)


class SettingsCircleTask(Widget):
    """ Circle Task settings and properties. """
    n_trials = ConfigParserProperty('20', 'CircleTask', 'n_trials', 'app', val_type=int,
                                    verify=lambda x: x > 0, errorvalue=20)
    n_blocks = ConfigParserProperty('3', 'CircleTask', 'n_blocks', 'app', val_type=int,
                                    verify=lambda x: x > 0, errorvalue=3)
    n_practice_trials = ConfigParserProperty('5', 'CircleTask', 'n_practice_trials', 'app', val_type=int,
                                             verify=lambda x: x >= 0, errorvalue=5)
    constrained_block = ConfigParserProperty('2', 'CircleTask', 'constrained_block', 'app', val_type=int)
    warm_up = ConfigParserProperty('1.0', 'CircleTask', 'warm_up_time', 'app', val_type=float,
                                   verify=lambda x: x > 0.0, errorvalue=1.0)
    trial_duration = ConfigParserProperty('2.0', 'CircleTask', 'trial_duration', 'app', val_type=float,
                                          verify=lambda x: x > 0.0, errorvalue=1.0)
    cool_down = ConfigParserProperty('0.5', 'CircleTask', 'cool_down_time', 'app', val_type=float,
                                     verify=lambda x: x > 0.0, errorvalue=0.5)
    email_recipient = ConfigParserProperty('', 'CircleTask', 'email_recipient', 'app', val_type=str)
    researcher = ConfigParserProperty('', 'CircleTask', 'researcher', 'app', val_type=str)
    
    def __init__(self, **kwargs):
        super(SettingsCircleTask, self).__init__(**kwargs)
        self.constraint = False
        self.practice_block = 0

    def set_practice_block(self, block):
        if self.n_practice_trials:
            # Don't advance practice_block when the current block gets reset to 0.
            if 0 < block <= 3:
                self.practice_block += 1
            # If we've done our 2 practice blocks, we're ready for the big leagues.
            if self.practice_block > 2 or block == 0:
                self.practice_block = 0

    def set_constraint_setting(self, block):
        # Second practice block and adjusted constrained block.
        self.constraint = (self.practice_block == 2) \
                          or (block == (self.constrained_block + bool(self.n_practice_trials) * 2))

    def on_new_block(self, new_block):
        # We don't count practice blocks.
        self.set_practice_block(new_block)
        self.set_constraint_setting(new_block)
