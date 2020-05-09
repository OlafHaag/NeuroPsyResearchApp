"""These options allow to show a different value than the value.

Most of this file is copied from :class:`kivy.uix.settings.SettingOptions`.
"""
from kivy.properties import DictProperty, ObjectProperty
from kivy.uix.settings import SettingItem, SettingsWithSidebar
from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog

from . import _
from ..widgets import CheckItem


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


class Settings(SettingsWithSidebar):
    """The settings for the editor.

    .. seealso:: mod:`kivy.uix.settings`"""

    def __init__(self, *args, **kwargs):
        """Create a new settings instance.

        The :class:`SettingOptionMapping` is added an can be used with the
        ``"optionmapping"`` type.
        """
        super().__init__(*args, **kwargs)
        self.register_type("optionmapping", SettingOptionMapping)


__all__ = ["SettingOptionMapping", "Settings"]
