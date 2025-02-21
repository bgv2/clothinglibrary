from django.shortcuts import get_object_or_404, render
from .models import Category, ContentPage, Item, ItemPhoto, Rental, Review, ReviewPhoto

def home(request):
    return render(request, '***REMOVED***/homepage.html')
