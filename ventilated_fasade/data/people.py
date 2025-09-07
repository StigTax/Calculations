from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from config import DB_URL
from .models_calc import Engineer, Manager, Address
from typing import Optional, List

_engine = create_engine(DB_URL, future=True)
_Session = sessionmaker(bind=_engine, future=True)


def get_session():
    return _Session()

# --- Engineer (одна запись) ---


def get_engineer(session) -> Optional[Engineer]:
    return session.execute(select(Engineer).limit(1)).scalar_one_or_none()


def upsert_engineer(session, first_name: str, last_name: str, email=None, phone=None) -> Engineer:
    eng = get_engineer(session)
    if eng:
        eng.first_name, eng.last_name, eng.email, eng.phone = first_name, last_name, email, phone
    else:
        eng = Engineer(first_name=first_name,
                       last_name=last_name, email=email, phone=phone)
        session.add(eng)
    session.flush()
    return eng

# --- Manager ---


def list_managers(session) -> List[Manager]:
    return session.execute(select(Manager).order_by(Manager.last_name, Manager.first_name)).scalars().all()


def add_manager(session, first_name: str, last_name: str, email=None, phone=None) -> Manager:
    # защита от дублей по ФИО или email
    q = select(Manager).where(
        (Manager.first_name == first_name) & (Manager.last_name == last_name)
    )
    if email:
        q = q.union_all(select(Manager).where(Manager.email == email))
    existing = session.execute(q).scalars().first()
    if existing:
        return existing
    m = Manager(first_name=first_name, last_name=last_name,
                email=email, phone=phone)
    session.add(m)
    session.flush()
    return m

# --- Address ---


def upsert_address(session, line1, city=None, region=None, postal_code=None, note=None) -> Address:
    q = select(Address).where(
        Address.line1 == line1, Address.city == city, Address.region == region, Address.postal_code == postal_code
    )
    a = session.execute(q).scalar_one_or_none()
    if a:
        a.note = note
    else:
        a = Address(line1=line1, city=city, region=region,
                    postal_code=postal_code, note=note)
        session.add(a)
    session.flush()
    return a
