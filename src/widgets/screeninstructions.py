from kivy.properties import ObjectProperty, StringProperty

from . import BaseScreen
from ..i18n import _


class ScreenInstructCircleTask(BaseScreen):
    """ Display that tells the user what to in next task. """
    settings = ObjectProperty()
    msg = StringProperty()
    title = StringProperty()
    
    def __init__(self, **kwargs):
        super(ScreenInstructCircleTask, self).__init__(**kwargs)
    
    def on_pre_enter(self, *args):
        self.settings.next_block()
        self.title = self.get_title()
        self.msg = self.get_message()
        self.set_img()

    def get_title(self):
        ct = self.settings.circle_task
        if ct.practice_block:
            start_msg = _("{}. Practice Block").format(ct.practice_block)
        else:
            block = (self.settings.current_block - bool(ct.n_practice_trials) * 2)
            start_msg = _("{}. Testing Block").format(block)
        return start_msg
        
    def get_message(self):
        ct = self.settings.circle_task
        if ct.practice_block:
            n_trials = ct.n_practice_trials
        else:
            n_trials = ct.n_trials
        read_msg = _("Please read the following information carefully before proceeding. Use scrolling to go through "
                     "the whole text. "
                     "At the end of this text you'll find an exemplary image of the task in progress."
                     )
        n_trials_msg = _("There are a total of {} trials in this block.").format(n_trials)
        n_tasks = int(ct.constraint) + 1
        # ToDo: ngettext for plurals
        task_suffix = ct.constraint * _("s")
        n_tasks_msg = _("You have {0} task{1} in this block. Be as quick and as accurate as possible while performing "
                        "the task{1}").format(n_tasks, task_suffix)
        vibration_msg = _("This will also be signaled to you by a short vibration. ") \
                        * self.settings.is_vibrate_enabled
        time_limit_msg = _("A trial starts by giving you {0} seconds time to prepare for the trial. During this time "
                           "the sliders are inactive and can't be moved. This is indicated by their dimmed color. "
                           "After this preparation phase the sliders become active. You can then touch and move them. "
                           "{4}"
                           "You'll have {1} seconds time to complete the task{3}. The time limitation is visualized "
                           "by counting down the seconds in the middle of the screen, as well as by an outer "
                           "[color=ff00ff]purple ring[/color] that will close as the time runs out. A trial ends "
                           "when the outer [color=ff00ff]purple ring[/color] closes and the countdown reaches 0.\n"
                           "Shortly thereafter ({2} seconds) you will be prompted to get ready for the next trial. "
                           ).format(ct.warm_up, ct.trial_duration, ct.cool_down, task_suffix, vibration_msg)
        time_limit_msg += _("The events for the start and end of the countdown for each trial will play distinctive "
                            "sounds. ") * self.settings.is_sound_enabled
        task1_msg = _("Hold your device with both hands so your thumbs can reach their respective side of the "
                      "screen comfortably.\n"
                      "In the middle of the screen you'll see a [b]white disk[/b] enclosed by a larger "
                      "[color=008000]green ring[/color]. Your task in each trial is to match the size of this "
                      "[b]white disk[/b] to the size of the [color=008000]green ring[/color], so the [b]white disk[/b] "
                      "accurately touches the [color=008000]green ring[/color]. You control the size of the disc by "
                      "using the [b]2 sliders[/b] located to the left and right side of the display with your thumbs. "
                      "Both sliders have an influence on the size of the disc and you'll need both at the same time to "
                      "get the [b]white disk[/b] to touch the [color=008000]green ring[/color]. Please perform the "
                      "task in a continuous motion and let go of the sliders when you think you reached the goal. "
                      "The sliders are deactivated once you let go of them."
                      )
        task2_msg = _("In addition you'll have to fulfill another task concurrently to the first task. On top of the "
                      "[color=008000]green ring[/color] there's a [color=3f84f2]blue arch[/color] which length is "
                      "controlled only by the slider with the blue handle and bar. You have to make the "
                      "[color=3f84f2]blue arch[/color] touch the small [color=3f84f2]blue dot[/color] that is sitting "
                      "on the [color=008000]green ring[/color]. Note that the blue slider still influences the size of "
                      "the [b]white disk[/b] as well. Accomplish both tasks at the same time!")
        instructions = [read_msg,
                        n_tasks_msg,
                        task1_msg,
                        task2_msg * ct.constraint,
                        time_limit_msg,
                        n_trials_msg,
                        ]
        msg = "\n\n".join(instructions)
        msg = msg.replace("\n\n\n\n", "\n\n")  # Cleanup if there's no 2nd task.
        return msg
    
    def set_img(self):
        if self.settings.circle_task.constraint:
            self.ids.instruct_img.source = 'res/CT_2tasks_trial.png'
        else:
            self.ids.instruct_img.source = 'res/CT_1task_trial.png'
