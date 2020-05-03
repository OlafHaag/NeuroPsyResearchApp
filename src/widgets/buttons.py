from kivymd.uix.list import OneLineAvatarIconListItem


class ItemConfirm(OneLineAvatarIconListItem):
    divider = None

    def __init__(self, **kwargs):
        # Add a value keyword that's stored in the item. If none is given, use the text.
        self.value = kwargs.pop('value', self.text)
        super(ItemConfirm, self).__init__(**kwargs)
        self.active = False
        self.ids.check.allow_no_selection = False
    
    @property
    def active(self):
        return self.__active
    
    @active.setter
    def active(self, state):
        #print(f"{'de' if not state else ''}activate {self.value}!")
        self.__active = state
    
    def set_icon(self, instance_check):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False
