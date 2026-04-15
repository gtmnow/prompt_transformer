from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.profile import (
    BehavioralAdjProfile,
    BrainChemistryProfile,
    EnvironmentDetailsProfile,
    FinalProfile,
    TypeDetailProfile,
)


PROFILE_ROWS = [
    {
        "user_id_hash": "user_1",
        "structure": 0.95,
        "answer_first": 0.9,
        "tone_directness": 0.8,
        "detail_level": 0.75,
        "ambiguity_reduction": 0.9,
        "exploration_level": 0.2,
        "context_loading": 0.65,
        "profile_version": "v1",
    },
    {
        "user_id_hash": "user_2",
        "structure": 0.2,
        "answer_first": 0.25,
        "tone_directness": 0.45,
        "detail_level": 0.4,
        "ambiguity_reduction": 0.3,
        "exploration_level": 0.9,
        "context_loading": 0.8,
        "profile_version": "v1",
    },
    {
        "user_id_hash": "user_3",
        "structure": 0.8,
        "answer_first": 0.7,
        "tone_directness": 0.65,
        "detail_level": 0.95,
        "ambiguity_reduction": 0.95,
        "exploration_level": 0.35,
        "context_loading": 0.85,
        "profile_version": "v1",
    },
    {
        "user_id_hash": "user_4",
        "structure": 0.5,
        "answer_first": 0.5,
        "tone_directness": 0.5,
        "detail_level": 0.5,
        "ambiguity_reduction": 0.5,
        "exploration_level": 0.5,
        "context_loading": 0.5,
        "profile_version": "v1",
    },
]


def seed_table(session: Session, model: type[FinalProfile]) -> None:
    for row in PROFILE_ROWS:
        exists = session.get(model, row["user_id_hash"])
        if exists:
            continue
        session.add(model(**row))


def run_seed() -> None:
    session = SessionLocal()
    try:
        for model in (
            FinalProfile,
            TypeDetailProfile,
            BrainChemistryProfile,
            EnvironmentDetailsProfile,
            BehavioralAdjProfile,
        ):
            seed_table(session, model)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()
