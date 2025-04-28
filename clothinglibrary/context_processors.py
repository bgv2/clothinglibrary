from .models import BorrowRequest, CollectionAccessRequest, PromotionRequest

def pending_requests_count(request):
    if request.user.is_authenticated and getattr(request.user, 'is_librarian', False):
        borrow_count = BorrowRequest.objects.filter(status='PENDING').count()
        access_count = CollectionAccessRequest.objects.filter(status='PENDING').count()
        promotion_count = PromotionRequest.objects.filter(status='PENDING').count()
        total_pending = borrow_count + access_count + promotion_count
        return {'total_pending_requests': total_pending}
    else:
        return {'total_pending_requests': 0}