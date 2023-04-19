from fastapi import APIRouter

router = APIRouter()

@router.get('/')
async def get_company_name():
    return {'Company Name':'Example Company, LLC'}

@router.get('/employee')
async def number_of_employees():
    return 160