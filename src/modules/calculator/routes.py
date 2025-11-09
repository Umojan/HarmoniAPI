"""Calculator routes for calorie calculation."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.db.engine import get_session
from src.modules.calculator.schemas import (
    CalculateRequest,
    CalculateResponse,
    TariffInfo,
)
from src.modules.calculator.service import CalculatorService

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/calculator/calculate",
    response_model=CalculateResponse,
    status_code=status.HTTP_200_OK,
)
async def calculate_calories(
    request_data: CalculateRequest,
    session: AsyncSession = Depends(get_session),
) -> CalculateResponse:
    """
    Calculate personalized daily calorie requirements and recommend tariff.

    Uses **Mifflin-St Jeor formula (1990)** to calculate BMR, applies activity
    multiplier for TDEE, and adjusts based on fitness goal.

    ## Request Body
    - **gender**: User gender (`male` or `female`)
    - **age**: User age in years (15-120)
    - **weight_kg**: User weight in kilograms (30-300)
    - **height_cm**: User height in centimeters (100-250)
    - **activity_level**: Physical activity level (`sedentary`, `light`, `moderate`, `active`, `very_active`)
    - **goal**: Fitness goal (`weight_loss`, `maintenance`, `muscle_gain`)

    ## Response
    - **recommended_calories**: Recommended daily calorie intake (integer)
    - **tariff**: Recommended tariff plan (object or null if no matching tariff)

    ## Example Request
    ```json
    {
        "gender": "female",
        "age": 25,
        "weight_kg": 65,
        "height_cm": 170,
        "activity_level": "moderate",
        "goal": "weight_loss"
    }
    ```

    ## Example Response
    ```json
    {
        "recommended_calories": 1711,
        "tariff": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Fit Start",
            "description": "Starter plan for weight loss",
            "calories": 1650,
            "base_price": 4900
        }
    }
    ```
    """
    calculator_service = CalculatorService(session)

    # Calculate calories and find matching tariff
    recommended_calories, tariff = await calculator_service.calculate(
        gender=request_data.gender,
        age=request_data.age,
        weight_kg=request_data.weight_kg,
        height_cm=request_data.height_cm,
        activity_level=request_data.activity_level,
        goal=request_data.goal,
    )

    # Build response
    tariff_info = None
    if tariff:
        tariff_info = TariffInfo(
            id=str(tariff.id),
            name=tariff.name,
            description=tariff.description,
            calories=tariff.calories,
            base_price=tariff.base_price,
        )

    logger.info(
        f"Calorie calculation: {recommended_calories} kcal/day, "
        f"tariff={tariff.name if tariff else 'None'}"
    )

    return CalculateResponse(
        recommended_calories=recommended_calories,
        tariff=tariff_info,
    )
