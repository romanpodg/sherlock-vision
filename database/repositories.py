from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Investigation
from core.states import UserState
import logging

logger = logging.getLogger("sherlock_vision.repo")

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, vk_user_id: int) -> User:
        result = await self.session.execute(select(User).where(User.vk_user_id == vk_user_id))
        user = result.scalars().first()
        
        if not user:
            user = User(vk_user_id=vk_user_id)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"Created new user with vk_id {vk_user_id}")
            
        return user

class InvestigationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_investigation(self, user_id: int) -> Investigation | None:
        result = await self.session.execute(
            select(Investigation)
            .where(Investigation.user_id == user_id)
            .where(Investigation.is_finished == False)
        )
        return result.scalars().first()

    async def create_investigation(self, user_id: int, case_id: str) -> Investigation:
        inv = Investigation(
            user_id=user_id,
            case_id=case_id,
            state=UserState.CASE_INTRO.value
        )
        self.session.add(inv)
        await self.session.commit()
        await self.session.refresh(inv)
        return inv

    async def update_state(self, investigation_id: int, new_state: UserState):
        result = await self.session.execute(
            select(Investigation).where(Investigation.id == investigation_id)
        )
        inv = result.scalars().first()
        if inv:
            inv.state = new_state.value
            await self.session.commit()
