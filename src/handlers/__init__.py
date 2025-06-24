from aiogram import Router
from . import (
    start,
    admin,
    announce,
    my_ads,
    search,
    confirm,
    my_signups,
    my_ads_players,
    add_hall,
    hall_request,
    menu,
    profile
)
# убрали debug_any_callback!

router = Router()
router.include_router(start.router)
router.include_router(admin.router) 
router.include_router(announce.router)
router.include_router(my_ads.router)
router.include_router(search.router)
router.include_router(confirm.router)
router.include_router(my_signups.router)
router.include_router(my_ads_players.router)
router.include_router(add_hall.router)
router.include_router(hall_request.router)
router.include_router(menu.router)
router.include_router(profile.router)
