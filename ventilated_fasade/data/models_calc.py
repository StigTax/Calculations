from sqlalchemy import (
    Column, Integer, String,
    DateTime, ForeignKey, UniqueConstraint,
    JSON, Table
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class Engineer(Base):
    __tablename__ = "engineers"
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("first_name", "last_name", name="uq_engineer_name"),)

    @property
    def initials(self) -> str:
        # Первые буквы Фамилия+Имя (кириллица допустима)
        fi = (self.last_name[:1] or "").upper() + \
            (self.first_name[:1] or "").upper()
        return fi


class Manager(Base):
    __tablename__ = "managers"
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    __table_args__ = (UniqueConstraint(
        "first_name", "last_name", name="uq_manager_name"),)


class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True)
    line1 = Column(String, nullable=False)
    city = Column(String, nullable=True)
    region = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    note = Column(String, nullable=True)
    __table_args__ = (
        UniqueConstraint(
            "line1", "city", "region", "postal_code", name="uq_address"
        ),)


calculation_managers = Table(
    "calculation_managers", Base.metadata,
    Column("calculation_id", ForeignKey("calculations.id"), primary_key=True),
    Column("manager_id",     ForeignKey("managers.id"),     primary_key=True),
)


class Calculation(Base):
    __tablename__ = "calculations"
    id = Column(Integer, primary_key=True)
    engineer_id = Column(Integer, ForeignKey("engineers.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)

    base_number = Column(String, nullable=False)  # ФИ-001-0925
    version = Column(Integer, nullable=False, default=0)
    number = Column(String, nullable=False)  # итоговый номер (с суффиксом)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    seq = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
    status = Column(String, default="draft", nullable=False)

    input_payload = Column(JSON, nullable=False)
    result_payload = Column(JSON, nullable=False)

    engineer = relationship("Engineer")
    address = relationship("Address")
    managers = relationship(
        "Manager", secondary=calculation_managers, backref="calculations")

    __table_args__ = (
        UniqueConstraint("engineer_id", "year", "month",
                         "seq", name="uq_calc_series"),
        UniqueConstraint("base_number", "version", name="uq_calc_version"),
        UniqueConstraint("number", name="uq_calc_number"),
    )
