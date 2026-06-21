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
# 4. HLAVNÝ INPUT OBJEKT
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

        self._validate_context_consistency()

    def _validate_context_consistency(self) -> None:
        source      = self.context.source
        interaction = self.context.interaction
        stimulus    = self.context.stimulus

        # Q&A stimuli are only meaningful in a dialogue, not in a monologue.
        if interaction == "monologue" and stimulus in {"question_prompt", "answer_context"}:
            raise ValueError(
                f"Inconsistent context: stimulus='{stimulus}' implies a dialogue partner, "
                f"but interaction='{interaction}'. "
                f"Set interaction='dialogue' or use a non-conversational stimulus."
            )

        # A written or uploaded document cannot be the behavioural result of
        # hearing someone speak — that is an auditory verbal interaction.
        if source in {"written_record", "uploaded_document"} and stimulus == "auditory_verbal_stimulus":
            raise ValueError(
                f"Inconsistent context: source='{source}' is a written artefact, "
                f"but stimulus='{stimulus}' presupposes a spoken/auditory origin. "
                f"Use stimulus='written_verbal_stimulus' or 'nonverbal_object' for written texts."
            )

        # A spoken recording cannot be controlled by a written text as stimulus.
        if source == "spoken_record" and stimulus == "written_verbal_stimulus":
            raise ValueError(
                f"Inconsistent context: source='{source}' describes live speech, "
                f"but stimulus='{stimulus}' implies the speaker was reading a text. "
                f"Use stimulus='auditory_verbal_stimulus' for spoken responses."
            )

        # A genuine dialogue must involve some form of verbal exchange;
        # 'none' explicitly rules out any controlling stimulus.
        if interaction == "dialogue" and stimulus == "none":
            raise ValueError(
                f"Inconsistent context: interaction='{interaction}' requires a verbal stimulus, "
                f"but stimulus='{stimulus}' explicitly denies one. "
                f"Use stimulus='auditory_verbal_stimulus', 'question_prompt', or 'answer_context' "
                f"for dialogues."
            )


# ==========================================================
# 5. FILE LOADER
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

    context = InputContext(

        source=source,

        interaction=interaction,

        stimulus=stimulus,

        speaker=speaker,

        addressee=addressee,

        notes=notes,
    )

    metadata = TextMetadata(

        text_id=text_id or str(uuid4()),

        corpus_id=corpus_id,

        source_id=source_id,

        document_id=document_id,

        book=book,

        chapter=chapter,

        verse=verse,

        unit=unit,
    )

    text_input = TextInput(

        text=text,

        context=context,

        metadata=metadata,
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

    text = load_text_from_file(
        str(path)
    )

    return create_input_from_text(

        text=text,

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