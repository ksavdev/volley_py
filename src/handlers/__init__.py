from aiogram import Router
from . import (
    start,
    announce,
    my_ads,
    search,
    confirm,
    my_signups,
    my_ads_players,
    add_hall,
)
# убрали debug_any_callback!

router = Router()
router.include_router(start.router)
router.include_router(announce.router)
router.include_router(my_ads.router)
router.include_router(search.router)
router.include_router(confirm.router)
router.include_router(my_signups.router)
router.include_router(my_ads_players.router)
router.include_router(add_hall.router)
