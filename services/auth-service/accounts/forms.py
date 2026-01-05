from django import forms 
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from accounts.models import User 



class UserCreationForm(forms.ModelForm):
    """
        - A form for creating new users. Includes all the required fields, plus a repeated password.
        - hashing password while  user is created from admin panel
    """

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label = "Password Confirmation", widget=forms.PasswordInput
    )

    class Meta:
        model = User 
        fields = (
            "email", 
            "username", 
            "name", 
            "phone_number"
        )

    def clean_password2(self):
        # check that two passowrd match eatch other exactly if not then show raise validation error
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password's don't match!")
        return password2
    
    def save(self, commit=True):
        # Save the provided passowrd in hashed format 
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
    

class UserChangeForm(forms.ModelForm):
    """
        A form for updating users. Includes all the fields on
        the user, but replaces the password field with admin's
        disabled password hash display field.

    """

    password = ReadOnlyPasswordHashField(
        help_text="Passwords are not stored in plain text."
    )

    class Meta:
        model = User 
        fields = "__all__"


