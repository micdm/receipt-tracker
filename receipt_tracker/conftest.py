from mixer.backend.django import mixer as default_mixer
from pytest import fixture

from receipt_tracker.models import User


@fixture
def mixer():
    return default_mixer


@fixture
def guest_client(client):
    return client


@fixture
def authorized_client(client, user):
    client.force_login(user)
    return client


@fixture
def user(mixer):
    user = mixer.blend(User)
    user.set_password('password')
    user.save()
    return user
