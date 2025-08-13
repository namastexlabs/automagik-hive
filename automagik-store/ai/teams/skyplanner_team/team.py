"""SkyPlanner Team - Travel planning coordination team."""

import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from agno.team import Team
from agno.models import ModelConfig
from agno.storage import PostgresStorage
from agno.tools.reasoning import ReasoningTools


# Response models for structured output
class AirbnbListing(BaseModel):
    """Airbnb accommodation listing."""
    name: str
    description: str
    address: Optional[str] = None
    price: Optional[str] = None
    dates_available: Optional[List[str]] = None
    url: Optional[str] = None


class Attraction(BaseModel):
    """Tourist attraction or point of interest."""
    name: str
    description: str
    location: str
    rating: Optional[float] = None
    visit_duration: Optional[str] = None
    best_time_to_visit: Optional[str] = None


class WeatherInfo(BaseModel):
    """Weather forecast information."""
    average_temperature: str
    precipitation: str
    recommendations: str
    forecast_details: Optional[Dict[str, Any]] = None


class TravelPlan(BaseModel):
    """Complete travel plan structure."""
    airbnb_listings: List[AirbnbListing]
    attractions: List[Attraction]
    weather_info: Optional[WeatherInfo] = None
    suggested_itinerary: Optional[List[str]] = None
    local_tips: Optional[List[str]] = None
    budget_estimate: Optional[Dict[str, str]] = None


def get_skyplanner_team(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    **kwargs
) -> Team:
    """
    Factory function to create the SkyPlanner travel coordination team.
    
    Args:
        model_id: Optional model override
        user_id: User identifier for personalization
        session_id: Session identifier for context
        debug_mode: Enable debug logging
        **kwargs: Additional team parameters
    
    Returns:
        Configured SkyPlanner team instance
    """
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Extract configurations
    team_config = config["team"]
    model_config = config["model"]
    storage_config = config["storage"]
    memory_config = config["memory"]
    display_config = config["display"]
    
    # Override model if specified
    if model_id:
        model_config["id"] = model_id
    
    # Load member agents dynamically
    # In production, this would use the agent registry
    members = []
    for member_id in config["members"]:
        # Import and instantiate each agent
        if member_id == "airbnb-agent":
            from ..agents.airbnb_agent.agent import get_airbnb_agent
            members.append(get_airbnb_agent(user_id=user_id, session_id=session_id))
        elif member_id == "maps-agent":
            from ..agents.maps_agent.agent import get_maps_agent
            members.append(get_maps_agent(user_id=user_id, session_id=session_id))
        elif member_id == "web-search-agent":
            from ..agents.web_search_agent.agent import get_web_search_agent
            members.append(get_web_search_agent(user_id=user_id, session_id=session_id))
        elif member_id == "weather-agent":
            from ..agents.weather_agent.agent import get_weather_agent
            members.append(get_weather_agent(user_id=user_id, session_id=session_id))
    
    # Create team tools
    tools = []
    for tool_config in config.get("tools", []):
        if tool_config["name"] == "ReasoningTools":
            tools.append(ReasoningTools(
                add_instructions=tool_config.get("add_instructions", True)
            ))
    
    # Create team instance
    return Team(
        name=team_config["name"],
        team_id=team_config["team_id"],
        mode=team_config["mode"],
        members=members,
        instructions=config["instructions"],
        model=ModelConfig(
            provider=model_config["provider"],
            id=model_config["id"],
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens", 8000)
        ),
        storage=PostgresStorage(
            table_name=storage_config["table_name"],
            auto_upgrade_schema=storage_config.get("auto_upgrade_schema", True)
        ),
        memory=memory_config,
        tools=tools,
        response_model=TravelPlan,  # Structured output
        user_id=user_id,
        session_id=session_id,
        debug_mode=debug_mode,
        markdown=display_config.get("markdown", True),
        show_tool_calls=display_config.get("show_tool_calls", True),
        show_members_responses=display_config.get("show_members_responses", True),
        add_datetime_to_instructions=display_config.get("add_datetime_to_instructions", True),
        stream=config.get("streaming", {}).get("stream", True),
        stream_member_events=config.get("streaming", {}).get("stream_member_events", True),
        stream_intermediate_steps=config.get("streaming", {}).get("stream_intermediate_steps", True),
        **kwargs
    )