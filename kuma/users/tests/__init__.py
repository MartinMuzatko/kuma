from nose.tools import ok_

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from allauth.account.models import EmailAddress

from kuma.core.tests import KumaTestCase

from ..models import UserProfile


class UserTestCase(KumaTestCase):
    """Base TestCase for the users app test cases."""
    fixtures = ['test_users.json']

    def setUp(self):
        super(UserTestCase, self).setUp()
        self.user_model = get_user_model()


def profile(user, **kwargs):
    """Return a saved profile for a given user."""
    return UserProfile.objects.get(user=user)


def user(save=False, **kwargs):
    if 'username' not in kwargs:
        kwargs['username'] = get_random_string(length=15)
    password = kwargs.pop('password', 'password')
    user = get_user_model()(**kwargs)
    user.set_password(password)
    if save:
        user.save()
    return user


def email(save=False, **kwargs):
    if 'user' not in kwargs:
        kwargs['user'] = user(save=True)
    if 'email' not in kwargs:
        kwargs['email'] = '%s@%s.com' % (get_random_string(),
                                         get_random_string())
    email = EmailAddress(**kwargs)
    if save:
        email.save()
    return email


def verify_strings_in_response(test_strings, response):
    for test_string in test_strings:
        ok_(test_string in response.content,
            msg="Expected '%s' in content." % test_string)


def verify_strings_not_in_response(test_strings, response):
    for test_string in test_strings:
        ok_(test_string not in response.content,
            msg="Found unexpected '%s' in content." % test_string)
