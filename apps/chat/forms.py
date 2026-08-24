from typing import ClassVar

from django import forms

from .models import ChatMessage
from .moderation import moderate_message


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ("body",)
        labels: ClassVar[dict[str, str]] = {"body": "Mensagem"}
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "body": forms.Textarea(
                attrs={
                    "rows": 3,
                    "maxlength": 1000,
                    "placeholder": "Escreva uma mensagem clara e respeitosa.",
                    "autocomplete": "off",
                }
            )
        }

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("Escreva uma mensagem antes de enviar.")
        self.moderation_result = moderate_message(body)
        if self.moderation_result.blocked:
            raise forms.ValidationError("Mensagem não enviada por possível uso indevido do chat.")
        return body
