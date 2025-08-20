from django import forms
from .models import Makale, Mesaj

class MakaleForm(forms.ModelForm):
    class Meta:
        model = Makale
        fields = ['email', 'pdf']

class MesajForm(forms.ModelForm):
    class Meta:
        model = Mesaj
        fields = ['icerik']
        widgets = {
            'icerik': forms.Textarea(attrs={
                'placeholder': 'Mesajınızı yazın...',
                'rows': 3,
                'style': 'width:100%; padding:10px; border-radius:6px; border:1px solid #ccc; font-size:14px;',
            }),
        }
