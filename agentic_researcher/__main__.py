import argparse
import asyncio
import json

from app.database import SessionLocal
from app.schemas.agentic_research import ResearchInput
from app.services.agentic.pipeline import agentic_research_service


async def _run(args: argparse.Namespace) -> None:
    payload = ResearchInput(
        address=args.address,
        city=args.city,
        state=args.state,
        zip=args.zip_code,
        apn=args.apn,
        strategy=args.strategy,
        assumptions={},
    )

    job = await agentic_research_service.run_sync(payload=payload)

    db = SessionLocal()
    try:
        output = agentic_research_service.get_full_output(
            db=db,
            property_id=job.research_property_id,
            job_id=job.id,
        )
    finally:
        db.close()

    print(
        json.dumps(
            {
                "job_id": job.id,
                "property_id": job.research_property_id,
                "trace_id": job.trace_id,
                "status": job.status.value,
                "output": output,
            },
            default=str,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run agentic real estate research")
    parser.add_argument("address", help="Property address")
    parser.add_argument("--city")
    parser.add_argument("--state")
    parser.add_argument("--zip", dest="zip_code")
    parser.add_argument("--apn")
    parser.add_argument(
        "--strategy",
        choices=["flip", "rental", "wholesale"],
        default="wholesale",
    )
    args = parser.parse_args()

    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
