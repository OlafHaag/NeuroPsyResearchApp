from configparser import ConfigParser
import webbrowser

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, ConfigParserProperty
from kivy.clock import Clock

from . import LanguagePopup, BlockingPopup

from ..i18n import _


class ScreenHome(Screen):
    """ Display that gives general information. """
    # As a workaround for internationalization to work set actual message in on_pre_enter().
    home_msg = StringProperty(_('Initiating...'))
    is_first_run = ConfigParserProperty('1', 'General', 'is_first_run', 'app', val_type=int)
    
    def __init__(self, **kwargs):
        super(ScreenHome, self).__init__(**kwargs)
        # Procedure related.
        self.register_event_type('on_language_changed')
        
    def on_pre_enter(self, *args):
        """ Reset data collection each time before a new task is started. """
        App.get_running_app().settings.reset_current()
        self.home_msg = _('Welcome!')  # ToDo: General Information
    
        app = App.get_running_app()
        app.reset_data_collection()

        if self.is_first_run:
            # Wait 1 frame
            Clock.schedule_once(lambda dt: self.first_run_language_choice(), 1)

    def first_run_language_choice(self):
        pop = LanguagePopup()
        pop.msg = _("You can also change the language in the settings later.")
        pop.bind(on_dismiss=lambda obj: self.dispatch('on_language_changed'))
        pop.open()

    def on_language_changed(self):
        pass


class ScreenOutro(Screen):
    """ Display at the end of a session. """
    settings = ObjectProperty()
    outro_msg = StringProperty(_("Initiating..."))
    
    def on_pre_enter(self, *args):
        app = App.get_running_app()
        
        self.outro_msg = _('[color=ff00ff][b]Thank you[/b][/color] for participating!') + "\n\n"  # Workaround for i18n.
        if self.settings.is_local_storage_enabled:
            app.write_data_to_files()
            dest = App.get_running_app().get_storage_path()
            self.outro_msg += _("Files were{}saved to [i]{}[/i].").format(' ' if dest.exists() else _(' [b]not[/b] '),
                                                                          dest)
        else:
            self.outro_msg += _("Results were [b]not[/b] locally stored as files.\n"
                                "You can enable this in the settings.")
    
        app.upload_btn_enabled = self.settings.is_upload_enabled
        
    def on_upload(self):
        # Show we're busy. Heroku dyno sleeps so it can take some time for the response.
        upload_info = BlockingPopup(title=_("Uploading..."))
        upload_info.msg = _("Waking up server.\nPlease be patient.")
        upload_info.open()
        app = App.get_running_app()
        # Workaround to make info popup show up.
        Clock.schedule_once(lambda dt: app.upload_data(), 0)
        upload_info.dismiss()

    def visit_website(self):
        webbrowser.open_new(self.settings.server_uri)


class ScreenTerms(Screen):
    """ Display terms and conditions for using the app. """
    # As a workaround for internationalization to work set actual message in on_pre_enter().
    terms_msg = StringProperty(_('Initiating...'))
    is_first_run = ConfigParserProperty('1', 'General', 'is_first_run', 'app', val_type=int)
    
    def __init__(self, **kwargs):
        super(ScreenTerms, self).__init__(**kwargs)
        self.register_event_type('on_terms_close')
        
    def get_app_details(self):
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
    
    def on_pre_enter(self, *args):
        """ Update text and arrange button depending on whether this is the first time or not. """
        # ToDo: remove decline button when not first run.
        if not self.is_first_run:
            pass
            
        app_details = self.get_app_details()
        
        self.terms_msg = _("[b]Terms & Conditions[/b]\n\n"
                           "By downloading or using the app, these terms will automatically apply to you – "
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
                    terms_src="[App Privacy Policy Generator](https://app-privacy-policy-generator.firebaseapp.com/)")  # ToDo: Link?

    def on_terms_close(self, *args):
        """ Default handler for event. on_pre_leave fires too late, i.e. after on_pre_enter of next screen. """
        if self.is_first_run:
            self.is_first_run = 0
