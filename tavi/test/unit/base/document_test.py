# -*- coding: utf-8 -*-
import unittest
from unit import LogCapture
from tavi.base.documents import BaseDocument
from tavi.documents import EmbeddedDocument
from tavi.fields import EmbeddedField, ListField, StringField
from tavi.fields import DateTimeField, FloatField


class BaseDocumentNoFieldsTest(unittest.TestCase):
    class NoFieldsSample(BaseDocument):
        pass

    def setUp(self):
        super(BaseDocumentNoFieldsTest, self).setUp()
        self.no_fields_sample = self.NoFieldsSample()

    def test_get_fields(self):
        self.assertEqual([], self.no_fields_sample.fields)

    def test_get_errors(self):
        self.assertEqual(0, self.no_fields_sample.errors.count)

    def test_valid(self):
        self.assertEqual(True, self.no_fields_sample.valid)

    def test_get_field_values(self):
        self.assertEqual({}, self.no_fields_sample.field_values)


class BaseDocumentModelValidationTest(unittest.TestCase):
    class Sample(BaseDocument):
        name = StringField("name", required=True)
        payment_type = StringField("payment_type")
        created_at = DateTimeField("created_at")
        status = StringField("my_status", choices=["Good", "Bad"])

        def __validate__(self):
            self.errors.clear("status")
            if self.payment_type and not self.status:
                self.errors.add("status", "is required if payment type is set")

    def setUp(self):
        super(BaseDocumentModelValidationTest, self).setUp()
        self.sample = self.Sample(name="John", payment_type="Debit")

    def test_pass_model_level_validation(self):
        self.sample.status = "Good"
        self.assertTrue(self.sample.valid, self.sample.errors.full_messages)
        self.assertEqual(0, self.sample.errors.count)

    def test_fail_model_level_validation(self):
        self.assertFalse(self.sample.valid)
        self.assertEqual([
            "Status is required if payment type is set",
            "My Status value must be in list"
            ], self.sample.errors.full_messages)

    def test_clears_model_level_errors(self):
        self.assertFalse(self.sample.valid)
        self.assertEqual([
            "Status is required if payment type is set",
            "My Status value must be in list"
            ], self.sample.errors.full_messages)

        self.sample.status = "Bad"
        self.assertTrue(self.sample.valid, self.sample.errors.full_messages)
        self.assertEqual(0, self.sample.errors.count)

    def test_clearing_model_validation_does_not_clear_field_validation(self):
        self.assertFalse(self.sample.valid)
        self.assertIn(
            "Status is required if payment type is set",
            self.sample.errors.full_messages
        )
        self.sample.status = "Not a valid status"
        self.assertFalse(self.sample.valid)
        self.assertEqual(
            ["My Status value must be in list"],
            self.sample.errors.full_messages
        )


class BaseDocumentPropertiesTest(unittest.TestCase):
    class Sample(BaseDocument):
        name = StringField("name", required=True)
        password = StringField("password", persist=False)
        payment_type = StringField("payment_type")
        created_at = DateTimeField("created_at")
        status = StringField("my_status")

    class Address(EmbeddedDocument):
        street = StringField("street")
        city = StringField("city")

    def setUp(self):
        super(BaseDocumentPropertiesTest, self).setUp()
        self.sample = self.Sample()

    def test_get_fields(self):
        self.assertEqual(
            ["name", "payment_type", "created_at", "status"],
            self.sample.fields
        )

    def test_get_field_values(self):
        sample = self.Sample(name="John")
        self.assertEqual({
            "name": "John",
            "payment_type": None,
            "created_at": None,
            "status": None
        }, sample.field_values)

    def test_get_mongo_field_values(self):
        sample = self.Sample(name="John", status="active")
        self.assertEqual({
            "name": "John",
            "payment_type": None,
            "created_at": None,
            "my_status": "active"
        }, sample.mongo_field_values)

    def test_get_errors(self):
        self.sample.name = None
        self.assertEqual(
            ["Name is required"],
            self.sample.errors.full_messages
        )

    def test_valid_when_no_errors(self):
        self.sample.name = "test"
        self.assertTrue(self.sample.valid, "expected sample to be valid")

    def test_invalid_when_errors(self):
        self.sample.name = None
        self.assertFalse(self.sample.valid, "expected sample to be invalid")

    def test_get_field_values_with_embedded_field(self):
        class SampleWithEmbeddedField(BaseDocument):
            name = StringField("name", required=True)
            address = EmbeddedField("address", self.Address)

        sample = SampleWithEmbeddedField(name="John")
        sample.address = self.Address()
        sample.address.street = "123 Elm St."
        sample.address.city = "Anywhere"

        self.assertEqual({
            "name": "John",
            "address": {
                "street": "123 Elm St.",
                "city": "Anywhere"
            }}, sample.field_values)

    def test_get_field_values_with_embedded_list_field(self):
        class SampleWithEmbeddedListField(BaseDocument):
            addresses = ListField("addresses", self.Address)

        sample = SampleWithEmbeddedListField()
        address = self.Address(street="123 Elm Street", city="Anywhere")

        sample.addresses.append(address)

        self.assertEqual({
            "addresses": [{
                "street": "123 Elm Street",
                "city": "Anywhere"
            }]}, sample.field_values)


class BaseDocumentDirtyFieldCheckingTest(unittest.TestCase):
    class Sample(BaseDocument):
        name = StringField("name", required=True)
        password = StringField("password", persist=False)
        payment_type = StringField("payment_type")
        created_at = DateTimeField("created_at")
        status = StringField("my_status")

    def setUp(self):
        super(BaseDocumentDirtyFieldCheckingTest, self).setUp()
        self.sample = self.Sample()

    def test_field_are_not_dirty_when_initialized(self):
        self.assertEqual(0, len(self.sample.changed_fields))

    def test_field_is_added_to_changed_list_when_changed(self):
        self.sample.name = "my sample"
        self.assertEqual(set(["name"]), self.sample.changed_fields)

    def test_field_is_added_to_changed_list_only_once(self):
        self.sample.name = "my sample"
        self.assertEqual(set(["name"]), self.sample.changed_fields)
        self.sample.name = "changed name"
        self.assertEqual(set(["name"]), self.sample.changed_fields)


class BaseDocumentInitializationTest(unittest.TestCase):
    class Sample(BaseDocument):
        name = StringField("name", required=True)
        password = StringField("password", persist=False)
        payment_type = StringField("payment_type")
        created_at = DateTimeField("created_at")

    def setUp(self):
        super(BaseDocumentInitializationTest, self).setUp()
        self.sample = self.Sample()

    def test_init_with_kwargs(self):
        sample = self.Sample(name="John")
        self.assertEqual("John", sample.name)

    def test_init_ignore_non_field_kwargs(self):
        with LogCapture() as log:
            sample = self.Sample(name="John", not_a_field=True)
            self.assertEqual("John", sample.name)

        msg = "Ignoring unknown field for Sample: 'not_a_field' = 'True'"
        self.assertEqual([msg], log.messages["warning"])

    def test_init_with_kwargs_does_not_overwrite_attributes(self):
        class User(BaseDocument):
            first_name = StringField("first_name")
            last_name = StringField("last_name")

        user_a = User(first_name="John", last_name="Doe")
        user_b = User(first_name="Walter", last_name="White")

        self.assertEqual("John", user_a.first_name)
        self.assertEqual("Doe", user_a.last_name)

        self.assertEqual("Walter", user_b.first_name)
        self.assertEqual("White", user_b.last_name)

    def test_init_multiple_does_not_overwrite_attributes(self):
        class User(BaseDocument):
            first_name = StringField("first_name")
            last_name = StringField("last_name")

        user_a = User()
        user_a.first_name = "John"
        user_a.last_name = "Doe"

        user_b = User()
        user_b.first_name = "Walter"
        user_b.last_name = "White"

        self.assertEqual("John", user_a.first_name)
        self.assertEqual("Doe", user_a.last_name)

        self.assertEqual("Walter", user_b.first_name)
        self.assertEqual("White", user_b.last_name)

    def test_assign_to_list_field(self):
        class OrderLine(EmbeddedDocument):
            price = FloatField("price")

        class Order(BaseDocument):
            name = StringField("name")
            total = FloatField("total")
            order_lines = ListField("order_lines", OrderLine)

        order = Order()
        order_line = OrderLine(price=3.0)
        order.order_lines.append(order_line)

        self.assertEqual(3.0, order.order_lines[0].price)

    def test_init_with_embedded_list_args(self):
        class OrderLine(EmbeddedDocument):
            price = FloatField("price")

        class Order(BaseDocument):
            name = StringField("name")
            total = FloatField("total")
            order_lines = ListField("order_lines", OrderLine)

        order_hash = {
            "name": "foo",
            "total": 1.1,
            "order_lines": [{
                    "price": 2.1
            }]
        }
        order = Order(**order_hash)
        self.assertEqual("foo", order.name)
        self.assertEqual(2.1, order.order_lines[0].price)
