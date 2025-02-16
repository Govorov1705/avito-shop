from pydantic import BaseModel


class Item(BaseModel):
    type: str
    cost: int


class TransactionBase(BaseModel):
    amount: int


class TransactionFromUser(TransactionBase):
    fromUser: str


class TransactionToUser(TransactionBase):
    toUser: str


class CoinHistory(BaseModel):
    received: list[TransactionFromUser]
    sent: list[TransactionToUser]


class InfoResponse(BaseModel):
    coins: int
    inventory: list[Item]
    coinHistory: CoinHistory


class SendCoinRequest(TransactionToUser):
    pass
