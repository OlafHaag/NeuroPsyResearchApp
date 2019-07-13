""" Defines kivy Settings class. """
from kivy.uix.settings import SettingItem, SettingsWithSidebar
from kivy.uix.button import Button

from i18n.settings import SettingOptionMapping


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
