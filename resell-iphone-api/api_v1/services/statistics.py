from datetime import datetime

from sqlalchemy import select, func, and_

from core.db.tables import User, Order, Item, Role
from core.models.statistics import StatisticsResponse
from database import db


async def get_statistics() -> StatisticsResponse:
    sessionmaker = db.sessionmaker
    async with sessionmaker() as session:
        # Get current year and month
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month

        # Get total users
        total_users = await session.execute(
            select(func.count(User.id))
        )
        total_users_count = total_users.scalar()

        # Get seller role id
        seller_role = await session.execute(
            select(Role.id).where(Role.name == 'seller')
        )
        seller_role_id = seller_role.scalar()

        # Get buyer role id
        buyer_role = await session.execute(
            select(Role.id).where(Role.name == 'buyer')
        )
        buyer_role_id = buyer_role.scalar()

        # Get total sellers (users with role 'seller')
        total_sellers = await session.execute(
            select(func.count(User.id)).where(User.role_id == seller_role_id)
        )
        total_sellers_count = total_sellers.scalar()

        # Get total buyers (users with role 'buyer')
        total_buyers = await session.execute(
            select(func.count(User.id)).where(User.role_id == buyer_role_id)
        )
        total_buyers_count = total_buyers.scalar()

        # Get active sellers (users who have items)
        active_sellers = await session.execute(
            select(func.count(func.distinct(Item.user_id)))
        )
        active_sellers_count = active_sellers.scalar()

        # Get active buyers (users who have orders)
        active_buyers = await session.execute(
            select(func.count(func.distinct(Order.buyer_id)))
        )
        active_buyers_count = active_buyers.scalar()

        # Get total orders
        total_orders = await session.execute(
            select(func.count(Order.id))
        )
        total_orders_count = total_orders.scalar()

        # Get yearly orders
        yearly_orders = await session.execute(
            select(func.count(Order.id)).where(
                func.extract('year', Order.created_at) == current_year
            )
        )
        yearly_orders_count = yearly_orders.scalar()

        # Get monthly orders
        monthly_orders = await session.execute(
            select(func.count(Order.id)).where(
                and_(
                    func.extract('year', Order.created_at) == current_year,
                    func.extract('month', Order.created_at) == current_month
                )
            )
        )
        monthly_orders_count = monthly_orders.scalar()

        # Get total profit
        total_profit = await session.execute(
            select(func.sum(Order.total))
        )
        total_profit_amount = total_profit.scalar() or 0.0

        # Get yearly profit
        yearly_profit = await session.execute(
            select(func.sum(Order.total)).where(
                func.extract('year', Order.created_at) == current_year
            )
        )
        yearly_profit_amount = yearly_profit.scalar() or 0.0

        # Get monthly profit
        monthly_profit = await session.execute(
            select(func.sum(Order.total)).where(
                and_(
                    func.extract('year', Order.created_at) == current_year,
                    func.extract('month', Order.created_at) == current_month
                )
            )
        )
        monthly_profit_amount = monthly_profit.scalar() or 0.0

        return StatisticsResponse(
            total_users=total_users_count,
            total_sellers=total_sellers_count,
            total_buyers=total_buyers_count,
            active_sellers=active_sellers_count,
            active_buyers=active_buyers_count,
            total_orders=total_orders_count,
            yearly_orders=yearly_orders_count,
            monthly_orders=monthly_orders_count,
            total_profit=total_profit_amount,
            yearly_profit=yearly_profit_amount,
            monthly_profit=monthly_profit_amount,
            last_updated=current_date
        ) 