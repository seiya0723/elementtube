from django import forms
from .models import Notify,NotifyTarget,News

class NotifyAdminForm(forms.ModelForm):

    class Meta:
        model   = Notify
        fields  = [ "category","dt","title","content", ]

    content     = forms.CharField(  widget  = forms.Textarea( attrs={ "maxlength":str(Notify.content.field.max_length), } ),
                                    label   = Notify.content.field.verbose_name 
                                    )

class NotifyTargetAdminForm(forms.ModelForm):

    class Meta:
        model   = NotifyTarget
        fields  = [ "notify","user" ]


class NewsAdminForm(forms.ModelForm):

    class Meta:
        model   = News
        fields  = [ "dt","start_date","end_date","category","title","content" ]

    content     = forms.CharField(  widget  = forms.Textarea( attrs={ "maxlength":str(News.content.field.max_length), } ),
                                    label   = News.content.field.verbose_name 
                                    )




