import codecs
import types
import typing

from dynamicscope import DYNAMIC_SCOPE
import mnllib
import mnllib.bis

from mnlscript.utils import fhex
from mnlscript.bis.globals import Globals


type LanguageName = typing.Literal["jp", "en", "fr", "de", "it", "es"]
LANGUAGE_IDS: dict[LanguageName, int] = {
    # "jp": 0x43,
    "en": 0x44,
    "fr": 0x45,
    # "de": 0x46,
    # "it": 0x47,
    # TODO
    "es": 0x48,
}
DEFAULT_LANGUAGE: LanguageName = "en"


CODEC_ERROR_HANDLER_KEEP_LITERAL = "mnlscript:keepliteral"


def keepliteral_errors(error: UnicodeError) -> tuple[str | bytes, int]:
    if isinstance(error, UnicodeEncodeError):
        return bytes([ord(x) for x in error.object[error.start : error.end]]), error.end
    if isinstance(error, UnicodeDecodeError):
        return (
            "".join([chr(x) for x in error.object[error.start : error.end]]),
            error.end,
        )
    if isinstance(error, UnicodeTranslateError):
        return error.object[error.start : error.end], error.end
    raise error


codecs.register_error(CODEC_ERROR_HANDLER_KEEP_LITERAL, keepliteral_errors)


TT = typing.TypeVar("TT", bytes, None) # had to introduce a whole-ass patch file bc this was giving me shit lol


@typing.overload
def emit_text_table[TT: (
    bytes,
    None,
)](  # pyright: ignore [reportOverlappingOverload]
    text_table_id: int, text_table: TT, *, room_id: int | None = None
) -> TT: ...
@typing.overload
def emit_text_table(  # pyright: ignore [reportOverlappingOverload]
    text_table_id: int,
    *args: typing.Any,
    room_id: int | None = None,
    **kwargs: typing.Any,
) -> mnllib.bis.TextTable: ...


def emit_text_table(
    text_table_id: int,
    *args: typing.Any,
    room_id: int | None = None,
    **kwargs: typing.Any,
) -> mnllib.bis.TextTable | bytes | None:
    if room_id is None:
        room_id = typing.cast(int, DYNAMIC_SCOPE.script_index) // 3

    if len(args) > 0 and isinstance(args[0], (bytes, types.NoneType)):
        text_table: mnllib.bis.TextTable | bytes | None = args[0]
    else:
        text_table = mnllib.bis.TextTable(*args, **kwargs)
    Globals.text_tables[room_id][text_table_id] = text_table
    return text_table


class TextEntryDefinition(typing.NamedTuple):
    text: str
    textbox_size: tuple[int, int]


@typing.overload
def emit_text_entry(
    text: str, /, textbox_size: tuple[int, int], *, room_id: int | None = None
) -> int | None: ...
@typing.overload
def emit_text_entry(
    entry: TextEntryDefinition | dict[LanguageName, TextEntryDefinition],
    /,
    *,
    room_id: int | None = None,
) -> int | None: ...


def emit_text_entry(
    entry: str | TextEntryDefinition | dict[LanguageName, TextEntryDefinition],
    /,
    textbox_size: tuple[int, int] | None = None,
    *,
    room_id: int | None = None,
) -> int | None:
    if room_id is None:
        room_id = typing.cast(int, DYNAMIC_SCOPE.script_index) // 3

    if isinstance(entry, str) and textbox_size is None:
        raise TypeError("textbox_size must not be None if entry is a str")

    text_entry_index: int | None = None
    for language_name, language_id in LANGUAGE_IDS.items():
        if isinstance(entry, dict):
            current_language_entry = entry.get(language_name, entry[DEFAULT_LANGUAGE])
        elif isinstance(entry, TextEntryDefinition):
            current_language_entry = entry
        else:
            current_language_entry = TextEntryDefinition(
                entry, typing.cast(tuple[int, int], textbox_size)
            )

        if language_id not in Globals.text_tables[room_id]:
            Globals.text_tables[room_id][language_id] = mnllib.bis.TextTable(
                [], is_dialog=True, textbox_sizes=[]
            )  # TODO: is_dialog
        text_table = Globals.text_tables[room_id][language_id]
        if not isinstance(text_table, mnllib.bis.TextTable):
            raise TypeError(
                f"emit_text_entry() text table for room {fhex(room_id, 4)} with "
                f"language ID {fhex(language_id, 2)} must be an mnllib.bis.TextTable, "
                f"not '{type(text_table).__name__}'"
            )
        if text_entry_index is None:
            text_entry_index = len(text_table.entries)
        elif len(text_table.entries) != text_entry_index:
            raise ValueError(
                "all text tables must have the same length for emit_text_entry() but "
                f"table {fhex(language_id, 2)} of room {fhex(room_id, 4)} has "
                f"a length of {len(text_table.entries)} instead of {text_entry_index}"
            )
        text_table.entries.append(
            current_language_entry.text.encode(
                mnllib.bis.BIS_ENCODING, errors=CODEC_ERROR_HANDLER_KEEP_LITERAL
            )
        )
        if text_table.textbox_sizes is not None:
            text_table.textbox_sizes.append(current_language_entry.textbox_size)

    return text_entry_index