"""Create an isolated in-memory clone of a dataset. Used by the executor."""

from app.sandbox.executor import Sandbox

reset_dataset = Sandbox.connect

__all__ = ["reset_dataset"]
