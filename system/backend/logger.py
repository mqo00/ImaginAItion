"""
Game Logging System for ImaginAItion
Logs all game events, player actions, and results for research analysis
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import uuid


@dataclass
class PlayerAction:
    """Base class for player actions"""
    timestamp: str
    game_id: str
    round_num: int
    turn_num: int
    player_sid: str
    player_name: str
    action_type: str


@dataclass
class ImageGenerationLog(PlayerAction):
    """Log data for image generation events"""
    prompt: str
    image_url: Optional[str]
    prompt_tokens: List[str]
    reference_image_id: Optional[int]
    reference_image_path: Optional[str]
    reference_description: Optional[str]
    generation_success: bool
    prompt_timestamp: Optional[str] = None  # Timestamp when player submitted prompt
    image_generated_timestamp: Optional[str] = None  # Timestamp when image returned from model
    error_message: Optional[str] = None


@dataclass
class VoteLog(PlayerAction):
    """Log data for voting events"""
    voted_for_sid: str
    voted_for_name: str
    vote_timestamp: str


@dataclass
class QuickDrawLog(PlayerAction):
    """Log data for quick draw events"""
    prompt: str
    image_url: Optional[str]
    prompt_tokens: List[str]
    generation_success: bool
    prompt_timestamp: Optional[str] = None  # Timestamp when player submitted prompt
    image_generated_timestamp: Optional[str] = None  # Timestamp when image returned from model
    error_message: Optional[str] = None


@dataclass
class RoundResult:
    """Round result data structure"""
    round_num: int
    reference_image: Dict[str, Any]
    player_results: List[Dict[str, Any]]
    round_duration: Optional[float] = None


@dataclass
class GameSessionLog:
    """Complete game session log"""
    game_id: str
    start_timestamp: str
    end_timestamp: Optional[str]
    players: Dict[str, str]  # sid -> name mapping
    total_rounds: int
    game_completed: bool
    final_scores: Dict[str, Dict[str, Any]]
    round_results: List[RoundResult]
    player_actions: List[Dict[str, Any]]  # All player actions


def sanitize_filename_component(text: str, max_length: int = 20) -> str:
    """Sanitize a string to be safe for use in filenames"""
    if not text:
        return "unknown"
    
    # Convert to lowercase and replace spaces with underscores
    text = text.lower().replace(' ', '_')
    
    # Remove special characters, keep only alphanumeric and underscores
    text = re.sub(r'[^a-z0-9_]', '', text)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Ensure it's not empty after sanitization
    return text if text else "unknown"


def extract_first_tokens(prompt: str, num_tokens: int = 3) -> str:
    """Extract first N tokens from a prompt for filename"""
    if not prompt:
        return "unknown"
    
    tokens = prompt.strip().split()
    first_tokens = tokens[:num_tokens]
    
    # Join with underscores and sanitize
    result = '_'.join(first_tokens)
    return sanitize_filename_component(result, max_length=30)


def generate_human_readable_filename(
    timestamp: Optional[str] = None,
    round_num: Optional[int] = None,
    player_name: Optional[str] = None,
    action_type: str = "prompt",  # "prompt" or "quickdraw"
    prompt: Optional[str] = None,
    extension: str = "png"
) -> str:
    """
    Generate human-readable filename for images
    Format: {timestamp}-img-{roundnum}-{playername}-{prompt/quickdraw}-{first3_prompt_tokens}.png
    """
    
    # Generate timestamp if not provided
    if not timestamp:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    else:
        # Convert ISO timestamp to filename format
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            timestamp = dt.strftime('%Y%m%d_%H%M%S')
        except:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    # Sanitize components - handle tutorial round (0) specially
    if round_num == 0:
        round_str = "tutorial"
    elif round_num is not None:
        round_str = str(round_num)
    else:
        round_str = "x"
    
    player_str = sanitize_filename_component(player_name, max_length=15)
    action_str = "quickdraw" if action_type == "quick_draw" else "prompt"
    prompt_tokens = extract_first_tokens(prompt)
    
    # Construct filename
    filename = f"{timestamp}-img-{round_str}-{player_str}-{action_str}-{prompt_tokens}.{extension}"
    
    return filename


def handle_filename_collision(base_filename: str, existing_files: set) -> str:
    """Handle filename collisions by appending a counter"""
    if base_filename not in existing_files:
        return base_filename
    
    # Extract extension
    parts = base_filename.rsplit('.', 1)
    if len(parts) == 2:
        name, ext = parts
        extension = f".{ext}"
    else:
        name = base_filename
        extension = ""
    
    # Try with counters
    counter = 1
    while True:
        new_filename = f"{name}_{counter:02d}{extension}"
        if new_filename not in existing_files:
            return new_filename
        counter += 1
        if counter > 99:  # Safety limit
            break
    
    # Fallback to UUID if we can't find a unique name
    uuid_suffix = uuid.uuid4().hex[:8]
    return f"{name}_{uuid_suffix}{extension}"


class GameLogger:
    """Main logging utility class"""
    
    def __init__(self, logs_directory: str = "logs/games"):
        self.logs_directory = os.path.abspath(logs_directory)
        print(f"🗂️  Initializing GameLogger with directory: {self.logs_directory}")
        
        try:
            os.makedirs(self.logs_directory, exist_ok=True)
            print(f"✅ Created/verified logs directory: {self.logs_directory}")
            
            # Test write permissions
            test_file = os.path.join(self.logs_directory, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"✅ Write permissions verified for: {self.logs_directory}")
            
        except Exception as e:
            print(f"❌ ERROR: Failed to initialize logs directory: {e}")
            print(f"❌ Current working directory: {os.getcwd()}")
            print(f"❌ Directory path: {self.logs_directory}")
            raise
        
    def _get_timestamp(self) -> str:
        """Get ISO formatted timestamp"""
        return datetime.utcnow().isoformat() + 'Z'
    
    def _get_log_filename(self, game_id: str) -> str:
        """Generate log filename for a game with timestamp prefix for auto-sorting"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        return os.path.join(self.logs_directory, f"{timestamp}_game_{game_id}.json")
    
    def start_game_log(self, game_id: str, players: Dict[str, str]) -> None:
        """Initialize a new game log"""
        log_data = GameSessionLog(
            game_id=game_id,
            start_timestamp=self._get_timestamp(),
            end_timestamp=None,
            players=players.copy(),
            total_rounds=3,
            game_completed=False,
            final_scores={},
            round_results=[],
            player_actions=[]
        )
        
        self._write_log(game_id, log_data)
    
    def log_image_generation(self, game_id: str, round_num: int, turn_num: int,
                           player_sid: str, player_name: str, prompt: str,
                           image_url: Optional[str], prompt_tokens: List[str],
                           reference_image_id: Optional[int] = None,
                           reference_image_path: Optional[str] = None,
                           reference_description: Optional[str] = None,
                           generation_success: bool = True,
                           prompt_timestamp: Optional[str] = None,
                           image_generated_timestamp: Optional[str] = None,
                           error_message: Optional[str] = None) -> None:
        """Log image generation event"""

        action = ImageGenerationLog(
            timestamp=self._get_timestamp(),
            game_id=game_id,
            round_num=round_num,
            turn_num=turn_num,
            player_sid=player_sid,
            player_name=player_name,
            action_type="image_generation",
            prompt=prompt,
            image_url=image_url,
            prompt_tokens=prompt_tokens,
            reference_image_id=reference_image_id,
            reference_image_path=reference_image_path,
            reference_description=reference_description,
            generation_success=generation_success,
            prompt_timestamp=prompt_timestamp,
            image_generated_timestamp=image_generated_timestamp,
            error_message=error_message
        )

        self._append_action(game_id, action)
    
    def log_vote(self, game_id: str, round_num: int, turn_num: int,
                 voter_sid: str, voter_name: str, voted_for_sid: str, 
                 voted_for_name: str) -> None:
        """Log voting event"""
        
        action = VoteLog(
            timestamp=self._get_timestamp(),
            game_id=game_id,
            round_num=round_num,
            turn_num=turn_num,
            player_sid=voter_sid,
            player_name=voter_name,
            action_type="vote",
            voted_for_sid=voted_for_sid,
            voted_for_name=voted_for_name,
            vote_timestamp=self._get_timestamp()
        )
        
        self._append_action(game_id, action)
    
    def log_quick_draw(self, game_id: str, player_sid: str, player_name: str,
                      prompt: str, image_url: Optional[str], prompt_tokens: List[str],
                      generation_success: bool = True,
                      prompt_timestamp: Optional[str] = None,
                      image_generated_timestamp: Optional[str] = None,
                      error_message: Optional[str] = None) -> None:
        """Log quick draw event"""

        action = QuickDrawLog(
            timestamp=self._get_timestamp(),
            game_id=game_id,
            round_num=-1,  # Quick draws are not tied to specific rounds
            turn_num=-1,   # Quick draws are not tied to specific turns
            player_sid=player_sid,
            player_name=player_name,
            action_type="quick_draw",
            prompt=prompt,
            image_url=image_url,
            prompt_tokens=prompt_tokens,
            generation_success=generation_success,
            prompt_timestamp=prompt_timestamp,
            image_generated_timestamp=image_generated_timestamp,
            error_message=error_message
        )

        self._append_action(game_id, action)
    
    def log_round_result(self, game_id: str, round_num: int, 
                        reference_image: Dict[str, Any],
                        player_results: List[Dict[str, Any]],
                        round_duration: Optional[float] = None) -> None:
        """Log complete round results (prevents duplicates)"""
        
        print(f"📊 Attempting to log round result: game={game_id}, round={round_num}, players={len(player_results)}")
        
        # Check if this round has already been logged
        log_data = self._load_log(game_id)
        if log_data:
            existing_rounds = [r.get("round_num") for r in log_data.round_results]
            print(f"📊 Existing rounds: {existing_rounds}")
            if round_num in existing_rounds:
                print(f"⚠️  Round {round_num} already logged for game {game_id}, skipping duplicate")
                return
        else:
            print(f"⚠️  No existing log data found for game {game_id}")
        
        round_result = RoundResult(
            round_num=round_num,
            reference_image=reference_image,
            player_results=player_results,
            round_duration=round_duration
        )
        
        print(f"📊 Creating round result: {round_result}")
        self._append_round_result(game_id, round_result)
        print(f"✅ Round {round_num} logged successfully for game {game_id}")
    
    def finalize_game_log(self, game_id: str, final_scores: Dict[str, Dict[str, Any]],
                         game_completed: bool = True) -> None:
        """Finalize game log with final scores"""
        log_data = self._load_log(game_id)
        if log_data:
            log_data.end_timestamp = self._get_timestamp()
            log_data.final_scores = final_scores
            log_data.game_completed = game_completed
            self._write_log(game_id, log_data)
    
    def _find_log_file(self, game_id: str) -> Optional[str]:
        """Find existing log file by game_id"""
        if not os.path.exists(self.logs_directory):
            return None
        
        # Look for files ending with _game_{game_id}.json
        for filename in os.listdir(self.logs_directory):
            if filename.endswith(f'_game_{game_id}.json'):
                return os.path.join(self.logs_directory, filename)
        return None
    
    def _load_log(self, game_id: str) -> Optional[GameSessionLog]:
        """Load existing log data"""
        # First try to find existing file
        filename = self._find_log_file(game_id)
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return GameSessionLog(**data)
            except Exception as e:
                print(f"Error loading log for game {game_id}: {e}")
        return None
    
    def _write_log(self, game_id: str, log_data: GameSessionLog) -> None:
        """Write log data to file"""
        # For updates, use existing file; for new logs, create timestamped file
        existing_file = self._find_log_file(game_id)
        if existing_file:
            filename = existing_file
        else:
            filename = self._get_log_filename(game_id)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(asdict(log_data), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing log for game {game_id}: {e}")
    
    def _append_action(self, game_id: str, action: PlayerAction) -> None:
        """Append action to existing log"""
        log_data = self._load_log(game_id)
        if log_data:
            log_data.player_actions.append(asdict(action))
            self._write_log(game_id, log_data)
    
    def _append_round_result(self, game_id: str, round_result: RoundResult) -> None:
        """Append round result to existing log"""
        log_data = self._load_log(game_id)
        if log_data:
            log_data.round_results.append(asdict(round_result))
            self._write_log(game_id, log_data)
    
    def get_game_log(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve complete game log"""
        log_data = self._load_log(game_id)
        return asdict(log_data) if log_data else None
    
    def get_log_filepath(self, game_id: str) -> Optional[str]:
        """Get the full file path for a game log"""
        return self._find_log_file(game_id)
    
    def list_game_logs(self) -> List[str]:
        """List all available game log IDs (sorted chronologically by timestamp)"""
        if not os.path.exists(self.logs_directory):
            return []
        
        log_files = [f for f in os.listdir(self.logs_directory) if '_game_' in f and f.endswith('.json')]
        # Sort by filename (timestamp prefix ensures chronological order)
        log_files.sort()
        
        # Extract game IDs from filenames (format: YYYYMMDD_HHMMSS_game_{game_id}.json)
        game_ids = []
        for filename in log_files:
            if '_game_' in filename:
                # Split on '_game_' and take the part after it, then remove .json
                game_id = filename.split('_game_', 1)[1].replace('.json', '')
                game_ids.append(game_id)
        
        return game_ids
    
    def list_game_logs_with_timestamps(self) -> List[Dict[str, str]]:
        """List all available game logs with timestamps and metadata"""
        if not os.path.exists(self.logs_directory):
            return []
        
        log_files = [f for f in os.listdir(self.logs_directory) if '_game_' in f and f.endswith('.json')]
        log_files.sort()  # Chronological order
        
        logs_info = []
        for filename in log_files:
            if '_game_' in filename:
                # Extract timestamp and game_id
                parts = filename.split('_game_', 1)
                timestamp_str = parts[0]
                game_id = parts[1].replace('.json', '')
                
                # Get file modification time as backup
                filepath = os.path.join(self.logs_directory, filename)
                mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                # Read actual start_timestamp from log data
                start_timestamp = None
                end_timestamp = None
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                        start_timestamp = log_data.get('start_timestamp')
                        end_timestamp = log_data.get('end_timestamp')
                except Exception as e:
                    print(f"Error reading log file {filename}: {e}")
                
                logs_info.append({
                    "game_id": game_id,
                    "timestamp": timestamp_str,
                    "start_timestamp": start_timestamp,
                    "end_timestamp": end_timestamp,
                    "filename": filename,
                    "modified": mod_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "size_bytes": os.path.getsize(filepath)
                })
        
        return logs_info
    
    def export_logs_for_analysis(self, output_path: str) -> bool:
        """Export all logs in a format suitable for analysis"""
        try:
            all_logs = []
            for game_id in self.list_game_logs():
                log_data = self.get_game_log(game_id)
                if log_data:
                    all_logs.append(log_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_logs, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting logs: {e}")
            return False


# Global logger instance
game_logger = GameLogger()