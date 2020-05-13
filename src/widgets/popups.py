from configparser import ConfigParser

from kivy.app import App
from kivy.properties import StringProperty, ConfigParserProperty
from kivy.core.window import Window

from kivymd.uix.button import MDRectangleFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import BaseListItem

from . import CheckItem, UserItem, UserAddItem
from ..i18n import (_,
                    list_translated_languages,
                    translation_to_language_code,
                    DEFAULT_LANGUAGE)
from ..utility import create_user_identifier


# ToDo: Distinguish Info, Warning and Error by icon or color.
class SimplePopup(MDDialog):
    
    def __init__(self, **kwargs):
        kwargs.update(buttons=[MDRaisedButton(text=_("OK"), on_release=self.dismiss)], auto_dismiss=False)
        super(SimplePopup, self).__init__(**kwargs)


class BlockingPopup(MDDialog):
    
    def __init__(self, **kwargs):
        kwargs.update(auto_dismiss=False)
        # ToDo: Display progress indicator. e.g. 'progress-upload' icon
        super(BlockingPopup, self).__init__(**kwargs)


class LanguagePopup(MDDialog):
    """ For first run ask which language to use. """
    current_language = ConfigParserProperty(DEFAULT_LANGUAGE, 'Localization', 'language', 'app', val_type=str)
    
    def __init__(self, **kwargs):
        # Gather options.
        languages = list_translated_languages()
        languages.sort()
        items = [CheckItem(text=lang, value=translation_to_language_code(lang)) for lang in languages]
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
    
    def on_current_language(self, *args):
        pass
        
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
        # Update the config value. The on_current_language callback will take care of switching to the language.
        self.current_language = lang_code

    def on_open(self):
        self.select_current_language()

    def on_dismiss(self):
        self.change_language()


class UsersPopup(MDDialog):
    """ Dialog for User management. """
    current_user = ConfigParserProperty('Default', 'General', 'current_user', 'app', val_type=str)
    
    def __init__(self, **kwargs):
        self.register_event_type('on_add_user')
        self.register_event_type('on_edit_user')
        self.register_event_type('on_remove_user')
        
        # Gather options.
        items = self.get_items()
        default_kwargs = dict(
            title=_("Choose Active User"),
            type="confirmation",
            auto_dismiss=False,  # Otherwise the callback doesn't fire?!
            size_hint_x=0.8,
            items=items,
            buttons=[MDRaisedButton(
                text=_("OK"),
                on_release=self.dismiss
            ),
            ]
        )
        default_kwargs.update(kwargs)
        super(UsersPopup, self).__init__(**default_kwargs)
        app = App.get_running_app()
        app.settings.bind(user_ids=lambda instance, ids: self.update_items(ids),
                          user_aliases=lambda instance, aliases: self.update_aliases(aliases))
    
    def get_items(self):
        """ Return list items for user management. """
        app = App.get_running_app()
        user_ids = app.settings.user_ids
        user_aliases = app.settings.user_aliases
        items = list()
        for user_id in user_ids:
            item = UserItem(text=user_aliases[user_ids.index(user_id)], value=user_id)
            item.bind(on_remove=self.remove_item,
                      on_edit=lambda instance: self.dispatch('on_edit_user', instance.value, instance.text),
                      on_active=lambda instance, state: self.set_current_user(instance.value, state),
                      )
            items.append(item)
        # The last item should be to add a new user.
        items.append(UserAddItem(text=_("Add User"),
                                 value='add',
                                 on_release=lambda instance: self.dispatch('on_add_user'),
                                 )
                     )
        return items

    def set_current_user(self, user_id, state):
        """ Sets the user_id to be current user if state is True. """
        if state:
            self.current_user = user_id
        
    def select_item(self, user_id):
        """ Activate item with value equal to user_id. """
        for item in self.items:
            if item.value == user_id:
                item.set_icon(item.ids.check)
                break
        self.current_user = user_id
    
    def update_items(self, ids):
        """ Add widgets that are missing from ids. """
        app = App.get_running_app()
        user_aliases = app.settings.user_aliases
        # Gather values of present items.
        item_ids = [i.value for i in self.items[:-1]]  # Leave out the add user item at the end.
        # Get (asymmetric) difference between the two. Only those, that aren't present yet.
        diff = set(ids).difference(item_ids)
        for user_id in diff:
            item = UserItem(text=user_aliases[ids.index(user_id)], value=user_id)
            item.bind(on_remove=self.remove_item,
                      on_edit=lambda instance: self.dispatch('on_edit_user', instance.value, instance.text),
                      on_active=lambda instance, state: self.set_current_user(instance.value, state),
                      )
            self.edit_padding_for_item(item)
            self.items.insert(-1, item)
            self.ids.box_items.add_widget(item, index=1)
        self.set_height()
    
    def update_aliases(self, aliases):
        """ Update all the texts of the widgets. """
        # Gather values of present items.
        item_texts = [i.text for i in self.items[:-1]]  # Leave out the add user item at the end.
        # In case a new user was just added or removed, we may already be up-to-date.
        if len(item_texts) != len(aliases):
            return
        # Now we assume the order of items is the same as in settings.user_aliases.
        for i, item in enumerate(self.items[:-1]):
            # Just set all aliases.
            item.text = aliases[i]
    
    def remove_item(self, instance):
        """ Remove widget from list. """
        # Get currently selected item.
        for item in self.items[:-1]:
            if item.active:
                selected_user_id = item.value
                break
        self.dispatch('on_remove_user', instance.value, instance.text)
        self.ids.box_items.remove_widget(instance)  # Maybe do garbage collection with gc.collect()?
        self.items.remove(instance)
        # If removed item was current user, select first entry.
        if instance.value == selected_user_id:
            self.items[0].set_icon(self.items[0].ids.check)
        self.set_height()
    
    def set_height(self):
        height = 0
    
        for item in self.items:
            if issubclass(item.__class__, BaseListItem):
                height += item.height  # calculate height contents
    
        if (height + self.get_normal_height()) > Window.height:
            self.set_normal_height()
            self.ids.scroll.height = self.get_normal_height()
        else:
            self.ids.scroll.height = height
    
    def on_items(self, instance, items):
        """ Disable remove button, when only 1 item left. """
        # When there's only 1 id, prevent the last one to be deleted.
        if len(items) <= 2:  # Account for add user item.
            self.items[0].remove_disabled = True
        else:
            self.items[0].remove_disabled = False
            
    def on_add_user(self):
        # It's the manager's task to decide what should happen now.
        pass
    
    def on_edit_user(self, *args, **kwargs):
        # It's the manager's task to decide what should happen now.
        pass
    
    def on_remove_user(self, user_id, user_alias):
        pass
    
    def on_open(self):
        self.select_item(self.current_user)
    
    def on_dismiss(self):
        pass
        
        
class ScrollText(MDBoxLayout):
    text = StringProperty(_('Loading...'))

    def __init__(self, **kwargs):
        self.text = kwargs.pop('text', _("not found"))
        self.height = (Window.height * 0.8) - 100
        super(ScrollText, self).__init__(**kwargs)


class TextInputPopup(MDDialog):
    """ Prompt user to input text.
    Content class needs to have property 'input'.
    """
    input = StringProperty()

    def __init__(self, **kwargs):
        default_kwargs = dict(
            title=_("Set New Value"),
            type="custom",
            content_cls=TextInputContent(),
            auto_dismiss=False,  # Otherwise the callbacks don't fire?!
            buttons=[
                MDRectangleFlatButton(
                    text=_("CANCEL"),
                    on_release=self.dismiss
                ),
                MDRaisedButton(
                    text=_("OK"),
                    on_release=lambda _: self.confirm(),
                ),
            ],
        )
        default_kwargs.update(kwargs)
        super(TextInputPopup, self).__init__(**default_kwargs)
        self.register_event_type('on_confirm')
        # Link this class' input to content_cls' input.
        # Property events are not dispatched when the values are equal, so this doesn't result in endless recursion.
        self.bind(input=self.content_cls.setter('input'))
        self.content_cls.bind(input=self.setter('input'))

    def confirm(self):
        if not self.content_cls.ids.textfield.error:
            self.dispatch('on_confirm', self.input)
            self.dismiss()
    
    def on_confirm(self, value):
        pass


class TextInputContent(MDBoxLayout):
    """ Content class for TextInputPopup. """
    description = StringProperty()
    input = StringProperty()
    
    def __init__(self, **kwargs):
        super(TextInputContent, self).__init__(**kwargs)
        self.ids.textfield.bind(text=self.on_text, on_text_validate=self.check_errors, on_touch_up=self.check_errors)
    
    def check_errors(self, *args):
        # e.g. when required:
        #self.ids.textfield.error = len(self.ids.textfield.strip(' ')) == 0
        pass
    
    def on_text(self, instance, value):
        self.input = value  # Somehow StringProperty isn't updated by input. Do it manually.


class NumericInputPopup(TextInputPopup):
    
    def __init__(self, **kwargs):
        _type = kwargs.pop('type', str)
        default_kwargs = dict(
            content_cls=NumericInputContent(type=_type),
        )
        default_kwargs.update(kwargs)
        super(NumericInputPopup, self).__init__(**default_kwargs)


class NumericInputContent(TextInputContent):
    """ Content class for NumericInputPopup. Checks for float and integer input. """

    def __init__(self, **kwargs):
        self.type = kwargs.pop('type', str)
        super(NumericInputContent, self).__init__(**kwargs)
        
    def check_errors(self, *args):
        # In case comma is used instead of dot.
        text = self.ids.textfield.text.replace(",", ".")
        try:
            self.type(text)
            self.ids.textfield.error = False
        except ValueError:
            self.ids.textfield.error = True
            
    def on_text(self, instance, value):
        num_string = value.replace(",", ".")
        try:
            if self.type is int:
                num = int(float(num_string))
            elif self.type is float:
                num = float(num_string)
            else:
                # If we don't know the type.
                is_float = '.' in num_string
                if is_float:
                    num = float(num_string)
                else:
                    num = int(num_string)
            self.input = str(num)
        except ValueError:
            return
     
        
class UserEditPopup(TextInputPopup):
    """ Dialog for editing user information. """

    def __init__(self, **kwargs):
        self.user_id = None
        default_kwargs = dict(
            title=_("Edit User"),
            content_cls=UserInput(),
            size_hint_x=0.6,
        )
        default_kwargs.update(kwargs)
        super(UserEditPopup, self).__init__(**default_kwargs)
        self.register_event_type('on_user_edited')
    
    def open(self, *args, **kwargs):
        is_new = kwargs.pop('add', False)
        self.user_id = kwargs.pop('user_id', None)
        if not self.user_id:
            self.user_id = create_user_identifier()
            
        self.title = _("Add New User") if is_new else _("Edit User")
        self.input = kwargs.pop('user_alias', '')
        super(UserEditPopup, self).open()
        
    def confirm(self):
        if not self.content_cls.ids.textfield.error:
            self.dispatch('on_user_edited', user_id=self.user_id, user_alias=self.input)
            self.dismiss()
    
    def on_dismiss(self):
        # FixMe: Reset error status of textfield.
        #self.property('user_alias').dispatch(self)
        self.content_cls.ids.textfield.error = False
    
    def on_user_edited(self, *args, **kwargs):
        """ Default implementation of event. """
        pass


class UserInput(TextInputContent):
    """ Content class for UserInputPopup. """
    def check_errors(self, *args):
        self.ids.textfield.error = len(self.ids.textfield.text.strip(' ')) == 0


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
