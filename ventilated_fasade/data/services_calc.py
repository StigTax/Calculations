# data/services_calc.py
from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from .models_calc import Calculation, Engineer


def _mmYY(dt: datetime) -> str:
    return f"{dt.month:02d}{str(dt.year)[-2:]}"


def make_base_number(initials: str, seq: int, dt: datetime) -> str:
    return f"{initials}-{seq:03d}-{_mmYY(dt)}"


def make_number(base: str, version: int) -> str:
    return base if version == 0 else f"{base}-{version}"


def next_seq_for_engineer_month(session, engineer_id: int, dt: datetime) -> int:
    q = (select(func.max(Calculation.seq))
         .where(Calculation.engineer_id == engineer_id,
                Calculation.year == dt.year,
                Calculation.month == dt.month))
    last = session.execute(q).scalar()
    return 1 if last is None else int(last)+1


def create_calc(session, engineer: Engineer, address_id: Optional[int],
                input_payload: dict, result_payload: dict, dt: Optional[datetime] = None) -> Calculation:

    dt = dt or datetime.utcnow()
    seq = next_seq_for_engineer_month(session, engineer.id, dt)
    base = make_base_number(engineer.initials, seq, dt)
    number = make_number(base, 0)
    calc = Calculation(
        engineer_id=engineer.id, address_id=address_id,
        base_number=base, version=0, number=number,
        year=dt.year, month=dt.month, seq=seq,
        input_payload=input_payload, result_payload=result_payload, status="draft"
    )
    session.add(calc)
    session.flush()
    return calc


def create_revision(session, base_number: str,
                    input_payload: dict, result_payload: dict) -> Calculation:

    last_v = (session.execute(select(func.max(Calculation.version))
                              .where(Calculation.base_number == base_number)).scalar() or 0)
    new_v = last_v+1
    series = session.execute(
        select(Calculation).where(
            Calculation.base_number == base_number).limit(1)
    ).scalar_one()
    number = make_number(base_number, new_v)
    rev = Calculation(
        engineer_id=series.engineer_id, address_id=series.address_id,
        base_number=base_number, version=new_v, number=number,
        year=series.year, month=series.month, seq=series.seq,
        input_payload=input_payload, result_payload=result_payload, status="draft"
    )
    session.add(rev)
    session.flush()
    return rev
