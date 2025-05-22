

from django import forms
from .models import Feedback, Attachment

class FeedbackForm(forms.ModelForm):

    attachment = forms.ImageField(
        required=False,
        label="Прикрепить изображение (jpg, png)"
    )
    
    class Meta:
        model = Feedback
        fields = ['title', 'content', 'email_visible']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Введите заголовок отзыва'}),
            'content': forms.Textarea(attrs={'placeholder': 'Введите ваш отзыв', 'rows': 5}),
        }
    
    def save(self, commit=True):

        feedback = super().save(commit=commit)
        image = self.cleaned_data.get('attachment')
        if commit:
            if image:
                Attachment.objects.create(feedback=feedback, image=image)
        else:
           
            self._attachment = image
        return feedback
