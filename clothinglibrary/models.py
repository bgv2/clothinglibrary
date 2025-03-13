from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone

def is_librarian(self):
    return self.groups.filter(name='Librarians').exists()
User.add_to_class('is_librarian', is_librarian)

def is_patron(self):
    return self.groups.filter(name='Patrons').exists()
User.add_to_class('is_patron', is_patron)


class ContentPage(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    slug = models.SlugField(unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class Item(models.Model):
    CONDITION_CHOICES = [
        ('NW', 'Brand New'),
        ('EC', 'Excellent Condition'),
        ('GC', 'Good Condition'),
        ('FR', 'Fair/Visible Wear'),
    ]
    CATEGORY_CHOICES = [
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

    lender = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    size = models.CharField(max_length=100)
    measurements = models.CharField(max_length=200, blank=True, null=True)
    care_instructions = models.TextField(blank=True, null=True)
    condition = models.CharField(max_length=2, choices=CONDITION_CHOICES)
    flaws = models.TextField(blank=True)
    times_worn = models.PositiveIntegerField(default=0)
    max_rental_duration = models.PositiveIntegerField(help_text="Maximum rental duration in days")
    protection_info = models.TextField(help_text="Insurance/Protection details", blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_available(self):
        now = timezone.now().date()
        return not self.rentals.filter(
            end_date__gte=now
        ).exclude(status__in=['returned', 'overdue']).exists()

    def __str__(self):
        return self.name

class ItemPhoto(models.Model):
    item = models.ForeignKey(Item, related_name='photos', on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='item_photos/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Photo for {self.item.name}"

class Rental(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('on_loan', 'On Loan'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]

    item = models.ForeignKey(Item, related_name='rentals', on_delete=models.CASCADE)
    renter = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.status == 'returned':
            self.item.times_worn += 1
            self.item.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} - {self.get_status_display()}"

class Review(models.Model):
    item = models.ForeignKey(Item, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    event = models.CharField(max_length=200, blank=True)
    user_size = models.CharField(max_length=100, blank=True)
    flaws_noted = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])

    def __str__(self):
        return f"Review for {self.item.name} by {self.user.username}"

class ReviewPhoto(models.Model):
    review = models.ForeignKey(Review, related_name='photos', on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='review_photos/')

    def __str__(self):
        return f"Photo for review by {self.review.user.username}"