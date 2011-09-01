from contextlib import contextmanager
import datetime
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.test.client import RequestFactory
import fudge
from fudge.inspector import arg
import unittest
from ._utils import TestCase

try:
    from registration.backends import default as registration
    from registration.signals import user_activated
    from registration.signals import user_registered
    from registration.models import RegistrationProfile
except ImportError:
    user_activated, user_registered = False, False

from .. import base


@contextmanager
def verified_mocks():
    fudge.clear_expectations
    fudge.clear_calls()
    yield
    fudge.verify()


@contextmanager
def fake_user_class(verify=True):
    random_object = object()
    user_class = fudge.Fake()
    user_class.is_callable().expects_call().times_called(1) \
            .returns(random_object)
    if verify:
        with verified_mocks():
            yield (user_class, random_object)
    else:
        yield (user_class, random_object)


@contextmanager
def fake_group_class(verify=True):
    random_object = object()
    group_class = fudge.Fake()
    group_class.is_callable().expects_call().times_called(1) \
            .returns(random_object)
    if verify:
        with verified_mocks():
            yield (group_class, random_object)
    else:
        yield (group_class, random_object)


@contextmanager
def fake_profile_class(verify=True):
    random_object = object()
    profile_class = fudge.Fake()
    profile_class.is_callable().expects_call().times_called(1) \
            .returns(random_object)
    if verify:
        with verified_mocks():
            yield (profile_class, random_object)
    else:
        yield (profile_class, random_object)


class BackendTestCase(TestCase):
    def test_returns_user_class_instance(self):
        with fake_user_class() as (user_class, random_object):
            b = base.Backend()
            b.user_class = user_class
            self.assertEqual(b.user, random_object)

    def test_only_instantiates_one_user_backend(self):
        with fake_user_class() as (user_class, random_object):
            b = base.Backend()
            b.user_class = user_class
            b.user
            b.user, "this will raise an error if not memoized"

    def test_backend_is_passed_to_user_backend(self):
        with fake_user_class(verify=False) as (user_class, random_object):
            b = base.Backend()
            user_class.with_args(b)
            b.user_class = user_class
            with verified_mocks():
                b.user, "make sure the backend was provide to the user_class"

    def test_provides_UserBackend_by_default(self):
        b = base.Backend()
        self.assertIsA(b.user, base.UserBackend)

    def test_returns_group_class_instance(self):
        with fake_group_class() as (group_class, random_object):
            b = base.Backend()
            b.group_class = group_class
            self.assertEqual(b.group, random_object)

    def test_only_instantiates_one_group_backend(self):
        with fake_group_class() as (group_class, random_object):
            b = base.Backend()
            b.group_class = group_class
            b.group
            b.group, "this will raise an error if not memoized"

    def test_backend_is_passed_to_group_backend(self):
        with fake_group_class(verify=False) as (group_class, random_object):
            b = base.Backend()
            group_class.with_args(b)
            b.group_class = group_class
            with verified_mocks():
                b.group, "make sure the backend was provide to the group_class"

    def test_provides_GroupBackend_by_default(self):
        b = base.Backend()
        self.assertIsA(b.group, base.GroupBackend)

    def test_returns_profile_class_instance(self):
        with fake_profile_class() as (profile_class, random_object):
            b = base.Backend()
            b.profile_class = profile_class
            self.assertEqual(b.profile, random_object)

    def test_only_instantiates_one_profile_backend(self):
        with fake_profile_class() as (profile_class, random_object):
            b = base.Backend()
            b.profile_class = profile_class
            b.profile
            b.profile, "this will raise an error if not memoized"

    def test_backend_is_passed_to_profile_backend(self):
        with fake_profile_class(verify=False) as (profile_class, random_object):
            b = base.Backend()
            profile_class.with_args(b)
            b.profile_class = profile_class
            with verified_mocks():
                b.profile, "make sure the backend was provide to the profile_class"

    def test_provides_ProfileBackend_by_default(self):
        b = base.Backend()
        self.assertIsA(b.profile, base.ProfileBackend)

    def test_subclasses_can_control_what_user_class_is_used(self):
        class MySpecialUserBackend(base.UserBackend):
            pass

        class MySpecialSubClass(base.Backend):
            user_class = MySpecialUserBackend

        b = MySpecialSubClass()
        self.assertIsA(b.user, MySpecialUserBackend)

        self.assertIsA(base.Backend().user, base.UserBackend,
                msg="sanity check to make sure subclasses don't bleed through")

    def test_subclasses_can_control_what_group_class_is_used(self):
        class MySpecialGroupBackend(base.GroupBackend):
            pass

        class MySpecialSubClass(base.Backend):
            group_class = MySpecialGroupBackend

        b = MySpecialSubClass()
        self.assertIsA(b.group, MySpecialGroupBackend)

        self.assertIsA(base.Backend().group, base.GroupBackend,
                msg="sanity check to make sure subclasses don't bleed through")


class UserBackendTestCase(TestCase):
    def test_sets_backend_to_provided_value(self):
        random_object = object()
        user_backend = base.UserBackend(random_object)
        self.assertEqual(user_backend.backend, random_object)


class GroupBackendTestCase(TestCase):
    def test_sets_backend_to_provided_value(self):
        random_object = object()
        group_backend = base.GroupBackend(random_object)
        self.assertEqual(group_backend.backend, random_object)


class ProfileBackendTestCase(TestCase):
    def test_sets_backend_to_provided_value(self):
        random_object = object()
        profile_backend = base.ProfileBackend(random_object)
        self.assertEqual(profile_backend.backend, random_object)


class RandomBackendForTesting(object):
    pass


class get_backendTestCase(TestCase):
    def test_returns_Backend_by_default(self):
        b = base.get_backend()
        self.assertIsA(b, base.Backend)

    def test_pays_attention_to_settings(self):
        with self.settings(ARMSTRONG_CRM_BACKEND="%s.RandomBackendForTesting" %
                __name__):
            b = base.get_backend()
            self.assertIsA(b, RandomBackendForTesting)


class ReceivingSignalsTestCase(TestCase):
    def setUp(self):
        super(ReceivingSignalsTestCase, self).setUp()
        base.activate()
        fudge.clear_calls()
        fudge.clear_expectations()
        self.factory = RequestFactory()

    def tearDown(self):
        super(ReceivingSignalsTestCase, self).tearDown()
        fudge.verify()

    def expected_payload(self, expected=None):
        def test_is_a(instance):
            def test(value):
                self.assertIsA(value, instance)
                return True
            return test

        payload = {}
        for key, value in expected.items():
            if value:
                type_data = type(value).__mro__
                if len(type_data) is 3 and type_data[-2] is type:
                    payload[key] = arg.passes_test(test_is_a(value))
                else:
                    payload[key] = value
            else:
                payload[key] = arg.any()
        return payload

    def expected_django_payload(self, model_class, is_delete=False, is_create=False):
        payload = {"instance": model_class, "signal": None, "using": None,
                   "created": is_create, }
        if not is_delete:
            payload["raw"] = None
        else:
            del payload["created"]
        return self.expected_payload(payload)


    def expected_user_payload(self, is_delete=False, is_create=False):
        return self.expected_django_payload(User, is_delete=is_delete, is_create=is_create)

    def expected_group_payload(self, is_delete=False, is_create=False):
        return self.expected_django_payload(Group, is_delete=is_delete, is_create=is_create)

    def expected_model(self, expected):
        def test(actual):
            self.assertIsA(actual, expected)
            return True
        return arg.passes_test(test)

    def expected_user_model(self):
        return self.expected_model(User)

    def expected_group_model(self):
        return self.expected_model(Group)

    def test_dispatches_user_create(self):
        fake_create = fudge.Fake()
        fake_create.is_callable().expects_call().with_args(
                self.expected_user_model(),
                **self.expected_user_payload(is_create=True))
        with fudge.patched_context(base.UserBackend, "created", fake_create):
            User.objects.create(username="foobar")

    def test_dispatches_user_update(self):
        fake_update = fudge.Fake()
        fake_update.is_callable().expects_call().with_args(
                self.expected_user_model(),
                **self.expected_user_payload())
        with fudge.patched_context(base.UserBackend, "updated", fake_update):
            u = User.objects.create(username="foobar")
            u.username = "foobar-modified"
            u.save()

    def test_dispatch_user_delete(self):
        fake_deleted = fudge.Fake()
        fake_deleted.is_callable().expects_call().with_args(
                self.expected_user_model(),
                **self.expected_user_payload(is_delete=True))
        with fudge.patched_context(base.UserBackend, "deleted", fake_deleted):
            u = User.objects.create(username="foobar")
            u.delete()

    def test_dispatches_group_create(self):
        fake_create = fudge.Fake()
        fake_create.is_callable().expects_call().with_args(
                self.expected_group_model(),
                **self.expected_group_payload(is_create=True))
        with fudge.patched_context(base.GroupBackend, "created", fake_create):
            Group.objects.create(name="foobar")

    def test_dispatches_group_update(self):
        fake_update = fudge.Fake()
        fake_update.is_callable().expects_call().with_args(
                self.expected_group_model(),
                **self.expected_group_payload())
        with fudge.patched_context(base.GroupBackend, "updated", fake_update):
            g = Group.objects.create(name="foobar")
            g.groupname = "foobar-modified"
            g.save()

    def test_dispatch_group_delete(self):
        fake_deleted = fudge.Fake()
        fake_deleted.is_callable().expects_call().with_args(
                self.expected_group_model(),
                **self.expected_group_payload(is_delete=True))
        with fudge.patched_context(base.GroupBackend, "deleted", fake_deleted):
            g = Group.objects.create(name="foobar")
            g.delete()


    def expected_registration_payload(self):
        return self.expected_payload(expected={
                "user": User,
                "signal": None,
                "request": None,
        })

    @unittest.skipIf(user_activated is False,
            "django-registration is not installed")
    def test_activate_signal_if_available(self):
        activated = fudge.Fake()
        activated.is_callable().expects_call().with_args(
                self.expected_user_model(),
                **self.expected_registration_payload())
        r = registration.DefaultBackend()
        request = self.factory.get("/activate")
        with fudge.patched_context(base.UserBackend, "activated", activated):
            u = User.objects.create(username="bob")
            a = RegistrationProfile.objects.create_profile(u)
            r.activate(request, a.activation_key)

    @unittest.skipIf(user_registered is False,
            "django-registration is not installed")
    def test_register_signal_if_available(self):
        registered = fudge.Fake()
        registered.is_callable().expects_call().with_args(
                self.expected_user_model(),
                **self.expected_registration_payload())
        r = registration.DefaultBackend()
        request = self.factory.get("/register")
        with fudge.patched_context(base.UserBackend, "registered", registered):
            r.register(request, username="bob", email="bob@example.com",
                    password1="foobar")
