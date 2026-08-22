import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal
from uuid import uuid4


# ==========================================================
# 1. TYPOVÉ DEFINÍCIE
# ==========================================================

# Odkiaľ pochádza analyzovaný záznam
SourceType = Literal[
    "spoken_record",     # audio/prepis hovorenia
    "written_record",    # dokument/esej/list
    "uploaded_document",
    "transcript",        # prepis interakcie
    "unknown",
]

# Typ interakcie
InteractionType = Literal[
    "monologue",
    "dialogue",
    "unknown",
]

# ČO kontrolovalo verbálne správanie
# (Skinnerov controlling stimulus)
StimulusType = Literal[
    "nonverbal_object",          # reálny objekt/udalost
    "written_verbal_stimulus",   # písaný text ako stimul
    "auditory_verbal_stimulus",  # počutá reč
    "question_prompt",           # otázka ako stimul pre odpoveď
    "answer_context",            # výrok je odpoveď na predchádzajúcu otázku
    "private_event",             # vnútorný stav/pocit
    "none",
    "unknown",
]


TextUnitType = Literal[
    "corpus",
    "document",
    "book",
    "chapter",
    "section",
    "verse",
    "paragraph",
    "sentence",
    "fragment",
    "unknown",
]

# ==========================================================
# 2. KONTEXT
# ==========================================================

@dataclass
class InputContext:

    source: SourceType = "unknown"

    interaction: InteractionType = "unknown"

    stimulus: StimulusType = "unknown"

    speaker: Optional[str] = None
    addressee: Optional[str] = None

    notes: Optional[str] = None

# ==========================================================
# 3. METADATA
# ==========================================================

@dataclass
class TextMetadata:

    text_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    corpus_id: Optional[str] = None
    source_id: Optional[str] = None
    document_id: Optional[str] = None

    book: Optional[str] = None
    chapter: Optional[int] = None
    verse: Optional[int] = None

    unit: TextUnitType = "unknown"

# ==========================================================
# 4. SKINNER CONTEXT CONSISTENCY
# ==========================================================

# Codes are shared with the Streamlit UI (app._context_warnings) so the same
# four Skinner-context rules cannot drift between validate() and the sidebar.
CONTEXT_ISSUE_QA_MONO = "qa_mono"
CONTEXT_ISSUE_AUDIO_WRITTEN = "audio_written"
CONTEXT_ISSUE_WRITTEN_SPOKEN = "written_spoken"
CONTEXT_ISSUE_DIALOGUE_NONE = "dialogue_none"

_CONTEXT_ERROR_MESSAGES = {
    CONTEXT_ISSUE_QA_MONO: (
        "Inconsistent context: stimulus='{stimulus}' implies a dialogue partner, "
        "but interaction='{interaction}'. "
        "Set interaction='dialogue' or use a non-conversational stimulus."
    ),
    CONTEXT_ISSUE_AUDIO_WRITTEN: (
        "Inconsistent context: source='{source}' is a written artefact, "
        "but stimulus='{stimulus}' presupposes a spoken/auditory origin. "
        "Use stimulus='written_verbal_stimulus' or 'nonverbal_object' for written texts."
    ),
    CONTEXT_ISSUE_WRITTEN_SPOKEN: (
        "Inconsistent context: source='{source}' describes live speech, "
        "but stimulus='{stimulus}' implies the speaker was reading a text. "
        "Use stimulus='auditory_verbal_stimulus' for spoken responses."
    ),
    CONTEXT_ISSUE_DIALOGUE_NONE: (
        "Inconsistent context: interaction='{interaction}' requires a verbal stimulus, "
        "but stimulus='{stimulus}' explicitly denies one. "
        "Use stimulus='auditory_verbal_stimulus', 'question_prompt', or 'answer_context' "
        "for dialogues."
    ),
}


def context_inconsistency_codes(
    source: str,
    interaction: str,
    stimulus: str,
) -> list[str]:
    """Return Skinner-context inconsistency codes (empty if the triple is valid).

    Q&A stimuli require dialogue; written artefacts cannot be auditory-controlled;
    spoken records cannot be written-controlled; dialogue cannot have stimulus=none.
    """
    codes: list[str] = []
    if interaction == "monologue" and stimulus in {"question_prompt", "answer_context"}:
        codes.append(CONTEXT_ISSUE_QA_MONO)
    if source in {"written_record", "uploaded_document"} and stimulus == "auditory_verbal_stimulus":
        codes.append(CONTEXT_ISSUE_AUDIO_WRITTEN)
    if source == "spoken_record" and stimulus == "written_verbal_stimulus":
        codes.append(CONTEXT_ISSUE_WRITTEN_SPOKEN)
    if interaction == "dialogue" and stimulus == "none":
        codes.append(CONTEXT_ISSUE_DIALOGUE_NONE)
    return codes


# ==========================================================
# 5. HLAVNÝ INPUT OBJEKT
# ==========================================================

@dataclass
class TextInput:

    text: str

    context: InputContext = field(
        default_factory=InputContext
    )

    metadata: TextMetadata = field(
        default_factory=TextMetadata
    )

    def validate(self) -> None:

        if self.text is None:
            raise ValueError(
                "Input text is missing."
            )

        if not isinstance(self.text, str):
            raise TypeError(
                "Input text must be a string."
            )

        if not self.text.strip():
            raise ValueError(
                "Input text is empty."
            )

        if len(self.text.strip()) < 2:
            raise ValueError(
                "Input text is too short."
            )

        if self.metadata.chapter is not None and self.metadata.chapter < 1:
            raise ValueError(
                "Chapter must be a positive integer."
            )

        if self.metadata.verse is not None and self.metadata.verse < 1:
            raise ValueError(
                "Verse must be a positive integer."
            )

        for code in context_inconsistency_codes(
            self.context.source, self.context.interaction, self.context.stimulus
        ):
            raise ValueError(
                _CONTEXT_ERROR_MESSAGES[code].format(
                    source=self.context.source,
                    interaction=self.context.interaction,
                    stimulus=self.context.stimulus,
                )
            )


# ==========================================================
# 6. FILE LOADER
# ==========================================================

def load_text_from_file(
    file_path: str
) -> str:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File does not exist: {file_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    raw_text = path.read_text(
        encoding="utf-8"
    )

    stripped = raw_text.strip()

    if stripped.startswith("{") and stripped.endswith("}"):

        try:
            parsed = ast.literal_eval(stripped)

            if isinstance(parsed, dict):
                return " ".join(
                    str(value)
                    for value in parsed.values()
                )

        except (SyntaxError, ValueError):
            pass

    return raw_text

# ==========================================================
# 6. FACTORY: TEXT → INPUT
# ==========================================================

def create_input_from_text(
    text: str,
    source: SourceType = "unknown",
    interaction: InteractionType = "unknown",
    stimulus: StimulusType = "unknown",
    speaker: Optional[str] = None,
    addressee: Optional[str] = None,
    notes: Optional[str] = None,
    corpus_id: Optional[str] = None,
    source_id: Optional[str] = None,
    document_id: Optional[str] = None,
    book: Optional[str] = None,
    chapter: Optional[int] = None,
    verse: Optional[int] = None,
    unit: TextUnitType = "unknown",
    text_id: Optional[str] = None,
) -> TextInput:
    text_input = TextInput(
        text=text,
        context=InputContext(
            source=source,
            interaction=interaction,
            stimulus=stimulus,
            speaker=speaker,
            addressee=addressee,
            notes=notes,
        ),
        metadata=TextMetadata(
            text_id=text_id or str(uuid4()),
            corpus_id=corpus_id,
            source_id=source_id,
            document_id=document_id,
            book=book,
            chapter=chapter,
            verse=verse,
            unit=unit,
        ),
    )
    text_input.validate()
    return text_input

# ==========================================================
# 7. FACTORY: FILE → INPUT
# ==========================================================

def create_input_from_file(
    file_path: str,
    source: SourceType = "written_record",
    interaction: InteractionType = "monologue",
    stimulus: StimulusType = "unknown",
    speaker: Optional[str] = None,
    addressee: Optional[str] = None,
    notes: Optional[str] = None,
    corpus_id: Optional[str] = None,
    source_id: Optional[str] = None,
    document_id: Optional[str] = None,
    book: Optional[str] = None,
    chapter: Optional[int] = None,
    verse: Optional[int] = None,
    unit: TextUnitType = "document",
    text_id: Optional[str] = None,
) -> TextInput:
    path = Path(file_path)
    return create_input_from_text(
        text=load_text_from_file(str(path)),
        source=source,
        interaction=interaction,
        stimulus=stimulus,
        speaker=speaker,
        addressee=addressee,
        notes=notes,
        corpus_id=corpus_id,
        source_id=source_id or path.name,
        document_id=document_id,
        book=book,
        chapter=chapter,
        verse=verse,
        unit=unit,
        text_id=text_id,
    )

# ==========================================================
# 8. TEST BLOCK
# ==========================================================

if __name__ == "__main__":

    sample = create_input_from_text(
        text="Na počátku stvořil Bůh nebe a zemi.",
        source="written_record",
        interaction="monologue",
        stimulus="unknown",
        speaker=None,
        addressee=None,
        notes="General religious text test",
        corpus_id="test_corpus",
        source_id="manual_sample",
        document_id="genesis_sample",
        book="Genesis",
        chapter=1,
        verse=1,
        unit="verse",
)

    print(sample)