from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator

ENTITY_TYPES = ["ppi_issuer", "payment_aggregator", "stock_broker"]


class Conditions(BaseModel):
    entity_types: list[Literal["ppi_issuer", "payment_aggregator", "stock_broker"]] = Field(default_factory=list, max_length=3)
    jurisdiction: Literal["IN"] = "IN"
    activity: str | None = Field(default=None, max_length=100)


class Scenario(BaseModel):
    rule: str = Field(min_length=3, max_length=2000)
    conditions: Conditions
    entity_ids: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_rule(self):
        self.rule = self.rule.strip()
        if len(self.rule) < 3 or not self.conditions.entity_types:
            raise ValueError("Enter a rule and select at least one target entity type")
        return self


class Ask(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    regulator: Literal["RBI", "SEBI"] | None = None
    as_of: date | None = None
    effective_only: bool = True


class Comparison(BaseModel):
    entity_ids: list[str] = Field(min_length=2, max_length=3)
    as_of: date | None = None


class VersionReview(BaseModel):
    reviewer: str = Field(min_length=3, max_length=120)
    rationale: str = Field(min_length=10, max_length=2000)
    status: Literal["draft", "consultation", "final", "withdrawn", "superseded"]
    publication_date: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.effective_from and self.effective_to and self.effective_to <= self.effective_from:
            raise ValueError("Effective-to must be after effective-from (exclusive)")
        return self


class ObligationReview(BaseModel):
    reviewer: str = Field(min_length=3, max_length=120)
    rationale: str = Field(min_length=10, max_length=2000)
    conditions: Conditions
    action: str = Field(min_length=5, max_length=2000)
    quote: str = Field(min_length=10, max_length=4000)
    status: Literal["approved", "rejected"]


class ProfileReview(BaseModel):
    reviewer: str = Field(min_length=3, max_length=120)
    rationale: str = Field(min_length=10, max_length=2000)
    entity_types: list[str] = Field(max_length=20)
    activities: list[str] = Field(default_factory=list, max_length=40)
    jurisdiction: Literal["IN"] = "IN"
    effective_from: date
    effective_to: date | None = None
    source_url: str = Field(min_length=10, max_length=2000)
    complete_entity_types: bool = False

    @model_validator(mode="after")
    def valid_period(self):
        if not self.source_url.startswith("https://"):
            raise ValueError("Provide an HTTPS profile evidence URL")
        if self.effective_to and self.effective_to <= self.effective_from:
            raise ValueError("Invalid profile validity period")
        return self
