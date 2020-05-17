from kivy.app import App
from kivy.properties import StringProperty

from . import BaseScreen
from ..i18n import _


class ScreenConsentCircleTask(BaseScreen):
    """ Tell the user about conditions of participation and require consent. """
    consent_msg = StringProperty(_("Loading..."))
    
    def __init__(self, **kwargs):
        super(ScreenConsentCircleTask, self).__init__(**kwargs)
    
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
                             "beforehand. No particular stress or even injuries are to be expected when performing the "
                             "tasks.\n\n"
                             
                             "The study will take approximately {} minutes to complete.\n\n"
                             
                             "[b]Voluntary Participation:[/b]\n"
                             "Participation in the study is voluntary."
                             "You can revoke your consent to participate in this study at any time while performing "
                             "the task and without giving reasons, without incurring any disadvantages. "
                             "After completing all the tasks you are offered to upload the collected data."
                             "You can therefore withdraw your consent to the storage and processing of the data until "
                             "the end of task completion. "
                             "If you cancel your participation before completion, or if you decide not to transmit the "
                             "data after completing the tasks, no data will be transmitted.\n\n"
  
                             "[b]Privacy:[/b]\n"
                             "No personally identifiable information such as your name, address, telephone number, "
                             "IP-address or social security number will be collected as part of the research data. "
                             "In order to identify research data that was recorded with the same device, a character "
                             "string is transmitted, which does not allow personal identification of the device or "
                             "its users. For each user account created in the app, a randomly generated character "
                             "string is created, which is transferred as part of the research data so that it can be "
                             "assigned to an anonymously participating person. The name chosen for the user account "
                             "is not transmitted. The collected research data will not reveal who you are. It is the "
                             "responsibility of the participants to protect their user account and the device "
                             "against unauthorized access.\n"
                             "The research data are first transferred to a third party provider on their servers "
                             "within the European Union. You can find out more about the data protection measures of "
                             "the third-party provider at the following Internet address:\n"
                             "https://www.heroku.com/policy/security#data-security\n"
                             "After transfer of the research data, complete deletion of the data recorded by your "
                             "participation can no longer be guaranteed, since it is not possible for us to assign a "
                             "data set to you. Furthermore, backup copies of the data are created within the "
                             "infrastructure of the third-party provider. And moreover, immediate public access to "
                             "the research data and its results from automated processing is possible, see [i]Usage of "
                             "Anonymized Data[/i].\n\n"
  
                             "[b]Usage of Anonymized Data:[/b]\n"
                             "The results and research data from this study will be published as a scientific "
                             "publication. This is done in anonymized form, i.e. without the research data on its "
                             "own being able to identify a specific person. The fully anonymized data from this study "
                             "are made available on the Internet as open data under the CC-BY-SA license. This means "
                             "that the research data can also be used for purposes other than this study, including "
                             "commercial purposes. "
                             "After completing the study, the data is possibly stored and published in a national or "
                             "international data archive. This study thus follows the recommendations of the German "
                             "Research Foundation (DFG) and the German Society for Psychology (DGPs) for quality "
                             "assurance in research.\n\n"
  
                             "I hereby confirm that I have understood the participation information described above "
                             "and that I agree to the conditions of participation mentioned.\n\n").format(duration)
