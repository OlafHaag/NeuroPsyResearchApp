import json

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.settings import Settings, SettingItem, SettingString
from kivy.properties import ObjectProperty, DictProperty

from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.label import MDLabel

from . import CheckItem
from . import TextInputPopup, NumericInputPopup
from ..i18n import _


class SettingThemedTitle(MDLabel):
    """ A simple title label, used to organize the settings in sections. """
    title = MDLabel.text
    panel = ObjectProperty(None)
    
    
class SettingThemedString(SettingString):
    """ Implementation of a string setting on top of a :class:`SettingString`.
    It is visualized with a :class:`MDLabel` widget that, when clicked,
    will open a MDDialog for text input so the user can enter a custom value.
    """
    
    def _set_value(self, value):
        self.value = value
        self._dismiss()
        
    def _create_popup(self, instance):
        # create popup layout
        self.popup = popup = TextInputPopup(title=self.title)
        popup.content_cls.description = self.desc
        popup.input = self.value
        popup.bind(on_confirm=lambda j, text: self._set_value(text), on_dismiss=self._dismiss)
        popup.open()
    
    def _dismiss(self, *largs):
        self.popup = None
        

class SettingThemedNumeric(SettingThemedString):
    
    def _set_value(self, value):
        self.value = value  # Triggers on_config_changed event.
        # Display the config value in case of error.
        config_val = self.panel.get_value(self.section, self.key)
        if value != config_val:
            self.value = config_val
        self._dismiss()
        
    def _get_numeric_type(self):
        # Must have set defaults, so the key at least exists.
        num_string = self.panel.get_value(self.section, self.key)
        is_float = '.' in num_string
        try:
            if is_float:
                float(num_string)
                return float
            else:
                int(num_string)
                return int
        except ValueError:
            return str
        
    def _create_popup(self, instance):
        # create popup layout
        self.popup = popup = NumericInputPopup(title=self.title, type=self._get_numeric_type())
        popup.content_cls.description = self.desc
        popup.input = self.value
        popup.bind(on_confirm=lambda j, text: self._set_value(text), on_dismiss=self._dismiss)
        popup.open()
        
        
class SettingButtons(SettingItem):
    """ Implementation of buttons in the settings that when clicked can trigger an action. """
    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        kw = kwargs.copy()
        kw.pop('buttons', None)
        super(SettingButtons, self).__init__(**kw)
        for button in kwargs['buttons']:
            btn_widget = MDRaisedButton(text=button['title'])
            btn_widget.ID = button['id']
            self.add_widget(btn_widget)
            btn_widget.bind(on_release=self.on_button_pressed)
            
    def set_value(self, section, key, value):
        # _set_value normally reads the configparser values and runs on an error
        # to do nothing here
        return
    
    def on_button_pressed(self, instance):
        self.panel.settings.dispatch('on_config_change', self.panel.config, self.section, self.key, instance.ID)
    
    
class SettingOptionMapping(SettingItem):
    """Implementation of an option list on top of a :class:`SettingThemedItem`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivymd.uix.dialog.MDDialog` with a
    list of options from which the user can select.
    """

    options = DictProperty({})
    '''A mapping of key strings to value strings.
    The values are displayed to the user.
    The keys can be found in the value attribute.

    :attr:`options` is a :class:`~kivy.properties.DictProperty` and defaults
    to ``{}``.
    '''

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it is shown.

    :attr:`popup` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    def on_panel(self, instance, value):
        """The panel is set. Bind to open a popup when it is clicked."""
        if value is None:
            return
        self.fbind('on_release', self._show_confirmation_dialog)

    def _set_option(self, value):
        self.value = value

    def _show_confirmation_dialog(self, instance):
        """ Layout a popup with single-choice items. """
        
        if not self.popup:
            # Gather options.
            items = list()
            for option, text in sorted(self.options.items(), key=lambda t: t[1]):
                opt = CheckItem(text=text, value=option)
                items.append(opt)

            self.popup = MDDialog(
                title=self.title,
                type="confirmation",
                items=items,
                auto_dismiss=False,  # Otherwise the callbacks don't fire?!
                buttons=[
                    MDFlatButton(
                        text=_("CANCEL"),
                        on_release=self.cancel_handler
                    ),
                    MDRaisedButton(
                        text=_("OK"),
                        on_release=self.confirm_handler
                    ),
                ],
                width=min(0.95 * Window.width, dp(500)),
            )
        # Make SettingThemedItem's value the active item.
        for item in self.popup.items:
            if item.value == self.value:
                item.set_icon(item.ids.check)
                break
                
        self.popup.open()
    
    def confirm_handler(self, widget):
        for item in self.popup.items:
            if item.active:
                # It's a single-choice selection, stop when we find it.
                self._set_option(item.value)
                break
        self.popup.dismiss()

    def cancel_handler(self, widget):
        self.popup.dismiss()


class SettingsWithTabbedPanels(Settings):
    """ A settings widget that displays settings panels as pages in a tabbed layout. """

    __events__ = ('on_close', )

    def __init__(self, *args, **kwargs):
        self.interface_cls = TabbedSettingsInterface
        super(SettingsWithTabbedPanels, self).__init__(*args, **kwargs)
        # Override default setting types.
        self.register_type('string', SettingThemedString)
        self.register_type('numeric', SettingThemedNumeric)
        self.register_type('title', SettingThemedTitle)
        # Custom setting types.
        self.register_type("optionmapping", SettingOptionMapping)
        self.register_type('buttons', SettingButtons)
    
    def on_close(self, *args):
        pass


class SettingsTab(FloatLayout, MDTabsBase):
    """ Class implementing content for a settings tab. """
    pass


class TabbedSettingsInterface(FloatLayout):
    close_button = ObjectProperty()

    __events__ = ('on_close',)
    
    def __init__(self, *args, **kwargs):
        super(TabbedSettingsInterface, self).__init__(*args, **kwargs)
        self.close_button.bind(on_release=lambda j: self.dispatch('on_close'))

    def add_panel(self, panel, name, uid):
        scrollview = ScrollView(scroll_type=['bars', 'content'])
        scrollview.add_widget(panel)
        tab = SettingsTab(text=name)
        tab.add_widget(scrollview)
        self.ids.tabs.add_widget(tab)
        
    def on_close(self, *args):
        pass
