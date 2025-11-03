# inventory/tests.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Product, TestRecord
from audit_trail.models import AuditLog

User = get_user_model()

class InventoryTestCase(APITestCase):
    def setUp(self):
        """
        Set up users, groups, and permissions for all tests.
        """
        # Create Users
        self.analyst_user = User.objects.create_user(username='analyst', password='password123')
        self.supervisor_user = User.objects.create_user(username='supervisor', password='password123')

        # Create Groups
        self.analyst_group = Group.objects.create(name='Analyst')
        self.supervisor_group = Group.objects.create(name='Supervisor')
        
        self.analyst_user.groups.add(self.analyst_group)
        self.supervisor_user.groups.add(self.supervisor_group)

        # Get ContentType for TestRecord to fetch its permissions
        content_type = ContentType.objects.get_for_model(TestRecord)

        # Assign permissions to Analyst
        add_test_perm = Permission.objects.get(codename='add_testrecord', content_type=content_type)
        view_test_perm = Permission.objects.get(codename='view_testrecord', content_type=content_type)
        self.analyst_group.permissions.add(add_test_perm, view_test_perm)

        # Assign permissions to Supervisor (includes analyst permissions + approval)
        approve_test_perm = Permission.objects.get(codename='can_approve_test_records', content_type=content_type)
        self.supervisor_group.permissions.add(add_test_perm, view_test_perm, approve_test_perm)
        
        # Refresh users to ensure permissions are loaded
        self.analyst_user.refresh_from_db()
        self.supervisor_user.refresh_from_db()

        # Create a sample product for use in tests
        self.product = Product.objects.create(name='Test Product')

        # Authenticate the client as the supervisor by default for most tests
        self.client.force_authenticate(user=self.supervisor_user)

    def test_product_update_is_audited(self):
        """
        Ensure that updating a model with AuditableMixin creates an UPDATE log.
        """
        self.product.description = "A new description for testing"
        self.product.save()
        
        self.assertTrue(
            AuditLog.objects.filter(
                content_type__model='product', 
                object_id=self.product.id,
                action_type='UPDATE'
            ).exists()
        )

    def test_create_test_record(self):
        """
        Ensure an analyst can create a new test record.
        """
        self.client.force_authenticate(user=self.analyst_user)
        url = '/api/inventory/tests/'
        data = {
            'product': self.product.id,
            'sample_id': 'SAMPLE-001',
            'batch_no': 'BATCH-001',
            'parameter_values': [] 
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(TestRecord.objects.count(), 1)
        
        record = TestRecord.objects.get()
        self.assertEqual(record.status, 'PENDING')
        self.assertEqual(record.analyst, self.analyst_user)

    def test_supervisor_can_approve_test(self):
        """
        Ensure a supervisor can approve a test and the action is audited.
        """
        record = TestRecord.objects.create(
            product=self.product,
            sample_id='SAMPLE-002',
            batch_no='BATCH-002',
            analyst=self.analyst_user
        )

        url = f'/api/inventory/tests/{record.id}/approve_reject/'
        data = {'status': 'APPROVED', 'supervisor_comments': 'Test passed.'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        record.refresh_from_db()
        self.assertEqual(record.status, 'APPROVED')
        self.assertEqual(record.approved_by, self.supervisor_user)

        self.assertTrue(
            AuditLog.objects.filter(
                user=self.supervisor_user, object_id=record.id, action_type='APPROVED'
            ).exists()
        )
    
    def test_analyst_cannot_approve_test(self):
        """
        Ensure a user without 'can_approve_test_records' permission cannot approve.
        """
        record = TestRecord.objects.create(
            product=self.product,
            sample_id='SAMPLE-003',
            batch_no='BATCH-003',
            analyst=self.analyst_user
        )
        url = f'/api/inventory/tests/{record.id}/approve_reject/'
        data = {'status': 'APPROVED'}
        
        self.client.force_authenticate(user=self.analyst_user)
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- NEW TEST FOR RETEST FUNCTIONALITY ---
    def test_supervisor_can_order_retest(self):
        """
        Ensure a supervisor can order a retest, which creates a new pending test record.
        """
        # --- ENSURE THIS IS CORRECT: test_date is no longer needed ---
        original_record = TestRecord.objects.create(
            product=self.product,
            sample_id='SAMPLE-004',
            batch_no='BATCH-004',
            analyst=self.analyst_user,
            status='REJECTED'
        )

        url = f'/api/inventory/tests/{original_record.id}/order_retest/'
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TestRecord.objects.count(), 2)

        retest_record = TestRecord.objects.get(id=response.data['id'])
        self.assertEqual(retest_record.status, 'PENDING')
        self.assertEqual(retest_record.sample_id, 'SAMPLE-004')
        self.assertIsNone(retest_record.analyst)
        self.assertEqual(retest_record.retest_of, original_record)

        original_record.refresh_from_db()
        self.assertEqual(original_record.status, 'RETEST')

        self.assertTrue(AuditLog.objects.filter(user=self.supervisor_user, object_id=original_record.id, action_type='RETEST_ORDERED').exists())

    def test_analyst_cannot_order_retest(self):
        """
        Ensure a user without 'can_approve_test_records' permission cannot order a retest.
        """
        # --- ENSURE THIS IS CORRECT: test_date is no longer needed ---
        original_record = TestRecord.objects.create(
            product=self.product,
            sample_id='SAMPLE-005',
            batch_no='BATCH-005',
            analyst=self.analyst_user
        )
        
        url = f'/api/inventory/tests/{original_record.id}/order_retest/'
        
        self.client.force_authenticate(user=self.analyst_user)
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
