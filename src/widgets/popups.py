from kivy.app import App
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ConfigParserProperty
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog

from . import ItemConfirm
from ..i18n import (_,
                    list_translated_languages,
                    translation_to_language_code,
                    DEFAULT_LANGUAGE)


class SimplePopup(Popup):
    msg = StringProperty(_('Initiating...'))
    
    def __init__(self, **kwargs):
        super(SimplePopup, self).__init__(**kwargs)


class BlockingPopup(Popup):
    msg = StringProperty(_('Initiating...'))
    
    def __init__(self, **kwargs):
        super(BlockingPopup, self).__init__(**kwargs)


class LanguagePopup(MDDialog):
    """ For first run ask which language to use. """
    current_language = ConfigParserProperty(DEFAULT_LANGUAGE, 'Localization', 'language', 'app', val_type=str)
    
    def __init__(self, **kwargs):
        # Gather options.
        languages = list_translated_languages()
        languages.sort()
        items = [ItemConfirm(text=lang, value=translation_to_language_code(lang)) for lang in languages]
        default_kwargs = dict(
            title=_("Choose Language"),
            text=_("You can also change the language in the settings later."),
            type="confirmation",
            auto_dismiss=False,  # Otherwise the callback doesn't fire?!
            items=items,
            buttons=[MDRaisedButton(
                text=_("OK"),
                on_release=self.dismiss
            ),
            ]
        )
        default_kwargs.update(kwargs)
        super(LanguagePopup, self).__init__(**default_kwargs)
    
    def select_current_language(self):
        """ Activate item for currently chosen language. """
        for item in self.items:
            if item.value == self.current_language:
                item.set_icon(item.ids.check)
                break
        
    def change_language(self):
        for item in self.items:
            if item.active:
                lang_code = item.value  # There's at least the default language.
                break
        # Use the app's function to change language instead of i18n's just in case we do something special there.
        app = App.get_running_app()
        app.switch_language(lang=lang_code)
        # Now also update the config.
        self.current_language = lang_code

    def on_open(self):
        self.select_current_language()

    def on_dismiss(self):
        self.change_language()
