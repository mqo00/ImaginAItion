from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi_socketio import SocketManager
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from pydantic import BaseModel
from fastapi.websockets import WebSocket
from typing import Dict, List
import json
import random
import asyncio
import os
from openai import OpenAI, BadRequestError
from dotenv import load_dotenv
import tiktoken
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRouter
import requests
from fastapi.responses import FileResponse
import re
from datetime import datetime, timedelta
import pytz
import zipfile
from concurrent.futures import ThreadPoolExecutor
import base64
import uuid
import time
from logger import game_logger, generate_human_readable_filename, handle_filename_collision
import secrets
import hashlib

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

app = FastAPI()

# Custom CORS middleware that won't interfere with Socket.IO
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Skip CORS for Socket.IO endpoints (they handle their own CORS)
        if request.url.path.startswith("/socket.io/"):
            return await call_next(request)

        # Handle CORS preflight requests
        if request.method == "OPTIONS":
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "*",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Credentials": "true",
                }
            )

        # Process request
        response = await call_next(request)

        # Add CORS headers to response
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"

        return response

# Add custom CORS middleware
app.add_middleware(CustomCORSMiddleware)

# Configure SocketManager with CORS - this will handle Socket.IO CORS only
sio = SocketManager(
    app=app,
    mount_location="/socket.io/",
    cors_allowed_origins="*"  # Allow all origins for Socket.IO
)

# mount static file serving for reference images
app.mount("/static", StaticFiles(directory="static"), name="static")

# mount static file serving for generated images
# Ensure the (gitignored) output directory exists before mounting it.
os.makedirs("generated_images", exist_ok=True)
app.mount("/generated_images", StaticFiles(directory="generated_images"), name="generated_images")

# OpenAI - client will be created per room with user-provided API key
load_dotenv()

# Get backend URL from environment variable, fallback to localhost for development
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5001")


def resolve_room_api_key(room):
    """Return the OpenAI API key for a room.
    Always prefers the room-specific key the player supplied. 
    """
    api_key = getattr(room, 'api_key', None)
    if api_key:
        return api_key
    return None

# image database
REFERENCE_IMAGES = [
    {
        "id": 1,
        "image_path": "/static/reference_images/ref_01.png",
        "description": "A happily married couple",
        "categories": ["cultural", "demographic"]
    },
    {
        "id": 2,
        "image_path": "/static/reference_images/ref_02.png",
        "description": "An exotic building",
        "categories": ["demographic"]
    },
    {
        "id": 3,
        "image_path": "/static/reference_images/ref_03.png",
        "description": "A kid wearing traditional clothing",
        "categories": ["cultural", "demographic"]
    },
    {
        "id": 4,
        "image_path": "/static/reference_images/ref_04.png",
        "description": "Happy family celebrating holiday in December",
        "categories": ["demographic"]
    },
    {
        "id": 5,
        "image_path": "/static/reference_images/ref_05.png",
        "description": "A nurse checking patient charts in a hospital",
        "categories": ["biological"]
    },
    {
        "id": 6,
        "image_path": "/static/reference_images/ref_06.png",
        "description": "CEO",
        "categories": ["biological", "demographic"]
    },
    {
        "id": 7,
        "image_path": "/static/reference_images/ref_07.png",
        "description": "Holding baby",
        "categories": ["biological"]
    },
    {
        "id": 8,
        "image_path": "/static/reference_images/ref_08.png",
        "description": "A blind athlete crossing finish line in race",
        "categories": ["biological"]
    },
    {
        "id": 9,
        "image_path": "/static/reference_images/ref_09.png",
        "description": "An orchard where everything except the apple is red",
        "categories": ["co-occurrence"]
    },
    {
        "id": 10,
        "image_path": "/static/reference_images/ref_10.png",
        "description": "A pretty cow in Pictionary style",
        "categories": ["realism"]
    },
    {
        "id": 11,
        "image_path": "/static/reference_images/ref_11.png",
        "description": "A birthday party with no cake or balloons or hats",
        "categories": ["co-occurrence"]
    },
    {
        "id": 12,
        "image_path": "/static/reference_images/ref_12.png",
        "description": "Friendship as a simple drawing",
        "categories": ["realism"]
    },
    {
        "id": 13,
        "image_path": "/static/reference_images/ref_13.png",
        "description": "A happy castle of cats",
        "categories": ["co-occurrence"]
    },
    {
        "id": 14,
        "image_path": "/static/reference_images/ref_14.png",
        "description": "A sad cow",
        "categories": ["realism"]
    },
    {
        "id": 15,
        "image_path": "/static/reference_images/ref_15.png",
        "description": "A man",
        "categories": ["demographic", "cultural", "biological"]
    },
    {
        "id": 16,
        "image_path": "/static/reference_images/ref_16.png",
        "description": "An Asian woman",
        "categories": ["demographic", "biological", "cultural"]
    },
    {
        "id": 17,
        "image_path": "/static/reference_images/ref_17.png",
        "description": "A criminal",
        "categories": ["biological", "cultural"]
    },
    {
        "id": 18,
        "image_path": "/static/reference_images/ref_18.png",
        "description": "Person fixing a car engine",
        "categories": ["biological"]
    },
    {
        "id": 19,
        "image_path": "/static/reference_images/ref_19.png",
        "description": "Startup founder giving a TED talk",
        "categories": ["biological", "demographic"]
    },
    {
        "id": 20,
        "image_path": "/static/reference_images/ref_20.png",
        "description": "Meet Dr. Li, a rocket scientist from New York",
        "categories": ["cultural", "biological"]
    },
    {
        "id": 21,
        "image_path": "/static/reference_images/ref_21.JPG",
        "description": "There are three blocks. A little farther away, there are four yellow blocks.",
        "categories": ["number & spatial"]
    },
    {
        "id": 22,
        "image_path": "/static/reference_images/ref_22.JPG",
        "description": "There are three colorful flowers. A short distance away, there are eight little butterflies.",
        "categories": ["number & spatial"]
    },
    {
        "id": 23,
        "image_path": "/static/reference_images/ref_23.JPG",
        "description": "There are 3 cars. A little farther away, there are 11 cars.",
        "categories": ["number & spatial"]
    },
    {
        "id": 24,
        "image_path": "/static/reference_images/ref_24.JPG",
        "description": "There are 3 flowers in one spot. A little ways off, there are 17 more flowers.",
        "categories": ["number & spatial"]
    },
    {
        "id": 25,
        "image_path": "/static/reference_images/ref_25.JPG",
        "description": "There are 4 stars. A little farther away, there are 14 stars.",
        "categories": ["number & spatial"]
    },
    {
        "id": 26,
        "image_path": "/static/reference_images/ref_26.png",
        "description": "A horse riding an astronaut",
        "categories": ["co-occurrence"]
    },
    {
        "id": 27,
        "image_path": "/static/reference_images/ref_27.png",
        "description": "Serious people taking notes",
        "categories": ["biological", "demographic"]
    },
    {
        "id": 28,
        "image_path": "/static/reference_images/ref_28.png",
        "description": "A soft robot that can swim like a shark",
        "categories": ["realism"]
    },
]

# build the image pool dynamically by category
def build_image_pool_by_category():
    pool = {}
    categories = ["cultural", "demographic", "biological", "co-occurrence", "realism", "number & spatial"]
    
    for category in categories:
        pool[category] = [img for img in REFERENCE_IMAGES if category in img["categories"]]
    
    return pool

REFERENCE_IMAGE_POOL_BY_CATEGORY = build_image_pool_by_category()

# unified image pool kept for backward compatibility
REFERENCE_IMAGE_POOL = []
for category, images in REFERENCE_IMAGE_POOL_BY_CATEGORY.items():
    REFERENCE_IMAGE_POOL.extend(images)



# API Router for API routes
router = APIRouter()

# Admin authentication.
# Credentials are read from environment variables. Set ADMIN_USERNAME and
# ADMIN_PASSWORD before deploying; the development fallbacks below MUST NOT be
# used in any public/production deployment.
ADMIN_CREDENTIALS = {
    "username": os.getenv("ADMIN_USERNAME", "admin"),
    "password": os.getenv("ADMIN_PASSWORD", "admin"),
}

# Session storage (in production, use Redis or database)
admin_sessions = {}

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminSession:
    def __init__(self, token: str, username: str):
        self.token = token
        self.username = username
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=24)
    
    def is_valid(self):
        return datetime.now() < self.expires_at

def verify_admin_token(token: str = Query(None)):
    """Verify admin authentication token"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    session = admin_sessions.get(token)
    if not session or not session.is_valid():
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return session


class Room:
    def __init__(self, room_id: str, tutorial: bool, categories: List[str] = None):
        self.room_id = room_id
        # Stores player WebSocket connections
        self.max_players = 3
        self.players: Dict[str, str] = {}
        self.sid_to_players: Dict[str, str] = {}  # {sid: player_id}
        self.tutorial = tutorial
        self.categories = categories or ["cultural", "demographic", "biological", "co-occurrence", "realism", "number & spatial"]
        self.num_rounds = len(self.categories)  # Auto-calculate rounds based on categories
        self.game_state = {
            "current_round": 0,  # Tracks the current round (1 to num_rounds)
            "current_turn": 0,  # Tracks the current turn (0-2 per round: Generate→Guessing→Result)
            "using_adjectives": {},
            "started_at": None,  # Store the start time of the game
            "ended_at": None,  # Store the end time of the game
            "rounds": self._create_rounds_structure(self.num_rounds, tutorial),
            "category_sequence": [],  # Store randomized category sequence for the game
            "used_image_ids": set(),  # Track used image IDs to prevent duplicates
            "final_result": None,  # Final game result
        }
        self.player_state = {}
        self.quick_draw_results = {}  # Store quick draw results for each player {player_id: [results]}
    
    def _create_rounds_structure(self, num_rounds: int, tutorial: bool):
        """Create dynamic rounds structure based on configuration"""
        rounds = {}
        
        # Tutorial round (round 0)
        if tutorial:
            rounds[0] = {
                "started_at": None,
                "ended_at": None,
                "turns": {
                    0: {"time_limit": -1, "status": "waiting", "data": {}},  # Generate
                    1: {"time_limit": -1, "status": "waiting", "data": {}},  # Guessing
                    2: {"time_limit": -1}  # Result
                },
                "nouns": [],
                "adjectives": {},  # Store adjectives for each player
                "used_adjectives_id": {},
                "result": None,  # Store final round result
            }
        
        # Main game rounds (1 to num_rounds)
        for i in range(1, num_rounds + 1):
            rounds[i] = {
                "started_at": None,
                "ended_at": None,
                "turns": {
                    0: {"time_limit": 70, "status": "waiting", "data": {}},  # Generate
                    1: {"time_limit": 20, "status": "waiting", "data": {}},  # Voting
                    2: {"time_limit": -1, "status": "waiting", "data": {}},  # Reveal Prompt
                    3: {"time_limit": -1}  # Result
                },
                "nouns": [],
                "adjectives": {},  # Store adjectives for each player
                "used_adjectives_id": {},
                "result": None,  # Store final round result
            }
        
        return rounds

    def add_player(self, sid: str, player_id: str):
        try:
            print(f"🔧 add_player called: sid={sid[:8]}..., player_id={player_id}, current players={len(self.players)}")
            if len(self.players) < self.max_players:
                self.players[player_id] = sid
                print(f"🔧 Initializing player_state for {sid[:8]}...")
                self.player_state[sid] = {
                    "current_turn": 0,
                    "current_round": 0,
                    "round": {
                        0: {"total": 0,
                            "choose": 0,
                            "prompt": 0,
                            "guess": 0,
                            },
                        1: {"total": 0,
                            "choose": 0,
                            "prompt": 0,
                            "guess": 0,
                            },
                        2: {"total": 0,
                            "choose": 0,
                            "prompt": 0,
                            "guess": 0,
                            },
                        3: {"total": 0,
                            "choose": 0,
                            "prompt": 0,
                            "guess": 0,
                            },
                        4: {"total": 0,
                            "choose": 0,
                            "prompt": 0,
                            "guess": 0,
                            },
                        5: {"total": 0,
                            "choose": 0,
                            "prompt": 0,
                            "guess": 0,
                            },
                        6: {"total": 0,
                            "choose": 0,
                            "prompt": 0,
                            "guess": 0,
                            },
                    },
                    "score": 0,
                    "tutorial_score": 0,
                }
                self.sid_to_players[sid] = player_id
                print(f"✅ Player {player_id} added successfully. player_state keys: {list(self.player_state.keys())}")
                return True
            else:
                print(f"⚠️ Cannot add player {player_id}: room full ({len(self.players)}/{self.max_players})")
            return False
        except Exception as e:
            print(f"❌ Error adding player: {e}")
            import traceback
            traceback.print_exc()
            return

    def get_players(self):
        return list(self.players.keys())

    def is_game_over(self):
        # decide the game-end condition based on the configured number of rounds
        # tutorial mode: tutorial round + configured rounds (round 0, 1, 2, ..., num_rounds)
        # normal mode: configured rounds (round 1, 2, ..., num_rounds)
        if self.tutorial:
            return self.game_state["current_round"] > self.num_rounds
        else:
            return self.game_state["current_round"] > self.num_rounds


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}  # {room_id: Room}
        self.sid_to_room: Dict[str, str] = {}  # {sid: room_id}

    # check if start with tutorial
    def create_room(self, sid: str, room_id: str, tutorial: bool, categories: List[str] = None) -> str:
        self.rooms[room_id] = Room(room_id, tutorial, categories)
        return room_id

    def get_room(self, room_id: str) -> Room:
        return self.rooms.get(room_id)


class RoomRequestCreate(BaseModel):
    sid: str
    room_id: str
    player_name: str
    tutorial: bool
    categories: List[str] = None
    api_key: str = None


class RoomRequest(BaseModel):
    sid: str
    room_id: str
    player_name: str


class PlayerRequest(BaseModel):
    sid: str


class ChoosingRequest(BaseModel):
    sid: str
    sentence: List
    random: bool


class VoteRequest(BaseModel):
    room_id: str
    voter_sid: str
    voted_for_sid: str
    image_url: str


room_manager = RoomManager()


sid_to_room = {}

# Session management for player reconnection
# Maps session_token -> {"room_id": str, "player_name": str, "current_sid": str}
player_sessions = {}
# Maps room_id -> {player_name -> session_token} for quick lookup
room_player_sessions = {}

def generate_session_token():
    """Generate a unique session token for player identification"""
    return secrets.token_urlsafe(32)

def create_player_session(room_id: str, player_name: str, sid: str):
    """Create a new session for a player"""
    session_token = generate_session_token()
    player_sessions[session_token] = {
        "room_id": room_id,
        "player_name": player_name,
        "current_sid": sid
    }

    # Track session by room and player name
    if room_id not in room_player_sessions:
        room_player_sessions[room_id] = {}
    room_player_sessions[room_id][player_name] = session_token

    print(f"🔑 Created session {session_token[:8]}... for {player_name} in room {room_id}")
    return session_token

def update_session_sid(session_token: str, new_sid: str):
    """Update the SID for an existing session (for reconnection)"""
    if session_token in player_sessions:
        old_sid = player_sessions[session_token]["current_sid"]
        player_sessions[session_token]["current_sid"] = new_sid
        print(f"🔄 Updated session {session_token[:8]}... SID: {old_sid[:8]}... -> {new_sid[:8]}...")
        return True
    return False

def get_session_info(session_token: str):
    """Get session information by token"""
    return player_sessions.get(session_token)

def reconnect_player(session_token: str, new_sid: str):
    """Reconnect a player with existing session to update their SID"""
    session_info = get_session_info(session_token)
    if not session_info:
        return None

    room_id = session_info["room_id"]
    player_name = session_info["player_name"]
    old_sid = session_info["current_sid"]

    room = room_manager.get_room(room_id)
    if not room:
        return None

    # If SID hasn't changed, no need to update mappings
    if old_sid == new_sid:
        print(f"✅ Reconnected {player_name} in room {room_id}: SID unchanged ({new_sid[:8]}...)")
        return {
            "room_id": room_id,
            "player_name": player_name,
            "old_sid": old_sid,
            "new_sid": new_sid
        }

    # Update all mappings from old_sid to new_sid
    # 1. Update room.players mapping
    if player_name in room.players and room.players[player_name] == old_sid:
        room.players[player_name] = new_sid

    # 2. Update room.sid_to_players mapping
    if old_sid in room.sid_to_players:
        room.sid_to_players[new_sid] = room.sid_to_players[old_sid]
        del room.sid_to_players[old_sid]

    # 3. Update room.player_state mapping
    if old_sid in room.player_state:
        room.player_state[new_sid] = room.player_state[old_sid]
        del room.player_state[old_sid]

    # 4. Update sid_to_room mapping
    if old_sid in sid_to_room:
        del sid_to_room[old_sid]
    sid_to_room[new_sid] = room_id

    # 5. Update game_state data structures that use sid as keys
    for round_num in room.game_state["rounds"]:
        round_data = room.game_state["rounds"][round_num]

        # Update adjectives mapping
        if "adjectives" in round_data and old_sid in round_data["adjectives"]:
            round_data["adjectives"][new_sid] = round_data["adjectives"][old_sid]
            del round_data["adjectives"][old_sid]

        # Update turns data
        if "turns" in round_data:
            for turn_num in round_data["turns"]:
                turn_data = round_data["turns"][turn_num]
                if "data" in turn_data and old_sid in turn_data["data"]:
                    turn_data["data"][new_sid] = turn_data["data"][old_sid]
                    del turn_data["data"][old_sid]

                # Update vote_counts if this is a voting turn
                if "data" in turn_data and "vote_counts" in turn_data["data"]:
                    vote_counts = turn_data["data"]["vote_counts"]

                    # Update vote_counts keys (voted_for_sid)
                    if old_sid in vote_counts:
                        vote_counts[new_sid] = vote_counts[old_sid]
                        del vote_counts[old_sid]

                    # Update voter_sid inside each vote object
                    for voted_for_sid, votes_list in vote_counts.items():
                        for vote in votes_list:
                            if vote.get("voter_sid") == old_sid:
                                vote["voter_sid"] = new_sid

    # 6. Update session token mapping
    update_session_sid(session_token, new_sid)

    print(f"✅ Reconnected {player_name} in room {room_id}: {old_sid[:8]}... -> {new_sid[:8]}...")
    return {
        "room_id": room_id,
        "player_name": player_name,
        "old_sid": old_sid,
        "new_sid": new_sid
    }


def generate_category_sequence_for_room(room):
    """Generate category sequence ensuring each selected category appears exactly once"""
    # Since num_rounds = len(categories), we can ensure each category appears exactly once
    sequence = room.categories[:]  # Copy the list
    random.shuffle(sequence)  # Randomize the order
    return sequence

def set_nouns(room_id: str):
    room = room_manager.get_room(room_id)
    
    # Generate randomized category sequence for the game using configured categories
    if not room.game_state["category_sequence"]:
        room.game_state["category_sequence"] = generate_category_sequence_for_room(room)
    
    # Set reference images based on category sequence, preventing duplicates
    for i in range(1, room.num_rounds + 1):  # Use configured number of rounds
        category = room.game_state["category_sequence"][i-1]
        category_images = REFERENCE_IMAGE_POOL_BY_CATEGORY[category]
        
        # Filter out already used images
        available_images = [img for img in category_images if img["id"] not in room.game_state["used_image_ids"]]
        
        # If no available images in this category, reset the used_image_ids and use all category images
        if not available_images:
            available_images = category_images
            # Log warning but continue (this shouldn't happen with proper category distribution)
            print(f"Warning: All images in category '{category}' have been used. Resetting for round {i}")
        
        selected_image = random.choice(available_images)
        room.game_state["used_image_ids"].add(selected_image["id"])
        
        room.game_state["rounds"][i]["reference_image"] = selected_image
        room.game_state["rounds"][i]["category"] = category
        # Keep nouns empty for now - will be replaced by reference image descriptions
        room.game_state["rounds"][i]["nouns"] = []
    
    # Tutorial round (round 0) - use first category as example
    if room.tutorial:
        tutorial_category = room.game_state["category_sequence"][0]
        tutorial_images = REFERENCE_IMAGE_POOL_BY_CATEGORY[tutorial_category]
        
        # Filter out already used images for tutorial
        available_tutorial_images = [img for img in tutorial_images if img["id"] not in room.game_state["used_image_ids"]]
        
        if not available_tutorial_images:
            available_tutorial_images = tutorial_images
        
        tutorial_image = random.choice(available_tutorial_images)
        room.game_state["used_image_ids"].add(tutorial_image["id"])
        room.game_state["rounds"][0]["reference_image"] = tutorial_image
        room.game_state["rounds"][0]["category"] = tutorial_category
        room.game_state["rounds"][0]["nouns"] = []


def set_adjectives(room_id: str, sid: str):
    # Use simple adjectives from words.json for now
    with open("words.json") as f:
        data = json.load(f)
    room = room_manager.get_room(room_id)
    
    # Determine rounds to process - use configured number of rounds
    if room.tutorial:
        rounds_to_process = range(room.num_rounds + 1)  # 0 to num_rounds (includes tutorial)
    else:
        rounds_to_process = range(1, room.num_rounds + 1)  # 1 to num_rounds
    
    for i in rounds_to_process:
        # Randomly select 6 adjectives for each player in each round
        room.game_state["rounds"][i]["adjectives"][sid] = random.sample(data["adjectives"], min(6, len(data["adjectives"])))
        # Store adjective IDs for tracking
        room.game_state["rounds"][i]["used_adjectives_id"][sid] = [
            data["adjectives"].index(adj) for adj in room.game_state["rounds"][i]["adjectives"][sid]
        ]
    print(room.game_state)


def replace_sids_with_names(game_state, sid_to_players):
    """
    Replace keys of the dictionary with player names instead of sids.
    """
    if isinstance(game_state, dict):
        new_state = {}

        for key, value in game_state.items():
            # If the key itself is a sid, replace it with the player name
            new_key = sid_to_players.get(key, key)

            # Recursively process values
            new_state[new_key] = replace_sids_with_names(value, sid_to_players)

        return new_state

    elif isinstance(game_state, list):
        return [replace_sids_with_names(item, sid_to_players) for item in game_state]

    else:
        return game_state  # Return unchanged if not a dict or list


def replace_sid_values(game_state, sid_to_players):
    """
    Replace all values in the game state that are sids with player names.
    """

    if isinstance(game_state, dict):
        return {key: replace_sid_values(value, sid_to_players) for key, value in game_state.items()}

    elif isinstance(game_state, list):
        return [replace_sid_values(item, sid_to_players) for item in game_state]

    elif isinstance(game_state, str):  # Check if value is a string and replace if needed
        return sid_to_players.get(game_state, game_state)

    else:
        return game_state  # Return unchanged if not dict, list, or string


def get_timestamp():
    return datetime.now(pytz.timezone("America/New_York")).isoformat()


def check_all_players_voted(room, current_round, current_turn):
    """Check whether all players have voted"""
    if current_turn != 1:  # only check during the voting phase
        return True
    
    turns_data = room.game_state["rounds"][current_round]["turns"][current_turn]["data"]
    total_players = len(room.players)
    
    # count players who have voted - using the actual SID rather than player_id
    voted_players = 0
    for player_sid in room.players.values():  # use .values() to get the actual SID
        if player_sid in turns_data and "vote" in turns_data[player_sid]:
            voted_players += 1
    
    print(f"🗳️ Vote check: {voted_players}/{total_players} players have voted")
    print(f"🔍 Player SIDs: {list(room.players.values())}")
    print(f"🔍 Voted SIDs: {[sid for sid in room.players.values() if sid in turns_data and 'vote' in turns_data[sid]]}")
    return voted_players >= total_players


@router.get("/api/logs")
async def get_logs(room_id: str = Query(None)):
    if room_id is None:
        # Return logs for all rooms
        logs = {}
        for room_id in room_manager.rooms:
            log = await process_logs(room_id)
            logs[room_id] = log
        return logs
    log = await process_logs(room_id)
    return log


async def post_process_player_state(player_state: Dict[str, Any], players):
    result = {}
    for player in players:
        result[player] = {}
        result[player]["round"] = player_state[player]["round"]
        result[player]["total_score"] = player_state[player]["score"]

    return result


async def process_logs(room_id: str):
    room = room_manager.get_room(room_id)
    if room.game_state["final_result"] == False:
        return
    sid_to_players = room.sid_to_players
    players = list(sid_to_players.values())

    replaced_game_state = replace_sids_with_names(
        room.game_state, sid_to_players)
    replaced_game_state = replace_sid_values(
        replaced_game_state, sid_to_players)
    replaced_player_state = replace_sids_with_names(
        room.player_state, sid_to_players
    )
    replaced_player_state = replace_sid_values(
        replaced_player_state, sid_to_players)
    final_player_state = await post_process_player_state(replaced_player_state, players)

    log = {}
    log["room_id"] = room_id
    log["players"] = list(room.players.keys())
    log["sid_to_player_name"] = sid_to_players
    # Create dynamic rounds structure for logging
    log["rounds"] = {}
    if room.tutorial:
        log["rounds"]["tutorial"] = {}
    for i in range(1, room.num_rounds + 1):
        log["rounds"][i] = {}
    
    # Process all rounds (tutorial + configured rounds)
    rounds_to_log = range(room.num_rounds + 1) if room.tutorial else range(1, room.num_rounds + 1)
    for i in rounds_to_log:
        log["rounds"][i if i != 0 else "tutorial"] = {
            "nouns": room.game_state["rounds"][i]["nouns"],
            "adjectives_assinged": replaced_game_state["rounds"][i]["adjectives"],
            "adjectives_used": replaced_game_state["rounds"][i]["used_adjectives_id"],
            "turns": {
                "choosing": replaced_game_state["rounds"][i]["turns"][0]["data"],
                "drawing": replaced_game_state["rounds"][i]["turns"][1]["data"],
                "guessing": replaced_game_state["rounds"][i]["turns"][2]["data"],
            },
            "results": replaced_game_state["rounds"][i]["result"]
        }
    log["final_results"] = final_player_state
    return log


@router.get("/api/has_tutorial")
async def has_tutorial(room_id: str):
    room = room_manager.get_room(room_id)
    return room.tutorial


@router.post("/api/create-room")
async def create_game_room(request: RoomRequestCreate):
    room_manager.create_room(request.sid, request.room_id, request.tutorial, request.categories)
    if not request.tutorial:
        room = room_manager.get_room(request.room_id)
        room.game_state["current_round"] = 1

    # Store API key if provided
    if request.api_key:
        room_manager.rooms[request.room_id].api_key = request.api_key
        room_manager.rooms[request.room_id].host_sid = request.sid
        print(f"🔑 Room {request.room_id} configured with custom API key")

    room_manager.rooms[request.room_id].add_player(
        request.sid, request.player_name)
    sid_to_room[request.sid] = request.room_id
    set_nouns(request.room_id)
    set_adjectives(request.room_id, request.sid)

    # Create session token for reconnection support
    session_token = create_player_session(request.room_id, request.player_name, request.sid)

    print(f"🟢 Room {request.room_id} created by {request.player_name}")
    print(f"room_manager.rooms[request.room_id].players: {room_manager.rooms[request.room_id].players}")
    return {"message": "Room created successfully", "session_token": session_token}


@router.post("/api/join-room")
async def get_room(request: RoomRequest):
    room = room_manager.get_room(request.room_id)
    if room and len(room.players) < room.max_players:
        room.add_player(request.sid, request.player_name)
        sid_to_room[request.sid] = request.room_id
        # join the user to the Socket.IO room immediately so they receive broadcasts
        try:
            await sio.enter_room(request.sid, request.room_id)
        except (ValueError, KeyError) as e:
            # Socket not fully connected yet, that's ok - will join on socket connect event
            print(f"⚠️ Could not join socket room (socket not ready): {e}")

        set_adjectives(request.room_id, request.sid)

        # Create session token for reconnection support
        session_token = create_player_session(request.room_id, request.player_name, request.sid)

        return {"room": room.__dict__, "session_token": session_token}
    return {"message": "Room not found"}


class ReconnectRequest(BaseModel):
    session_token: str
    sid: str


@router.post("/api/reconnect")
async def reconnect(request: ReconnectRequest):
    """Reconnect a player using their session token"""
    result = reconnect_player(request.session_token, request.sid)
    if result:
        # Try to join the socket room (will fail if socket not connected, which is ok for testing)
        try:
            await sio.enter_room(request.sid, result["room_id"])
        except (ValueError, KeyError) as e:
            # Socket not connected yet, that's ok - it will be joined when socket connects
            print(f"⚠️ Could not join socket room (socket not ready): {e}")

        room = room_manager.get_room(result["room_id"])

        # Prepare room data for JSON response (handle non-serializable objects)
        room_data = None
        if room:
            try:
                room_dict = room.__dict__.copy()
                # Convert sets to lists for JSON serialization
                if "game_state" in room_dict and "used_image_ids" in room_dict["game_state"]:
                    room_dict["game_state"]["used_image_ids"] = list(room_dict["game_state"]["used_image_ids"])
                room_data = room_dict
            except Exception as e:
                print(f"⚠️ Could not serialize room data: {e}")
                # Return minimal room data
                room_data = {"room_id": room.room_id, "players": room.players}

        return {
            "success": True,
            "room_id": result["room_id"],
            "player_name": result["player_name"],
            "room": room_data
        }
    return {"success": False, "message": "Invalid session token"}


@router.post("/api/choosing")
async def choosing(request: ChoosingRequest):
    room_id = sid_to_room.get(request.sid)
    room = room_manager.get_room(room_id)
    room.game_state["rounds"][room.game_state["current_round"]
                              ]["turns"][room.game_state["current_turn"]]["data"][request.sid] = {"sentence": request.sentence, "timestamp": get_timestamp(), "random": request.random}
    return {"message": "Sentence received"}


@sio.on("get-players")
async def get_players(sid, data=None):
    # Get room_id from data (preferred) or fallback to sid lookup
    room_id = None
    if data and isinstance(data, dict) and "room_id" in data:
        room_id = data["room_id"]
    else:
        room_id = sid_to_room.get(sid)

    if not room_id:
        await sio.emit("error", {"message": "Player not in any room"}, room=sid)
        return

    room = room_manager.get_room(room_id)
    if not room:
        await sio.emit("error", {"message": "Room not found"}, room=sid)
        return

    # Transport upgrade detection has been removed from this handler
    # All SID migrations should be handled through the /api/reconnect endpoint
    # This prevents race conditions and incorrect player matching
    if sid not in room.player_state:
        print(f"⚠️ SID {sid[:8]}... not found in player_state")
        print(f"🔍 Current player_state keys: {list(room.player_state.keys())}")
        print(f"🔍 Current room.players: {room.players}")
        print(f"⚠️ Player should call /api/reconnect to restore their session")

    players = room.get_players()
    await sio.enter_room(sid, room_id)
    await sio.emit("players", {"players": players}, room=room_id)
    await sio.emit("num_players", {"num_players": len(players)}, room=room_id)

    # Only start game if it hasn't been started yet
    if len(players) == room.max_players and room.game_state.get("started_at") is None:
        room.game_state["started_at"] = get_timestamp()

        # Initialize game logging
        game_logger.start_game_log(room_id, room.sid_to_players)

        # notify all players the game has started
        await sio.emit("game-started", {
            "message": "Game started! All players joined.",
            "started_at": room.game_state["started_at"]
        }, room=room_id)
        # new 3-phase flow: start at round 1, turn 0 (Generate phase)
        await start_turn_timer(room, 1, 0)


@ sio.on("connect")
async def connect(sid, environ):
    print(f"✅ Client {sid} connected")


@ sio.on("message")
async def handle_message(sid, data):
    print(f"🔹 Message from {sid}: {data}")
    await sio.emit("response", {"message": "Hello from server!"}, room=sid)

turn_timers = {}


async def start_turn_timer(room, round_num, turn_num):
    time_limit = room.game_state["rounds"][round_num]["turns"][turn_num]["time_limit"]
    print(f"🕐 Starting timer for room {room.room_id}, round {round_num}, turn {turn_num}, time_limit: {time_limit}s")

    # Cancel any existing timer for this room before starting a new one
    if room.room_id in turn_timers:
        turn_timers[room.room_id].cancel()  # Stop previous task
        try:
            await turn_timers[room.room_id]  # Wait for it to be cancelled
        except asyncio.CancelledError:
            print(f"🔴 Previous timer for room {room.room_id} cancelled and stopped")

    async def timer_task():
        if time_limit == -1:
            return
        for remaining_time in range(time_limit, -1, -1):
            await sio.emit("update_timer", {"time_left": remaining_time}, room=room.room_id)
            if remaining_time > 0:
                await asyncio.sleep(1)  # Wait 1 second
            # If the task is cancelled while sleeping, it will raise asyncio.CancelledError
        
        # When timer reaches 0 in Generate phase, handle special logic
        if turn_num == 0:  # Generate phase
            print(f"⏰ Generate timer finished for room {room.room_id}, handling prompt submissions")
            # notify the frontend the timer has ended and it should start auto-submit
            await sio.emit("generate_timer_ended", {"message": "Timer ended, processing submissions..."}, room=room.room_id)
            # give the frontend a moment to handle auto-submit
            await asyncio.sleep(2)
            await handle_generate_timer_end(room, round_num)
        elif turn_num == 1:  # Voting phase
            print(f"⏰ Voting timer finished for room {room.room_id}, checking if all players voted")
            await handle_voting_timer_end(room, round_num, turn_num)
        else:
            # For other phases, move to next turn immediately
            print(f"⏰ Timer finished for room {room.room_id}, moving to next turn")
            update_game_turn(room)
            await move_to_next_turn(room, triggered_by_timer=True)

    # Start and store the new timer task
    if time_limit != -1:
        turn_timers[room.room_id] = asyncio.create_task(timer_task())
        print(f"✅ Timer task started for room {room.room_id}")
    else:
        print(f"⏸️ No timer needed for room {room.room_id} (time_limit=-1)")

async def handle_generate_timer_end(room, round_num):
    """Handle when Generate phase timer ends - wait for all generations to complete"""
    print(f"🔄 Handling generate timer end for room {room.room_id}, round {round_num}")
    
    # Wait for all image generations to complete
    await wait_for_all_generations(room, round_num)
    
    # Now move to next turn
    update_game_turn(room)
    await move_to_next_turn(room, triggered_by_timer=True)

async def handle_voting_timer_end(room, round_num, turn_num):
    """Handle when Voting phase timer ends - check if all players voted"""
    print(f"🔄 Handling voting timer end for room {room.room_id}, round {round_num}")
    
    if check_all_players_voted(room, round_num, turn_num):
        print("✅ All players have voted, proceeding to next phase")
        update_game_turn(room)
        await move_to_next_turn(room, triggered_by_timer=True)
    else:
        print("⚠️ Not all players have voted, showing reminder and waiting")
        # send a voting reminder to players who have not voted
        await send_vote_reminders(room, round_num, turn_num)

async def send_vote_reminders(room, round_num, turn_num):
    """Send vote reminders to players who haven't voted yet"""
    turns_data = room.game_state["rounds"][round_num]["turns"][turn_num]["data"]
    
    # find players who have not voted yet - using the actual SID
    players_not_voted = []
    for player_sid in room.players.values():  # use .values() to get the actual SID
        if player_sid not in turns_data or "vote" not in turns_data[player_sid]:
            players_not_voted.append(player_sid)
    
    print(f"📢 Sending vote reminders to {len(players_not_voted)} players: {players_not_voted}")
    
    # send a reminder to all players who have not voted
    for player_sid in players_not_voted:
        await sio.emit("show_vote_reminder", {
            "message": "Please vote to continue the game"
        }, room=player_sid)

async def wait_for_all_generations(room, round_num):
    """Wait for all pending image generations to complete"""
    print(f"⏳ Waiting for all image generations to complete in room {room.room_id}")
    
    max_wait_time = 60  # Maximum wait time in seconds
    check_interval = 2  # Check every 2 seconds
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        # Check if all players have either submitted an image or have a placeholder
        all_ready = True
        current_turn = room.game_state["current_turn"]
        turns_data = room.game_state["rounds"][round_num]["turns"][current_turn]["data"]
        
        for player_sid in room.players.values():  # Get all player sids
            if player_sid not in turns_data or "submitted_image" not in turns_data[player_sid]:
                # Player hasn't submitted yet, check if they have a pending generation
                if not has_pending_generation(room.room_id, player_sid):
                    # Check if player has generated images but not submitted
                    if player_sid in turns_data and "all" in turns_data[player_sid] and turns_data[player_sid]["all"]:
                        # Auto-submit the last generated image
                        last_generation = turns_data[player_sid]["all"][-1]
                        if last_generation.get("images"):
                            image_name = last_generation["images"][0]
                            turns_data[player_sid]["submitted_image"] = {
                                "url": f"http://localhost:5001/generated_images/{image_name}",
                                "name": image_name,
                                "random": last_generation.get("random", False),
                                "auto_submitted": True
                            }
                            turns_data[player_sid]["prompt"] = last_generation.get("prompt", "")
                            turns_data[player_sid]["timestamp"] = get_timestamp()
                            print(f"✅ Auto-submitted image for player {player_sid} to round {round_num}, turn {current_turn}")
                        else:
                            # No images generated, create placeholder
                            await create_placeholder_image(room, round_num, player_sid)
                    else:
                        # No pending generation and no generated images, create placeholder
                        await create_placeholder_image(room, round_num, player_sid)
                else:
                    all_ready = False
                    
        if all_ready:
            print(f"✅ All players ready in room {room.room_id}")
            break
            
        await asyncio.sleep(check_interval)
        elapsed_time += check_interval
        
        # Emit progress update
        await sio.emit("generation_progress", {
            "message": f"Waiting for image generation... ({elapsed_time}/{max_wait_time}s)"
        }, room=room.room_id)
    
    # If we've exceeded max wait time, create placeholders for any remaining players
    if elapsed_time >= max_wait_time:
        print(f"⚠️ Max wait time exceeded for room {room.room_id}, creating placeholders")
        current_turn = room.game_state["current_turn"]
        turns_data = room.game_state["rounds"][round_num]["turns"][current_turn]["data"]
        
        for player_sid in room.players.values():
            if player_sid not in turns_data or "submitted_image" not in turns_data[player_sid]:
                await create_placeholder_image(room, round_num, player_sid)

def has_pending_generation(room_id, player_sid):
    """Check if a player has a pending image generation"""
    room_id_str = str(room_id)
    if room_id_str in generated_images and player_sid in generated_images[room_id_str]:
        images = generated_images[room_id_str][player_sid]
        # Empty array means generation in progress, non-empty means completed or failed
        return len(images) == 0
    return False

async def create_placeholder_image(room, round_num, player_sid):
    """Create a placeholder image for players who didn't submit or failed generation"""
    print(f"🖼️ Creating placeholder image for player {player_sid} in room {room.room_id}")
    
    current_turn = room.game_state["current_turn"]
    turns_data = room.game_state["rounds"][round_num]["turns"][current_turn]["data"]
    
    # Initialize player data if it doesn't exist
    if player_sid not in turns_data:
        turns_data[player_sid] = {}
    
    # Create placeholder image data
    placeholder_url = "/static/placeholder_no_prompt.png"  # We'll create this image
    turns_data[player_sid]["submitted_image"] = {
        "url": placeholder_url,
        "name": "placeholder_no_prompt.png",
        "random": True,
        "is_placeholder": True
    }
    turns_data[player_sid]["prompt"] = "No prompt submitted"
    turns_data[player_sid]["timestamp"] = get_timestamp()
    
    # Also update the generated_images structure
    room_id_str = str(room.room_id)
    if room_id_str not in generated_images:
        generated_images[room_id_str] = {}
    generated_images[room_id_str][player_sid] = [placeholder_url]

# for first turn of the game that does not have tutorial


@sio.on("start-turn-timer")
async def start_turn_timer_temp(sid):
    room_id = sid_to_room.get(sid)
    if not room_id:
        return
    
    room = room_manager.get_room(room_id)
    if not room:
        return
    
    if len(room.players) < room.max_players:
        return
    
    # start the timer for the current round/turn instead of always 1,0
    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]
    print(f"🔄 Manual timer start requested for room {room.room_id}, round {current_round}, turn {current_turn}")
    
    await start_turn_timer(room, current_round, current_turn)

@sio.on("auto-submit-prompt")
async def auto_submit_prompt(sid, data):
    """Handle auto-submission when timer ends with content in input"""
    print(f"🔄 Auto-submitting prompt for player {sid}: {data.get('prompt', '')}")
    
    room_id = data.get("room_id")
    prompt = data.get("prompt", "").strip()
    
    if not room_id or not prompt:
        await sio.emit("auto_submit_failed", {"error": "Missing room_id or prompt"}, room=sid)
        return
    
    # Check if player has already submitted an image for this turn
    room = room_manager.get_room(room_id)
    if not room:
        await sio.emit("auto_submit_failed", {"error": "Room not found"}, room=sid)
        return
    
    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]
    
    # Check if player already has a submitted image for this turn
    turns_data = room.game_state["rounds"][current_round]["turns"][current_turn].get("data", {})
    if sid in turns_data and "submitted_image" in turns_data[sid]:
        print(f"⚠️ Player {sid} already submitted an image, ignoring auto-submit")
        await sio.emit("auto_submit_failed", {"error": "Image already submitted"}, room=sid)
        return
    
    # Check if player already has image generation in progress
    room_id_str = str(room_id)
    if (room_id_str in generated_images and 
        sid in generated_images[room_id_str] and 
        len(generated_images[room_id_str][sid]) == 0):  # Empty array = generation in progress
        print(f"⚠️ Player {sid} has image generation in progress, ignoring auto-submit")
        await sio.emit("auto_submit_failed", {"error": "Image generation already in progress"}, room=sid)
        return
    
    try:
        # Start image generation
        image_url = await generate_image_for_player(room_id, sid, prompt, auto_submitted=True)
        await sio.emit("auto_submit_success", {
            "message": "Prompt auto-submitted successfully",
            "image_url": image_url,
            "prompt": prompt
        }, room=sid)
    except Exception as e:
        print(f"Error in auto-submit: {e}")
        # Create placeholder for failed auto-submission
        room = room_manager.get_room(room_id)
        if room:
            await create_placeholder_image(room, current_round, sid)

        # Check if it's an API key error
        error_message = str(e)
        if "401" in error_message or "AuthenticationError" in str(type(e)) or "invalid_api_key" in error_message:
            await sio.emit("auto_submit_failed", {"error": "Invalid OpenAI API key. Please check your API key."}, room=sid)
        else:
            await sio.emit("auto_submit_failed", {"error": str(e)}, room=sid)


def update_game_turn(room, player_turns=None):
    """
    Update the game turn and round.
    Args:
        room: The game room object.
        player_turns: List of player turns. If provided, update based on player state; otherwise, increment game state.
    """
    if player_turns:
        # Update based on player state (from player_done)
        # When all players complete a turn, we should advance to the NEXT turn
        current_game_turn = room.game_state["current_turn"]
        next_turn = current_game_turn + 1  # Always advance to next turn when all players are done
        print(f"🔄 Player-driven update: current_game_turn={current_game_turn}, advancing to next_turn={next_turn}")
        print(f"🔍 Player turns were: {player_turns}")
    else:
        # Increment game state (from timer)
        current_game_turn = room.game_state["current_turn"]
        next_turn = current_game_turn + 1
        print(f"🔄 Timer-driven update: current_game_turn={current_game_turn}, next_turn={next_turn}")

    # Check if need to advance to next round (4 turns per round)
    if next_turn % 4 == 0 and next_turn != 0:
        # Move to next round
        room.game_state["rounds"][room.game_state["current_round"]]["ended_at"] = get_timestamp()
        room.game_state["rounds"][room.game_state["current_round"]]["turns"][current_game_turn]["ended_at"] = get_timestamp()
        room.game_state["current_round"] += 1

        if room.game_state["current_round"] > room.num_rounds:
            room.game_state["ended_at"] = get_timestamp()
            if room.tutorial and 0 in room.game_state["rounds"]:
                room.game_state["rounds"][0]["started_at"] = room.game_state["started_at"]

        room.game_state["current_turn"] = 0

        # reset every player's turn state to the first turn of the new round
        for sid in room.player_state:
            old_turn = room.player_state[sid]["current_turn"]
            room.player_state[sid]["current_turn"] = 0
            room.player_state[sid]["current_round"] = room.game_state["current_round"]
            print(f"👤 Reset player {sid} for new round: turn {old_turn} -> 0, round -> {room.game_state['current_round']}")

        if room.game_state["current_round"] <= room.num_rounds and room.game_state["current_round"] in room.game_state["rounds"]:
            room.game_state["rounds"][room.game_state["current_round"]]["started_at"] = get_timestamp()
            room.game_state["rounds"][room.game_state["current_round"]]["turns"][0]["started_at"] = get_timestamp()

        print(f"🔄 Advanced to new round {room.game_state['current_round']}, turn {room.game_state['current_turn']}")
        return True
    else:
        # Continue to next turn in current round
        room.game_state["rounds"][room.game_state["current_round"]]["turns"][current_game_turn]["ended_at"] = get_timestamp()
        room.game_state["current_turn"] = next_turn
        room.game_state["rounds"][room.game_state["current_round"]]["turns"][next_turn]["started_at"] = get_timestamp()

        print(f"🔄 Advanced to turn {room.game_state['current_turn']} in round {room.game_state['current_round']}")
        return False


async def move_to_next_turn(room, triggered_by_timer=False):
    print(f"🔄 move_to_next_turn called for room {room.room_id}, current_turn: {room.game_state['current_turn']}, current_round: {room.game_state['current_round']}, triggered_by_timer: {triggered_by_timer}")

    if room.is_game_over():
        print(f"🏁 Game over for room {room.room_id}")
        await sio.emit("game_over", {"message": "Game finished!"}, room=room.room_id)
    else:
        # If triggered by timer, manually update all player states
        if triggered_by_timer:
            print("⏰ Timer triggered transition, updating all player states")
            for sid in room.player_state:
                old_turn = room.player_state[sid]["current_turn"]
                room.player_state[sid]["current_turn"] = room.game_state["current_turn"]
                print(f"👤 Updated player {sid} turn: {old_turn} -> {room.player_state[sid]['current_turn']}")
        
        print(f"📤 Sending next-turn-ready: round={room.game_state['current_round']}, turn={room.game_state['current_turn']}")
        
        # compute the global turn number for the frontend
        # fix: the global turn is based on completed rounds plus the current round's turn
        completed_rounds = room.game_state["current_round"] - 1  # number of completed rounds (1-based, hence -1)
        global_turn = completed_rounds * 4 + room.game_state["current_turn"]
        
        await sio.emit("next-turn-ready", {
            "current_round": room.game_state["current_round"],
            "current_turn": global_turn,  # send the global turn number to the frontend
            "round_turn": room.game_state["current_turn"],  # keep the within-round turn number
            "moving_to_next_turn": True
        }, room=room.room_id)

        # Add a small delay to ensure frontend state is updated before starting timer
        await asyncio.sleep(0.1)
        
        # Start new turn timer
        asyncio.create_task(start_turn_timer(
            room, room.game_state["current_round"], room.game_state["current_turn"]))


@sio.on("player-done")
async def player_done(sid, data):
    print(f"🎯 Received player-done from {sid} with data: {data}")
    room_id = data["room_id"]
    room = room_manager.get_room(room_id)

    if not room:
        print(f"❌ Room {room_id} not found")
        return

    print(f"🔍 DEBUG player_state keys: {list(room.player_state.keys())}")
    print(f"🔍 DEBUG room.players: {room.players}")
    print(f"🔍 DEBUG sid_to_room for this sid: {sid_to_room.get(sid)}")

    if sid not in room.player_state:
        print(f"⚠️ Player {sid} not found in room {room_id}")
        print(f"Available players: {list(room.player_state.keys())}")
        return

    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]
    print(f"🎮 Current game state: round {current_round}, turn {current_turn}")

    old_turn = room.player_state[sid]["current_turn"]
    room.player_state[sid]["current_turn"] += 1
    print(f"👤 Player {sid} turn: {old_turn} -> {room.player_state[sid]['current_turn']}")

    all_turns = [player["current_turn"]
                 for player in room.player_state.values()]

    print(f"🔍 All player turns: {all_turns}")

    if len(set(all_turns)) == 1:
        print("✅ All players are on the same turn:", all_turns[0])
        
        # during the voting phase, check whether all players have voted
        current_round = room.game_state["current_round"]
        current_turn = room.game_state["current_turn"]
        
        if current_turn == 1 and not check_all_players_voted(room, current_round, current_turn):
            print("⚠️ Not all players have voted yet, cannot proceed")
            await sio.emit("waiting", {
                "message": "Waiting for all players to vote before continuing"
            }, room=room_id)
            return
        
        # use the unified turn-update logic, passing player turns
        round_changed = update_game_turn(room, all_turns)
        
        print(f"🔍 After update_game_turn: game_turn={room.game_state['current_turn']}, game_round={room.game_state['current_round']}, round_changed={round_changed}")
        
        # if the round changed, every player's turn was already reset in update_game_turn
        # no need to re-check sync; go straight to the next turn
        await move_to_next_turn(room)
    else:
        await sio.emit(
            "waiting", {"message": "Waiting for other players"}, room=room_id)
        print("Waiting for other players. Current turns:", all_turns)


@ sio.on("disconnect")
async def disconnect(sid):
    print(f"❌ Client {sid} disconnected")


@router.get("/api/adjectives")
async def get_adjectives(room_id: str, sid: str):
    try:
        room = room_manager.get_room(room_id)
        current_round = room.game_state["current_round"]
        print(current_round)
        print(room.game_state)
        return room.game_state["rounds"][current_round]["adjectives"][sid]
    except Exception as e:
        print(f"Error getting adjectives: {e}")


@router.get("/api/nouns")
async def get_nouns(room_id: str):
    try:
        room = room_manager.get_room(room_id)
        current_round = room.game_state["current_round"]
        return room.game_state["rounds"][current_round]["nouns"]
    except Exception as e:
        print(f"Error getting nouns: {e}")


@router.get("/api/reference-image")
async def get_reference_image(room_id: str, sid: str = None):
    """Get the reference image for the current round"""
    if not room_id:
        return {"error": "Room ID is required"}
    
    if not sid or sid == "undefined":
        return {"error": "Valid Socket ID is required"}
    
    # special handling for tutorial mode
    if room_id.startswith("tutorial_"):
        # seed the RNG from the room ID to pick a random tutorial reference image
        seed = hash(room_id) % len(REFERENCE_IMAGE_POOL)
        reference_image = REFERENCE_IMAGE_POOL[seed]
        return reference_image
    
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}
    
    current_round = room.game_state["current_round"]
    
    # Use categorized reference image assigned to this round
    if "reference_image" in room.game_state["rounds"][current_round]:
        reference_image = room.game_state["rounds"][current_round]["reference_image"]
        # Add category information to the response
        reference_image["category"] = room.game_state["rounds"][current_round].get("category", "unknown")
        return reference_image
    
    # Fallback to old system if no categorized image is set
    seed = hash(f"{room_id}_{current_round}") % len(REFERENCE_IMAGE_POOL)
    reference_image = REFERENCE_IMAGE_POOL[seed]
    
    return reference_image

@router.get("/api/reference-image-pool")
async def get_reference_image_pool():
    """Get info on the whole reference-image pool (for testing/debugging)"""
    return {
        "total_images": len(REFERENCE_IMAGE_POOL),
        "images": REFERENCE_IMAGE_POOL
    }

@router.get("/api/voting-images")
async def get_voting_images(room_id: str, sid: str):
    """Get images generated by other players this round, for voting"""
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}

    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]

    # get data from the previous turn (Generate phase)
    generate_turn = 0  # the Generate phase is always turn 0
    turns_data = room.game_state["rounds"][current_round]["turns"][generate_turn]["data"]

    print(f"🗳️  Fetching voting images for room {room_id}, requester SID: {sid[:8]}...")
    print(f"🗳️  All player SIDs in generate turn: {list(turns_data.keys())}")

    # find the current user's player_name to exclude all of that player's SIDs (including old ones)
    current_player_name = room.sid_to_players.get(sid)
    print(f"🔍 Current player name: {current_player_name}")

    images = []

    # iterate over all players' data, excluding the current user (including old SIDs)
    for player_sid, player_data in turns_data.items():
        print(f"🔍 Checking player {player_sid[:8]}... (requester: {sid[:8]})")

        # exclude the player's own current SID
        if player_sid == sid:
            print(f"  ⏭️  Skipping own image (current SID)")
            continue

        # exclude the player's own old SID: check whether this SID belongs to the same player
        sid_player_name = room.sid_to_players.get(player_sid)
        if sid_player_name == current_player_name and current_player_name is not None:
            print(f"  ⏭️  Skipping own image (old SID, player: {current_player_name})")
            continue

        # check whether the player submitted an image
        if "submitted_image" in player_data:
            submitted_image = player_data["submitted_image"]
            player_name = room.sid_to_players.get(player_sid, f"Player {player_sid[:8]}")
            
            images.append({
                "creator_sid": player_sid,
                "creator_name": player_name,
                "image_url": process_image_url(submitted_image["url"]),
                "prompt": player_data.get("prompt", "No prompt available")
            })
    
    return {"images": images}

@router.post("/api/vote")
async def vote_for_image(request: VoteRequest):
    """Handle a user vote"""
    room = room_manager.get_room(request.room_id)
    if not room:
        return {"error": "Room not found"}
    
    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]
    
    # ensure we are in the voting phase (turn 1)
    if current_turn != 1:
        return {"error": "Not in voting phase"}
    
    # initialize the voting data structure
    turns_data = room.game_state["rounds"][current_round]["turns"][current_turn]["data"]
    
    if request.voter_sid not in turns_data:
        turns_data[request.voter_sid] = {}
    
    # store vote info
    turns_data[request.voter_sid]["vote"] = {
        "voted_for_sid": request.voted_for_sid,
        "image_url": request.image_url,
        "timestamp": get_timestamp()
    }
    
    # initialize vote tallies (if absent)
    if "vote_counts" not in turns_data:
        turns_data["vote_counts"] = {}
    
    # update the vote count
    if request.voted_for_sid not in turns_data["vote_counts"]:
        turns_data["vote_counts"][request.voted_for_sid] = []
    
    # check whether the player already voted (prevent double voting)
    existing_votes = [vote for vote in turns_data["vote_counts"][request.voted_for_sid] 
                     if vote["voter_sid"] == request.voter_sid]
    
    if not existing_votes:
        turns_data["vote_counts"][request.voted_for_sid].append({
            "voter_sid": request.voter_sid,
            "timestamp": get_timestamp()
        })
        
        # Log the vote
        voter_name = room.sid_to_players.get(request.voter_sid, f"Player {request.voter_sid[:8]}")
        voted_for_name = room.sid_to_players.get(request.voted_for_sid, f"Player {request.voted_for_sid[:8]}")
        
        game_logger.log_vote(
            game_id=request.room_id,
            round_num=current_round,
            turn_num=current_turn,
            voter_sid=request.voter_sid,
            voter_name=voter_name,
            voted_for_sid=request.voted_for_sid,
            voted_for_name=voted_for_name
        )
    
    print(f"✅ Vote recorded: {request.voter_sid} voted for {request.voted_for_sid}")
    print(f"Current vote counts: {turns_data.get('vote_counts', {})}")
    
    # check whether all players have voted; if so, auto-advance to the next phase
    if check_all_players_voted(room, current_round, current_turn):
        print("🎯 All players have now voted! Auto-advancing to next phase...")
        
        # cancel the current timer (if any)
        if room.room_id in turn_timers:
            turn_timers[room.room_id].cancel()
            print(f"⏰ Cancelled voting timer for room {room.room_id}")
        
        # advance to the next phase
        update_game_turn(room)
        await move_to_next_turn(room, triggered_by_timer=False)
    
    return {"message": "Vote recorded successfully"}

@router.get("/api/vote-results")
async def get_vote_results(room_id: str, sid: str):
    """Get voting results for the Result phase"""
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}
    
    current_round = room.game_state["current_round"]
    
    # get voting-phase data (turn 1)
    voting_turn = 1
    voting_data = room.game_state["rounds"][current_round]["turns"][voting_turn]["data"]
    
    # get Generate-phase data (turn 0) to obtain image info
    generate_data = room.game_state["rounds"][current_round]["turns"][0]["data"]
    
    results = []
    
    # iterate over all players who generated an image
    for player_sid, player_data in generate_data.items():
        if "submitted_image" in player_data:
            player_name = room.sid_to_players.get(player_sid, f"Player {player_sid[:8]}")
            
            # count the votes this player received
            vote_count = 0
            voters = []
            
            if "vote_counts" in voting_data and player_sid in voting_data["vote_counts"]:
                votes = voting_data["vote_counts"][player_sid]
                vote_count = len(votes)
                voters = [vote["voter_sid"] for vote in votes]
            
            results.append({
                "creator_sid": player_sid,
                "creator_name": player_name,
                "image_url": process_image_url(player_data["submitted_image"]["url"]),
                "prompt": player_data.get("prompt", "No prompt available"),
                "vote_count": vote_count,
                "voters": voters
            })
    
    # sort by vote count
    results.sort(key=lambda x: x["vote_count"], reverse=True)
    
    return {"results": results}

@router.get("/api/reveal-data")
async def get_reveal_data(room_id: str, sid: str):
    """Get Reveal-phase data: images, prompts and vote info"""
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}
    
    current_round = room.game_state["current_round"]
    
    # get Generate-phase data (turn 0)
    generate_data = room.game_state["rounds"][current_round]["turns"][0]["data"]
    
    # get voting-phase data (turn 1)
    voting_data = room.game_state["rounds"][current_round]["turns"][1]["data"]
    
    results = []
    
    # iterate over all players who generated an image
    for player_sid, player_data in generate_data.items():
        if "submitted_image" in player_data:
            player_name = room.sid_to_players.get(player_sid, f"Player {player_sid[:8]}")
            
            # get vote info
            vote_count = 0
            voters = []
            voter_names = []
            
            if "vote_counts" in voting_data and player_sid in voting_data["vote_counts"]:
                votes = voting_data["vote_counts"][player_sid]
                vote_count = len(votes)
                voters = [vote["voter_sid"] for vote in votes]
                voter_names = [room.sid_to_players.get(voter_sid, f"Player {voter_sid[:8]}") 
                             for voter_sid in voters]
            
            results.append({
                "creator_sid": player_sid,
                "creator_name": player_name,
                "image_url": process_image_url(player_data["submitted_image"]["url"]),
                "prompt": player_data.get("prompt", "No prompt available"),
                "vote_count": vote_count,
                "voters": voters,
                "voter_names": voter_names
            })
    
    # sort by vote count (high to low)
    results.sort(key=lambda x: x["vote_count"], reverse=True)
    
    return {"data": results}

def calculate_prompt_tokens(prompt):
    """Count the number of tokens in a prompt (using OpenAI's tiktoken)"""
    if not prompt:
        return 0
    if prompt == "No prompt submitted":
        return 0

    # Use GPT-4o encoding for accurate tokenization
    encoding = tiktoken.encoding_for_model("gpt-4o")
    tokens = encoding.encode(prompt.strip())
    return len(tokens)

def calculate_score(prompt, vote_count, prompt_tokens_list, player_tokens):
    """
    Compute score: new scoring rules
    - 1 point per vote received
    - the player with the longest prompt loses 1 point
    - if several (but not all) players tie for longest, they each lose 1 point
    - if everyone is the same length, no penalty
    - special rule: if any player has 0 tokens, only compare players with non-zero tokens
    """
    if not prompt:
        player_tokens = 0
    
    # base score: vote count * 1
    vote_score = vote_count
    
    # compute penalty
    penalty = 0
    
    # filter out players with 0 tokens, compare only valid submissions
    non_zero_tokens = [tokens for tokens in prompt_tokens_list if tokens > 0]
    
    if len(non_zero_tokens) > 1 and len(set(non_zero_tokens)) > 1:  # multiple non-zero players with differing lengths
        max_tokens = max(non_zero_tokens)
        if player_tokens > 0 and player_tokens == max_tokens:
            penalty = 1
    
    # final score
    final_score = max(0, vote_score - penalty)
    
    return {
        "total_score": final_score,
        "vote_score": vote_score,
        "penalty": penalty,
        "prompt_tokens": player_tokens
    }

@router.get("/api/final-results")
async def get_final_results(room_id: str, sid: str):
    """Get final-results page data: score calculation and ranking"""
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}
    
    current_round = room.game_state["current_round"]
    
    # get Generate-phase data (turn 0)
    generate_data = room.game_state["rounds"][current_round]["turns"][0]["data"]
    
    # get voting-phase data (turn 1)
    voting_data = room.game_state["rounds"][current_round]["turns"][1]["data"]
    
    # first collect all players' prompt tokens for penalty calculation
    all_prompt_tokens = []
    player_prompt_tokens = {}
    
    for player_sid, player_data in generate_data.items():
        if "submitted_image" in player_data:
            prompt = player_data.get("prompt", "")
            tokens = calculate_prompt_tokens(prompt)
            all_prompt_tokens.append(tokens)
            player_prompt_tokens[player_sid] = tokens
    
    results = []
    
    # iterate over all players who generated an image
    for player_sid, player_data in generate_data.items():
        if "submitted_image" in player_data:
            player_name = room.sid_to_players.get(player_sid, f"Player {player_sid[:8]}")
            prompt = player_data.get("prompt", "")
            
            # get vote info
            vote_count = 0
            voters = []
            voter_names = []
            
            if "vote_counts" in voting_data and player_sid in voting_data["vote_counts"]:
                votes = voting_data["vote_counts"][player_sid]
                vote_count = len(votes)
                voters = [vote["voter_sid"] for vote in votes]
                voter_names = [room.sid_to_players.get(voter_sid, f"Player {voter_sid[:8]}") 
                             for voter_sid in voters]
            
            # use the new scoring logic
            player_tokens = player_prompt_tokens[player_sid]
            score_info = calculate_score(prompt, vote_count, all_prompt_tokens, player_tokens)
            
            results.append({
                "creator_sid": player_sid,
                "creator_name": player_name,
                "image_url": process_image_url(player_data["submitted_image"]["url"]),
                "prompt": prompt,
                "vote_count": vote_count,
                "voters": voters,
                "voter_names": voter_names,
                "score_info": score_info
            })
    
    # sort by total score (high to low)
    results.sort(key=lambda x: x["score_info"]["total_score"], reverse=True)
    
    return {"results": results}

@router.get("/api/debug-voting")
async def debug_voting_data(room_id: str):
    """Debug API: inspect voting-related data"""
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}
    
    current_round = room.game_state["current_round"]
    
    return {
        "room_id": room_id,
        "current_round": current_round,
        "generate_data": room.game_state["rounds"][current_round]["turns"][0]["data"],
        "voting_data": room.game_state["rounds"][current_round]["turns"][1]["data"],
        "players": room.sid_to_players
    }

@router.get("/api/sentence")
async def get_sentence(room_id: str, sid: str):
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}

    game_state = room.game_state
    current_round = game_state["current_round"]
    current_turn = game_state["current_turn"]

    prev_turn_data = game_state["rounds"][current_round]["turns"][current_turn-1]
    turn_data = game_state["rounds"][current_round]["turns"][current_turn]["data"]

    if "data" not in prev_turn_data or not prev_turn_data["data"]:
        return {"error": "No sentences available for this turn"}

    player_sentences = prev_turn_data["data"]
    player_ids = list(player_sentences.keys())  # Ordered list of player IDs

    if sid not in player_ids:
        return {"error": "No sentence found for this player"}

    # Ensure `assigned_sentences` exists for this turn
    # if "assigned_sentences" not in turn_data:
    #     turn_data["assigned_sentences"] = {}

    # If player already has an assigned sentence, return it
    # if sid in turn_data["assigned_sentences"]:
    #     return {"sentence": turn_data["assigned_sentences"][sid]}

    # Find the player's index in the ordered list
    player_index = player_ids.index(sid)
    # Next player in rotation
    assigned_index = (player_index + 1) % len(player_ids)
    assigned_sid = player_ids[assigned_index]  # Get next player's ID
    # Get assigned sentence
    assigned_sentence = player_sentences[assigned_sid]["sentence"]

    # Store assignment
    # turn_data["assigned_sentences"][sid] = {}
    # turn_data["assigned_sentences"][sid]["assigned_from"] = assigned_sid
    # turn_data["assigned_sentences"][sid]["sentence"] = assigned_sentence
    turn_data[sid] = {}
    turn_data[sid]["assigned_from"] = assigned_sid
    turn_data[sid]["sentence"] = assigned_sentence
    print(game_state)
    print(f"Player {sid} assigned sentence: {assigned_sentence}")

    return {"sentence": assigned_sentence}


generated_images: Dict[str, Dict[str, List]] = {}

TEST_LIST = ["https://placehold.co/165"]


class ImageRequest(BaseModel):
    prompt: str
    room_id: str
    sid: str


class ImageSubmission(BaseModel):
    image_url: str
    sid: str
    room_id: str
    prompt: str


def url_to_image(image_url):
    # Extract filename from URL (supports both old and new filename formats)
    if not image_url:
        return None
    
    # Extract filename from URL - matches any .png file that contains 'img-'
    # This handles both old format (img-abc123.png) and new format (20250825_185012-img-1-alice-prompt-fallacy.png)
    match = re.search(r"([^/]*img-[^/]*\.png)", image_url)
    return match.group(1) if match else None

def process_image_url(image_identifier):
    """
    Convert image identifier to full backend URL if needed.
    Handles both URLs and filenames (old and new formats).
    """
    if not image_identifier:
        return None
    
    if image_identifier.startswith('http'):
        # Already a full URL
        return image_identifier
    elif image_identifier.endswith('.png') and ('img-' in image_identifier or image_identifier.startswith('img-')):
        # Local filename (both old format img-xxx.png and new format timestamp-img-xxx.png)
        return f"{BACKEND_URL}/generated_images/{image_identifier}"
    else:
        # Unknown format - keep as is (might be placeholder URLs)
        return image_identifier


def store_image_from_url(image_url):
    """
    Store image in the backend storage (in the 'generated_images' folder)
    """
    file_name = os.path.join('generated_images', url_to_image(image_url))
    try:
        response = requests.get(image_url, stream=True, timeout=5)
        response.raise_for_status()
        with open(file_name, 'wb') as image_file:
            for chunk in response.iter_content(chunk_size=1024):
                image_file.write(chunk)

        print(f"Image saved: {file_name}")
        return file_name
    except Exception as e:
        print(f"Error saving image: {e}")
        return None


async def get_all_image_names(room_id: str):
    images = []
    room = room_manager.get_room(room_id)
    for i in range(4):
        for data in room.game_state["rounds"][i]["turns"][1].get("data", {}).values():
            for image in data.get("all", []):
                # Append all available image names (supports 1 or more)
                for img_name in image.get("images", []):
                    images.append(img_name)
    print(f"downloading all images from the room: {room_id}")

ZIP_DIR = "zipped_images"


async def download_all_images(room_id: str, image_list: List[str]):
    """download all images given zipped"""
    zip_filename = f"{room_id}_images.zip"
    zip_path = os.path.join(ZIP_DIR, zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for image_name in image_list:
            image_path = os.path.join("generated_images", image_name)
            if os.path.isfile(image_path):  # Check if the image exists
                zipf.write(image_path, arcname=image_name)
            else:
                print(f"Image not found: {image_name}")

    return FileResponse(zip_path, filename=zip_filename, media_type="application/zip")


@router.get("/api/image")
async def get_image(image_name: str, room_id: str = ""):
    """
    Returns the image with the given name.
    """
    if room_id != "":
        await get_all_image_names(room_id)
        return {"message": "Images downloaded successfully!"}
    file_path = os.path.join("generated_images", image_name)
    if not os.path.exists(file_path):
        print(f"Image not found: {file_path}")
        return {"error": "Image not found"}
    return FileResponse(file_path, media_type="image/png")


async def generate_image_for_player(room_id, sid, prompt, auto_submitted=False):
    """Helper function to generate image for a player"""
    global generated_images

    # Capture prompt submission timestamp
    prompt_timestamp = datetime.utcnow().isoformat() + 'Z'

    # Capture current game state at the START of generation to avoid race conditions
    room = room_manager.get_room(room_id)
    generation_round = room.game_state["current_round"]
    generation_turn = room.game_state["current_turn"]
    player_name = room.sid_to_players.get(sid, f"Player {sid[:8]}")

    # Use the player-supplied API key for this room (no silent server-key fallback)
    api_key = resolve_room_api_key(room)
    if not api_key:
        # Surface as an API key error so the player is prompted to enter their key
        raise ValueError("No OpenAI API key provided for this room (invalid_api_key)")
    room_client = OpenAI(api_key=api_key)
    
    
    # Ensure data structure initialization
    room_id_str = str(room_id)
    if room_id_str not in generated_images:
        generated_images[room_id_str] = {}
    if sid not in generated_images[room_id_str]:
        generated_images[room_id_str][sid] = []
    
    # Mark that generation is in progress
    generated_images[room_id_str][sid] = []  # Empty array indicates generation in progress
    
    if os.getenv("ENVIRONMENT") == "test":
        await asyncio.sleep(2)
        generated_images[room_id_str][sid] = TEST_LIST
        store_all_prompts(sid, room_id, prompt)
        
        # Auto-submit the image if this was an auto-submission
        if auto_submitted:
            await auto_submit_image(room_id, sid, TEST_LIST[0], prompt, generation_round, generation_turn)
        
        return TEST_LIST[0]
    
    try:
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()
        
        response = await loop.run_in_executor(executor, lambda: room_client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="medium",
            n=1,
        ))

        # Capture image generation completion timestamp
        image_generated_timestamp = datetime.utcnow().isoformat() + 'Z'

        # Handle both URL and base64 responses
        image_data = response.data[0]
        if image_data.url:
            # URL-based response (dall-e-3)
            url = image_data.url
            generated_images[room_id_str][sid] = [url]
            store_image_from_url(url)
            image_identifier = url
        elif image_data.b64_json:
            # Base64 response (gpt-image-1)
            # Generate human-readable filename
            timestamp = datetime.utcnow().isoformat() + 'Z'
            filename = generate_human_readable_filename(
                timestamp=timestamp,
                round_num=generation_round,
                player_name=player_name,
                action_type="prompt",
                prompt=prompt,
                extension="png"
            )
            
            # Handle filename collisions
            existing_files = set(os.listdir('generated_images')) if os.path.exists('generated_images') else set()
            filename = handle_filename_collision(filename, existing_files)
            
            filepath = os.path.join('generated_images', filename)
            
            # Decode and save base64 image
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(image_data.b64_json))
            
            # Store relative path
            generated_images[room_id_str][sid] = [filename]
            image_identifier = filename
        else:
            raise ValueError("No image URL or base64 data found in response")
        
        store_all_prompts(sid, room_id, prompt)
        
        # Log successful image generation using captured state from start of generation
        prompt_tokens = prompt.split() if prompt else []
        
        # Get reference image info for this round
        reference_image = room.game_state["rounds"][generation_round].get("reference_image", {})
        ref_id = reference_image.get("id")
        ref_path = reference_image.get("image_path")
        ref_description = reference_image.get("description")
        
        # Log image generation with reference data
        game_logger.log_image_generation(
            game_id=room_id,
            round_num=generation_round,
            turn_num=generation_turn,
            player_sid=sid,
            player_name=player_name,
            prompt=prompt,
            image_url=image_identifier,
            prompt_tokens=prompt_tokens,
            reference_image_id=ref_id,
            reference_image_path=ref_path,
            reference_description=ref_description,
            generation_success=True,
            prompt_timestamp=prompt_timestamp,
            image_generated_timestamp=image_generated_timestamp
        )
        
        # Auto-submit the image if this was an auto-submission
        if auto_submitted:
            await auto_submit_image(room_id, sid, image_identifier, prompt, generation_round, generation_turn)
        
        return image_identifier
    except Exception as e:
        print(f"Error generating image for player {sid}: {e}")
        # Mark generation as failed
        generated_images[room_id_str][sid] = ["FAILED"]
        
        # Log failed image generation using captured state from start of generation
        prompt_tokens = prompt.split() if prompt else []
        
        # Get reference image info for this round (same as success case)
        reference_image = room.game_state["rounds"][generation_round].get("reference_image", {})
        ref_id = reference_image.get("id")
        ref_path = reference_image.get("image_path")
        ref_description = reference_image.get("description")
        
        game_logger.log_image_generation(
            game_id=room_id,
            round_num=generation_round,
            turn_num=generation_turn,
            player_sid=sid,
            player_name=player_name,
            prompt=prompt,
            image_url=None,
            prompt_tokens=prompt_tokens,
            reference_image_id=ref_id,
            reference_image_path=ref_path,
            reference_description=ref_description,
            generation_success=False,
            prompt_timestamp=prompt_timestamp,
            image_generated_timestamp=None,
            error_message=str(e)
        )
        
        raise e

async def auto_submit_image(room_id, sid, image_url, prompt, target_round, target_turn):
    """Auto-submit image after generation"""
    try:
        room = room_manager.get_room(room_id)
        # Use the target round/turn from when generation started, not current state
        current_round = target_round
        current_turn = target_turn
        
        image_name = url_to_image(image_url)
        
        # Initialize turn data if needed
        if "data" not in room.game_state["rounds"][current_round]["turns"][current_turn]:
            room.game_state["rounds"][current_round]["turns"][current_turn]["data"] = {}
        
        turns_data = room.game_state["rounds"][current_round]["turns"][current_turn]["data"]
        
        if sid not in turns_data:
            turns_data[sid] = {}
        
        turns_data[sid]["submitted_image"] = {
            "url": image_url, 
            "name": image_name, 
            "random": False,
            "auto_submitted": True
        }
        turns_data[sid]["prompt"] = prompt
        turns_data[sid]["timestamp"] = get_timestamp()
        
        print(f"✅ Auto-submitted image for player {sid} to round {current_round}, turn {current_turn}")
    except Exception as e:
        print(f"Error auto-submitting image: {e}")
        raise e

@router.post("/api/generate-images")
async def generate_images(request: ImageRequest):
    global generated_images

    # Capture prompt submission timestamp
    prompt_timestamp = datetime.utcnow().isoformat() + 'Z'

    # Use the player-supplied API key for this room (no silent server-key fallback)
    room = room_manager.get_room(request.room_id)
    api_key = resolve_room_api_key(room)
    if not api_key:
        raise HTTPException(status_code=401, detail={
            "error": "invalid_api_key",
            "message": "No OpenAI API key provided for this room. Please enter your API key."
        })
    room_client = OpenAI(api_key=api_key)

    if os.getenv("ENVIRONMENT") == "test":
        # ensure the data structure is initialized
        room_id_str = str(request.room_id)
        if room_id_str not in generated_images:
            generated_images[room_id_str] = {}
        if request.sid not in generated_images[room_id_str]:
            generated_images[room_id_str][request.sid] = []
            
        await asyncio.sleep(2)
        generated_images[room_id_str][request.sid] = TEST_LIST
        store_all_prompts(request.sid, request.room_id, request.prompt)
        return {"message": "Images generated successfully!"}

    # ensure the data structure is initialized
    room_id_str = str(request.room_id)
    if room_id_str not in generated_images:
        generated_images[room_id_str] = {}
    if request.sid not in generated_images[room_id_str]:
        generated_images[room_id_str][request.sid] = []

    try:
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()

        async def generate_one_image():
            return await loop.run_in_executor(executor, lambda: room_client.images.generate(
                model="gpt-image-1",
                prompt=request.prompt,
                size="1024x1024",
                quality="medium",
                n=1,
            ))

        # Generate a single image
        response = await generate_one_image()

        # Capture image generation completion timestamp
        image_generated_timestamp = datetime.utcnow().isoformat() + 'Z'

        # Handle both URL and base64 responses
        image_data = response.data[0]
        if image_data.url:
            # URL-based response (dall-e-3)
            url = image_data.url
            generated_images[room_id_str][request.sid] = [url]
            store_image_from_url(url)
            image_identifier = url
        elif image_data.b64_json:
            # Base64 response (gpt-image-1)
            # Get game state info for filename generation
            room = room_manager.get_room(request.room_id)
            current_round = room.game_state["current_round"] if room else 0
            player_name = room.sid_to_players.get(request.sid, f"Player{request.sid[:8]}") if room else f"Player{request.sid[:8]}"
            
            # Generate human-readable filename
            timestamp = datetime.utcnow().isoformat() + 'Z'
            filename = generate_human_readable_filename(
                timestamp=timestamp,
                round_num=current_round,
                player_name=player_name,
                action_type="prompt",
                prompt=request.prompt,
                extension="png"
            )
            
            # Handle filename collisions
            existing_files = set(os.listdir('generated_images')) if os.path.exists('generated_images') else set()
            filename = handle_filename_collision(filename, existing_files)
            
            filepath = os.path.join('generated_images', filename)
            
            # Decode and save base64 image
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(image_data.b64_json))
            
            # Store relative path
            generated_images[room_id_str][request.sid] = [filename]
            image_identifier = filename
        else:
            raise ValueError("No image URL or base64 data found in response")

        store_all_prompts(request.sid, request.room_id, request.prompt)
        
        # Log successful image generation (only during generation phase)
        room = room_manager.get_room(request.room_id)
        if room:
            current_round = room.game_state["current_round"]
            current_turn = room.game_state["current_turn"]
            player_name = room.sid_to_players.get(request.sid, f"Player {request.sid[:8]}")
            prompt_tokens = request.prompt.split() if request.prompt else []
            
            # Only log if it's actually the generation phase (turn % 4 === 0)
            if current_turn % 4 == 0:
                # Get reference image info for this round
                reference_image = room.game_state["rounds"][current_round].get("reference_image", {})
                ref_id = reference_image.get("id")
                ref_path = reference_image.get("image_path")
                ref_description = reference_image.get("description")
                
                game_logger.log_image_generation(
                    game_id=request.room_id,
                    round_num=current_round,
                    turn_num=current_turn,
                    player_sid=request.sid,
                    player_name=player_name,
                    prompt=request.prompt,
                    image_url=image_identifier,
                    prompt_tokens=prompt_tokens,
                    reference_image_id=ref_id,
                    reference_image_path=ref_path,
                    reference_description=ref_description,
                    generation_success=True,
                    prompt_timestamp=prompt_timestamp,
                    image_generated_timestamp=image_generated_timestamp
                )
            else:
                print(f"⚠️  Prevented spurious image generation logging: player {player_name} (SID: {request.sid}) tried to generate during turn {current_turn} (not generation phase)")

        return {"message": "Images generated successfully!"}
    
    except BadRequestError as e:
        # Handle OpenAI content moderation rejections specifically
        error_message = str(e)
        print(f"OpenAI content moderation error for player {request.sid}: {error_message}")
        
        # Check if it's a moderation/safety issue
        is_moderation_error = False
        safety_violations = []
        
        try:
            if "safety system" in error_message or "moderation_blocked" in error_message:
                is_moderation_error = True
                # Try to extract safety violations from the error message
                if "safety_violations=[" in error_message:
                    start = error_message.find("safety_violations=[") + len("safety_violations=[")
                    end = error_message.find("]", start)
                    violations_str = error_message[start:end]
                    safety_violations = [v.strip() for v in violations_str.split(',')]
        except Exception:
            # If parsing fails, just treat it as a general moderation error
            is_moderation_error = "safety" in error_message.lower() or "moderation" in error_message.lower()
        
        # Mark generation as failed
        generated_images[room_id_str][request.sid] = ["FAILED"]
        
        # Log the moderation failure
        room = room_manager.get_room(request.room_id)
        if room:
            current_round = room.game_state["current_round"]
            current_turn = room.game_state["current_turn"]
            player_name = room.sid_to_players.get(request.sid, f"Player {request.sid[:8]}")
            prompt_tokens = request.prompt.split() if request.prompt else []
            
            # Only log if it's actually the generation phase (turn % 4 === 0)
            if current_turn % 4 == 0:
                # Get reference image info for this round
                reference_image = room.game_state["rounds"][current_round].get("reference_image", {})
                ref_id = reference_image.get("id")
                ref_path = reference_image.get("image_path")
                ref_description = reference_image.get("description")
                
                # Log with specific moderation failure details
                log_message = f"Content moderation blocked. Violations: {safety_violations}" if safety_violations else f"Content moderation blocked: {error_message}"
                
                game_logger.log_image_generation(
                    game_id=request.room_id,
                    round_num=current_round,
                    turn_num=current_turn,
                    player_sid=request.sid,
                    player_name=player_name,
                    prompt=request.prompt,
                    image_url=None,
                    prompt_tokens=prompt_tokens,
                    reference_image_id=ref_id,
                    reference_image_path=ref_path,
                    reference_description=ref_description,
                    generation_success=False,
                    prompt_timestamp=prompt_timestamp,
                    image_generated_timestamp=None,
                    error_message=log_message
                )
            else:
                print(f"⚠️  Prevented spurious moderation failure logging: player {player_name} (SID: {request.sid}) tried to generate during turn {current_turn} (not generation phase)")
        
        # Return a specific error response for content moderation
        if is_moderation_error:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "content_moderation_blocked",
                    "message": "Your image prompt was rejected by the content safety system. Please try a different prompt.",
                    "violations": safety_violations
                }
            )
        else:
            # Re-raise the original BadRequestError for other OpenAI API issues
            raise e
    
    except Exception as e:
        print(f"Error generating image for player {request.sid}: {e}")
        # Mark generation as failed
        generated_images[room_id_str][request.sid] = ["FAILED"]
        
        # Log failed image generation (only during generation phase)
        room = room_manager.get_room(request.room_id)
        if room:
            current_round = room.game_state["current_round"]
            current_turn = room.game_state["current_turn"]
            player_name = room.sid_to_players.get(request.sid, f"Player {request.sid[:8]}")
            prompt_tokens = request.prompt.split() if request.prompt else []
            
            # Only log if it's actually the generation phase (turn % 4 === 0)
            if current_turn % 4 == 0:
                # Get reference image info for this round
                reference_image = room.game_state["rounds"][current_round].get("reference_image", {})
                ref_id = reference_image.get("id")
                ref_path = reference_image.get("image_path")
                ref_description = reference_image.get("description")
                
                game_logger.log_image_generation(
                    game_id=request.room_id,
                    round_num=current_round,
                    turn_num=current_turn,
                    player_sid=request.sid,
                    player_name=player_name,
                    prompt=request.prompt,
                    image_url=None,
                    prompt_tokens=prompt_tokens,
                    reference_image_id=ref_id,
                    reference_image_path=ref_path,
                    reference_description=ref_description,
                    generation_success=False,
                    prompt_timestamp=prompt_timestamp,
                    image_generated_timestamp=None,
                    error_message=str(e)
                )
            else:
                print(f"⚠️  Prevented spurious failed image generation logging: player {player_name} (SID: {request.sid}) tried to generate during turn {current_turn} (not generation phase)")

        # Check if it's an authentication error (invalid API key)
        if "401" in str(e) or "AuthenticationError" in str(type(e)) or "invalid_api_key" in str(e):
            raise HTTPException(status_code=401, detail={
                "error": "invalid_api_key",
                "message": "Invalid OpenAI API key. Please check your API key."
            })
        else:
            raise HTTPException(status_code=500, detail={
                "error": "generation_failed",
                "message": f"Image generation failed: {str(e)}"
            })
# @router.post("/api/generate-images")
# async def generate_images(request: ImageRequest):
#     global generated_images
#     if os.getenv("ENVIRONMENT") == "test":
#         if request.room_id not in generated_images:
#             generated_images[request.room_id] = {}
#         # timeout for mocking generation time
#         await asyncio.sleep(2)
#         generated_images[str(request.room_id)][request.sid] = TEST_LIST
#         store_all_prompts(request.sid, request.room_id, request.prompt)
#         # for i in range(2):
#         #     store_image_from_url(
#         #         generated_images[str(request.room_id)][request.sid][i])
#         return {"message": "Images generated successfully!"}
#     if request.room_id not in generated_images:
#         generated_images[request.room_id] = {}
#     response = client.images.generate(
#         model="dall-e-2",
#         prompt=request.prompt,
#         size="256x256",
#         quality="standard",
#         n=2,
#     )
#     generated_images[str(request.room_id)][request.sid] = [
#         response.data[x].url for x in range(2)]
#
#     store_all_prompts(request.sid, request.room_id, request.prompt)
#
#     # Store images in the backend storage
#     for i in range(2):
#         store_image_from_url(response.data[i].url)
#
#     return {"message": "Images generated successfully!"}
#


@router.post("/api/generate-submit-images-timeout")
async def generate_images_timeout(request: ImageRequest):
    # Use the player-supplied API key for this room (no silent server-key fallback)
    room = room_manager.get_room(request.room_id)
    api_key = resolve_room_api_key(room)
    if not api_key:
        raise HTTPException(status_code=401, detail={
            "error": "invalid_api_key",
            "message": "No OpenAI API key provided for this room. Please enter your API key."
        })
    room_client = OpenAI(api_key=api_key)

    # ensure the data structure is initialized
    room_id_str = str(request.room_id)
    if room_id_str not in generated_images:
        generated_images[room_id_str] = {}
    if request.sid not in generated_images[room_id_str]:
        generated_images[room_id_str][request.sid] = []
    
    # if the turn is over and image was not selected, it will generate image using the sentence as a prompt and generate image
    if os.getenv("ENVIRONMENT") == "test":
        # timeout for mocking generation time
        await asyncio.sleep(2)
        generated_images[room_id_str][request.sid] = [TEST_LIST[0]]
        store_all_prompts(request.sid, request.room_id, request.prompt)
        room = room_manager.get_room(request.room_id)
        current_round = room.game_state["current_round"]
        current_turn = room.game_state["current_turn"]

        room.game_state["rounds"][current_round]["turns"][current_turn]["data"][request.sid]["submitted_image"] = {
            "url": "test_url", "name": "test_image_name", "random": True}
        room.game_state["rounds"][current_round]["turns"][current_turn]["data"][request.sid]["prompt"] = request.prompt
        room.game_state["rounds"][current_round]["turns"][current_turn]["data"][request.sid]["timestamp"] = get_timestamp()
        print(room.game_state)
        return {"message": "Images generated successfully!"}

    # Generate images asynchronously
    # response_task = asyncio.create_task(client.images.generate(
    #     model="dall-e-2",
    #     prompt=request.prompt,
    #     size="256x256",
    #     quality="standard",
    #     n=1,
    # ))
    #
    # response = await response_task

    response = room_client.images.generate(
        model="gpt-image-1",
        prompt=request.prompt,
        size="1024x1024",
        quality="medium",
        n=1,
    )
    
    # Handle both URL and base64 responses
    image_data = response.data[0]
    if image_data.url:
        # URL-based response (dall-e-3)
        image_url = image_data.url
        generated_images[room_id_str][request.sid] = [image_url]
        store_image_from_url(image_url)
        image_identifier = image_url
    elif image_data.b64_json:
        # Base64 response (gpt-image-1)
        # Get game state info for filename generation
        room = room_manager.get_room(request.room_id)
        current_round = room.game_state["current_round"] if room else 0
        player_name = room.sid_to_players.get(request.sid, f"Player{request.sid[:8]}") if room else f"Player{request.sid[:8]}"
        
        # Generate human-readable filename
        timestamp = datetime.utcnow().isoformat() + 'Z'
        filename = generate_human_readable_filename(
            timestamp=timestamp,
            round_num=current_round,
            player_name=player_name,
            action_type="prompt",
            prompt=request.prompt,
            extension="png"
        )
        
        # Handle filename collisions
        existing_files = set(os.listdir('generated_images')) if os.path.exists('generated_images') else set()
        filename = handle_filename_collision(filename, existing_files)
        
        filepath = os.path.join('generated_images', filename)
        
        # Decode and save base64 image
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data.b64_json))
        
        # Store relative path
        generated_images[room_id_str][request.sid] = [filename]
        image_identifier = filename
    else:
        raise ValueError("No image URL or base64 data found in response")
    
    store_all_prompts(request.sid, request.room_id, request.prompt, True)

    room = room_manager.get_room(request.room_id)
    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]

    # Extract image name based on whether it's URL or filename
    if image_data.url:
        # URL-based response
        image_name = url_to_image(image_identifier)
        stored_url = image_identifier
    else:
        # Base64 response - already have filename
        image_name = image_identifier
        stored_url = image_identifier

    room.game_state["rounds"][current_round]["turns"][current_turn]["data"][request.sid]["submitted_image"] = {
        "url": stored_url, "name": image_name, "random": True}
    room.game_state["rounds"][current_round]["turns"][current_turn]["data"][request.sid]["prompt"] = request.prompt
    room.game_state["rounds"][current_round]["turns"][current_turn]["data"][request.sid]["timestamp"] = get_timestamp()
    print(room.game_state)
    return {"message": "Timeout - Images generated with given sentence!"}


def store_all_prompts(sid: str, room_id: str, prompt: str, random: bool = False):
    room = room_manager.get_room(room_id)
    if room is None:
        print(f"⚠️ Error: Room {room_id} not found in store_all_prompts")
        return
        
    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]
    
    # ensure the data structure exists
    turns_data = room.game_state["rounds"][current_round]["turns"][current_turn]["data"]
    
    # initialize the sid if it does not exist
    if sid not in turns_data:
        turns_data[sid] = {}
    
    # initialize 'all' if it does not exist
    if "all" not in turns_data[sid]:
        turns_data[sid]["all"] = []
    
    # ensure generated-image data exists
    if str(room_id) not in generated_images:
        generated_images[str(room_id)] = {}
    if sid not in generated_images[str(room_id)]:
        generated_images[str(room_id)][sid] = []
    
    turns_data[sid]["all"].append({
        "prompt": prompt,
        "images": [url_to_image(x) for x in generated_images[str(room_id)][sid]],
        "timestamp": get_timestamp(),
        "random": random
    })
    print(f"✅ Stored prompt for {sid} in round {current_round} turn {current_turn}")
    print(room.game_state)


@router.get("/api/get-images")
async def get_images(room_id: str, sid: str):
    """
    Returns generated images for the given room.
    """
    print(f"📋 get-images request: room_id={room_id}, sid={sid}")
    print(f"📋 generated_images: {generated_images}")
    
    # Get the raw images (could be URLs or filenames)
    raw_images = generated_images[room_id].get(sid, [])
    
    # Convert filenames to full URLs using helper function
    processed_images = [process_image_url(image) for image in raw_images]
    
    print(f"📋 Processed {len(raw_images)} images: {processed_images}")
    return {"images": processed_images}


@router.post("/api/submit-image")
async def submit_image(request: ImageSubmission):
    """
    Receives image submission from a player.
    """
    room = room_manager.get_room(request.room_id)
    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]

    image_name = url_to_image(request.image_url)

    room.game_state["rounds"][current_round]["turns"][current_turn]["data"][request.sid]["submitted_image"] = {
        "url": request.image_url, "name": image_name, "random": False}
    room.game_state["rounds"][current_round]["turns"][current_turn]["data"][request.sid]["prompt"] = request.prompt
    room.game_state["rounds"][current_round]["turns"][current_turn]["data"][request.sid]["timestamp"] = get_timestamp()
    print(f"Player {request.sid} submitted image: {request.image_url}")
    print(room.game_state)
    return {"message": "Image received"}


@router.get("/api/get-assigned-values")
async def get_assigned_adjectives(sid: str, room_id: str):
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}

    game_state = room.game_state
    current_round = game_state["current_round"]
    current_turn = game_state["current_turn"]
    prev_turn_data = game_state["rounds"][current_round]["turns"][current_turn-1]["data"]

    # Get all available players except the current player and the assigned_from player
    available_sids = [
        player_sid for player_sid in prev_turn_data
        if player_sid != sid and sid != prev_turn_data[player_sid]["assigned_from"]
    ]

    chosen_sid = random.choice(available_sids)

    return {"image": process_image_url(prev_turn_data[chosen_sid]["submitted_image"]["url"]), "adjectives": game_state["rounds"][current_round]["adjectives"][prev_turn_data[chosen_sid]["assigned_from"]]}


@router.get("/api/get-adjectives")
def get_adjectives(room_id: str, sid: str):
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}

    game_state = room.game_state
    current_round = game_state["current_round"]
    current_turn = game_state["current_turn"]
    turn_data = game_state["rounds"][current_round]["turns"][current_turn]

    # Ensure required keys exist in game state
    if "adjectives" not in game_state or sid not in game_state["adjectives"]:
        return {"error": "No adjectives found for this player"}

    if "assigned_sentences" not in turn_data or sid not in turn_data["assigned_sentences"]:
        return {"error": "No assigned sentences for this player"}

    # Get the player who assigned the current player's sentence
    assigned_from = turn_data["assigned_sentences"][sid].get("assigned_from")

    # Get all available players except the current player and the assigned_from player
    available_sids = [
        player_sid for player_sid in game_state["adjectives"]
        if player_sid != sid and player_sid != assigned_from
    ]

    if not available_sids:
        return {"error": "No available adjectives"}

    # Select a random player from available players
    chosen_sid = random.choice(available_sids)

    return {"adjectives": game_state["adjectives"][chosen_sid]}


class GuessRequest(BaseModel):
    room_id: str
    sid: str
    guess: List
    random: bool


@router.post('/api/submit-guess')
async def submit_guess(request: GuessRequest):
    try:
        room = room_manager.get_room(request.room_id)
        current_round = room.game_state["current_round"]
        current_turn = room.game_state["current_turn"]

        room.game_state["rounds"][current_round]["turns"][current_turn]["data"][request.sid] = {
            "guess": request.guess, "timestamp": get_timestamp(), "random": request.random}
        print(f"Player {request.sid} submitted guess: {request.guess}")
        print(room.game_state)
        print(request)
        return {"message": "Guess received"}
    except Exception as e:
        print(f"Error submitting guess: {e}")


def find_assigned_to(game_state, current_round, assigned_from_value):
    """Finds the player ID who was assigned a sentence from the given assigned_from_value."""
    turn_data = game_state["rounds"][current_round]["turns"][1]["data"]

    for key, value in turn_data.items():
        if isinstance(value, dict) and value.get("assigned_from") == assigned_from_value:
            return key  # Return the key where assigned_from matches

    return None  # Return None if not found


@router.get("/api/get-round-results")
async def get_round_results(room_id: str, sid: str):
    room = room_manager.get_room(room_id)
    current_round = room.game_state["current_round"]
    return room.game_state["rounds"][current_round]["result"]


class CalculateResultsRequest(BaseModel):
    room_id: str
    sid: str


@router.post("/api/calculate-results")
async def calculate_results(request: CalculateResultsRequest):
    room = room_manager.get_room(request.room_id)
    current_round = room.game_state["current_round"]
    player_state = room.player_state
    players = list(room.sid_to_players.keys())
    result = {}
    for player in room.sid_to_players.keys():
        result[player] = {}
        result[player]["adjectives"] = room.game_state["rounds"][current_round]["adjectives"][player]
        result[player]["sentence"] = room.game_state["rounds"][current_round]["turns"][0]["data"][player]["sentence"]
        assigned_to_player = find_assigned_to(
            room.game_state, current_round, player)
        result[player]["image"] = room.game_state["rounds"][current_round]["turns"][1]["data"][assigned_to_player]["submitted_image"]
        result[player]["prompt"] = room.game_state["rounds"][current_round]["turns"][1]["data"][assigned_to_player]["prompt"]
        guessing_players = [
            player_sid for player_sid in room.sid_to_players.keys()
            if player_sid != player and player_sid != assigned_to_player
        ]
        guessing_player = random.choice(guessing_players)
        result[player]["guess"] = room.game_state["rounds"][current_round]["turns"][2]["data"][guessing_player]["guess"]
        result[player]["image_from"] = assigned_to_player
        result[player]["guess_from"] = guessing_player
        result[player]["first_correct"] = result[player]["sentence"][0] == result[player]["guess"][0]
        result[player]["second_correct"] = result[player]["sentence"][3] == result[player]["guess"][3]
        result[player]["owner_points"] = int(
            not result[player]["first_correct"]) + int(not result[player]["second_correct"])
        result[player]["guesser_points"] = int(
            result[player]["first_correct"]) + int(result[player]["second_correct"])
        result[player]["drawer_points"] = result[player]["guesser_points"]

    room.game_state["rounds"][current_round]["result"] = result
    player_state[players[0]
                 ]["round"][current_round]["choose"] = result[players[0]]["owner_points"]
    player_state[players[1]
                 ]["round"][current_round]["choose"] = result[players[1]]["owner_points"]
    player_state[players[2]
                 ]["round"][current_round]["choose"] = result[players[2]]["owner_points"]

    # drawer and guesser points are the same
    player_state[players[0]
                 ]["round"][current_round]["prompt"] = result[players[1]]["drawer_points"]
    player_state[players[1]
                 ]["round"][current_round]["prompt"] = result[players[2]]["drawer_points"]
    player_state[players[2]
                 ]["round"][current_round]["prompt"] = result[players[0]]["drawer_points"]
    player_state[players[0]
                 ]["round"][current_round]["guess"] = result[players[2]]["guesser_points"]
    player_state[players[1]
                 ]["round"][current_round]["guess"] = result[players[0]]["guesser_points"]
    player_state[players[2]
                 ]["round"][current_round]["guess"] = result[players[1]]["guesser_points"]

    # total points
    player_state[players[0]]["round"][current_round]["total"] = player_state[players[0]]["round"][current_round]["choose"] + \
        player_state[players[0]]["round"][current_round]["prompt"] + \
        player_state[players[0]]["round"][current_round]["guess"]
    player_state[players[1]]["round"][current_round]["total"] = player_state[players[1]]["round"][current_round]["choose"] + \
        player_state[players[1]]["round"][current_round]["prompt"] + \
        player_state[players[1]]["round"][current_round]["guess"]
    player_state[players[2]]["round"][current_round]["total"] = player_state[players[2]]["round"][current_round]["choose"] + \
        player_state[players[2]]["round"][current_round]["prompt"] + \
        player_state[players[2]]["round"][current_round]["guess"]

    # total points until now
    player_state[players[0]]["score"] = player_state[players[0]]["round"][1]["total"] + \
        player_state[players[0]]["round"][2]["total"] + \
        player_state[players[0]]["round"][3]["total"] + \
        player_state[players[0]]["round"][4]["total"] + \
        player_state[players[0]]["round"][5]["total"] + \
        player_state[players[0]]["round"][6]["total"]
    player_state[players[1]]["score"] = player_state[players[1]]["round"][1]["total"] + \
        player_state[players[1]]["round"][2]["total"] + \
        player_state[players[1]]["round"][3]["total"] + \
        player_state[players[1]]["round"][4]["total"] + \
        player_state[players[1]]["round"][5]["total"] + \
        player_state[players[1]]["round"][6]["total"]
    player_state[players[2]]["score"] = player_state[players[2]]["round"][1]["total"] + \
        player_state[players[2]]["round"][2]["total"] + \
        player_state[players[2]]["round"][3]["total"] + \
        player_state[players[2]]["round"][4]["total"] + \
        player_state[players[2]]["round"][5]["total"] + \
        player_state[players[2]]["round"][6]["total"]

    # points for tutorial round
    player_state[players[0]]["tutorial_score"] = player_state[players[0]
                                                              ]["round"][0]["total"]
    player_state[players[1]]["tutorial_score"] = player_state[players[1]
                                                              ]["round"][0]["total"]
    player_state[players[2]]["tutorial_score"] = player_state[players[2]
                                                              ]["round"][0]["total"]

    # print(result)
    print(player_state)
    if current_round == 3:
        room.game_state["final_result"] = True
        print("----------------Final result----------------")
    return result


# def calculate_result(room_id: str):
#     room = room_manager.get_room(room_id)
#     round_result = room.game_state["rounds"][room.game_state["current_round"]]["result"]
#     current_round = room.game_state["current_round"]
#     for player in room.sid_to_players.keys():
#         room.player_state[player]["score"] += round_result[player]["owner_points"]
#         room.player_state[round_result[player]["image_from"]
#                           ]["score"] += round_result[player]["drawer_points"]
#         room.player_state[round_result[player]["guess_from"]
#                           ]["score"] += round_result[player]["guesser_points"]


@router.get("/api/player-state")
async def send_result(room_id: str):
    room = room_manager.get_room(room_id)
    player_state = room.player_state
    print(player_state)
    return {"player_state": player_state}


@router.get("/api/game-results")
async def get_game_results(room_id: str):
    """
    Get final game results with all rounds calculated using the new voting-based scoring system.
    """
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}
    
    print(f"Game state for room {room_id}:")
    print(f"Available rounds: {list(room.game_state.get('rounds', {}).keys())}")
    print(f"Current round: {room.game_state.get('current_round', 'unknown')}")
    
    # Calculate results for all completed rounds using voting system
    for round_num in range(1, room.num_rounds + 1):  # rounds 1 to num_rounds
        if round_num in room.game_state.get("rounds", {}):
            round_data = room.game_state["rounds"][round_num]
            print(f"Round {round_num} structure: {list(round_data.keys())}")
            
            # Check if this round has the necessary data for voting-based calculation
            has_turns = "turns" in round_data
            
            if has_turns and len(round_data.get("turns", {})) >= 2:  # Need at least generate (turn 0) and voting (turn 1)
                try:
                    # Initialize player round scores if they don't exist
                    for player in room.sid_to_players.keys():
                        if "round" not in room.player_state[player]:
                            room.player_state[player]["round"] = {}
                        if round_num not in room.player_state[player]["round"]:
                            room.player_state[player]["round"][round_num] = {
                                "choose": 0, "prompt": 0, "guess": 0, "total": 0
                            }
                    
                    # Get generate data (turn 0) and voting data (turn 1)
                    generate_data = round_data.get("turns", {}).get(0, {}).get("data", {})
                    voting_data = round_data.get("turns", {}).get(1, {}).get("data", {})
                    
                    print(f"Round {round_num} - Generate data players: {list(generate_data.keys())}")
                    print(f"Round {round_num} - Voting data structure: {list(voting_data.keys())}")
                    
                    # Calculate scores based on voting results
                    if generate_data and voting_data:
                        # Get vote counts for each player
                        vote_counts = voting_data.get("vote_counts", {})
                        
                        # collect all players' prompt tokens this round for penalty calculation
                        all_prompt_tokens = []
                        player_prompt_tokens = {}
                        
                        for player_sid, player_data in generate_data.items():
                            if "submitted_image" in player_data:
                                prompt = player_data.get("prompt", "")
                                tokens = calculate_prompt_tokens(prompt)
                                all_prompt_tokens.append(tokens)
                                player_prompt_tokens[player_sid] = tokens
                        
                        for player_sid in room.sid_to_players.keys():
                            # Reset scores for this round
                            room.player_state[player_sid]["round"][round_num] = {
                                "choose": 0, "prompt": 0, "guess": 0, "total": 0
                            }
                            
                            # Check if player generated an image this round
                            if player_sid in generate_data and "submitted_image" in generate_data[player_sid]:
                                prompt = generate_data[player_sid].get("prompt", "")
                                
                                # Get vote count for this player
                                votes = vote_counts.get(player_sid, [])
                                vote_count = len(votes)
                                
                                # Calculate score using new scoring logic
                                player_tokens = player_prompt_tokens[player_sid]
                                score_info = calculate_score(prompt, vote_count, all_prompt_tokens, player_tokens)
                                final_score = score_info["total_score"]
                                
                                # Assign the score (using "choose" field for compatibility)
                                room.player_state[player_sid]["round"][round_num]["choose"] = final_score
                                room.player_state[player_sid]["round"][round_num]["total"] = final_score
                                
                                print(f"Player {player_sid} Round {round_num}: tokens={player_tokens}, votes={vote_count}, penalty={score_info['penalty']}, score={final_score}")
                            else:
                                print(f"Player {player_sid} did not generate an image in round {round_num}")
                        
                        # Log round results after all players are processed
                        round_start_time = round_data.get("started_at")
                        round_end_time = round_data.get("ended_at")
                        round_duration = None
                        if round_start_time and round_end_time:
                            try:
                                start = datetime.fromisoformat(round_start_time.replace('Z', '+00:00'))
                                end = datetime.fromisoformat(round_end_time.replace('Z', '+00:00'))
                                round_duration = (end - start).total_seconds()
                            except:
                                pass
                        
                        # Get the actual reference image that was assigned to this round
                        reference_image = room.game_state["rounds"][round_num].get("reference_image", {}).copy()
                        
                        # Fallback to seed-based calculation if not found (shouldn't happen in normal games)
                        if not reference_image:
                            seed = hash(f"{room_id}_{round_num}") % len(REFERENCE_IMAGE_POOL)
                            reference_image = REFERENCE_IMAGE_POOL[seed].copy()
                        
                        # Build player results for logging
                        player_results_for_log = []
                        for player_sid in room.sid_to_players.keys():
                            player_name = room.sid_to_players[player_sid]
                            result = {
                                "player_sid": player_sid,
                                "player_name": player_name,
                                "prompt": "",
                                "image_url": None,
                                "prompt_tokens": [],
                                "votes_received": 0,
                                "score": 0
                            }
                            
                            if player_sid in generate_data and "submitted_image" in generate_data[player_sid]:
                                player_data = generate_data[player_sid]
                                result["prompt"] = player_data.get("prompt", "")
                                result["prompt_tokens"] = result["prompt"].split() if result["prompt"] else []
                                submitted_image = player_data.get("submitted_image", {})
                                result["image_url"] = process_image_url(submitted_image.get("url") or submitted_image.get("image_url"))
                                result["votes_received"] = len(vote_counts.get(player_sid, []))
                                result["score"] = room.player_state[player_sid]["round"][round_num]["total"]
                            
                            player_results_for_log.append(result)
                        
                        # Log round results (always log when we have valid data)
                        print(f"Logging round result for round {round_num} with {len(player_results_for_log)} players")
                        game_logger.log_round_result(
                            game_id=room_id,
                            round_num=round_num,
                            reference_image=reference_image,
                            player_results=player_results_for_log,
                            round_duration=round_duration
                        )
                    else:
                        print(f"Round {round_num}: Missing generate or voting data")
                        # Set default scores
                        for player_sid in room.sid_to_players.keys():
                            room.player_state[player_sid]["round"][round_num] = {
                                "choose": 0, "prompt": 0, "guess": 0, "total": 0
                            }
                        
                except Exception as e:
                    print(f"Error calculating results for round {round_num}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Set default scores on error
                    for player_sid in room.sid_to_players.keys():
                        if "round" not in room.player_state[player_sid]:
                            room.player_state[player_sid]["round"] = {}
                        room.player_state[player_sid]["round"][round_num] = {
                            "choose": 0, "prompt": 0, "guess": 0, "total": 0
                        }
                    continue
            else:
                print(f"Round {round_num}: Insufficient turn data")
                # Set default scores
                for player_sid in room.sid_to_players.keys():
                    if "round" not in room.player_state[player_sid]:
                        room.player_state[player_sid]["round"] = {}
                    room.player_state[player_sid]["round"][round_num] = {
                        "choose": 0, "prompt": 0, "guess": 0, "total": 0
                    }
    
    # Calculate total scores
    for player in room.player_state:
        total_score = 0
        for round_num in range(1, room.num_rounds + 1):
            if ("round" in room.player_state[player] and 
                round_num in room.player_state[player]["round"] and
                "total" in room.player_state[player]["round"][round_num]):
                total_score += room.player_state[player]["round"][round_num]["total"]
        room.player_state[player]["score"] = total_score
        print(f"Player {player} total score: {total_score}")
    
    print("Final player_state:")
    for player, state in room.player_state.items():
        print(f"{player}: {state.get('score', 0)} points")
    
    # Log final game results with optimized data structure
    optimized_final_scores = {}
    for player_sid, player_data in room.player_state.items():
        optimized_final_scores[player_sid] = {
            "player_name": room.sid_to_players.get(player_sid, f"Player {player_sid[:8]}"),
            "total_score": player_data.get("score", 0),
            "round_scores": {
                str(round_num): player_data.get("round", {}).get(round_num, {}).get("total", 0)
                for round_num in range(1, room.num_rounds + 1)
            }
        }
    
    game_logger.finalize_game_log(room_id, optimized_final_scores, game_completed=True)
    
    return {"player_state": room.player_state}


@router.get("/api/round-details")
async def get_round_details(room_id: str, round_num: int):
    """
    Get detailed information for a specific round including reference image, 
    generated images, prompts, tokens, and vote data.
    """
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}
    
    if round_num < 1 or round_num > room.num_rounds:
        return {"error": f"Invalid round number. Must be between 1 and {room.num_rounds}"}
    
    if round_num not in room.game_state.get("rounds", {}):
        return {"error": f"Round {round_num} data not found"}
    
    round_data = room.game_state["rounds"][round_num]
    
    # Get reference image for this round - use the actual image assigned during game
    if "reference_image" in round_data:
        reference_image = round_data["reference_image"]
        # Add category information if available
        if "category" in round_data:
            reference_image["category"] = round_data["category"]
    else:
        # Fallback to old system for compatibility
        seed = hash(f"{room_id}_{round_num}") % len(REFERENCE_IMAGE_POOL)
        reference_image = REFERENCE_IMAGE_POOL[seed]
    
    # Get generate data (turn 0) and voting data (turn 1)
    generate_data = round_data.get("turns", {}).get(0, {}).get("data", {})
    voting_data = round_data.get("turns", {}).get(1, {}).get("data", {})
    vote_counts = voting_data.get("vote_counts", {})
    
    # Debug: Print basic structure info
    print(f"Round {round_num}: Processing {len(vote_counts)} players with votes")
    
    # Build player results for this round
    player_results = []
    
    for player_sid, player_name in room.sid_to_players.items():
        player_result = {
            "sid": player_sid,
            "name": player_name,
            "prompt": "",
            "generated_image": None,
            "tokens": 0,
            "votes": 0,
            "voters": [],
            "score": 0
        }
        
        # Get generation data
        if player_sid in generate_data and "submitted_image" in generate_data[player_sid]:
            player_gen_data = generate_data[player_sid]
            player_result["prompt"] = player_gen_data.get("prompt", "")
            submitted_image = player_gen_data.get("submitted_image", {})
            # Normalize the image URL field name for frontend consistency
            if submitted_image and "url" in submitted_image:
                submitted_image["image_url"] = submitted_image["url"]
            player_result["generated_image"] = submitted_image
            player_result["tokens"] = calculate_prompt_tokens(player_result["prompt"])
        
        # Get voting data
        if player_sid in vote_counts:
            votes = vote_counts[player_sid]
            player_result["votes"] = len(votes)
            # Get voter names
            voter_names = []
            for voter_data in votes:
                # Handle both string SIDs and dict structures
                if isinstance(voter_data, dict):
                    voter_sid = voter_data.get("voter_sid", str(voter_data))
                else:
                    voter_sid = voter_data
                
                voter_name = room.sid_to_players.get(voter_sid, f"Player {voter_sid}")
                voter_names.append(voter_name)
            player_result["voters"] = voter_names
        
        # Get score from player_state
        if ("round" in room.player_state.get(player_sid, {}) and 
            round_num in room.player_state[player_sid]["round"]):
            player_result["score"] = room.player_state[player_sid]["round"][round_num].get("total", 0)
        
        player_results.append(player_result)
    
    # Sort by score descending
    player_results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "round_number": round_num,
        "reference_image": reference_image,
        "player_results": player_results
    }


# Admin authentication endpoints
@router.post("/api/admin/login")
async def admin_login(request: AdminLoginRequest):
    """Admin login endpoint"""
    if (request.username == ADMIN_CREDENTIALS["username"] and 
        request.password == ADMIN_CREDENTIALS["password"]):
        
        # Generate session token
        token = secrets.token_urlsafe(32)
        session = AdminSession(token, request.username)
        admin_sessions[token] = session
        
        # Clean up expired sessions
        expired_tokens = [t for t, s in admin_sessions.items() if not s.is_valid()]
        for t in expired_tokens:
            del admin_sessions[t]
        
        return {
            "success": True,
            "token": token,
            "expires_at": session.expires_at.isoformat()
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/api/admin/logout")
async def admin_logout(session: AdminSession = Depends(verify_admin_token)):
    """Admin logout endpoint"""
    if session.token in admin_sessions:
        del admin_sessions[session.token]
    return {"success": True, "message": "Logged out successfully"}

@router.get("/api/admin/verify")
async def verify_admin_session(session: AdminSession = Depends(verify_admin_token)):
    """Verify admin session is still valid"""
    return {
        "valid": True,
        "username": session.username,
        "expires_at": session.expires_at.isoformat()
    }

# Protected admin log endpoints
@router.get("/api/admin/export-logs")
async def export_logs(session: AdminSession = Depends(verify_admin_token)):
    """Export all game logs for analysis (Admin only)"""
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            if game_logger.export_logs_for_analysis(f.name):
                return FileResponse(
                    f.name, 
                    media_type='application/json',
                    filename=f"imaginaition_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
            else:
                return {"error": "Failed to export logs"}
    except Exception as e:
        return {"error": f"Error exporting logs: {str(e)}"}

@router.get("/api/admin/game-log/{game_id}")
async def get_game_log(game_id: str, session: AdminSession = Depends(verify_admin_token)):
    """Get logs for a specific game (Admin only)"""
    log_data = game_logger.get_game_log(game_id)
    if log_data:
        return log_data
    else:
        return {"error": "Game log not found"}

@router.get("/api/admin/list-game-logs")
async def list_game_logs(session: AdminSession = Depends(verify_admin_token)):
    """List all available game logs (Admin only)"""
    log_ids = game_logger.list_game_logs()
    return {"game_logs": log_ids}

@router.get("/api/admin/list-game-logs-detailed")
async def list_game_logs_detailed(session: AdminSession = Depends(verify_admin_token)):
    """List all available game logs with timestamps and metadata (Admin only)"""
    logs_info = game_logger.list_game_logs_with_timestamps()
    return {"game_logs": logs_info}

# Keep original endpoints for backward compatibility (will be deprecated)
@router.get("/api/export-logs")
async def export_logs_deprecated():
    """Export all game logs for analysis (DEPRECATED - use /api/admin/export-logs)"""
    raise HTTPException(status_code=401, detail="This endpoint requires admin authentication. Use /api/admin/export-logs")

@router.get("/api/game-log/{game_id}")
async def get_game_log_deprecated(game_id: str):
    """Get logs for a specific game (DEPRECATED - use /api/admin/game-log/{game_id})"""
    raise HTTPException(status_code=401, detail="This endpoint requires admin authentication. Use /api/admin/game-log/{game_id}")

@router.get("/api/list-game-logs")
async def list_game_logs_deprecated():
    """List all available game logs (DEPRECATED - use /api/admin/list-game-logs)"""
    raise HTTPException(status_code=401, detail="This endpoint requires admin authentication. Use /api/admin/list-game-logs")

@router.get("/api/list-game-logs-detailed")
async def list_game_logs_detailed_deprecated():
    """List all available game logs with timestamps and metadata (DEPRECATED - use /api/admin/list-game-logs-detailed)"""
    raise HTTPException(status_code=401, detail="This endpoint requires admin authentication. Use /api/admin/list-game-logs-detailed")

@router.get("/api/debug-game-state")
async def debug_game_state(room_id: str):
    """Debug endpoint to inspect game state structure"""
    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}
    
    debug_info = {
        "room_id": room_id,
        "current_round": room.game_state.get("current_round", "unknown"),
        "available_rounds": list(room.game_state.get("rounds", {}).keys()),
        "player_state_keys": {player: list(state.keys()) for player, state in room.player_state.items()},
    }
    
    # Check each round's structure
    for round_num in room.game_state.get("rounds", {}):
        round_data = room.game_state["rounds"][round_num]
        debug_info[f"round_{round_num}_structure"] = {
            "keys": list(round_data.keys()),
            "has_adjectives": "adjectives" in round_data,
            "has_turns": "turns" in round_data,
            "num_turns": len(round_data.get("turns", {})) if "turns" in round_data else 0,
        }
        
        if "turns" in round_data:
            for turn_num, turn_data in round_data["turns"].items():
                debug_info[f"round_{round_num}_turn_{turn_num}"] = {
                    "keys": list(turn_data.keys()) if turn_data else [],
                    "has_data": "data" in turn_data if turn_data else False,
                    "players_in_data": list(turn_data.get("data", {}).keys()) if turn_data and "data" in turn_data else [],
                }
    
    return debug_info


@sio.on("get-player-state")
async def get_player_state(sid):
    room_id = sid_to_room.get(sid)
    if not room_id:
        await sio.emit("error", {"message": "Player not in any room"}, room=sid)
        return
    
    room = room_manager.get_room(room_id)
    if not room:
        await sio.emit("error", {"message": "Room not found"}, room=sid)
        return
    
    # calculate_result(room_id)
    await sio.emit("player-state", {"player_state": room.player_state}, room=room_id)


@router.get("/api/sid-to-players")
async def get_sid_to_players(room_id: str):
    room = room_manager.get_room(room_id)
    return room.sid_to_players


@router.get("/api/player-to-sid")
async def get_player_to_sid(room_id: str):
    room = room_manager.get_room(room_id)
    if not room:
        return {}
    return room.players


@sio.on("get-round-info")
async def get_round_info(sid):
    room_id = sid_to_room.get(sid)
    if not room_id:
        await sio.emit("error", {"message": "Player not in any room"}, room=sid)
        return
    
    room = room_manager.get_room(room_id)
    if not room:
        await sio.emit("error", {"message": "Room not found"}, room=sid)
        return
    
    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]
    await sio.emit("round-info", {"round": current_round}, room=sid)


@router.get("/api/round-info")
async def round_info(room_id: str):
    room = room_manager.get_room(room_id)
    if not room:
        return {"round": 0, "turn": 0, "total_rounds": 6}
    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]
    total_rounds = room.num_rounds  # Include total rounds for dynamic button logic
    return {"round": current_round, "turn": current_turn, "total_rounds": total_rounds}

@router.post("/api/generate-quick-draw")
async def generate_quick_draw(request: dict):
    """Generate a Quick Draw image"""
    prompt = request.get("prompt", "").strip()
    room_id = request.get("room_id")
    sid = request.get("sid")

    if not prompt or not room_id or not sid:
        return {"error": "Missing required parameters"}

    # Capture prompt submission timestamp
    prompt_timestamp = datetime.utcnow().isoformat() + 'Z'

    # Use the player-supplied API key for this room (no silent server-key fallback)
    room = room_manager.get_room(room_id)
    api_key = resolve_room_api_key(room)
    if not api_key:
        return {"error": "No OpenAI API key provided for this room. Please enter your API key."}
    room_client = OpenAI(api_key=api_key)

    try:
        print(f"🎨 Generating quick draw for {sid}: '{prompt}'")

        # call the OpenAI API to generate an image
        response = room_client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="medium",
            n=1,
        )

        # Capture image generation completion timestamp
        image_generated_timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Handle both URL and base64 responses
        image_data = response.data[0]
        if image_data.url:
            # URL-based response (dall-e-3)
            # Store the quick draw result
            if room_id in room_manager.rooms:
                room = room_manager.rooms[room_id]
                player_name = room.sid_to_players.get(sid)
                if player_name:
                    if player_name not in room.quick_draw_results:
                        room.quick_draw_results[player_name] = []

                    quick_draw_data = {
                        "prompt": prompt,
                        "image_url": image_data.url,
                        "timestamp": time.time()
                    }
                    room.quick_draw_results[player_name].append(quick_draw_data)

                    # log the quick draw
                    prompt_tokens = prompt.split() if prompt else []
                    game_logger.log_quick_draw(
                        game_id=room_id,
                        player_sid=sid,
                        player_name=player_name,
                        prompt=prompt,
                        image_url=quick_draw_data["image_url"],
                        prompt_tokens=prompt_tokens,
                        generation_success=True,
                        prompt_timestamp=prompt_timestamp,
                        image_generated_timestamp=image_generated_timestamp
                    )
                    
                    # broadcast the new quick draw result to everyone in the room
                    print(f"🔊 Broadcasting quick draw update for {player_name} to room {room_id}")
                    try:
                        await sio.emit("quick_draw_update", {
                            "player_name": player_name,
                            "quick_draw": quick_draw_data
                        }, room=room_id)
                        print(f"✅ Quick draw update broadcast successfully for {player_name}")
                    except Exception as e:
                        print(f"❌ Failed to broadcast quick draw update: {e}")
            
            print(f"✅ Quick draw generated successfully: {image_data.url}")
            return {"image_url": image_data.url}
        elif image_data.b64_json:
            # Base64 response (gpt-image-1)
            # Get player name for filename generation
            player_name = "unknown"
            if room_id in room_manager.rooms:
                room = room_manager.rooms[room_id]
                player_name = room.sid_to_players.get(sid, f"Player{sid[:8]}")
            
            # Generate human-readable filename for quick draw
            timestamp = datetime.utcnow().isoformat() + 'Z'
            filename = generate_human_readable_filename(
                timestamp=timestamp,
                round_num=None,  # Quick draws are not tied to rounds
                player_name=player_name,
                action_type="quick_draw",
                prompt=prompt,
                extension="png"
            )
            
            # Handle filename collisions
            existing_files = set(os.listdir('generated_images')) if os.path.exists('generated_images') else set()
            filename = handle_filename_collision(filename, existing_files)
            
            filepath = os.path.join('generated_images', filename)
            
            # Decode and save base64 image
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(image_data.b64_json))
            
            # Store the quick draw result
            processed_url = process_image_url(filename)
            if room_id in room_manager.rooms:
                room = room_manager.rooms[room_id]
                player_name = room.sid_to_players.get(sid)
                if player_name:
                    if player_name not in room.quick_draw_results:
                        room.quick_draw_results[player_name] = []
                    
                    quick_draw_data = {
                        "prompt": prompt,
                        "image_url": processed_url,
                        "timestamp": time.time()
                    }
                    room.quick_draw_results[player_name].append(quick_draw_data)
                    
                    # log the quick draw
                    prompt_tokens = prompt.split() if prompt else []
                    game_logger.log_quick_draw(
                        game_id=room_id,
                        player_sid=sid,
                        player_name=player_name,
                        prompt=prompt,
                        image_url=quick_draw_data["image_url"],
                        prompt_tokens=prompt_tokens,
                        generation_success=True,
                        prompt_timestamp=prompt_timestamp,
                        image_generated_timestamp=image_generated_timestamp
                    )

                    # broadcast the new quick draw result to everyone in the room
                    print(f"🔊 Broadcasting quick draw update for {player_name} to room {room_id}")
                    try:
                        await sio.emit("quick_draw_update", {
                            "player_name": player_name,
                            "quick_draw": quick_draw_data
                        }, room=room_id)
                        print(f"✅ Quick draw update broadcast successfully for {player_name}")
                    except Exception as e:
                        print(f"❌ Failed to broadcast quick draw update: {e}")
            
            print(f"✅ Quick draw generated successfully: {filename}")
            return {"image_url": processed_url}
        else:
            raise ValueError("No image URL or base64 data found in response")
        
    except Exception as e:
        print(f"❌ Error generating quick draw: {e}")

        # log the failed quick draw
        if room_id in room_manager.rooms:
            room = room_manager.rooms[room_id]
            player_name = room.sid_to_players.get(sid)
            if player_name:
                prompt_tokens = prompt.split() if prompt else []
                game_logger.log_quick_draw(
                    game_id=room_id,
                    player_sid=sid,
                    player_name=player_name,
                    prompt=prompt,
                    image_url=None,
                    prompt_tokens=prompt_tokens,
                    generation_success=False,
                    prompt_timestamp=prompt_timestamp,
                    image_generated_timestamp=None,
                    error_message=str(e)
                )
        
        # Check if it's an API key error
        error_message = str(e)
        if "401" in error_message or "AuthenticationError" in str(type(e)) or "invalid_api_key" in error_message:
            return {"error": "Invalid OpenAI API key. Please check your API key."}
        else:
            return {"error": f"Failed to generate image: {str(e)}"}


@router.get("/api/quick-draw-results/{room_id}")
async def get_quick_draw_results(room_id: str):
    """Get Quick Draw results for all players in the room"""
    if room_id not in room_manager.rooms:
        return {"error": "Room not found"}
    
    room = room_manager.rooms[room_id]
    players_info = []
    
    for player_name in room.sid_to_players.values():
        results = room.quick_draw_results.get(player_name, [])
        players_info.append({
            "player_name": player_name,
            "quick_draws": results
        })
    
    return {"players": players_info}


@router.get("/api/current-player/{room_id}/{sid}")
async def get_current_player(room_id: str, sid: str):
    """Get the current user's player info"""
    if room_id not in room_manager.rooms:
        return {"error": "Room not found"}
    
    room = room_manager.rooms[room_id]
    player_name = room.sid_to_players.get(sid)
    
    if not player_name:
        return {"error": "Player not found"}
    
    return {"player_name": player_name}


def generate_export_filename(image_path: str, game_data: dict) -> str:
    """Generate human-readable filename for image exports based on game log data"""
    try:
        # Find the action or round result that corresponds to this image
        for action in game_data.get("player_actions", []):
            if action.get("image_url") == image_path:
                # Found matching action - generate filename based on action data
                timestamp = action.get("timestamp", "")
                round_num = action.get("round_num", 0)
                player_name = action.get("player_name", "unknown")
                action_type = action.get("action_type", "prompt")
                prompt = action.get("prompt", "")
                
                # Handle tutorial round (0) and regular rounds
                display_round = 0 if round_num == 0 else round_num  # Pass 0 for tutorial, will be handled in generate_human_readable_filename
                
                return generate_human_readable_filename(
                    timestamp=timestamp,
                    round_num=display_round if display_round >= 0 else None,
                    player_name=player_name,
                    action_type=action_type,
                    prompt=prompt,
                    extension="png"
                )
        
        # Check round results for reference images or player results
        for round_result in game_data.get("round_results", []):
            round_num = round_result.get("round_num", 0)
            
            # Check reference image
            ref_image = round_result.get("reference_image", {})
            if ref_image.get("image_path") == image_path:
                # This is a reference image - handle tutorial round
                round_str = "tutorial" if round_num == 0 else f"round{round_num}"
                return f"ref-{round_str}-{ref_image.get('description', 'reference').lower().replace(' ', '_')}.jpg"
            
            # Check player results
            for player_result in round_result.get("player_results", []):
                if player_result.get("image_url") == image_path:
                    player_name = player_result.get("player_name", "unknown")
                    prompt = player_result.get("prompt", "")
                    
                    # Create timestamp for round result (if not available, use current time)
                    timestamp = datetime.utcnow().isoformat() + 'Z'
                    
                    return generate_human_readable_filename(
                        timestamp=timestamp,
                        round_num=round_num,
                        player_name=player_name,
                        action_type="prompt",
                        prompt=prompt,
                        extension="png"
                    )
        
        # If no match found, return None to use fallback
        return None
        
    except Exception as e:
        print(f"Error generating export filename for {image_path}: {e}")
        return None


@router.get("/api/export-game/{game_id}")
async def export_game_data(game_id: str, token: str = None):
    """Export game data and images as a ZIP file"""
    # verify the admin token
    if not token:
        return {"error": "Admin token required"}
    
    # check the admin session
    if token not in admin_sessions:
        return {"error": "Invalid admin token"}
    
    session = admin_sessions[token]
    if not session.is_valid():
        del admin_sessions[token]
        return {"error": "Admin token expired"}
    
    import zipfile
    import io
    import os
    import shutil
    import tempfile
    import json
    from pathlib import Path
    
    try:
        # find the game log file
        logs_dir = Path("logs/games")
        print(f"🔍 Looking for game {game_id} in {logs_dir.absolute()}")
        log_files = list(logs_dir.glob(f"*_game_{game_id}.json"))
        print(f"📁 Found {len(log_files)} matching files: {[f.name for f in log_files]}")
        
        if not log_files:
            return {"error": f"Game {game_id} not found"}
        
        log_file = log_files[0]
        
        # read the game log
        with open(log_file, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        
        # create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # collect all image paths
            image_paths = set()
            
            # collect images only from player_actions (covers all generated images and quick draws)
            for action in game_data.get("player_actions", []):
                if action.get("action_type") in ["image_generation", "quick_draw"]:
                    if "image_url" in action and action["image_url"]:
                        image_paths.add(action["image_url"])
                    if "reference_image_path" in action and action["reference_image_path"]:
                        image_paths.add(action["reference_image_path"])
            
            # collect reference images from round_results (these may not be in player_actions)
            for round_result in game_data.get("round_results", []):
                ref_image = round_result.get("reference_image", {})
                if "image_path" in ref_image:
                    image_paths.add(ref_image["image_path"])
            
            # normalize the path and copy the image
            images_dir = temp_path / "images"
            images_dir.mkdir()
            
            path_mapping = {}  # mapping of old path -> new path
            
            for image_path in image_paths:
                if not image_path:
                    continue
                
                # normalize the path
                normalized_path = normalize_image_path(image_path)
                local_file_path = get_local_file_path(normalized_path)
                
                if os.path.exists(local_file_path):
                    # Try to generate human-readable filename for export
                    human_filename = generate_export_filename(image_path, game_data)
                    if not human_filename:
                        # Fallback to original filename
                        human_filename = os.path.basename(local_file_path)
                    
                    # Handle collisions in export directory
                    export_files = set(os.listdir(images_dir)) if os.path.exists(images_dir) else set()
                    human_filename = handle_filename_collision(human_filename, export_files)
                    
                    new_path = f"images/{human_filename}"
                    
                    # copy the file
                    shutil.copy2(local_file_path, images_dir / human_filename)
                    path_mapping[image_path] = new_path
                    print(f"📁 Renamed {os.path.basename(local_file_path)} -> {human_filename}")
                else:
                    print(f"Warning: Image not found: {local_file_path}")
            
            # update paths in the game data
            updated_game_data = update_image_paths_in_data(game_data, path_mapping)
            
            # save the updated JSON
            json_file = temp_path / f"game_{game_id}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(updated_game_data, f, indent=2, ensure_ascii=False)
            
            # create the ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # add the JSON file
                zip_file.write(json_file, f"game_{game_id}.json")
                
                # add all images
                for image_file in images_dir.iterdir():
                    zip_file.write(image_file, f"images/{image_file.name}")
            
            zip_buffer.seek(0)
            
            # return the ZIP file
            from fastapi.responses import Response
            return Response(
                content=zip_buffer.getvalue(),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename=game_{game_id}_export.zip"}
            )
            
    except Exception as e:
        print(f"Error exporting game {game_id}: {e}")
        return {"error": f"Failed to export game: {str(e)}"}


@router.post("/api/tutorial-generate-images")
async def tutorial_generate_images(request: dict):
    """Image-generation endpoint dedicated to the tutorial"""
    prompt = request.get("prompt", "").strip()
    api_key = request.get("api_key", "").strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    try:
        # create the OpenAI client
        client = OpenAI(api_key=api_key)

        # generate image
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="medium",
            n=1,
        )

        # handle the response
        image_data = response.data[0]
        if image_data.url:
            # URL-based response
            return {"image_url": image_data.url}
        elif image_data.b64_json:
            # Base64 response - convert to data URL for tutorial use
            import base64
            image_b64 = image_data.b64_json
            data_url = f"data:image/png;base64,{image_b64}"
            return {"image_url": data_url}
        else:
            raise HTTPException(status_code=500, detail="No image URL or base64 data returned")

    except Exception as e:
        print(f"Error in tutorial image generation: {e}")
        if "api_key" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(status_code=401, detail="Invalid API key")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/api/tutorial-quick-draw")
async def tutorial_quick_draw(request: dict):
    """Quick Draw endpoint dedicated to the tutorial"""
    prompt = request.get("prompt", "").strip()
    api_key = request.get("api_key", "").strip()

    if not prompt:
        return {"error": "Prompt is required"}

    if not api_key:
        return {"error": "API key is required"}

    try:
        # create the OpenAI client
        client = OpenAI(api_key=api_key)

        # generate image
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="medium",
            n=1,
        )

        # handle the response
        image_data = response.data[0]
        if image_data.url:
            # URL-based response
            return {"image_url": image_data.url}
        elif image_data.b64_json:
            # Base64 response - convert to data URL for tutorial use
            import base64
            image_b64 = image_data.b64_json
            data_url = f"data:image/png;base64,{image_b64}"
            return {"image_url": data_url}
        else:
            return {"error": "No image URL or base64 data returned"}

    except Exception as e:
        print(f"Error in tutorial quick draw: {e}")
        if "api_key" in str(e).lower() or "unauthorized" in str(e).lower():
            return {"error": "Invalid API key"}
        return {"error": f"Image generation failed: {str(e)}"}


def normalize_image_path(path: str) -> str:
    """Normalize an image path"""
    if not path:
        return ""
    
    # strip the URL prefix
    if path.startswith("http://") or path.startswith("https://"):
        # extract the path portion
        from urllib.parse import urlparse
        parsed = urlparse(path)
        path = parsed.path
    
    # ensure it starts with /
    if not path.startswith("/"):
        path = "/" + path
    
    return path


def get_local_file_path(normalized_path: str) -> str:
    """Convert a normalized path to a local file path"""
    # remove the leading /
    if normalized_path.startswith("/"):
        normalized_path = normalized_path[1:]
    
    # determine the local path based on the path type
    if normalized_path.startswith("static/reference_images/"):
        # Reference images
        return normalized_path.replace("static/", "")
    elif normalized_path.startswith("generated_images/"):
        # Generated images
        return normalized_path
    else:
        # may be a bare filename; assume it lives in the generated_images directory
        filename = os.path.basename(normalized_path)
        return f"generated_images/{filename}"


def update_image_paths_in_data(data: dict, path_mapping: dict) -> dict:
    """Recursively update image paths in the data"""
    if isinstance(data, dict):
        updated = {}
        for key, value in data.items():
            if key in ["image_url", "image_path", "reference_image_path"] and value in path_mapping:
                updated[key] = path_mapping[value]
            else:
                updated[key] = update_image_paths_in_data(value, path_mapping)
        return updated
    elif isinstance(data, list):
        return [update_image_paths_in_data(item, path_mapping) for item in data]
    else:
        return data


@sio.on("timer-start")
async def timer_start(sid):
    room_id = sid_to_room.get(sid)
    if not room_id:
        await sio.emit("error", {"message": "Player not in any room"}, room=sid)
        return
    
    room = room_manager.get_room(room_id)
    if not room:
        await sio.emit("error", {"message": "Room not found"}, room=sid)
        return
    
    current_round = room.game_state["current_round"]
    current_turn = room.game_state["current_turn"]
    await sio.emit("timer-started", {"time_limit": room.game_state["rounds"][current_round]["turns"][current_turn]["time_limit"]}, room=room_id)

# ------------------------------
#  REGISTER API ROUTES FIRST
# ------------------------------
app.include_router(router)

# ------------------------------
#  MOUNT STATIC FILES LAST
# ------------------------------
# In our Docker setup, Nginx serves the frontend, so we don't need this
# if os.getenv("ENVIRONMENT") == "production":
#     app.mount("/", StaticFiles(directory="frontend-dist",
#               html=True), name="frontend")

# ------------------------------
#  START FASTAPI SERVER
# ------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True, log_level="debug")
