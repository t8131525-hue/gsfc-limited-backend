# audit_trail/tests.py
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from inventory.models import Product
from .models import AuditLog
from .request import set_current_request

User = get_user_model()

class AuditTrailTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.factory = RequestFactory()
        request = self.factory.get('/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        set_current_request(request)
        AuditLog.objects.all().delete()

    def tearDown(self):
        set_current_request(None)

    def test_create_action_is_logged(self):
        self.assertEqual(AuditLog.objects.count(), 0)
        product = Product.objects.create(name='Test Product')
        self.assertEqual(AuditLog.objects.count(), 1)
        log = AuditLog.objects.first()
        self.assertEqual(log.action_type, 'CREATE')
        self.assertEqual(log.user, self.user)

    def test_update_action_is_logged(self):
        """
        This is the corrected test for updates.
        It specifically checks if an UPDATE log exists, which is more reliable.
        """
        product = Product.objects.create(name='Original Name')
        
        # Update the product
        product.name = 'Updated Name'
        product.save()

        # Specifically check if an UPDATE log for this object was created.
        log_exists = AuditLog.objects.filter(
            content_type__model='product',
            object_id=product.id,
            action_type='UPDATE'
        ).exists()

        self.assertTrue(log_exists, "An UPDATE log for the product was not created.")

    def test_delete_action_is_logged(self):
        """
        This is the robust test for deletes.
        """
        product = Product.objects.create(name='To Be Deleted')
        product_id = product.id
        content_type = ContentType.objects.get_for_model(Product)

        self.assertEqual(AuditLog.objects.count(), 1)

        product.delete()

        self.assertEqual(AuditLog.objects.count(), 2)
        
        # Specifically check that the DELETE log exists.
        try:
            AuditLog.objects.get(
                content_type=content_type,
                object_id=str(product_id),
                action_type='DELETE'
            )
        except AuditLog.DoesNotExist:
            self.fail("The specific 'DELETE' log was not found in the audit trail.")

    def test_no_log_on_save_with_no_changes(self):
        """
        This test ensures that saving an object without making any changes
        does not create an unnecessary UPDATE log.
        """
        product = Product.objects.create(name='No Change Product')
        self.assertEqual(AuditLog.objects.count(), 1)
        
        # Save the object again without any changes
        product.save()
        
        # The log count should still be 1, as no UPDATE log should be created.
        self.assertEqual(AuditLog.objects.count(), 1)