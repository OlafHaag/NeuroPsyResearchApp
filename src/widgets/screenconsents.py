from kivy.properties import StringProperty

from . import BaseScreen
from ..i18n import _


class ScreenConsentCircleTask(BaseScreen):
    """ Tell the user about conditions of participation and require consent. """
    consent_msg = StringProperty(_("Loading..."))
    
    def __init__(self, **kwargs):
        super(ScreenConsentCircleTask, self).__init__(**kwargs)
    
    def on_pre_enter(self, *args):
        # ToDo:  Translate to English. Update Information
        self.consent_msg = _("[size=32]Consent[/size]\n\n"
                             "Lesen Sie bitte die folgenden Informationen aufmerksam durch, bevor Sie fortfahren. "
                             "Scrollen Sie dazu bis zum Ende des Textes.\n\n"
                             "[b]Erklärung zum Experiment:[/b]\n"
                             "Es freut uns sehr, dass Sie sich bereit erklärt haben, an unserem Experiment "
                             "teilzunehmen. Dieses Experiment hat zum Ziel zu erforschen, wie sich die Genauigkeit bei "
                             "der Ausführung einer Bewegungsaufgabe ändert, wenn gleichzeitig eine weitere Aufgabe mit "
                             "der Bewegung bewältigt wird. Die jeweilige Aufgabe wird Ihnen zuvor genau beschrieben "
                             "und erklärt. Bei der Ausführung der Aufgaben sind keinerlei besondere Belastungen oder "
                             "gar Schäden zu erwarten.\n\n"
                             
                             "[b]Freiwilligkeit:[/b]\n"
                             "Die Teilnahme an der Studie ist freiwillig. "
                             "Sie können jederzeit und ohne Angabe von Gründen Ihre Einwilligung zur Teilnahme an "
                             "dieser Studie widerrufen, ohne dass Ihnen daraus Nachteile entstehen. Eine Übertragung"
                             "Ihrer Daten können Sie erst nach Ende der vollständig absolvierten Aufgaben ausführen. "
                             "Somit können Sie Ihre Einwilligung zur Speicherung der Daten bis zum Ende der "
                             "Datenerhebung widerrufen. Brechen Sie Ihre Teilnahme vor Beendigung ab, oder "
                             "entscheiden Sie sich gegen eine Übermittlung der Daten nach Vollendung der Aufgaben, "
                             "werden keine Daten übertragen.\n\n"
                             #"In diesem Fall kann kein Anspruch auf eine entsprechende Vergütung oder die "
                             #"entsprechende Anzahl Versuchspersonenstunden für den bis dahin erbrachten Zeitaufwand "
                             #"erfasst werden, sofern diese vorgesehen sind.\n\n"
                             
                             "[b]Datenschutz:[/b]\n"
                             "Es werden keine personenbezogenen Daten erhoben. Um Daten zu ermitteln, die vom selben "
                             "Gerät stammen, wird eine Zeichenkette übermittelt, die keine Identifikation des Gerätes "
                             "selbst ermöglicht. Eine zweite, zufällige Zeichenkette wird als Ihr persönlicher Code "
                             "erstellt, um die Daten einer anonymen Person zuordnen zu können. Diese Zeichenkette "
                             "wird Ihnen am Ende dieser Information, sowie vor der Datenübertragung angezeigt. "
                             "Die Daten werden zunächst an einen Drittanbieter auf dessen Server innerhalb der "
                             "Europäischen Union übertragen. Über die Datenschutzmaßnahmen des Drittanbieters können "
                             "Sie sich unter folgender Internet-Adresse informieren:\n"
                             "https://www.heroku.com/policy/security#data-security\n"
                             "Nach Übertragung der Daten kann keine vollständige Löschung Ihres persönlichen "
                             "Datensatzes mehr gewährleistet werden, da u.a. Sicherheitskopien in der Infrastruktur "
                             "desDrittanbieters angelegt werden. Desweiteren ist ein sofortiger Zugang der "
                             "Öffentlichkeitzu den Daten möglich, siehe [i]Verwendung der anonymisierten Daten[/i].\n\n"
        
                             "[b]Verwendung der anonymisierten Daten:[/b]\n"
                             "Die Ergebnisse und Daten dieser Studie werden als wissenschaftliche Publikation "
                             "veröffentlicht. Dies geschieht in anonymisierter Form, d. h. ohne dass die Daten einer "
                             "spezifischen Person zugeordnet werden können. Die vollständig anonymisierten Daten "
                             "dieser Studie werden als offene Daten unter der CC-BY-SA Lizenz im Internet zugänglich "
                             "gemacht. Nach Abschluss der Studie können die Daten in einem nationalen oder "
                             "internationalen Datenarchiv gespeichert und veröffentlicht werden. Damit folgt diese "
                             "Studie den Empfehlungen der Deutschen Forschungsgemeinschaft (DFG) und der Deutschen "
                             "Gesellschaft für Psychologie (DGPs) zur Qualitätssicherung in der Forschung.\n\n"
        
                             "Hiermit versichere ich, dass ich die oben beschriebenen Teilnahme-Informationen "
                             "verstanden habe und mit den genannten Teilnahmebedingungen einverstanden bin.\n\n")
