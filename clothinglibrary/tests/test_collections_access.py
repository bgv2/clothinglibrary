from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from ***REMOVED***.models import Collection, CollectionAccessRequest

class CollectionAccessTests(TestCase):
    def setUp(self):
        self.patron = User.objects.create_user(username='patron', password='testpass')
        self.librarian = User.objects.create_user(username='librarian', password='testpass', is_staff=True)

        # tests if patrons can make private collections
        self.public_collection = Collection.objects.create(title='Public Collection', is_public=True)
        self.private_collection = Collection.objects.create(title='Private Collection', is_public=False)

    def test_public_collection_accessible_by_patron(self):
        self.client.login(username='patron', password='testpass')
        url = reverse('collection_detail', args=[self.public_collection.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_private_collection_accessible_with_approved_access_request(self):
        CollectionAccessRequest.objects.create(
            user=self.patron,
            collection=self.private_collection,
            status='APPROVED'
        )
        self.client.login(username='patron', password='testpass')
        url = reverse('collection_detail', args=[self.private_collection.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_private_collection_accessible_by_librarian(self):
        self.client.login(username='librarian', password='testpass')
        url = reverse('collection_detail', args=[self.private_collection.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)