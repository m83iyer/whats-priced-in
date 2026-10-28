"""Errors for inputs that do not define a readable reverse valuation."""

from __future__ import annotations


class ModelError(ValueError):
    """The inputs do not define a reverse valuation we can stand behind."""


class LiveDataNotImplemented(NotImplementedError):
    """A live market fetcher is a stub. The MVP is numbers in, numbers out."""
