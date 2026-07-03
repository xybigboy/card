"""
Pydantic 模型 - 请求/响应数据验证
"""
from typing import Optional, List
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ConsumeCardsRequest(BaseModel):
    material_card_ids: List[int]


class UserResponse(BaseModel):
    id: int
    username: str
    card_gold: int
    free_draws: int
    rating: int
    wins: int
    losses: int

    class Config:
        from_attributes = True


class CardResponse(BaseModel):
    id: int
    template_id: int
    name: str
    rarity: str
    stars: int
    level: int
    attack: float
    defense: float
    hp: float
    speed: float
    skill_name: Optional[str]
    skill_desc: Optional[str]
    skill_type: Optional[str] = None
    skill_value: Optional[float] = None
    skill_trigger: Optional[str] = None
    skill_param: Optional[float] = None
    skills_json: Optional[str] = None
    is_on_battle: bool
    category: str
    image: str
    selected_image: Optional[str] = None

    class Config:
        from_attributes = True


class BulkSellRequest(BaseModel):
    rarity: str
    exclude_on_battle: bool = True


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class CardTemplateRequest(BaseModel):
    name: str
    rarity: str
    base_stars: int
    base_attack: float
    base_defense: float
    base_hp: float
    speed: float
    skill_name: Optional[str] = None
    skill_desc: Optional[str] = None
    skill_type: Optional[str] = None
    skill_value: Optional[float] = None
    skill_trigger: Optional[str] = None
    skill_param: Optional[float] = None
    skills_json: Optional[str] = None
    category: str = "其他"
    image: str = "card-default"


class CardTemplateResponse(BaseModel):
    id: int
    name: str
    rarity: str
    base_stars: int
    base_attack: float
    base_defense: float
    base_hp: float
    speed: float
    skill_name: Optional[str]
    skill_desc: Optional[str]
    skill_type: Optional[str]
    skill_value: Optional[float]
    skill_trigger: Optional[str] = None
    skill_param: Optional[float] = None
    skills_json: Optional[str] = None
    category: str
    image: str

    class Config:
        from_attributes = True


class AIGenerateRequest(BaseModel):
    provider_id: int
    count: int = 5
    category: str = ""
    theme: str = ""
    image_provider_id: Optional[int] = None  # 图片生成provider ID，不传则不生成图片


class BatchSaveRequest(BaseModel):
    cards: list


class AIProviderCreate(BaseModel):
    name: str
    base_url: str
    model: str
    api_key: str
    provider_type: str = "text"  # text / image
    is_active: bool = True


class AIProviderUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    provider_type: Optional[str] = None
    is_active: Optional[bool] = None


class ImageGenerateRequest(BaseModel):
    provider_id: int
    prompt: str
    size: str = "1024x1024"
    n: int = 1


class CardImageGenerateRequest(BaseModel):
    image_provider_id: int
    template_ids: Optional[List[int]] = None
    style: str = "default"  # default / realistic / anime / custom
    custom_style: str = ""  # 自定义风格描述（style=custom时使用）
    include_text: bool = False  # 图片是否带文字


class RewardRequest(BaseModel):
    target_type: str  # "all" / "user"
    username: Optional[str] = None  # 指定玩家名（target_type="user"时必填）
    card_gold: int = 0  # 卡金数量
    template_id: Optional[int] = None  # 卡片模板ID（发卡）
    card_count: int = 1  # 发卡数量
    card_stars: int = 1  # 卡片星级


class ChallengeByNameRequest(BaseModel):
    username: str


class GuildCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class GuildApplyRequest(BaseModel):
    guild_id: int


class GuildDepositRequest(BaseModel):
    amount: int


class GuildDistributeRequest(BaseModel):
    member_ids: List[int]
    amounts: List[int]
