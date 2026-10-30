"""Site-type profiles: what differs between kinds of business, kept out of the core.

A profile holds the words that expand a seed for autocomplete, the rule for what counts as a buyer
question, and the angles for predicted questions. A site type without its own profile uses
"generic". Adding a site type means adding one entry here.
"""

from dataclasses import dataclass

QUESTION_WORDS = ["how", "how much", "how to", "what", "why", "when", "where", "which", "who",
                  "can", "do", "does", "is", "are", "should"]


@dataclass(frozen=True)
class Profile:
    before: list[str]      # words put before a seed for autocomplete
    after: list[str]       # words put after a seed for autocomplete
    buyer: str             # what counts as a buyer question, for the tagger
    angles: str            # what predicted questions should cover


SERVICES = Profile(
    before=QUESTION_WORDS,
    after=["cost", "price", "vs", "near me", "for", "with", "without", "worth it", "or", "and"],
    buyer="""one a person would ask while deciding whether, when or whom to hire for these services
(price, value, what is included, how often, which option, what to expect). It is not a buyer
question if it is about doing the job yourself, buying equipment or supplies, running or pricing a
business that offers the service, or one specific other company.""",
    angles="""why, what happens if, when and when not, risks and worries, what is included, how
long it takes, comparisons between options, cost, and hiring someone versus doing it yourself""",
)

B2B_SOFTWARE = Profile(
    before=QUESTION_WORDS + ["best", "top", "cheapest", "types of"],
    after=["pricing", "cost", "vs", "alternatives", "for small business", "features", "types",
           "disadvantages", "reviews", "free", "per user", "integration", "comparison", "or", "and"],
    buyer="""one a person or business would ask while researching, comparing, choosing, buying,
switching or setting up software in this category: what it is and what it does, the types,
features, the best options, pricing, comparisons and alternatives (including named vendors),
downsides and risks, and fit for their size or industry. It is not a buyer question if it is about
personal or consumer use, taxes or accounting, a different product category, a how-to unrelated to
choosing or using this software, or news and trivia about one company.""",
    angles="""what it is and does, the types, must-have features, the best options for their size,
pricing and cost per user, comparisons between vendors and alternatives, downsides and risks,
switching from what they use now, setup, and integrations with their other tools""",
)

GENERIC = Profile(
    before=QUESTION_WORDS,
    after=["cost", "price", "vs", "best", "alternatives", "for", "with", "without", "worth it",
           "or", "and"],
    buyer="""one a person would ask while deciding whether, what and from whom to buy or use what
this business offers (what it is, price, value, options, comparisons, risks, what to expect). It
is not a buyer question if it is about doing it yourself, an unrelated product, running a business
that offers the same thing, or news and trivia about one company.""",
    angles="""what it is, why it matters, when and when not, risks and worries, what is included,
cost, comparisons between options, and doing it yourself versus paying for it""",
)

PROFILES = {"services": SERVICES, "b2b-software": B2B_SOFTWARE, "generic": GENERIC}


def profile(site_type: str) -> Profile:
    return PROFILES.get(site_type, GENERIC)
