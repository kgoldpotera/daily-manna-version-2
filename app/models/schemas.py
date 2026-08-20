from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class MessageText(BaseModel):
    body: str

class MessageInteractiveButtonReply(BaseModel):
    id: str
    title: str

class MessageInteractive(BaseModel):
    type: str
    button_reply: Optional[MessageInteractiveButtonReply] = None

class Context(BaseModel):
    group_id: Optional[str] = None
    from_: Optional[str] = Field(None, alias="from")

class Message(BaseModel):
    from_: str = Field(alias="from")
    id: str
    timestamp: str
    type: str
    text: Optional[MessageText] = None
    interactive: Optional[MessageInteractive] = None
    context: Optional[Context] = None

class Value(BaseModel):
    messaging_product: str
    metadata: Dict[str, Any]
    contacts: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Message]] = None

class Change(BaseModel):
    value: Value
    field: str

class Entry(BaseModel):
    id: str
    changes: List[Change]

class WebhookPayload(BaseModel):
    object: str
    entry: List[Entry]
