from django.forms import ModelForm
from ***REMOVED***.models import Item

class ItemForm(ModelForm):
    class Meta:
        model = Item
        fields = [
            'name', 'description', 'size', 'measurements', 'care_instructions',
            'condition', 'flaws', 'max_rental_duration', 'protection_info', 'category'
        ]
        error_messages = {
            'name': {
                'required': "The item name is required.",
                'max_length': "The name is too long.",
            },
            'description': {
                'required': "Please provide a description for the item.",
            },
            'size': {
                'required': "Please specify the size.",
            },
            'measurements': {
                'required': "Please provide the measurements.",
            },
            'care_instructions': {
                'required': "Please provide care instructions.",
            },
            'condition': {
                'required': "Please select a condition.",
            },
            'max_rental_duration': {
                'required': "Please specify the maximum rental duration (in days).",
            },
            'protection_info': {
                'required': "Please provide protection or insurance details.",
            },
            'category': {
                'required': "Please select a category.",
            },
        }