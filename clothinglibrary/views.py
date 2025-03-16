from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ItemForm, UserProfileForm
from .models import Item, UserProfile


def home(request):
    return render(request, '***REMOVED***/homepage.html')

def catalog(request):
    return render(request, '***REMOVED***/catalog.html', {'items': Item.objects.all()})

def profile(request):
    return render(request, '***REMOVED***/profile.html')

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

@login_required
def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, '***REMOVED***/edit_profile.html', {'form': form})