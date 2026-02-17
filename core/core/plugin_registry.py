"""
Plugin registry for dynamic feature discovery.
Used by reports, automation triggers, and other extensible features.
"""

class PluginRegistry:
    def __init__(self):
        self._report_generators = {}
        self._automation_triggers = []
        self._webhook_handlers = {}

    def register_report(self, name: str, func):
        """Register a report generator function."""
        self._report_generators[name] = func

    def get_report(self, name: str):
        """Get report generator by name."""
        return self._report_generators.get(name)

    def register_automation_trigger(self, trigger_type: str):
        """Register an automation trigger type."""
        if trigger_type not in self._automation_triggers:
            self._automation_triggers.append(trigger_type)

    @property
    def automation_triggers(self):
        """Get all registered automation triggers."""
        return self._automation_triggers

    def register_webhook_handler(self, event_type: str, func):
        """Register a webhook handler function."""
        self._webhook_handlers[event_type] = func

    def get_webhook_handler(self, event_type: str):
        """Get webhook handler by event type."""
        return self._webhook_handlers.get(event_type)


# Singleton instance
registry = PluginRegistry()