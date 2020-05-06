from kivy.properties import ObjectProperty, StringProperty

from . import BaseScreen
from ..i18n import _


class ScreenInstructCircleTask(BaseScreen):
    """ Display that tells the user what to in next task. """
    settings = ObjectProperty()
    instruction_msg = StringProperty(_("Loading..."))
    
    def __init__(self, **kwargs):
        super(ScreenInstructCircleTask, self).__init__(**kwargs)
        self.df_unconstraint_msg = _("Loading...")
        self.df_constraint_msg = _("Loading...")
    
    def on_pre_enter(self, *args):
        self.settings.next_block()
        self.update_messages()
        self.set_instruction_msg()
        self.set_img()
    
    def update_messages(self):
        if self.settings.circle_task.practice_block:
            n_trials = self.settings.circle_task.n_practice_trials
            start_msg = _("{}. practice block").format(self.settings.circle_task.practice_block)
        else:
            n_trials = self.settings.circle_task.n_trials
            block = (self.settings.current_block - bool(self.settings.circle_task.n_practice_trials) * 2)
            start_msg = _("{}. test block").format(block)
        start_msg = start_msg
        read_msg = _("Please read the instructions carefully.")
        n_trials_msg = _("There are a total of {} trials in this block.").format(n_trials)
        n_tasks = int(self.settings.circle_task.constraint) + 1
        # ToDo: ngettext for plurals
        task_suffix = self.settings.circle_task.constraint * _("s")
        n_tasks_msg = _("You have {} task{} in this block.").format(n_tasks, task_suffix)
        time_limit_msg = _("A trial ends when the outer [color=ff00ff]purple ring[/color] reaches 100% (circle closes)"
                           " and the countdown reaches 0.\nShortly thereafter you will be prompted to get ready for "
                           "the next trial.")
        task1_msg = _("Use the [b]2 sliders[/b] to match the size of the [b]white disk[/b] to the "
                      "[color=008000]green ring[/color].")
        task2_msg = _("Concurrently bring the [color=3f84f2]blue arch[/color] to the [color=3f84f2]blue disc[/color] "
                      "by using one of the sliders. It will be the same slider during the block.")
        instructions = [start_msg, n_tasks_msg, task1_msg, time_limit_msg, n_trials_msg]
        self.df_unconstraint_msg = "\n\n".join(instructions)
        instructions.insert(3, task2_msg)
        self.df_constraint_msg = "\n\n".join(instructions)
    
    def set_instruction_msg(self):
        """ Change displayed text on instruction screen. """
        if self.settings.circle_task.constraint:
            self.instruction_msg = self.df_constraint_msg
        else:
            self.instruction_msg = self.df_unconstraint_msg

    def set_img(self):
        if self.settings.circle_task.constraint:
            self.ids.CT_instruct_img.source = 'res/CT_2tasks_trial.png'
        else:
            self.ids.CT_instruct_img.source = 'res/CT_1task_trial.png'
