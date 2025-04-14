from datetime import timezone
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator

from ***REMOVED*** import settings
from .forms import ItemForm, PromotePatronForm, UserProfileForm
from .models import BorrowRequest, Item, Rental, UserProfile, ItemPhoto, Review, Collection
import boto3
import uuid

def home(request):
    return render(request, '***REMOVED***/homepage.html')

def catalog(request):
    CATEGORY_ORDER = [
        ('formal', 'Formal Wear'),
        ('casual', 'Casual Wear'),
        ('sports', 'Sportswear'),
        ('vintage', 'Vintage'),
        ('street', 'Streetwear'),
        ('active', 'Activewear'),
        ('denim', 'Denim'),
        ('outerwear', 'Outerwear'),
        ('accessories', 'Accessories'),
        ('other', 'Other'),
    ]
    
    # Build a dictionary keyed by category code, each value is a list of items
    items_by_category = {}
    for code, label in CATEGORY_ORDER:
        items_by_category[code] = Item.objects.filter(category=code).order_by('created_at')

    return render(request, '***REMOVED***/catalog.html', {
        'CATEGORY_ORDER': CATEGORY_ORDER,
        'items_by_category': items_by_category
    })


def catalog_view(request):
    items = Item.objects.prefetch_related('photos').all()  # Fetch items and related photos
    # Resource: ChatGPT 4o
    # Prompt: Can I filter by a function in a Django model?
    # Date: March 30, 2025 7:20pm
    all_collections = Collection.objects.all()
    visible_collections = [collection for collection in all_collections if collection.user_can_view(request.user)]
    return render(request, '***REMOVED***/catalog.html', {"items": items, "collections": visible_collections})


@method_decorator(login_required, name='dispatch')
class CollectionCreateView(CreateView):
    model = Collection
    fields = ['title', 'description', 'items', 'is_public']
    template_name = '***REMOVED***/create_collection.html'
    success_url = '/catalog/'

    def form_valid(self, form):
        if (not form.cleaned_data.get('is_public')) and (not self.request.user.is_librarian()):
            form.add_error('is_public', "You must be a librarian to create a private collection.")
            return self.form_invalid(form)
        items = form.cleaned_data.get('items')
        if items:
            for item in items:
                if Collection.objects.filter(items__in=[item], is_public=False).exists():
                    form.add_error('items', f"{item} is already in a private collection.")
                    return self.form_invalid(form)
        form.instance.creator = self.request.user
        return super().form_valid(form)

class CollectionUpdateView(UpdateView):
    model = Collection
    fields = ['title', 'description', 'items']
    template_name = '***REMOVED***/edit_collection.html'
    success_url = '/catalog/'

@method_decorator(login_required, name='dispatch')
class CollectionDeleteView(DeleteView):
    model = Collection
    template_name = '***REMOVED***/delete_collection.html'
    success_url = '/catalog/'

    # get which collections the user can delete
    def get_queryset(self):
        if self.request.user.is_librarian():
            return Collection.objects.all()
        return self.model.objects.filter(creator=self.request.user)

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
                file_key = f"item_photos/{item.pk}_{uuid.uuid4().hex}_{photo_file.name}"
                # Create an S3 client using credentials from settings
                s3_client = boto3.client('s3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
                # Upload the file-like object directly
                s3_client.upload_fileobj(
                    photo_file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    file_key,
                    ExtraArgs={
                        "CacheControl": "max-age=2628000", # 30 days
                        "ContentType": photo_file.content_type, 
                    },
                )
                # Construct the photo URL
                photo_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_key}"
                # Save the ItemPhoto object
                ItemPhoto.objects.create(item=item, photo=photo_url, is_primary=True)

            return redirect('item_detail', item_id=item.pk)
    else:
        form = ItemForm()

    return render(request, '***REMOVED***/add_item.html', {'form': form})

class ItemDeleteView(DeleteView):
    model = Item
    template_name = '***REMOVED***/delete_item.html'
    success_url = '/catalog/'
    def get_queryset(self):
        if self.request.user.is_librarian():
            return Item.objects.all()
        # non-librarians can't delete
        return Item.objects.none()

def item_detail(request, item_id):
    item = get_object_or_404(Item.objects.prefetch_related('photos'), pk=item_id)
    return render(request, '***REMOVED***/item_detail.html', {'item': item})

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

@login_required
def add_review(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == 'POST':
        comment = request.POST.get('comment')
        rating = request.POST.get('rating')
        if not comment or not rating:
            return redirect('item_detail', item_id=item_id)
        Review.objects.create(
            item=item,
            user=request.user,
            comment=comment,
            rating=rating
        )
        return redirect('item_detail', item_id=item_id)
    return redirect('item_detail', item_id=item_id)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if review.user == request.user:  # Ensure the logged-in user is the author
        review.delete()
    return redirect('item_detail', item_id=review.item.id)

@method_decorator(login_required, name='dispatch')
# TODO: make this redirect to 404 instead of infinite redirect loop
@method_decorator(user_passes_test(lambda u: u.is_librarian()), name='dispatch')
class PromotePatronsFormView(FormView):
    template_name = '***REMOVED***/promote_patrons.html'
    form_class = PromotePatronForm
    success_url = '/catalog/'
    def form_valid(self, form):
        if not self.request.user.is_librarian():
            form.add_error(None, 'You must be a librarian to promote other users.')
        if form.errors:
            return self.form_invalid(form)
        form.promote_users()
        return super().form_valid(form)


@login_required
def request_borrow(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if not item.is_available:
        return redirect('item_detail', item_id=item_id)

    # Check if a pending request already exists
    if BorrowRequest.objects.filter(item=item, user=request.user, status='PENDING').exists():
        return redirect('item_detail', item_id=item_id)

    BorrowRequest.objects.create(item=item, user=request.user)
    return redirect('item_detail', item_id=item_id)

@login_required
def my_borrowed_items(request):
    borrowed_items = Rental.objects.filter(renter=request.user, status='on_loan')
    return render(request, '***REMOVED***/my_borrowed_items.html', {'borrowed_items': borrowed_items})
    
@user_passes_test(lambda u: u.is_librarian())
def manage_borrow_requests(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        request_id = request.POST.get('request_id')
        borrow_request = get_object_or_404(BorrowRequest, pk=request_id)

        if action == 'approve':
            borrow_request.status = 'APPROVED'
            borrow_request.date_approved = timezone.now()
            borrow_request.due_date = timezone.now().date() + timezone.timedelta(days=14)  # Example: 14-day loan
            borrow_request.save()

            try:
                # Ensure all required fields are valid
                if borrow_request.item and borrow_request.user and borrow_request.due_date:
                    Rental.objects.create(
                        item=borrow_request.item,
                        renter=borrow_request.user,
                        start_date=timezone.now().date(),
                        end_date=borrow_request.due_date,
                        status='on_loan'
                    )
                    messages.success(request, f"Borrow request for {borrow_request.item.name} approved.")
                else:
                    raise ValueError("Invalid data for creating a rental.")
            except Exception as e:
                error_message = f"An error occurred while approving the borrow request: {e}"
                messages.error(request, error_message)
                borrow_request.status = 'PENDING'
                borrow_request.save()
                return redirect('manage_borrow_requests')

        elif action == 'deny':
            borrow_request.status = 'DENIED'
            borrow_request.save()
            messages.error(request, f"Borrow request for {borrow_request.item.name} denied.")

        return redirect('manage_borrow_requests')

    pending_requests = BorrowRequest.objects.filter(status='PENDING').select_related('item', 'user')
    return render(request, '***REMOVED***/manage_borrow_requests.html', {'pending_requests': pending_requests})