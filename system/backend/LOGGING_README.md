# ImaginAItion Game Logging System

This document describes the comprehensive logging system implemented for the ImaginAItion game to track user behavior and game events for research purposes.

## Overview

The logging system captures all important game events including:
- Game start/end timestamps
- Image generation attempts (prompts, images, timestamps)
- Voting behavior (who voted for whom, when)
- Round results with scores and performance metrics
- Complete game scoreboard data that can recreate any game state

## System Architecture

### Core Components

1. **`logger.py`** - Main logging utility with data models and functions
2. **`logs/games/`** - Directory where all game logs are stored
3. **API endpoints** - For retrieving and exporting logs

### Data Models

#### GameSessionLog
- `game_id`: Unique identifier for the game
- `start_timestamp`/`end_timestamp`: Game duration tracking
- `players`: Mapping of player SIDs to names
- `game_completed`: Whether the game finished normally
- `final_scores`: Complete scoring breakdown
- `round_results`: Results for each round
- `player_actions`: All individual player actions

#### Player Actions
- **ImageGenerationLog**: Prompt, generated image URL, tokens, success/failure
- **VoteLog**: Voter, target, timestamp
- **RoundResult**: Reference image, player results, duration

## Integration Points

The logging system is integrated at these key points in `main.py`:

1. **Game Start** (`handle_players` function): Initializes game log when all players join
2. **Image Generation** (`generate_image_for_player` function): Logs all generation attempts
3. **Voting** (`vote_for_image` function): Records all votes in real-time  
4. **Round Results** (`get_game_results` function): Logs complete round data
5. **Game End** (`get_game_results` function): Finalizes log with final scores

## API Endpoints

### Game Log Management
- `GET /api/list-game-logs` - List all available game log IDs
- `GET /api/list-game-logs-detailed` - List logs with timestamps, file sizes, and metadata
- `GET /api/game-log/{game_id}` - Retrieve specific game log
- `GET /api/export-logs` - Export all logs as JSON for analysis

### Usage Examples

```bash
# List all games (just IDs)
curl http://localhost:5001/api/list-game-logs

# List all games with timestamps and metadata
curl http://localhost:5001/api/list-game-logs-detailed

# Get specific game log
curl http://localhost:5001/api/game-log/room_abc123

# Export all logs for analysis
curl http://localhost:5001/api/export-logs -o game_logs.json
```

## Log File Structure

Each game creates a timestamped JSON file in `logs/games/YYYYMMDD_HHMMSS_game_{game_id}.json` with this structure:

### File Naming Convention
- **Format**: `YYYYMMDD_HHMMSS_game_{game_id}.json`
- **Example**: `20250815_163044_game_room_abc123.json`
- **Benefits**: 
  - ✅ **Chronological auto-sorting** in file browsers
  - ✅ **No filename collisions** (timestamp uniqueness)
  - ✅ **Easy batch processing** by date ranges
  - ✅ **Game ID preservation** for direct lookup

```json
{
  "game_id": "room_abc123",
  "start_timestamp": "2025-08-15T16:15:23.123456Z",
  "end_timestamp": "2025-08-15T16:25:45.789012Z", 
  "players": {
    "player_sid_1": "Alice",
    "player_sid_2": "Bob",
    "player_sid_3": "Charlie"
  },
  "total_rounds": 3,
  "game_completed": true,
  "final_scores": {
    "player_sid_1": {
      "score": 7,
      "round": {
        "1": {"total": 2, "choose": 2, "prompt": 0, "guess": 0},
        "2": {"total": 3, "choose": 3, "prompt": 0, "guess": 0},
        "3": {"total": 2, "choose": 2, "prompt": 0, "guess": 0}
      }
    }
  },
  "round_results": [
    {
      "round_num": 1,
      "reference_image": {
        "id": 5,
        "image_path": "/static/reference_images/happy_cat.png",
        "description": "A happy cat"
      },
      "player_results": [
        {
          "player_sid": "player_sid_1",
          "player_name": "Alice", 
          "prompt": "a fluffy orange cat sitting happily",
          "image_url": "https://example.com/generated_image.png",
          "prompt_tokens": ["a", "fluffy", "orange", "cat", "sitting", "happily"],
          "votes_received": 2,
          "score": 2
        }
      ],
      "round_duration": 95.5
    }
  ],
  "player_actions": [
    {
      "timestamp": "2025-08-15T16:16:00.123456Z",
      "game_id": "room_abc123",
      "round_num": 1,
      "turn_num": 0,
      "player_sid": "player_sid_1",
      "player_name": "Alice",
      "action_type": "image_generation",
      "prompt": "a fluffy orange cat sitting happily",
      "image_url": "https://example.com/generated_image.png",
      "prompt_tokens": ["a", "fluffy", "orange", "cat", "sitting", "happily"],
      "reference_image_id": 5,
      "reference_image_path": "/static/reference_images/happy_cat.png",
      "reference_description": "A happy cat",
      "generation_success": true
    },
    {
      "timestamp": "2025-08-15T16:17:30.456789Z",
      "game_id": "room_abc123", 
      "round_num": 1,
      "turn_num": 1,
      "player_sid": "player_sid_2",
      "player_name": "Bob",
      "action_type": "vote",
      "voted_for_sid": "player_sid_1",
      "voted_for_name": "Alice",
      "vote_timestamp": "2025-08-15T16:17:30.456789Z"
    }
  ]
}
```

## Research Analysis 

### Data Available for Analysis
- **Prompt Strategy**: Analysis of prompt length, complexity, keyword usage
- **Voting Patterns**: Who votes for whom, voting timing, consensus analysis
- **Performance Metrics**: Score correlation with prompt tokens, round duration impact
- **Image Generation**: Success rates, prompt-to-image quality correlation

### Recreating Game States
The logs contain complete information to recreate any game's scoreboard:
- All prompts and generated images
- Complete voting records
- Round-by-round score calculations
- Final leaderboard with detailed breakdown

## Security & Privacy

- Logs are stored locally in the backend only
- No personally identifiable information is stored beyond game session player names
- Image URLs are logged but actual image data is not duplicated
- Logs can be safely exported for research without exposing sensitive data

## Maintenance

### Log File Management
- Each game creates one JSON file (~2-10KB depending on game length)
- No automatic cleanup - logs persist for manual analysis
- Export functionality allows bulk data extraction

### Monitoring
- Check `logs/games/` directory size periodically
- Monitor for any failed log writes (logged to console)
- Verify log integrity using the built-in test system
