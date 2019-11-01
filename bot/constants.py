"""
Loads bot configuration from YAML files.
By default, this simply loads the default
configuration located at `config-default.yml`.
If a file called `config.yml` is found in the
project directory, the default configuration
is recursively updated with any settings from
the custom configuration. Any settings left
out in the custom user configuration will stay
their default values from `config-default.yml`.
"""


import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import List

import yaml
from yaml.constructor import ConstructorError

log = logging.getLogger(__name__)


def _required_env_var_constructor(loader, node):
    """
    Implements a custom YAML tag for loading required environment
    variables. If the environment variable is set, this function
    will simply return it. Otherwise, a `CRITICAL` log message is
    given and the `KeyError` is re-raised.

    Example usage in the YAML configuration:

        bot:
            token: !REQUIRED_ENV 'BOT_TOKEN'
    """

    value = loader.construct_scalar(node)

    try:
        return os.environ[value]
    except KeyError:
        log.critical(
            f"Environment variable `{value}` is required, but was not set. "
            "Set it in your environment or override the option using it in your `config.yml`."
        )
        raise


def _env_var_constructor(loader, node):
    """
    Implements a custom YAML tag for loading optional environment
    variables. If the environment variable is set, returns the
    value of it. Otherwise, returns `None`.

    Example usage in the YAML configuration:

        # Optional app configuration. Set `MY_APP_KEY` in the environment to use it.
        application:
            key: !ENV 'MY_APP_KEY'
    """

    default = None

    try:
        # Try to construct a list from this YAML node
        value = loader.construct_sequence(node)

        if len(value) >= 2:
            # If we have at least two values,
            # then we have both a key and a default value
            default = value[1]
            key = value[0]
        else:
            # Otherwise, we just have a key
            key = value[0]
    except ConstructorError:
        # This YAML node is a plain value rather than a list,
        # so we just have a key
        value = loader.construct_scalar(node)

        key = str(value)

    return os.getenv(key, default)


def _join_var_constructor(loader, node):
    """
    Implements a custom YAML tag for concatenating other tags in
    the document to strings. This allows for a much more DRY configuration
    file.
    """

    fields = loader.construct_sequence(node)
    return "".join(str(x) for x in fields)


yaml.SafeLoader.add_constructor("!ENV", _env_var_constructor)
yaml.SafeLoader.add_constructor("!JOIN", _join_var_constructor)
yaml.SafeLoader.add_constructor("!REQUIRED_ENV", _required_env_var_constructor)


with open("config-default.yml", encoding="UTF-8") as f:
    _CONFIG_YAML = yaml.safe_load(f)


def _recursive_update(original, new):
    """
    Helper method which implements a recursive `dict.update`
    method, used for updating the original configuration with
    configuration specified by the user.
    """

    for key, value in original.items():
        if key not in new:
            continue

        if isinstance(value, Mapping):
            if not any(isinstance(subvalue, Mapping) for subvalue in value.values()):
                original[key].update(new[key])
            _recursive_update(original[key], new[key])
        else:
            original[key] = new[key]


if Path("config.yml").exists():
    log.info("Found `config.yml` file, loading constants from it.")
    with open("config.yml", encoding="UTF-8") as f:
        user_config = yaml.safe_load(f)
    _recursive_update(_CONFIG_YAML, user_config)


class YAMLGetter(type):
    """
    Implements a custom metaclass used for accessing
    configuration data by simply accessing class attributes.
    Supports getting configuration from up to two levels
    of nested configuration through `section` and `subsection`.

    `section` specifies the YAML configuration section (or "key")
    in which the configuration lives, and must be set.

    `subsection` is an optional attribute specifying the section
    within the section from which configuration should be loaded.

    Example Usage:

        # config.yml
        bot:
            prefixes:
                direct_message: ''
                guild: '!'

        # config.py
        class Prefixes(metaclass=YAMLGetter):
            section = "bot"
            subsection = "prefixes"

        # Usage in Python code
        from config import Prefixes
        def get_prefix(bot, message):
            if isinstance(message.channel, PrivateChannel):
                return Prefixes.direct_message
            return Prefixes.guild
    """

    subsection = None

    def __getattr__(cls, name):
        name = name.lower()

        try:
            if cls.subsection is not None:
                return _CONFIG_YAML[cls.section][cls.subsection][name]
            return _CONFIG_YAML[cls.section][name]
        except KeyError:
            dotted_path = '.'.join(
                (cls.section, cls.subsection, name)
                if cls.subsection is not None else (cls.section, name)
            )
            log.critical(
                f"Tried accessing configuration variable at `{dotted_path}`, "
                "but it could not be found.")
            raise

    def __getitem__(cls, name):
        return cls.__getattr__(name)


# Dataclasses
class Bot(metaclass=YAMLGetter):
    section = "bot"

    activity: str
    cogs: list
    help_prefix: str
    token: str


class Channels(metaclass=YAMLGetter):
    section = "guild"
    subsection = "channels"

    admins: int
    news: int
    skins: int
    team_setups: int


class Categories(metaclass=YAMLGetter):
    section = "guild"
    subsection = "categories"

    setups: int


class VRS(metaclass=YAMLGetter):
    section = "credentials"
    subsection = "vrs"

    email: str
    password: str


class Roles(metaclass=YAMLGetter):
    section = "guild"
    subsection = "roles"

    admin: int
    pilotes: int
    moderator: int


class Guild(metaclass=YAMLGetter):
    section = "guild"

    id: int
    ignored: List[int]


class Keys(metaclass=YAMLGetter):
    section = "keys"

    deploy_bot: str
    deploy_site: str
    omdb: str
    site_api: str
    youtube: str


class Prefixes(metaclass=YAMLGetter):
    section = "bot"
    subsection = "prefixes"

    guild: list
    direct_message: list


class Reddit(metaclass=YAMLGetter):
    section = "reddit"

    request_delay: int
    subreddits: list


class Postgres(metaclass=YAMLGetter):
    section = "postgresql"

    host: str
    database: str
    user: str
    password: str


class URLs(metaclass=YAMLGetter):
    section = "urls"

    bot_avatar: str
    captain_coaster: str
    deploy: str
    gitlab_bot_repo: str
    omdb: str
    site: str
    site_api: str
    site_facts_api: str
    site_clean_api: str
    site_hiphopify_api: str
    site_idioms_api: str
    site_logs_api: str
    site_logs_view: str
    site_names_api: str
    site_quiz_api: str
    site_schema: str
    site_settings_api: str
    site_special_api: str
    site_tags_api: str
    site_user_api: str
    site_user_complete_api: str
    site_infractions: str
    site_infractions_user: str
    site_infractions_type: str
    site_infractions_by_id: str
    site_infractions_user_type_current: str
    site_infractions_user_type: str
    status: str
    paste_service: str


# Paths
BOT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BOT_DIR, os.pardir))

DEBUG_MODE = True if 'local' in os.environ.get("SITE_URL", "local") else False

# Bot replies
NEGATIVE_REPLIES = [
    "Noooooo!!",
    "Nope.",
    "I'm sorry Dave, I'm afraid I can't do that.",
    "I don't think so.",
    "Not gonna happen.",
    "Out of the question.",
    "Huh? No.",
    "Nah.",
    "Naw.",
    "Not likely.",
    "No way, José.",
    "Not in a million years.",
    "Fat chance.",
    "Certainly not.",
    "NEGATORY."
]

POSITIVE_REPLIES = [
    "Yep.",
    "Absolutely!",
    "Can do!",
    "Affirmative!",
    "Yeah okay.",
    "Sure.",
    "Sure thing!",
    "You're the boss!",
    "Okay.",
    "No problem.",
    "I got you.",
    "Alright.",
    "You got it!",
    "ROGER THAT",
    "Of course!",
    "Aye aye, cap'n!",
    "I'll allow it."
]

ERROR_REPLIES = [
    "Please don't do that.",
    "You have to stop.",
    "Do you mind?",
    "In the future, don't do that.",
    "That was a mistake.",
    "You blew it.",
    "You're bad at computers.",
    "Are you trying to kill me?",
    "Noooooo!!"
]

CC_TAUNT = [
    "On est chez les disney fans ici ?",
    "J'en ai marre des lambdas ...",
    "Vous voulez pas visiter autre chose que le parc Spirou ?",
    "Faut sortir un peu les nerds ...",
    "Vous avez laissé quelque neurones sur Goudurix ?",
    "La culture ici c'est un peu comme Mirapolis ... une légende.",
    "Si c'est bleu c'est Mack ?' Bah voyons...",
    "Eh ben, c'est plus calme qu'un 15 Août au Parc Spirou, par ici...",
    "Ça se dit coasterfan, et ça reconnait pas un coaster chinois pourri ? Non mais allô, quoi...",
    "Personne ? Vous êtes moins fiables que Lightning Rod, en fait...",
    "Et c'est le point qui s'envole, comme le technicien d'Hyperion...",
    "Oui, c'est pas un coaster facile à reconnaître. Tu t'es cru sur Ameworld, là, ou quoi ?",
    "Aussi efficaces que les opérateurs de Port Aventura... Non mais sérieux...",
    "AIRRR TIME'S UPPP. Désolé, j'ai oublié de prendre mes cachets.",
    "Hello les riders, c'est Angie et Barbara Gourde ! Voici la bonne réponse :",
    "Vous devriez avoir honte, enfiler un caleçon rouge et tourner des vidéos sur votre lit en guise de châtiment",
    "En même temps, avec tes 41 coasters, avoue que t'étais mal barré...",
    "Comme CanCanCoaster, vous faites les beaux de l'extérieur, mais quand il s'agit de passer aux choses sérieuses, il n'y a plus grand-chose...",
    "Vous avez la gueule de bois, ou quoi ? Rassurez-moi, on est pas sur Bieres'n'Parks...?",
    "Dites-vous que pour chaque coaster pourri non trouvé, un petit lutin de l'équipe a sacrifié 5 minutes de sa vie à le rentrer manuellement dans la base...",
    "Bon, si vous continuez sur cette lignée, on va finir plus rouillés que le lift de The Monster... ON SE REVEILLE !",
    "Le bon parc était Quanching... Xuixing... Quiching... Oh, et puis merde, de toute façon, les chinois c'est tous les mêmes.",
    "A chaque coaster non trouvé, un chaton meurt dans le monde. Ou le parking de Disney augmente de 5€. Au choix.",
    "Toujours pas trouvé ? Votre cerveau est plus mou que le launch de Blue Fire"
]
