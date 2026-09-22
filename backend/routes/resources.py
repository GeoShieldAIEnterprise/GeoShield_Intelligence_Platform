from fastapi import APIRouter
import sqlite3

from backend.services.dispatcher import get_nearest_resources
from core.config import settings
from pathlib import Path

router = APIRouter()


DATABASE = Path(settings.data_dir) / "geoshield.db"


@router.get("/resources/{county}")
def get_resources(county: str):

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # Try an exact match first
    cursor.execute(
        """
        SELECT *
        FROM infrastructure
        WHERE LOWER(TRIM(county)) = LOWER(TRIM(?))
        """,
        (county,),
    )

    resources = cursor.fetchall()

    # If nothing is found, try a partial match
    if len(resources) == 0:

        cursor.execute(
            """
            SELECT *
            FROM infrastructure
            WHERE LOWER(county) LIKE LOWER(?)
            """,
            (f"%{county}%",),
        )

        resources = cursor.fetchall()

    conn.close()

    # Temporary incident location (Nairobi CBD)
    disaster_location = (-1.286389, 36.817223)

    nearest = get_nearest_resources(
        disaster_location,
        resources,
        limit=10
    )

    return nearest