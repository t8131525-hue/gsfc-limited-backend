# inventory/tests.py

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

# Import all your models
from .models import (
    Product,
    Version,
    ProductGrade,
    ParameterDefinition,
    Lab,
    TestRecord,
    TestResult,
)

User = get_user_model()


class InventoryAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up a consistent database state for all API tests.
        This runs once per test class.
        """
        # 1. Create Groups
        cls.analyst_group = Group.objects.create(name="Analyst")
        cls.manager_group = Group.objects.create(name="Manager")

        # 2. Create Users
        cls.analyst_user = User.objects.create_user(
            username="analyst", password="password123"
        )
        cls.admin_user = User.objects.create_superuser(
            username="admin", password="password123"
        )
        cls.manager_user = User.objects.create_user(
            username="manager", password="password123"
        )

        cls.analyst_user.groups.add(cls.analyst_group)
        cls.manager_user.groups.add(cls.manager_group)

        app_label = "inventory"
        inventory_permissions = Permission.objects.filter(
            content_type__app_label=app_label
        )

        cls.manager_group.permissions.add(*inventory_permissions)

        analyst_perms_codenames = [
            "can_view_test_records",
            "can_manage_test_records",
            "can_view_products",
            "can_view_product_grades",
        ]
        analyst_permissions = Permission.objects.filter(
            content_type__app_label=app_label, codename__in=analyst_perms_codenames
        )
        cls.analyst_group.permissions.add(*analyst_permissions)

        cls.lab = Lab.objects.create(name="Main Lab")
        cls.product = Product.objects.create(name="Super Cement")
        cls.v_draft = Version.objects.create(
            product=cls.product,
            version_name="v0.1-DRAFT",
            status="DRAFT",
            created_by=cls.manager_user,
        )

        cls.v_locked_simple = Version.objects.create(
            product=cls.product,
            version_name="v1.0-Simple",
            status="DRAFT",
            created_by=cls.manager_user,
        )
        cls.param_int = ParameterDefinition.objects.create(
            owner=cls.v_locked_simple,
            name="Viscosity",
            data_type="INTEGER",
            min_value=10,
            max_value=20,
        )
        cls.v_locked_simple.status = "LOCKED"
        cls.v_locked_simple.save()

        # Active Version (With Grades)
        cls.v_active_grades = Version.objects.create(
            product=cls.product,
            version_name="v2.0-Grades",
            status="DRAFT",
            created_by=cls.manager_user,
        )
        cls.grade_a = ProductGrade.objects.create(
            version=cls.v_active_grades, name="Grade A"
        )
        cls.param_enum = ParameterDefinition.objects.create(
            owner=cls.grade_a,
            name="Color",
            data_type="ENUM",
            is_required=True,
            enum_options=["Red", "Blue", "Green"],
        )
        cls.param_bool = ParameterDefinition.objects.create(
            owner=cls.grade_a,
            name="Waterproof",
            data_type="BOOLEAN",
            is_required=True,
            boolean_true_label="Yes",
            boolean_false_label="No",
        )
        cls.v_active_grades.status = "LOCKED"
        cls.v_active_grades.is_active = True  # This also saves
        cls.v_active_grades.save()

        # 6. Test Records
        cls.tr_pending = TestRecord.objects.create(
            version=cls.v_active_grades,
            lab=cls.lab,
            product_grade=cls.grade_a,
            sample_id="S-001",
            batch_no="B-001",
            status="PENDING",
            analyst=cls.analyst_user,
        )
        cls.tr_approved = TestRecord.objects.create(
            version=cls.v_locked_simple,
            lab=cls.lab,
            sample_id="S-002",
            batch_no="B-002",
            status="APPROVED",
            analyst=cls.analyst_user,
            decision="APPROVED",
            approved_by=cls.manager_user,
            approved_at=timezone.now(),
        )
        cls.tr_rejected = TestRecord.objects.create(
            version=cls.v_locked_simple,
            lab=cls.lab,
            sample_id="S-003",
            batch_no="B-003",
            status="REJECTED",
            analyst=cls.analyst_user,
            decision="REJECTED",
            approved_by=cls.manager_user,
            approved_at=timezone.now(),
        )
        cls.tr_unassigned = TestRecord.objects.create(
            version=cls.v_active_grades,
            lab=cls.lab,
            product_grade=cls.grade_a,
            sample_id="S-004",
            batch_no="B-004",
            status="PENDING",
            analyst=None,
        )

        # 7. Test Results
        TestResult.objects.create(
            test_record=cls.tr_approved, parameter=cls.param_int, value_decimal=15
        )
        TestResult.objects.create(
            test_record=cls.tr_pending, parameter=cls.param_enum, value_string="Red"
        )

    def setUp(self):
        """
        Log in the admin user by default for most tests.
        Individual tests can re-authenticate as needed.
        """
        # We use manager_user as the default auth, as they have all perms
        self.client.force_authenticate(user=self.manager_user)

    # --- TestRecordViewSet Tests ---

    def test_test_record_list_unauthenticated(self):
        self.client.logout()
        # CORRECTED URL
        response = self.client.get("/api/inventory/tests/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_test_record_list_as_analyst(self):
        """
        Test that an analyst only sees their own records
        due to the `get_queryset` override.
        """
        self.client.force_authenticate(user=self.analyst_user)
        # CORRECTED URL
        response = self.client.get("/api/inventory/tests/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Based on setup, analyst should see 3 records
        # (pending, approved, rejected). Unassigned is not theirs.
        self.assertEqual(len(response.data["results"]), 3)
        self.assertEqual(response.data["results"][0]["id"], self.tr_rejected.id)
        self.assertEqual(response.data["results"][1]["id"], self.tr_approved.id)
        self.assertEqual(response.data["results"][2]["id"], self.tr_pending.id)

    def test_test_record_list_as_admin(self):
        """
        Test that an admin (with `can_view_all_test_records`) sees all records.
        """
        self.client.force_authenticate(user=self.admin_user)
        # CORRECTED URL
        response = self.client.get("/api/inventory/tests/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin should see all 4 records
        self.assertEqual(len(response.data["results"]), 4)

    def test_test_record_create_as_analyst(self):
        """
        Test the happy path for an analyst creating a new test record.
        """
        self.client.force_authenticate(user=self.analyst_user)
        record_count = TestRecord.objects.count()
        result_count = TestResult.objects.count()

        data = {
            "version": self.v_active_grades.id,
            "lab": self.lab.id,
            "product_grade": self.grade_a.id,
            "sample_id": "S-NEW-001",
            "batch_no": "B-NEW-001",
            "results_input": [
                {"parameter": self.param_enum.id, "value": "Blue"},
                {"parameter": self.param_bool.id, "value": True},
            ],
        }
        # CORRECTED URL
        response = self.client.post("/api/inventory/tests/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check database
        self.assertEqual(TestRecord.objects.count(), record_count + 1)
        self.assertEqual(TestResult.objects.count(), result_count + 2)

        new_record = TestRecord.objects.latest("created_at")
        self.assertEqual(new_record.analyst, self.analyst_user)
        self.assertEqual(new_record.status, "PENDING")
        self.assertEqual(new_record.parameter_values.count(), 2)  # Use related_name

    def test_test_record_create_validation_model(self):
        """
        Test that the TestRecord.clean() validation is triggered.
        (e.g., missing product_grade when version has grades)
        """
        self.client.force_authenticate(user=self.analyst_user)
        data = {
            "version": self.v_active_grades.id,  # This version HAS grades
            "lab": self.lab.id,
            "product_grade": None,  # But we are not providing one
            "sample_id": "S-FAIL-001",
            "batch_no": "B-FAIL-001",
            "results_input": [],
        }
        # CORRECTED URL
        response = self.client.post("/api/inventory/tests/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # This error message comes from TestRecord.clean()
        self.assertIn("product grade must be selected", str(response.data))

    def test_test_record_create_validation_serializer(self):
        """
        Test that the TestRecordSerializer.validate_version is triggered.
        (e.g., trying to test against a DRAFT version)
        """
        self.client.force_authenticate(user=self.analyst_user)
        data = {
            "version": self.v_draft.id,  # DRAFT version
            "lab": self.lab.id,
            "sample_id": "S-FAIL-002",
            "batch_no": "B-FAIL-002",
            "results_input": [],
        }
        # CORRECTED URL
        response = self.client.post("/api/inventory/tests/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # This error message comes from TestRecordSerializer.validate_version
        self.assertIn(
            "Can only create test records for an active version",
            str(response.data["version"]),
        )

    def test_test_record_update_results_as_analyst(self):
        """
        Test analyst updating their own PENDING record's results.
        """
        self.client.force_authenticate(user=self.analyst_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_pending.id}/"
        data = {
            "results_input": [
                {"parameter": self.param_enum.id, "value": "Green"},
            ]
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check database
        self.tr_pending.refresh_from_db()
        result = self.tr_pending.parameter_values.first()
        self.assertEqual(result.value_string, "Green")

    def test_test_record_update_results_on_locked_record(self):
        """
        Test that updating results on an APPROVED record fails.
        This triggers TestResult.clean() via TestRecordSerializer.update().
        """
        self.client.force_authenticate(user=self.analyst_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_approved.id}/"
        data = {
            "results_input": [
                {"parameter": self.param_int.id, "value": 18},
            ]
        }
        response = self.client.patch(url, data, format="json")

        # The serializer update will call result_instance.save(),
        # which calls result_instance.full_clean(), triggering the
        # TestResult.clean() validation error.
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot change test results", str(response.data))

    # --- TestRecordViewSet Custom Actions ---

    def test_action_assign_as_manager(self):
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_unassigned.id}/assign/"
        data = {"analyst_id": self.analyst_user.id}

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.tr_unassigned.refresh_from_db()
        self.assertEqual(self.tr_unassigned.analyst, self.analyst_user)

    def test_action_assign_as_analyst_forbidden(self):
        self.client.force_authenticate(user=self.analyst_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_unassigned.id}/assign/"
        data = {"analyst_id": self.analyst_user.id}

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_action_assign_to_already_assigned_record(self):
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_pending.id}/assign/"
        data = {"analyst_id": self.analyst_user.id}

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been assigned", str(response.data))

    def test_action_approve_as_manager(self):
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_pending.id}/approve_reject/"
        data = {"status": "APPROVED", "supervisor_comments": "Looks good."}

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.tr_pending.refresh_from_db()
        self.assertEqual(self.tr_pending.status, "APPROVED")
        self.assertEqual(self.tr_pending.decision, "APPROVED")
        self.assertEqual(self.tr_pending.approved_by, self.manager_user)
        self.assertEqual(self.tr_pending.supervisor_comments, "Looks good.")

    def test_action_approve_as_analyst_forbidden(self):
        self.client.force_authenticate(user=self.analyst_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_pending.id}/approve_reject/"
        data = {"status": "APPROVED"}

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_action_approve_record_not_pending(self):
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_approved.id}/approve_reject/"
        data = {"status": "APPROVED"}

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already been actioned", str(response.data))

    def test_action_order_retest_as_manager(self):
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_rejected.id}/order_retest/"
        data = {"analyst_id": self.analyst_user.id}

        retest_count = TestRecord.objects.count()

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that original record is updated
        self.tr_rejected.refresh_from_db()
        self.assertEqual(self.tr_rejected.status, "RETEST_ORDERED")
        self.assertEqual(self.tr_rejected.retest_ordered_by, self.manager_user)

        # Check that a new record is created
        self.assertEqual(TestRecord.objects.count(), retest_count + 1)
        new_retest = TestRecord.objects.latest("created_at")
        self.assertEqual(new_retest.retest_of, self.tr_rejected)
        self.assertEqual(new_retest.status, "PENDING")
        self.assertEqual(new_retest.analyst, self.analyst_user)
        self.assertEqual(response.data["id"], new_retest.id)

    def test_action_order_retest_on_pending_record(self):
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_pending.id}/order_retest/"
        data = {"analyst_id": self.analyst_user.id}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Can only order a retest for", str(response.data))

    def test_action_close_record_as_manager(self):
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_approved.id}/close_record/"

        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.tr_approved.refresh_from_db()
        self.assertEqual(self.tr_approved.status, "CLOSED")
        self.assertEqual(self.tr_approved.closed_by, self.manager_user)

    def test_action_close_record_on_pending_record(self):
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_pending.id}/close_record/"

        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot close a record with status", str(response.data))

    def test_action_download_pdf(self):
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_approved.id}/download-pdf/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("Report-", response["Content-Disposition"])

    def test_action_download_excel(self):
        # CORRECTED URL
        url = f"/api/inventory/tests/{self.tr_approved.id}/download-excel/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("Report-", response["Content-Disposition"])

    # --- ProductViewSet Tests ---

    def test_product_list(self):
        response = self.client.get("/api/inventory/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should use ProductListSerializer
        self.assertIn("product_id", response.data["results"][0])
        self.assertNotIn("versions", response.data["results"][0])
        self.assertEqual(response.data["results"][0]["name"], self.product.name)

    def test_product_list_active_filter(self):
        # Create a product with no active version
        Product.objects.create(name="Inactive Product")

        response = self.client.get("/api/inventory/products/?is_active=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Only the product with an active version (self.product) should be returned
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], self.product.name)

    def test_product_retrieve(self):
        url = f"/api/inventory/products/{self.product.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should use ProductSerializer (detailed)
        self.assertIn("versions", response.data)
        # This test will pass after fixing ProductSerializer
        self.assertEqual(
            response.data["active_version_name"], self.v_active_grades.version_name
        )
        self.assertEqual(response.data["versions"][0]["id"], self.v_active_grades.id)

    # --- VersionViewSet Tests ---

    def test_version_list_as_manager(self):
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get("/api/inventory/versions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Manager sees all 3 versions
        self.assertEqual(len(response.data), 3)
        # Should use VersionListSerializer (lightweight)
        self.assertIn("version_name", response.data[0])
        self.assertNotIn("grades", response.data[0])

    def test_version_list_as_analyst(self):
        """
        Analyst should only see LOCKED versions (per `get_queryset`).
        """
        self.client.force_authenticate(user=self.analyst_user)
        response = self.client.get("/api/inventory/versions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Analyst sees only the 2 LOCKED versions
        self.assertEqual(len(response.data), 2)
        version_names = {v["version_name"] for v in response.data}
        self.assertIn(self.v_locked_simple.version_name, version_names)
        self.assertIn(self.v_active_grades.version_name, version_names)
        self.assertNotIn(self.v_draft.version_name, version_names)

    def test_version_retrieve_nested(self):
        url = f"/api/inventory/versions/{self.v_active_grades.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should use VersionNestedSerializer (detailed)
        self.assertIn("grades", response.data)
        self.assertIn("parameters", response.data)
        self.assertEqual(len(response.data["grades"]), 1)
        self.assertEqual(len(response.data["parameters"]), 0)  # Params are on the grade
        self.assertEqual(response.data["grades"][0]["name"], self.grade_a.name)
        self.assertEqual(len(response.data["grades"][0]["parameters"]), 2)

    def test_version_create_validation_fail(self):
        """
        Test that Version.clean() is called by VersionSerializer.validate()
        """
        self.client.force_authenticate(user=self.manager_user)
        data = {
            "product": self.product.id,
            "version_name": "v4.0-Fail",
            "status": "LOCKED",  # Can't lock an empty version
        }
        response = self.client.post("/api/inventory/versions/", data, format="json")
        # This test will pass after fixing Version.clean()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot lock a version", str(response.data))

    def test_action_create_new_version(self):
        url = f"/api/inventory/versions/{self.v_active_grades.id}/create-new-version/"
        version_count = Version.objects.count()
        grade_count = ProductGrade.objects.count()

        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that a new version and new grades were created
        self.assertEqual(Version.objects.count(), version_count + 1)
        self.assertEqual(
            ProductGrade.objects.count(), grade_count + 1
        )  # 1 grade (grade_a)

        new_version = Version.objects.latest("created_at")
        self.assertEqual(new_version.status, "DRAFT")
        self.assertIn("Copy of", new_version.version_name)
        self.assertEqual(new_version.grades.count(), 1)
        self.assertNotEqual(new_version.grades.first().id, self.grade_a.id)

    # --- ParameterDefinitionViewSet Tests ---

    def test_parameter_list_filter_by_version(self):
        url = f"/api/inventory/parameters/?version_id={self.v_locked_simple.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], self.param_int.name)

    def test_parameter_list_filter_by_grade(self):
        url = f"/api/inventory/parameters/?grade_id={self.grade_a.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        param_names = {p["name"] for p in response.data}
        self.assertIn(self.param_enum.name, param_names)
        self.assertIn(self.param_bool.name, param_names)

    def test_parameter_create_on_version(self):
        data = {
            "name": "New Version Param",
            "data_type": "STRING",
            "version_id": self.v_draft.id,  # Can only add to DRAFT
        }
        response = self.client.post("/api/inventory/parameters/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_param = ParameterDefinition.objects.latest("created_at")
        self.assertEqual(new_param.owner, self.v_draft)

    def test_parameter_create_validation_fail(self):
        """
        Test that ParameterDefinition.clean() is called on create.
        (e.g., adding to a LOCKED version)
        """
        data = {
            "name": "New Failing Param",
            "data_type": "STRING",
            "version_id": self.v_locked_simple.id,  # LOCKED
        }
        response = self.client.post("/api/inventory/parameters/", data, format="json")
        # This test will pass after fixing ParameterDefinitionSerializer
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # This error comes from ParameterDefinition.clean()
        self.assertIn("LOCKED version", str(response.data))

    def test_parameter_create_serializer_validation(self):
        """
        Test that ParameterDefinitionSerializer.validate() is called.
        (e.g., providing both version_id and grade_id)
        """
        data = {
            "name": "Serialzer Fail",
            "data_type": "STRING",
            "version_id": self.v_draft.id,
            "grade_id": self.grade_a.id,  # Can't provide both
        }
        response = self.client.post("/api/inventory/parameters/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not both", str(response.data))

    # --- Dashboard & Stats View Tests ---

    def test_daily_stats_view_as_manager(self):
        """
        Tests the manager view, which should see ALL records from today.
        Relies *only* on setUpTestData.
        """
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        response = self.client.get("/api/inventory/stats/daily-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Manager sees all 4 records from setup
        self.assertEqual(response.data["total_tests"], 4)
        # tr_pending, tr_unassigned
        self.assertEqual(response.data["pending_tests"], 2)
        # tr_approved
        self.assertEqual(response.data["approved_tests"], 1)
        # tr_rejected
        self.assertEqual(response.data["rejected_tests"], 1)


    def test_daily_stats_view_as_analyst(self):
        """
        Tests the analyst view, which should only see THEIR records from today.
        Relies *only* on setUpTestData.
        """
        self.client.force_authenticate(user=self.analyst_user)
        # CORRECTED URL
        response = self.client.get("/api/inventory/stats/daily-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Analyst only sees their 3 records (ignores tr_unassigned)
        self.assertEqual(response.data["total_tests"], 3)
        # tr_pending
        self.assertEqual(response.data["pending_tests"], 1)
        # tr_approved
        self.assertEqual(response.data["approved_tests"], 1)
        # tr_rejected
        self.assertEqual(response.data["rejected_tests"], 1)

    def test_inventory_stats_view(self):
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        response = self.client.get("/api/inventory/stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Based on setUpTestData
        # 1 product
        # 2 pending tests (tr_pending, tr_unassigned)
        self.assertEqual(response.data["total_products"], 1)
        self.assertEqual(response.data["pending_tests"], 2)

    def test_user_stats_views(self):
        self.client.force_authenticate(user=self.manager_user)

        # Test performance chart
        url_chart = (
            f"/api/inventory/stats/users/{self.analyst_user.id}/performance-chart/"
        )
        response_chart = self.client.get(url_chart)
        self.assertEqual(response_chart.status_code, status.HTTP_200_OK)
        # Response should be a list of 7 days (default)
        self.assertEqual(len(response_chart.data), 7)
        self.assertIn("date", response_chart.data[0])
        self.assertIn("count", response_chart.data[0])

        # NOTE: UserSummaryCountsView is not registered in the provided urls.py
        # We will skip testing it.
        # url_summary = f"/api/inventory/stats/users/{self.analyst_user.id}/summary-counts/"
        # response_summary = self.client.get(url_summary)
        # self.assertEqual(response_summary.status_code, status.HTTP_200_OK)

    def test_product_quality_detail_view(self):
        self.client.force_authenticate(user=self.manager_user)
        # CORRECTED URL
        url = f"/api/inventory/products/{self.product.id}/quality-details/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.product.name)
        self.assertEqual(response.data["has_grades"], True)
