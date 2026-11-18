from collections import OrderedDict


class AssessmentCache:
    def __init__(self, max_entries=128):
        self.max_entries=max_entries;self.items=OrderedDict()
    def key(self, release, ticker, lookback_years):
        return (ticker.upper(),release.assessment_context,release.as_of,release.required_price_session,release.evidence_cutoff_at,lookback_years,release.policy_revision,release.release_revision)
    def get(self, key):
        value=self.items.get(key)
        if value is not None:self.items.move_to_end(key)
        return value
    def put(self, key, value):
        self.items[key]=value;self.items.move_to_end(key)
        while len(self.items)>self.max_entries:self.items.popitem(last=False)
