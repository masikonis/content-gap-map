"""Load a client file: private/<client>/client.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Site:
    name: str
    url: str


@dataclass
class Client:
    folder: Path
    name: str
    site_type: str
    language: str
    country: str
    seeds: list[str]
    primary: Site
    competitors: list[Site]


def load_client(folder: Path) -> Client:
    path = folder / "client.toml"
    if not path.exists():
        raise SystemExit(f"No client file at {path}. Copy examples/client.example.toml there.")
    data = tomllib.loads(path.read_text())
    try:
        return Client(
            folder=folder,
            name=data["name"],
            site_type=data["site_type"],
            language=data.get("language", "en"),
            country=data.get("country", "us"),
            seeds=data["seeds"],
            primary=Site(**data["primary"]),
            competitors=[Site(**c) for c in data.get("competitors", [])],
        )
    except KeyError as missing:
        raise SystemExit(f"{path} is missing {missing}.")
