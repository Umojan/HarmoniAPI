"""Calculator service for BMR, TDEE, and tariff recommendation."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.settings import settings
from src.modules.calculator.schemas import ActivityLevel, Gender, Goal
from src.modules.tariffs.models import Tariff

logger = get_logger(__name__)


class CalculatorService:
    """Service for calorie calculations and tariff recommendations."""

    # Activity level multipliers based on standard TDEE formulas
    ACTIVITY_MULTIPLIERS = {
        ActivityLevel.SEDENTARY: 1.2,
        ActivityLevel.LIGHT: 1.375,
        ActivityLevel.MODERATE: 1.55,
        ActivityLevel.ACTIVE: 1.725,
        ActivityLevel.VERY_ACTIVE: 1.9,
    }

    def __init__(self, session: AsyncSession):
        """Initialize calculator service.

        Args:
            session: Database session for tariff queries
        """
        self.session = session

    def calculate_bmr(
        self, gender: Gender, age: int, weight_kg: float, height_cm: float
    ) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor formula (1990).

        Formula:
        - Male: BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) + 5
        - Female: BMR = (10 × weight_kg) + (6.25 × height_cm) - (5 × age) - 161

        Args:
            gender: User gender
            age: User age in years
            weight_kg: User weight in kilograms
            height_cm: User height in centimeters

        Returns:
            Basal Metabolic Rate in kcal/day
        """
        base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)

        if gender == Gender.MALE:
            bmr = base + 5
        else:  # Gender.FEMALE
            bmr = base - 161

        logger.debug(
            f"BMR calculated: {bmr:.1f} kcal/day for {gender.value}, "
            f"age={age}, weight={weight_kg}kg, height={height_cm}cm"
        )

        return bmr

    def calculate_tdee(self, bmr: float, activity_level: ActivityLevel) -> float:
        """Calculate Total Daily Energy Expenditure.

        TDEE = BMR × Activity Multiplier

        Args:
            bmr: Basal Metabolic Rate
            activity_level: Physical activity level

        Returns:
            Total Daily Energy Expenditure in kcal/day
        """
        multiplier = self.ACTIVITY_MULTIPLIERS[activity_level]
        tdee = bmr * multiplier

        logger.debug(
            f"TDEE calculated: {tdee:.1f} kcal/day "
            f"(BMR={bmr:.1f} × {multiplier})"
        )

        return tdee

    def apply_goal_adjustment(self, tdee: float, goal: Goal) -> int:
        """Apply calorie adjustment based on fitness goal.

        Args:
            tdee: Total Daily Energy Expenditure
            goal: User fitness goal

        Returns:
            Recommended daily calorie intake (rounded to integer)
        """
        if goal == Goal.WEIGHT_LOSS:
            adjusted = tdee - settings.calculator_calorie_deficit
        elif goal == Goal.MUSCLE_GAIN:
            adjusted = tdee + settings.calculator_calorie_surplus
        else:  # Goal.MAINTENANCE
            adjusted = tdee

        result = round(adjusted)

        logger.debug(
            f"Goal adjustment applied: {result} kcal/day "
            f"(TDEE={tdee:.1f}, goal={goal.value})"
        )

        return result

    async def find_recommended_tariff(
        self, target_calories: int
    ) -> Optional[Tariff]:
        """Find tariff with closest calorie match.

        Args:
            target_calories: User's calculated daily calorie requirement

        Returns:
            Tariff with smallest absolute calorie difference, or None if no tariffs
            have calorie data
        """
        # Query all tariffs that have calories field populated
        stmt = select(Tariff).where(Tariff.calories.isnot(None))
        result = await self.session.execute(stmt)
        tariffs = result.scalars().all()

        if not tariffs:
            logger.warning("No tariffs with calorie data found")
            return None

        # Find tariff with minimum absolute difference
        best_tariff = min(
            tariffs,
            key=lambda t: abs(t.calories - target_calories),
        )

        calorie_diff = abs(best_tariff.calories - target_calories)
        logger.info(
            f"Recommended tariff: {best_tariff.name} "
            f"({best_tariff.calories} kcal, diff={calorie_diff})"
        )

        return best_tariff

    async def calculate(
        self,
        gender: Gender,
        age: int,
        weight_kg: float,
        height_cm: float,
        activity_level: ActivityLevel,
        goal: Goal,
    ) -> tuple[int, Optional[Tariff]]:
        """Calculate recommended calories and tariff.

        Args:
            gender: User gender
            age: User age
            weight_kg: User weight in kg
            height_cm: User height in cm
            activity_level: Physical activity level
            goal: Fitness goal

        Returns:
            Tuple of (recommended_calories, recommended_tariff)
        """
        # Step 1: Calculate BMR
        bmr = self.calculate_bmr(gender, age, weight_kg, height_cm)

        # Step 2: Calculate TDEE
        tdee = self.calculate_tdee(bmr, activity_level)

        # Step 3: Apply goal adjustment
        recommended_calories = self.apply_goal_adjustment(tdee, goal)

        # Step 4: Find matching tariff
        recommended_tariff = await self.find_recommended_tariff(recommended_calories)

        logger.info(
            f"Calculation complete: {recommended_calories} kcal/day, "
            f"tariff={recommended_tariff.name if recommended_tariff else 'None'}"
        )

        return recommended_calories, recommended_tariff
