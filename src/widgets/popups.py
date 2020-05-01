from kivy.app import App
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ConfigParserProperty
from kivy.factory import Factory

from ..i18n import (_,
                    list_translated_languages,
                    language_code_to_translation,
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


class LanguagePopup(Popup):
    msg = StringProperty(_('Initiating...'))
    current_language = ConfigParserProperty(DEFAULT_LANGUAGE, 'Localization', 'language', 'app', val_type=str)
    
    def __init__(self, **kwargs):
        super(LanguagePopup, self).__init__(**kwargs)
        
        btn_layout = self.ids.lang_btn_layout
        languages = list_translated_languages()
        self.btns = dict()
        for lang in languages:
            btn = Factory.LabeledCheckBox()
            btn.text = lang
            btn.group = 'lang'
            btn_layout.add_widget(btn)
            self.btns[lang] = btn
        # Select default language.
        if language_code_to_translation(DEFAULT_LANGUAGE) in languages:
            self.btns[language_code_to_translation(DEFAULT_LANGUAGE)].active = True
        else:
            # If English is not found, just use the first one.
            self.btns[languages[0]].active = True
    
    def change_language(self):
        selected_language = [lang for lang, btn in self.btns.items() if btn.active][0]  # Being bold here with indexing.
        lang_code = translation_to_language_code(selected_language)
        # Use the app's function to change language instead of i18n's just in case we do something special there.
        app = App.get_running_app()
        app.switch_language(lang=lang_code)
        # Now also update the config.
        self.current_language = lang_code
    
    def on_dismiss(self):
        self.change_language()

    def on_language_changed(self):
        """ Default handler for event. """
        pass
