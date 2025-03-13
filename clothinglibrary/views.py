from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import ContentPage, Item, ItemPhoto, Rental, Review, ReviewPhoto
from .forms import ItemForm

def home(request):
    return render(request, '***REMOVED***/homepage.html')



@login_required
def add_item(request):
    if not request.user.is_librarian():
        return redirect('home')

    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.lender = request.user
            item.save()
            # TODO: Eventually redirect to product detail page, not just home
            return redirect('home')
    else:
        form = ItemForm()

    return render(request, '***REMOVED***/add_item.html', {'form': form})
