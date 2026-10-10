"""Small reusable provider selection boundary."""

from .inference import DEFAULT_MODEL, DEFAULT_REVISION, LayaProvider
from .rules import RulesProvider
from .schemas import Incident, Prediction


class TriageService:
    def __init__(self, *, allow_download=False, model=DEFAULT_MODEL, revision=DEFAULT_REVISION):
        self.rules = RulesProvider()
        self.laya = LayaProvider(model=model, revision=revision, allow_download=allow_download)

    def predict(self, incident: Incident, provider: str) -> Prediction:
        if provider == "rules":
            return self.rules.predict(incident)
        if provider == "laya":
            return self.laya.predict(incident)
        raise ValueError(f"Unknown provider: {provider}")
