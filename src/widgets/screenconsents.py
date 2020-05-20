from kivy.app import App
from kivy.properties import StringProperty

from . import BaseScreen
from ..i18n import _


class ScreenConsentCircleTask(BaseScreen):
    """ Tell the user about conditions of participation and require consent. """
    consent_msg = StringProperty(_("Loading..."))
    
    def __init__(self, **kwargs):
        super(ScreenConsentCircleTask, self).__init__(**kwargs)
    
    def on_kv_post(self, base_widget):
        self.ids.consent_label.bind(on_ref_press=lambda instance, value: self.on_ref(value))
        
    def on_ref(self, value):
        if value == 'privacy':
            self.manager.show_privacy_policy()
    
    def on_consent(self):
        # Start collecting data for user_id.
        app = App.get_running_app()
        app.data_mgr.new_data_collection(app.settings.current_user)
        # Advance to the instructions.
        self.manager.transition.direction = 'up'
        self.manager.transition.duration = 0.5
        self.manager.current = self.manager.task_instructions[app.settings.current_task]
        
    def on_pre_enter(self, *args):
        # Estimate how long will the study take.
        app = App.get_running_app()
        s = app.settings.circle_task
        duration = (  (2 * s.n_practice_trials + s.n_blocks * s.n_trials)  # Number of total trials.
                    * (s.warm_up + s.trial_duration + s.cool_down)  # Duration per trial.
                    + (s.n_blocks * 120.0)  # Buffer for reading instructions.
                      )
        duration /= 60.0  # To minutes.
        duration = int(duration)  # Round.
        
        self.consent_msg = _("[size=32]Consent[/size]\n\n"
                             "Please read the following information carefully before proceeding."
                             "Use scrolling to go through the text to the end.\n\n"
                             "[b]Explanation of the experiment:[/b]\n"
                             "We are very pleased that you are interested in participating in our experiment. The goal "
                             "of this experiment is to investigate how the accuracy of performing a motion task "
                             "changes when the range of motion for solving the task gets limited by an additional, "
                             "concurrent task. The respective tasks are described and explained to you in detail "
                             "beforehand. No particular stress or even risks are to be expected when performing the "
                             "tasks.\n\n"
                             
                             "The study will take approximately {} minutes to complete.\n\n"
                             
                             "[b]Voluntary Participation:[/b]\n"
                             "Participation in the study is voluntary."
                             "You can revoke your consent to participate in this study at any time while performing "
                             "the tasks and without giving reasons, without incurring any disadvantages. To do so just "
                             "press the back button during the study or close the app."
                             "After completing all the tasks you are offered to upload the collected research data to "
                             "the Internet. "
                             "You can therefore withdraw your consent to the online storage and processing of the data "
                             "until the end of task completion. "
                             "If you cancel your participation before completion, or if you decide not to transmit the "
                             "data after completing the tasks, no data will be transmitted."
                             "\n\n"
                             "Please review the [ref=privacy][color=0000ff]Privacy Policy (press here)[/color][/ref] "
                             "carefully for information on what kind of data we collect and how we intend to use them."
                             "\n\n"
                             "I hereby confirm that I have read and understood the participation information described "
                             "above as well as the [ref=privacy][color=0000ff]Privacy Policy[/color][/ref]. "
                             "I agree to the conditions of participation and Privacy Policy.\n\n").format(duration)
