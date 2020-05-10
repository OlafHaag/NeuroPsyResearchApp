from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.settings import Settings, SettingItem, SettingsWithSidebar
from kivy.properties import ObjectProperty, DictProperty

from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.tab import MDTabsBase

from . import CheckItem
from ..i18n import _


class SettingsWithTabbedPanel(Settings):
    '''A settings widget that displays settings panels as pages in a
    :class:`~kivy.uix.tabbedpanel.TabbedPanel`.
    '''

    __events__ = ('on_close', )

    def __init__(self, *args, **kwargs):
        self.interface_cls = InterfaceWithTabbedPanel
        super(SettingsWithTabbedPanel, self).__init__(*args, **kwargs)

    def on_close(self, *args):
        pass
    
    
class InterfaceWithTabbedPanel(FloatLayout):
    """The content widget used by Settings. It stores and displays
    Settings panels in tabs of a TabbedPanel.
    """
    tabbedpanel = ObjectProperty()
    close_button = ObjectProperty()

    __events__ = ('on_close', )

    def __init__(self, *args, **kwargs):
        super(InterfaceWithTabbedPanel, self).__init__(*args, **kwargs)
        self.close_button.bind(on_release=lambda j: self.dispatch('on_close'))

    def add_panel(self, panel, name, uid):
        scrollview = ScrollView()
        scrollview.add_widget(panel)
        if not self.tabbedpanel.default_tab_content:
            self.tabbedpanel.default_tab_text = name
            self.tabbedpanel.default_tab_content = scrollview
        else:
            panelitem = TabbedPanelHeader(text=name, content=scrollview)
            self.tabbedpanel.add_widget(panelitem)

    def on_close(self, *args):
        pass


class SettingButtons(SettingItem):

    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        kw = kwargs.copy()
        kw.pop('buttons', None)
        super(SettingItem, self).__init__(**kw)
        for button in kwargs['buttons']:
            btn_widget = MDRaisedButton(text=button['title'])
            btn_widget.ID = button['id']
            self.add_widget(btn_widget)
            btn_widget.bind(on_release=self.on_button_pressed)
            
    def set_value(self, section, key, value):
        # set_value normally reads the configparser values and runs on an error
        # to do nothing here
        return
    
    def on_button_pressed(self, instance):
        self.panel.settings.dispatch('on_config_change', self.panel.config, self.section, self.key, instance.ID)


class SettingOptionMapping(SettingItem):
    """Implementation of an option list on top of a :class:`SettingItem`.
    It is visualized with a :class:`~kivy.uix.label.Label` widget that, when
    clicked, will open a :class:`~kivy.uix.popup.Popup` with a
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
        # Make SettingItem's value the active item.
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


class Settings(SettingsWithSidebar):  # Todo: Set own interface class to match theme.
    """The settings for the editor.

    .. see also:: mod:`kivy.uix.settings`"""

    def __init__(self, *args, **kwargs):
        """Create a new settings instance.

        The :class:`SettingOptionMapping` is added and can be used with the ``"optionmapping"`` type.
        The :class:`SettingButtons` is added and can be used with the ``"buttons"`` type.
        """
        super().__init__(*args, **kwargs)
        self.register_type("optionmapping", SettingOptionMapping)
        self.register_type('buttons', SettingButtons)
