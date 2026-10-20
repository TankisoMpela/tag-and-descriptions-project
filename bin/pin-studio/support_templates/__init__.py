"""Incoming reference remakes for the supporting-image catalogue."""

from . import fashion, objects, photo, poster, t30332

MODULES = (t30332, fashion, photo, poster, objects)


def register(api):
    for module in MODULES:
        module.register(api)
