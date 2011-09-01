from armstrong.utils.backends import GenericBackend
from django.db.models import get_model


class BaseBackend(object):
    def __init__(self, backend):
        self.backend = backend


class UserBackend(BaseBackend):
    """
    Backend for handling user events and sending them to the CRM.

    Each method receives a ``user`` representing the ``User`` model
    that the action was performed on.  It also receives a ``payload``
    parameter that is the ``**kwargs`` received by the signal.
    """

    def created(self, user, **payload):
        """
        Called when a new user is created
        """
        pass

    def updated(self, user, **payload):
        """
        Called when a user is updated
        """
        pass

    def deleted(self, user, **payload):
        """
        Called when a user is deleted
        """
        pass

    def activated(self, user, **payload):
        """
        Called when a new user activates their account

        Only called when django-registration is being used
        """
        pass

    def registered(self, user, **payload):
        """
        Called when a new user registers for an account

        Only called when django-registration is being used
        """
        pass


class GroupBackend(BaseBackend):
    """
    Backend for handling group events and sending them to the CRM.

    Each method receives a ``group`` representing the ``Group`` model
    that the action was performed on.  It also receives a ``**payload``
    parameter that is all of the keyword arguments received by the signal.
    """

    def created(self, group, **payload):
        """
        Called when a new group is created
        """
        pass

    def updated(self, group, **payload):
        """
        Called when a group is updated
        """
        pass

    def deleted(self, group, **payload):
        """
        Called when a group is deleted
        """
        pass


class ProfileBackend(BaseBackend):
    def created(self, profile, **payload):
        pass

    def updated(self, profile, **payload):
        pass

    def deleted(self, profile, **payload):
        pass

class Backend(object):
    user_class = UserBackend
    group_class = GroupBackend
    profile_class = ProfileBackend

    def __init__(self, *args, **kwargs):
        self._user = None
        self._group = None
        self._profile = None

    def get_user(self):
        return self.user_class(self)

    @property
    def user(self):
        if not self._user:
            self._user = self.get_user()
        return self._user

    def get_group(self):
        return self.group_class(self)

    @property
    def group(self):
        if not self._group:
            self._group = self.get_group()
        return self._group

    def get_profile(self):
        return self.profile_class(self)

    @property
    def profile(self):
        if not self._profile:
            self._profile = self.get_profile()
        return self._profile


backend = GenericBackend("ARMSTRONG_CRM_BACKEND",
        defaults="%s.Backend" % __name__)

get_backend = backend.get_backend


def dispatch_post_save_signal(sender, **kwargs):
    created = kwargs.get("created", False)
    model = kwargs["instance"]
    backend = getattr(get_backend(), sender._meta.module_name)
    getattr(backend, "created" if created else "updated")(model, **kwargs)


def dispatch_delete_signal(sender, **kwargs):
    model = kwargs["instance"]
    getattr(get_backend(), sender._meta.module_name).deleted(model, **kwargs)


def dispatch_user_activated(sender, **kwargs):
    user = kwargs["user"]
    get_backend().user.activated(user, **kwargs)


def dispatch_user_registered(sender, **kwargs):
    user = kwargs["user"]
    get_backend().user.registered(user, **kwargs)


def connect_signals(signal, handler, *models):
    for model in models:
        signal.connect(handler, sender=model)


def connect_post_save(*models):
    from django.db.models.signals import post_save
    connect_signals(post_save, dispatch_post_save_signal, *models)


def connect_post_delete(*models):
    from django.db.models.signals import post_delete
    connect_signals(post_delete, dispatch_delete_signal, *models)


def attempt_django_registration():
    try:
        from registration.signals import user_activated
        from registration.signals import user_registered
        user_activated.connect(dispatch_user_activated)
        user_registered.connect(dispatch_user_registered)
    except ImportError:
        pass

def attempt_to_activate_profile_signals():
    # TODO: add support for idios
    from django.conf import settings
    if not getattr(settings, "AUTH_PROFILE_MODULE", False):
        return

    profile_model = get_model(*settings.AUTH_PROFILE_MODULE.split("."))

    def post_save_handler(sender, **kwargs):
        model = kwargs["instance"]
        created = kwargs.get("created", False)
        getattr(get_backend().profile, "created" if created else "updated")(model, **kwargs)

    def post_delete_handler(sender, **kwargs):
        model = kwargs["instance"]
        get_backend().profile.deleted(model, **kwargs)

    from django.db.models.signals import post_save, post_delete
    post_save.connect(post_save_handler, sender=profile_model, weak=False)
    post_delete.connect(post_delete_handler, sender=profile_model, weak=False)

def activate():
    from django.contrib.auth.models import Group
    from django.contrib.auth.models import User
    connect_post_save(User, Group)
    connect_post_delete(User, Group)

    attempt_django_registration()
    attempt_to_activate_profile_signals()
    # TODO: add support for configurable model registration
