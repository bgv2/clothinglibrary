from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ItemForm, UserProfileForm
from .models import Item, UserProfile, ItemPhoto
import boto3


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
            if 'photo' in request.FILES:
                photo_file = request.FILES['photo']
                # Generate a unique file key for the image
                file_key = f"item_photos/{uuid.uuid4().hex}_{photo_file.name}"
                # Create an S3 client using credentials from settings
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                # Upload the file-like object directly
                s3_client.upload_fileobj(photo_file, settings.AWS_STORAGE_BUCKET_NAME, file_key)
                # Construct the photo URL
                photo_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_key}"
                # Save the ItemPhoto object
                ItemPhoto.objects.create(item=item, photo=photo_url, is_primary=True)

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