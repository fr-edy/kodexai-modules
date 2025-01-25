from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RegUpdateTypes(str, Enum):
    """Types of regulatory updates parsed from Regulators."""

    REGULATION = "regulation"  # Laws / regulations / directives
    NEWS = "news"  # News / press releases


class Regulators(str, Enum):
    """Financial regulators that are being parsed for regulatory updates of RegUpdateTypes.
    The string value contains the official abbreviation of the regulator."""

    MAS = "MAS"  # Monetary Authority of Singapore (SG)
    # TODO: add ECB

    @classmethod
    def from_string(cls, regulator_str: str):
        for regulator in cls:
            if regulator.value.lower() == regulator_str.lower():
                return regulator
        raise ValueError(f"{regulator_str} is not a valid {cls.__name__}")

    @property
    def full_name(self) -> str:
        """Return the full name of the regulator."""
        return {
            Regulators.MAS: "Monetary Authority of Singapore",
            # TODO: add ECB
        }[self]

    @property
    def language(self) -> str:
        return {
            Regulators.MAS: "English",
            # TODO: add ECB
        }[self]

    @property
    def base_url(self) -> str:
        return {
            Regulators.MAS: "https://www.mas.gov.sg",
            # TODO: add ECB
        }[self]


@dataclass
class RegulatorPublication:
    regulator: Regulators
    type: RegUpdateTypes
    web_title: str
    published_at: datetime
    web_url: str = None
    category: str = ""
    ai_topic: str = None
    related_urls: list[str] = field(default_factory=list)

    def __str__(self):
        return (
            f"{self.regulator.value} {self.type.value} from {self.published_at.strftime('%Y-%m-%d')}: "
            f"{self.web_title} ({self.web_url})"
        )
