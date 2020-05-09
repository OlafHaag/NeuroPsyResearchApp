from kivy.properties import StringProperty, BooleanProperty

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineAvatarIconListItem, OneLineIconListItem, IRightBodyTouch
from kivymd.uix.button import MDRoundFlatButton


class CheckItem(OneLineAvatarIconListItem):
    divider = None
    
    def __init__(self, **kwargs):
        # Add a value keyword that's stored in the item. If none is given, use the text.
        self.value = kwargs.pop('value', self.text)
        super(CheckItem, self).__init__(**kwargs)
        self.register_event_type('on_active')
        self.active = False
        self.ids.check.allow_no_selection = False
    
    @property
    def active(self):
        return self.__active
    
    @active.setter
    def active(self, state):
        self.__active = state
        self.dispatch('on_active', state)
    
    def set_icon(self, instance_check):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False
    
    def on_active(self, *args):
        pass


class UserItem(CheckItem):
    remove_disabled = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super(UserItem, self).__init__(**kwargs)
        self.register_event_type('on_edit')
        self.register_event_type('on_remove')

    def on_edit(self, *args):
        pass

    def on_remove(self, *args):
        pass
    
    
class UserAddItem(OneLineIconListItem):
    divider = None

    def __init__(self, **kwargs):
        # Add a value keyword that's stored in the item. If none is given, use the text.
        self.value = kwargs.pop('value', self.text)
        super(UserAddItem, self).__init__(**kwargs)


class ListItemContainer(IRightBodyTouch, MDBoxLayout):
    adaptive_width = True

    
class TaskButton(MDRoundFlatButton):
    task = StringProperty(allownone=False)
