""" Defines kivy Settings classes. """
from kivy.app import App
from kivy.uix.settings import SettingItem, SettingsWithSidebar
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import ConfigParserProperty
from kivy.properties import NumericProperty


from .i18n.settings import SettingOptionMapping
from src.config import WEBSERVER


class SettingButtons(SettingItem):

    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        kw = kwargs.copy()
        kw.pop('buttons', None)
        super(SettingItem, self).__init__(**kw)
        for button in kwargs['buttons']:
            btn_widget = Button(text=button['title'], font_size='15sp')
            btn_widget.ID = button['id']
            self.add_widget(btn_widget)
            btn_widget.bind(on_release=self.on_button_pressed)
            
    def set_value(self, section, key, value):
        # set_value normally reads the configparser values and runs on an error
        # to do nothing here
        return
    
    def on_button_pressed(self, instance):
        self.panel.settings.dispatch('on_config_change', self.panel.config, self.section, self.key, instance.ID)


class Settings(SettingsWithSidebar):
    """The settings for the editor.

    .. see also:: mod:`kivy.uix.settings`"""

    def __init__(self, *args, **kwargs):
        """Create a new settings instance.

        The :class:`SettingOptionMapping` is added an can be used with the ``"optionmapping"`` type.
        The :class:`SettingButtons` is added an can be used with the ``"buttons"`` type.
        """
        super().__init__(*args, **kwargs)
        self.register_type("optionmapping", SettingOptionMapping)
        self.register_type('buttons', SettingButtons)


class SettingsContainer(Widget):
    """ For now put all the settings for each task in here for simplicity.
        When (or if) more tasks get implemented and the need arises to separate them, come up with a better,
        modular solution.
    """
    # General properties.
    # language = ConfigParserProperty('en', 'Localization', 'language', 'app', val_type=str)
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
