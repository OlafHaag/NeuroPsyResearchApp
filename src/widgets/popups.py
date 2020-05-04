from configparser import ConfigParser

from kivy.app import App
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ConfigParserProperty
from kivy.core.window import Window

from kivymd.uix.button import MDRectangleFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout

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


class ScrollText(MDBoxLayout):
    text = StringProperty(_('Loading...'))

    def __init__(self, **kwargs):
        self.text = kwargs.pop('text', _("not found"))
        self.height = (Window.height * 0.8) - 100
        super(ScrollText, self).__init__(**kwargs)


class TermsPopup(MDDialog):
    """ Display terms and conditions for using the app. """

    is_first_run = ConfigParserProperty('1', 'General', 'is_first_run', 'app', val_type=int)

    def __init__(self, **kwargs):
        app = App.get_running_app()
        
        self.__reject_btn = MDRectangleFlatButton(
            text=_("DECLINE"),
            on_release=app.manager.quit
        )
        
        self.__accept_btn = MDRaisedButton(
            text=_("ACCEPT"),
            on_release=self.dismiss
        )
        
        content = ScrollText(text=self._get_terms_text())
        
        default_kwargs = dict(
            title=_("Terms & Conditions"),
            type='custom',
            content_cls=content,
            auto_dismiss=False,
            size_hint_x=0.9,
            buttons=[
                self.__reject_btn,
                self.__accept_btn,
            ],
        )
        default_kwargs.update(kwargs)
        super(TermsPopup, self).__init__(**default_kwargs)

    def _get_app_details(self):
        """ Get app's name, author and contact information. """
        try:
            with open('android.txt') as f:
                file_content = '[dummy_section]\n' + f.read()
        except IOError:
            print("WARNING: android.txt wasn't found! Setting app details to " + _("UNKNOWN."))
            return {'appname': _("UNKNOWN."), 'author': _("UNKNOWN."), 'contact': _("UNKNOWN.")}

        config_parser = ConfigParser()
        config_parser.read_string(file_content)
        details = {'appname': config_parser.get('dummy_section', 'title', fallback=_("UNKNOWN.")),
                   'author': config_parser.get('dummy_section', 'author', fallback=_("UNKNOWN.")),
                   'contact': config_parser.get('dummy_section', 'contact', fallback=_("UNKNOWN."))}
        return details
    
    def _get_terms_text(self):
        app_details = self._get_app_details()

        text = _("By downloading or using the app, these terms will automatically apply to you – "
                 "you should make sure therefore that you read them carefully before using the app. "
                 "You’re not allowed to attempt to extract the source code of the app from its distributed "
                 "form. The source code is provided separately under the open MIT license. "
                 "The app itself, and all the trade marks, copyright, database rights and other intellectual "
                 "property rights related to it, still belong to {author}.\n\n"
                 "{author} is committed to ensuring that the app is as useful and efficient as possible. "
                 "For that reason, we reserve the right to make changes to the app.\n\n"
                 "The {appname} app stores and processes de-identified data that you have provided to us, "
                 "in order to provide the Service. As it is with internet based services, a 100% anonymity "
                 "cannot be guaranteed. It’s your responsibility to keep your phone and access to the app "
                 "secure. We therefore recommend that you do not jailbreak or root your phone, which is the "
                 "process of removing software restrictions and limitations imposed by the official "
                 "operating system of your device. It could make your phone vulnerable to "
                 "malware/viruses/malicious programs, compromise your phone’s security features and it "
                 "could mean that the {appname} app won’t work properly or at all.\n\n"
                 "You should be aware that there are certain things that {author} will not take "
                 "responsibility for. Certain functions of the app will require the app to have an "
                 "active internet connection. The connection can be Wi-Fi, or provided by your mobile "
                 "network provider, but {author} cannot take responsibility for the app not working at "
                 "full functionality if you don’t have access to Wi-Fi, and you don’t have any of your data "
                 "allowance left.\n\n"
                 "If you’re using the app outside of an area with Wi-Fi, you should remember that your "
                 "terms of the agreement with your mobile network provider will still apply. As a result, "
                 "you may be charged by your mobile provider for the cost of data for the duration of the "
                 "connection while accessing the app, or other third party charges. In using the app, you’re "
                 "accepting responsibility for any such charges, including roaming data charges if you use "
                 "the app outside of your home territory (i.e. region or country) without turning off data "
                 "roaming. If you are not the bill payer for the device on which you’re using the app, "
                 "please be aware that we assume that you have received permission from the bill payer "
                 "for using the app.\n\n"
                 "Along the same lines, {author} cannot always take responsibility for the way you use the "
                 "app i.e. You need to make sure that your device stays charged – if it runs out of battery "
                 "and you can’t turn it on to avail the Service, {author} cannot accept responsibility.\n\n"
                 "With respect to {author}’s responsibility for your use of the app, when you’re using the "
                 "app, it’s important to bear in mind that although we endeavour to ensure that it is "
                 "updated and correct at all times, we do rely on third parties to provide information to us "
                 "so that we can make it available to you. {author} accepts no liability for any loss, "
                 "direct or indirect, you experience as a result of relying wholly on this functionality of "
                 "the app.\n\n"
                 "At some point, we may wish to update the app. The app is currently available on Android – "
                 "the requirements for system (and for any additional systems we decide to extend the "
                 "availability of the app to) may change, and you’ll need to download the updates if you "
                 "want to keep using the app. {author} does not promise that te app will always be updated "
                 "so that it is relevant to you and/or works with the Android version that you have "
                 "installed on your device. However, you promise to always accept updates to the application "
                 "when offered to you, We may also wish to stop providing the app, and may terminate use of "
                 "it at any time without giving notice of termination to you. Unless we tell you otherwise, "
                 "upon any termination, (a) the rights and licenses granted to you in these terms will end; "
                 "(b) you must stop using the app, and (if needed) delete it from your device.\n\n"
                 "[b]Changes to This Terms and Conditions[/b]\n"
                 "We may update the Terms and Conditions from time to time.\n\n "
                 "[b]Contact Us[/b]\n"
                 "If you have any questions or suggestions about my Terms and Conditions, do not hesitate "
                 "to contact us at {contact}.\n\n"
                 "This Terms and Conditions page was generated by {terms_src}").format(
                    author=app_details['author'],
                    appname=app_details['appname'],
                    contact=app_details['contact'],
                    terms_src="App Privacy Policy Generator")
        # ToDo: Link to Policy generator? (https://app-privacy-policy-generator.firebaseapp.com/)
        return text
    
    def on_dismiss(self):
        if self.is_first_run:
            self.is_first_run = 0
            
    def on_open(self):
        # When the terms are dismissed the first time, it means they were accepted.
        if not self.is_first_run:
            self.ids.button_box.remove_widget(self.__reject_btn)
            self.__accept_btn.text = _("CLOSE")
        self.content_cls.ids.scroll.scroll_y = 1
