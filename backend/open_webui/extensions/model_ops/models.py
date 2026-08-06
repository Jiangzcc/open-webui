from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Index, Integer, String

from .db import JSONField, ModelOpsBase


class ImageModelOperation(ModelOpsBase):
    __tablename__ = 'ext_image_model_operation'
    __table_args__ = (
        CheckConstraint('sort_order >= 0', name='ck_ext_image_model_operation_sort_order'),
        Index('ix_ext_image_model_operation_visibility', 'visible', 'enabled', 'sort_order', 'model_id'),
        Index('ix_ext_image_model_operation_recommended', 'recommended', 'sort_order', 'model_id'),
    )

    model_id = Column(String(256), primary_key=True)
    visible = Column(Boolean, nullable=False, server_default='true')
    enabled = Column(Boolean, nullable=False, server_default='true')
    recommended = Column(Boolean, nullable=False, server_default='false')
    sort_order = Column(Integer, nullable=False, server_default='1000')
    tags_json = Column(JSONField, nullable=False, server_default='[]')
    maintenance_message = Column(String(500), nullable=True)
    updated_by_id = Column(String(128), nullable=True)
    updated_by_name_snapshot = Column(String(256), nullable=True)
    updated_at = Column(BigInteger, nullable=False)


__all__ = ['ImageModelOperation']
