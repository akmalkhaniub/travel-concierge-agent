from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Travel Concierge Agent")


# --- Models ---

class FlightOption(BaseModel):
    airline: str
    flight_number: str
    departure: str
    arrival: str
    departure_time: datetime
    arrival_time: datetime
    price: float
    currency: str = "USD"


class HotelOption(BaseModel):
    name: str
    location: str
    check_in: str
    check_out: str
    price_per_night: float
    currency: str = "USD"
    rating: float = 4.0


class Activity(BaseModel):
    name: str
    location: str
    date: str | None = None
    duration_hours: float = 2.0
    price: float = 0.0
    category: str = "sightseeing"


class TripPlan(BaseModel):
    id: str = Field(default_factory=lambda: f"trip_{uuid.uuid4().hex[:8]}")
    destination: str
    start_date: str | None = None
    end_date: str | None = None
    flights: list[FlightOption] = Field(default_factory=list)
    hotels: list[HotelOption] = Field(default_factory=list)
    activities: list[Activity] = Field(default_factory=list)
    total_budget: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "planning"


class ChatRequest(BaseModel):
    message: str
    trip_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    reply: str
    trip_id: str | None = None
    actions_taken: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)


class PlanRequest(BaseModel):
    destination: str
    start_date: str | None = None
    end_date: str | None = None
    budget: float | None = None
    interests: list[str] = Field(default_factory=list)


trips: dict[str, TripPlan] = {}


# --- Mock tool implementations ---

def search_flights(origin: str, destination: str, date: str) -> list[FlightOption]:
    base_time = datetime.utcnow().replace(hour=8, minute=0, second=0)
    return [
        FlightOption(
            airline="SkyWay Airlines", flight_number="SW-142",
            departure=origin, arrival=destination,
            departure_time=base_time, arrival_time=base_time + timedelta(hours=3),
            price=349.00,
        ),
        FlightOption(
            airline="Global Air", flight_number="GA-887",
            departure=origin, arrival=destination,
            departure_time=base_time + timedelta(hours=4),
            arrival_time=base_time + timedelta(hours=7, minutes=30),
            price=275.00,
        ),
    ]


def search_hotels(destination: str, check_in: str, check_out: str) -> list[HotelOption]:
    return [
        HotelOption(
            name="Grand Plaza Hotel", location=destination,
            check_in=check_in, check_out=check_out,
            price_per_night=189.00, rating=4.5,
        ),
        HotelOption(
            name="Budget Inn Express", location=destination,
            check_in=check_in, check_out=check_out,
            price_per_night=89.00, rating=3.8,
        ),
    ]


def search_activities(destination: str, interests: list[str] | None = None) -> list[Activity]:
    activities = [
        Activity(name=f"Walking Tour of {destination}", location=destination, duration_hours=3, price=25.0, category="sightseeing"),
        Activity(name=f"Local Food Tasting", location=destination, duration_hours=2, price=55.0, category="food"),
        Activity(name=f"Museum of History", location=destination, duration_hours=2, price=15.0, category="culture"),
    ]
    if interests:
        interests_lower = {i.lower() for i in interests}
        filtered = [a for a in activities if a.category in interests_lower]
        if filtered:
            return filtered
    return activities


def get_weather(destination: str, date: str | None = None) -> dict:
    return {
        "destination": destination,
        "date": date or "upcoming",
        "temperature_high": 24,
        "temperature_low": 16,
        "condition": "Partly cloudy",
        "humidity": 55,
    }


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    mock_rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "CAD": 1.36}
    from_rate = mock_rates.get(from_currency.upper(), 1.0)
    to_rate = mock_rates.get(to_currency.upper(), 1.0)
    converted = amount / from_rate * to_rate
    return {"original": amount, "from": from_currency, "to": to_currency, "converted": round(converted, 2)}


TOOLS = {
    "search_flights": search_flights,
    "search_hotels": search_hotels,
    "search_activities": search_activities,
    "get_weather": get_weather,
    "convert_currency": convert_currency,
}


# --- Specialist agents ---

class BaseAgent:
    name: str = "base"

    def run(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class FlightSearchAgent(BaseAgent):
    name = "flight_search"

    def run(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        origin = context.get("origin", "NYC")
        destination = context.get("destination", "")
        date = context.get("start_date", "")
        flights = search_flights(origin, destination, date)
        return {
            "agent": self.name,
            "flights": [f.model_dump(mode="json") for f in flights],
            "summary": f"Found {len(flights)} flights from {origin} to {destination}.",
        }


class HotelSearchAgent(BaseAgent):
    name = "hotel_search"

    def run(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        destination = context.get("destination", "")
        check_in = context.get("start_date", "")
        check_out = context.get("end_date", "")
        hotels = search_hotels(destination, check_in, check_out)
        return {
            "agent": self.name,
            "hotels": [h.model_dump(mode="json") for h in hotels],
            "summary": f"Found {len(hotels)} hotels in {destination}.",
        }


class ActivityPlannerAgent(BaseAgent):
    name = "activity_planner"

    def run(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        destination = context.get("destination", "")
        interests = context.get("interests", [])
        activities = search_activities(destination, interests)
        weather = get_weather(destination, context.get("start_date"))
        return {
            "agent": self.name,
            "activities": [a.model_dump(mode="json") for a in activities],
            "weather": weather,
            "summary": f"Found {len(activities)} activities in {destination}.",
        }


AGENTS = {
    "flight_search": FlightSearchAgent(),
    "hotel_search": HotelSearchAgent(),
    "activity_planner": ActivityPlannerAgent(),
}


class Coordinator:
    """Parses intent, routes to specialists, merges results."""

    def classify_intent(self, message: str) -> list[str]:
        message_lower = message.lower()
        agents_needed = []
        if any(w in message_lower for w in ["flight", "fly", "airline", "plane"]):
            agents_needed.append("flight_search")
        if any(w in message_lower for w in ["hotel", "stay", "accommodation", "lodging"]):
            agents_needed.append("hotel_search")
        if any(w in message_lower for w in ["activity", "things to do", "attractions", "sightseeing", "tour"]):
            agents_needed.append("activity_planner")
        if not agents_needed:
            agents_needed = list(AGENTS.keys())
        return agents_needed

    def run(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        needed = self.classify_intent(message)
        results = {}
        actions = []
        for agent_name in needed:
            agent = AGENTS[agent_name]
            result = agent.run(message, context)
            results[agent_name] = result
            actions.append(f"Consulted {agent_name}")

        summaries = [r.get("summary", "") for r in results.values() if r.get("summary")]
        reply = "Here's what I found:\n" + "\n".join(f"- {s}" for s in summaries) if summaries else "I can help plan your trip. Tell me your destination and dates."

        return {"reply": reply, "results": results, "actions": actions}


coordinator = Coordinator()


# --- Endpoints ---

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    context = dict(req.context)
    if req.trip_id and req.trip_id in trips:
        trip = trips[req.trip_id]
        context.setdefault("destination", trip.destination)
        context.setdefault("start_date", trip.start_date)
        context.setdefault("end_date", trip.end_date)

    result = coordinator.run(req.message, context)
    return ChatResponse(
        reply=result["reply"],
        trip_id=req.trip_id,
        actions_taken=result["actions"],
        data=result["results"],
    )


@app.post("/trips/plan")
async def create_trip_plan(req: PlanRequest):
    trip = TripPlan(
        destination=req.destination,
        start_date=req.start_date,
        end_date=req.end_date,
        total_budget=req.budget,
    )

    context = {
        "destination": req.destination,
        "start_date": req.start_date or "",
        "end_date": req.end_date or "",
        "interests": req.interests,
        "origin": "NYC",
    }

    flight_result = AGENTS["flight_search"].run("", context)
    for f_data in flight_result.get("flights", []):
        trip.flights.append(FlightOption(**f_data))

    hotel_result = AGENTS["hotel_search"].run("", context)
    for h_data in hotel_result.get("hotels", []):
        trip.hotels.append(HotelOption(**h_data))

    activity_result = AGENTS["activity_planner"].run("", context)
    for a_data in activity_result.get("activities", []):
        trip.activities.append(Activity(**a_data))

    trip.status = "planned"
    trips[trip.id] = trip
    return trip.model_dump(mode="json")


@app.get("/trips/{trip_id}")
async def get_trip(trip_id: str):
    trip = trips.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip.model_dump(mode="json")


@app.get("/health")
async def health():
    return {"status": "healthy", "active_trips": len(trips)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
