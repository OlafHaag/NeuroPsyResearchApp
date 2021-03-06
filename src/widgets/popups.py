import webbrowser

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, ConfigParserProperty

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRectangleFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDIcon
from kivymd.uix.list import BaseListItem
from kivymd.uix.menu import MDDropdownMenu
from plyer import email

from . import CheckItem, UserItem, UserAddItem, RecycleLabel
from ..i18n import (_,
                    list_translated_languages,
                    translation_to_language_code,
                    DEFAULT_LANGUAGE)
from ..utility import create_user_identifier, switch_language, get_app_details, markdown_to_bbcode
from privacypolicy import get_policy
from terms import get_terms


# ToDo: Distinguish Info, Warning and Error by icon or color.
class SimplePopup(MDDialog):
    """ Simple popup with only an OK button. """
    def __init__(self, **kwargs):
        default_kwargs = dict(
            size_hint_x=0.8,
            auto_dismiss=False,
            buttons=[MDRaisedButton(text=_("OK"),
                                    on_release=self.dismiss)],
        )
        default_kwargs.update(kwargs)
        super(SimplePopup, self).__init__(**default_kwargs)
    
    def on_kv_post(self, base_widget):
        self.ids.text.bind(on_ref_press=lambda instance, value: self.open_link(value))

    def on_open(self):
        # Check height of popup, if it's too large, make smaller.
        container = self.ids.container
        if container.height > Window.height:
            container.size_hint_y = 0.95
            container.padding = ('24dp', '0dp', '8dp', '0dp')
            self.ids.text.font_style = 'Body2'
            self._spacer_top = 0
    
    def open_link(self, url):
        url = url.strip('"')
        if url.startswith('https://'):
            webbrowser.open_new(url)
        elif url.startswith('mailto:'):
            recipient = url[7:]
            details = get_app_details()
            email.send(recipient=recipient, subject=f"{details['appname']}", create_chooser=True)
            

class BlockingPopup(MDDialog):
    
    def __init__(self, **kwargs):
        kwargs.update(auto_dismiss=False)
        # ToDo: Properly position progress indicator.
        super(BlockingPopup, self).__init__(**kwargs)
        self.ids.spacer_top_box.add_widget(MDIcon(icon='progress-upload', halign='center'))


class ConfirmPopup(MDDialog):
    """ Simple popup asking for confirmation or cancellation.
    Has on_confirm event that can be bound to.
    """
    def __init__(self, **kwargs):
        self.register_event_type('on_confirm')
        default_kwargs = dict(
            title=_("Do you want to continue?"),
            type='simple',
            auto_dismiss=False,  # Otherwise the callback doesn't fire?!
            buttons=[
                MDRectangleFlatButton(
                    text=_("CANCEL"),
                    on_release=self.dismiss
                ),
                MDRaisedButton(
                    text=_("OK"),
                    on_release=lambda instance: self.dispatch('on_confirm'),
                ),
            ],
        )
        default_kwargs.update(kwargs)
        super(ConfirmPopup, self).__init__(**default_kwargs)
    
    def on_confirm(self, *args):
        self.dismiss()


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
            text=_("You can also change the language in the settings later."),  # Is disabled in type "confirmation". :(
            type="confirmation",
            auto_dismiss=False,
            items=items,
            buttons=[MDRaisedButton(
                text=_("OK"),
                on_release=self.dismiss
            ),
            ]
        )
        default_kwargs.update(kwargs)
        super(LanguagePopup, self).__init__(**default_kwargs)
        self.register_event_type('on_language_set')
    
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
        # If language did not change trigger event now.
        if lang_code == self.current_language:
            self.dispatch('on_language_set')
        # Update the config value. The on_current_language callback will take care of switching to the language.
        self.current_language = lang_code
        
    def on_current_language(self, instance, lang):
        """ Switches the language when config value changed.
        Only called when language value in config actually changed.
        """
        switch_language(lang)
        self.dispatch('on_language_set')

    def on_language_set(self):
        pass
    
    def on_pre_open(self):
        self.select_current_language()

    def on_pre_dismiss(self):
        self.change_language()


class UsersPopup(MDDialog):
    """ Dialog for User management. """
    current_user = ConfigParserProperty('Default', 'General', 'current_user', 'app', val_type=str)
    current_language = ConfigParserProperty('en', 'Localization', 'language', 'app', val_type=str)
    
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
            item = UserItem(text=user_aliases[user_ids.index(user_id)], value=user_id, height=dp(40))
            item.bind(on_remove=lambda instance: self.dispatch('on_remove_user', instance.value, instance.text),
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
            item = UserItem(text=user_aliases[ids.index(user_id)], value=user_id, height=dp(40))
            item.bind(on_remove=lambda instance: self.dispatch('on_remove_user', instance.value, instance.text),
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
    
    def remove_item(self, user_id):
        """ Remove widget from list. """
        instance = None
        selected_user_id = None
        # Get currently selected item.
        for item in self.items[:-1]:
            if item.active:
                selected_user_id = item.value
            if item.value == user_id:
                instance = item
            if selected_user_id and instance:
                break
        try:
            self.dispatch('on_remove_user', instance.value, instance.text)
            self.ids.box_items.remove_widget(instance)  # Maybe do garbage collection with gc.collect()?
            # If removed item was current user, select first entry.
            removed_id = instance.value
            self.items.remove(instance)
            if removed_id == selected_user_id:
                self.items[0].set_icon(self.items[0].ids.check)
        except AttributeError:
            print(f"ERROR: Can't remove user {user_id} from list. Not found.")
        self.set_height()
    
    def set_height(self):
        """ Racalculate the height of the popup. """
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
    
    def on_current_language(self, *args):
        # Language is switched AFTER this event fires, so we have to reschedule to next frame.
        Clock.schedule_once(lambda dt: self._update_language(), 1)
    
    def _update_language(self):
        self.title = _("Choose Active User")
        # Instead of clearing all widgets and rebuilding, just assert that the last item is always add user.
        self.items[-1].text = _("Add User")
    
    def on_pre_open(self):
        self.select_item(self.current_user)
        # In case the orientation was changed, we need to update the height.
        self.set_height()
    
    def on_dismiss(self):
        pass


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
                    on_release=lambda instance: self.confirm(),
                ),
            ],
        )
        default_kwargs.update(kwargs)
        super(TextInputPopup, self).__init__(**default_kwargs)
        self.register_event_type('on_confirm')
        self.ids.title.padding = (0, '12dp')
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
            size_hint_x=0.8,
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
        self.content_cls.set_text()
        super(UserEditPopup, self).open()
        
    def confirm(self):
        if not self.content_cls.ids.textfield.error:
            self.dispatch('on_user_edited', user_id=self.user_id, user_alias=self.input)
            self.dismiss()
    
    def on_dismiss(self):
        # ToDo: Reset error status of textfield.
        #self.property('user_alias').dispatch(self)
        self.content_cls.ids.textfield.error = False
    
    def on_user_edited(self, *args, **kwargs):
        """ Default implementation of event. """
        pass


class UserInput(TextInputContent):
    """ Content class for UserInputPopup. """
    
    def set_text(self):
        self.description = _("This name is just for you. It won't be uploaded to the server.")
        self.ids.textfield.hint_text = _("Enter Pseudonym")
        
    def check_errors(self, *args):
        self.ids.textfield.error = len(self.ids.textfield.text.strip(' ')) == 0


class DemographicsPopup(MDDialog):
    """ Popup for collecting demographic data on user. """
    input = StringProperty()
    
    def __init__(self, **kwargs):
        default_kwargs = dict(
            title=_("Demographic Information"),
            type="custom",
            content_cls=DemographicsContent(),
            auto_dismiss=False,
            size_hint_x=0.8,
            buttons=[
                MDRaisedButton(
                    text=_("OK"),
                    on_release=lambda instance: self.confirm(),
                ),
            ],
        )
        default_kwargs.update(kwargs)
        super(DemographicsPopup, self).__init__(**default_kwargs)
        self.register_event_type('on_confirm')
        self.ids.spacer_top_box.padding = (0, 0, 0, '8dp')
        self.ids.root_button_box.height = '64dp'
    
    def on_open(self):
        self._spacer_top = self.content_cls.height + self.ids.title.height + self.ids.root_button_box.height
    
    def confirm(self):
        self.dispatch('on_confirm',
                      self.content_cls.get_age_group(),
                      self.content_cls.get_gender_code(),
                      self.content_cls.get_exp_code())
        self.dismiss()
        
    def on_confirm(self, *args):
        pass
    

class DemographicsContent(MDBoxLayout):
    """ Content class for DemographicsPopup. Has dropdowns for age and gender options. """
    
    def __init__(self, **kwargs):
        super(DemographicsContent, self).__init__(**kwargs)
        self._no_answer_txt = _("no answer")
        # Age
        age_items = [{"text": self._no_answer_txt}, {'text': "<20"}] \
                  + [{"text": f"{i}-{i+9}"} for i in range(20, 80, 10)] \
                  + [{'text': "80+"}]
        self.ids.age_dropdown.text = age_items[0]['text']
        self.age_menu = MDDropdownMenu(
            caller=self.ids.age_dropdown,
            items=age_items,
            use_icon_item=False,
            callback=self.set_age_item,
            width_mult=4,
        )
        # Gender
        gender_items = [{'text': txt} for txt in (self._no_answer_txt, _("male"), _("female"), _("diverse"))]
        self.ids.gender_dropdown.text = gender_items[0]['text']
        self.gender_menu = MDDropdownMenu(
            caller=self.ids.gender_dropdown,
            items=gender_items,
            use_icon_item=False,
            callback=self.set_gender_item,
            width_mult=4,
        )
        # Gaming experience with touch devices.
        self.exp_answers = (self._no_answer_txt,
                            _("daily"),
                            _("several times a week"),
                            _("several times a month"),
                            _("several times a year"),
                            _("never"))
        exp_items = [{'text': txt} for txt in self.exp_answers]
        self.ids.exp_dropdown.text = exp_items[0]['text']
        self.exp_menu = MDDropdownMenu(
            caller=self.ids.exp_dropdown,
            items=exp_items,
            use_icon_item=False,
            callback=self.set_exp_item,
            width_mult=4,
        )

    def set_age_item(self, instance):
        self.ids.age_dropdown.set_item(instance.text)
        self.age_menu.dismiss()
        
    def set_gender_item(self, instance):
        self.ids.gender_dropdown.set_item(instance.text)
        self.gender_menu.dismiss()
    
    def set_exp_item(self, instance):
        self.ids.exp_dropdown.set_item(instance.text)
        self.exp_menu.dismiss()
        
    def get_age_group(self):
        if self.ids.age_dropdown.current_item == self._no_answer_txt:
            return ""
        else:
            return self.ids.age_dropdown.current_item  # Is '' by default when nothing was selected.
        
    def get_gender_code(self):
        if self.ids.gender_dropdown.current_item == _("male"):
            return 'm'
        elif self.ids.gender_dropdown.current_item == _("female"):
            return 'f'
        elif self.ids.gender_dropdown.current_item == _("diverse"):
            return 'd'
        else:
            return ""
        
    def get_exp_code(self):
        for i, answer in enumerate(self.exp_answers):
            if self.ids.exp_dropdown.current_item == answer:
                return i - 1  # No answer is hence coded as -1 here.
        else:
            return -1
        
        
class DifficultyRatingPopup(MDDialog):
    """ Ask the user how they perceived the difficulty of the task as this may be a confounding variable. """

    def __init__(self, **kwargs):
        # Gather options. Likert scale.
        options = [_("Very easy"),  _("Easy"),  _("Neutral"), _("Difficult"), _("Very difficult")]
        items = [CheckItem(text=opt, value=i, height=dp(36)) for i, opt in enumerate(options)]
        default_kwargs = dict(
            title=_("How difficult did you find the task?"),
            type="confirmation",
            auto_dismiss=False,
            items=items,
            buttons=[MDRaisedButton(
                text=_("OK"),
                on_release=lambda instance: self.confirm(),
            ),
            ]
        )
        default_kwargs.update(kwargs)
        super(DifficultyRatingPopup, self).__init__(**default_kwargs)
        self.register_event_type('on_confirm')
        # Make 'Neutral' default.
        self.items[2].set_icon(self.items[2].ids.check)

    def set_height(self):
        """ Racalculate the height of the popup. """
        height = 0
        for item in self.items:
            if issubclass(item.__class__, BaseListItem):
                height += item.height  # calculate height contents
    
        if (height + self.get_normal_height()) > Window.height:
            self.set_normal_height()
            self.ids.scroll.height = self.get_normal_height()
        else:
            self.ids.scroll.height = height
    
    def on_kv_post(self, base_widget):
        self.set_height()
        
    def on_pre_open(self):
        self.ids.scroll.scroll_y = 0.5
        
    def get_current_rating(self):
        """ Get active item. """
        for item in self.items:
            if item.active:
                return item.value
                
    def confirm(self):
        self.dispatch('on_confirm', self.get_current_rating())
        self.dismiss()
        
    def on_confirm(self, *args):
        pass
        
        
class PolicyPopup(SimplePopup):
    """ Display privacy policy for using the app. """
    
    def __init__(self, **kwargs):
        default_kwargs = dict(
            type='custom',
            size_hint_x=0.9,
        )
        if 'content_cls' not in kwargs:
            content = RecycleLabel(text=self._get_text(get_policy()), halign='justify')
            content.bind(on_ref_press=lambda instance, value: self.open_link(value))
            default_kwargs.update(content_cls=content)
            
        default_kwargs.update(kwargs)
        super(PolicyPopup, self).__init__(**default_kwargs)
        # Reduce the emtpy space.
        self.ids.spacer_top_box.size_hint_y = 1
        self.ids.spacer_top_box.padding = (0, 0, 0, 0)
        self.ids.container.size_hint_y = 0.9
        self.ids.container.padding = ('8dp', '8dp', '8dp', '0dp')  # left, top, right, bottom
        
    def _get_text(self, content_md):
        details = get_app_details()
        text = markdown_to_bbcode(content_md).format(appname=details['appname'],
                                                     author=details['author'],
                                                     contact=details['contact'],
                                                     source=details['source'])
        return text

    def on_pre_open(self):
        # In case the language changed, reload the policy text.
        self.content_cls.text = self._get_text(get_policy())
        self.content_cls.ids.rv.scroll_y = 1
        

class TermsPopup(PolicyPopup):
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
        # Show Terms and Privacy Policy together on first run.
        if self.is_first_run:
            text = self._get_text(get_terms()) + "\n\n" + self._get_text(get_policy())
        else:
            text = self._get_text(get_terms())
            
        content = RecycleLabel(text=text, halign='justify')
        content.bind(on_ref_press=lambda instance, value: self.open_link(value))
        
        default_kwargs = dict(
            content_cls=content,
            buttons=[
                self.__reject_btn,
                self.__accept_btn,
            ],
        )
        default_kwargs.update(kwargs)
        super(TermsPopup, self).__init__(**default_kwargs)

    def on_dismiss(self):
        if self.is_first_run:
            self.is_first_run = 0
            
    def on_pre_open(self):
        # When the terms are dismissed the first time, it means they were accepted.
        if not self.is_first_run:
            self.content_cls.text = self._get_text(get_terms())
            self.ids.button_box.remove_widget(self.__reject_btn)
            self.__accept_btn.text = _("CLOSE")
        self.content_cls.ids.rv.scroll_y = 1
