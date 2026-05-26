from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    vk_user_id = Column(Integer, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    investigations = relationship("Investigation", back_populates="user")

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    case_id = Column(String, nullable=False) # e.g. 'case_001_gallery_ring'
    state = Column(String, nullable=False) # e.g. 'MAIN_MENU', 'WITNESS_DIALOGUE'
    current_witness_id = Column(String, nullable=True)
    current_evidence_id = Column(String, nullable=True)
    suspect_description = Column(Text, nullable=True)
    score = Column(Integer, default=0)
    is_finished = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="investigations")
    evidence = relationship("InvestigationEvidence", back_populates="investigation")
    witnesses = relationship("InvestigationWitness", back_populates="investigation")
    images = relationship("GeneratedImage", back_populates="investigation")

class InvestigationEvidence(Base):
    __tablename__ = "investigation_evidence"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    evidence_id = Column(String, nullable=False)
    is_found = Column(Boolean, default=False)
    is_analyzed = Column(Boolean, default=False)

    investigation = relationship("Investigation", back_populates="evidence")

class InvestigationWitness(Base):
    __tablename__ = "investigation_witnesses"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    witness_id = Column(String, nullable=False)
    is_interviewed = Column(Boolean, default=False)
    dialog_history = Column(JSON, default=list) # List of dicts

    investigation = relationship("Investigation", back_populates="witnesses")

class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=False)
    image_type = Column(String, nullable=False) # 'portrait', 'evidence'
    prompt = Column(Text, nullable=False)
    operation_id = Column(String, nullable=True)
    status = Column(String, default="pending")
    local_path = Column(String, nullable=True)
    vk_attachment_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    investigation = relationship("Investigation", back_populates="images")

class MessageLog(Base):
    __tablename__ = "messages_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    investigation_id = Column(Integer, ForeignKey("investigations.id"), nullable=True)
    role = Column(String, nullable=False) # 'user', 'bot'
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
