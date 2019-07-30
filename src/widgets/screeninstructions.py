from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty

from ..i18n import _


class ScreenInstructCircleTask(Screen):
    """ Display that tells the user what to in next task. """
    settings = ObjectProperty()
    instruction_msg = StringProperty(_("Initiating..."))
    
    def __init__(self, **kwargs):
        super(ScreenInstructCircleTask, self).__init__(**kwargs)
        self.df_unconstraint_msg = _("Initiating...")
        self.df_constraint_msg = _("Initiating...")
    
    def on_pre_enter(self, *args):
        self.settings.next_block()
        self.update_messages()
        self.set_instruction_msg()
    
    def update_messages(self):
        n_trials_msg = _("There are a total of {} trials in this block.").format(self.settings.circle_task.n_trials)
        n_tasks = int(self.settings.circle_task.constraint) + 1
        # ToDo: ngettext for plurals
        task_suffix = self.settings.circle_task.constraint * _("s")
        n_tasks_msg = _("You have {} task{} in this block.").format(n_tasks, task_suffix) + "\n\n"
        time_limit_msg = _("A trial ends when the outer [color=ff00ff]purple ring[/color] reaches 100% (circle closes)"
                           " and the countdown reaches 0.\nShortly thereafter you will be prompted to get ready for "
                           "the next trial.") + "\n\n"
        task1_msg = _("Use the [b]2 sliders[/b] to match the size of the [b]white disk[/b] to the "
                      "[color=008000]green ring[/color].") + "\n\n"
        task2_msg = _("Concurrently bring the [color=3f84f2]blue arch[/color] to the [color=3f84f2]blue disc[/color] "
                      "by using one of the sliders. It will be the same slider during the block.") + "\n\n"
        self.df_unconstraint_msg = n_tasks_msg + task1_msg + time_limit_msg + n_trials_msg
        self.df_constraint_msg = n_tasks_msg + task1_msg + task2_msg + time_limit_msg + n_trials_msg
    
    def set_instruction_msg(self):
        """ Change displayed text on instruction screen. """
        if self.settings.circle_task.constraint:
            self.instruction_msg = self.df_constraint_msg
        else:
            self.instruction_msg = self.df_unconstraint_msg
