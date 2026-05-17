# LoL Insight Analysis Service

## 1. Project Purpose

This project is a portfolio project for a game data analyst role.

The goal is to build a web service that uses Riot API data to analyze League of Legends player behavior and provide clear, practical insights for improvement.

This should not be a simple match history website.  
It should be a data analysis service that turns match and timeline data into actionable feedback.

## 2. Target Company / Job Relevance

The project is designed to demonstrate skills relevant to a game data analyst role:

- Game player behavior analysis
- Business / service decision metric design
- SQL-based data analysis
- Data visualization and BI reporting
- Data-driven improvement suggestions
- User-facing insight delivery
- Patch / update performance analysis

## 3. Persona

The target user is:

> A League of Legends player who wants to improve but does not know exactly what they are doing well or poorly.

The service should help the user answer:

- Which champions am I good at?
- Against which opponents should I pick certain champions?
- Which champions should I practice next?
- Am I weak in laning, objectives, teamfights, or side-lane play?
- What should I focus on in the next game?

## 4. Tech Stack

Backend:
- Django
- Django REST Framework
- PostgreSQL

Frontend:
- Vue.js

Data / Analysis:
- Riot API
- SQL
- Python
- Power BI

Future optional:
- Redis
- Celery
- Scheduled data collection

## 5. MVP Scope

The first MVP should focus on recent ranked match analysis.

Input:
- Riot ID
- Tagline
- Region

Output:
- Recent match summary
- Champion performance summary
- Champion matchup insights
- Phase-based feedback
- Improvement recommendations

## 6. Core Analysis Areas

### 6.1 Basic Player Summary

Metrics:
- Recent N-game win rate
- Average KDA
- Average CS
- Average gold
- Average deaths
- Main position
- Champion pool
- Champion-specific win rate
- Win/loss difference indicators

### 6.2 Champion Pick Insight

The service should recommend:

1. Champions the user already performs well on
2. Opponent champions the user performs well against
3. Opponent champions the user struggles against
4. Champions the user should practice based on playstyle

Example feedback:

> Your Ahri win rate is high when facing melee assassins, but your CS difference drops against long-range poke champions. Consider picking Ahri as a counter-pick rather than blind-picking her.

### 6.3 Phase-Based Feedback

Game phases:

- 0–14 minutes: laning phase
- 14–25 minutes: mid-game / objective setup
- 25+ minutes: late-game / teamfight / side-lane

Metrics:

Laning:
- CS difference at 10 minutes
- Gold difference at 10 minutes
- XP difference at 10 minutes
- Deaths before 14 minutes

Objective:
- Deaths within 60 seconds before dragon, herald, baron
- Objective participation
- Vision score before objectives

Teamfight:
- Kill participation
- Teamfight survival
- Damage contribution
- Participation in multi-kill events

Side-lane:
- Deaths after 14 minutes in side areas
- CS gained in side lanes
- Deaths before major objectives while side-laning

### 6.4 Feedback Card Format

The service should produce simple and specific feedback cards.

Example:

> Your laning phase is strong, but you often lose your advantage before objectives.
> In your recent 20 games, your 10-minute CS difference is +8.4 on average.
> However, you died within 60 seconds before dragon in 37% of games.
> In your next games, push the wave and recall 1 minute before dragon, then help your jungler secure vision.

## 7. Database Design Draft

Main tables:

### riot_account

- id
- puuid
- game_name
- tag_line
- region
- created_at
- updated_at

### match

- id
- match_id
- game_version
- queue_id
- game_start_time
- game_duration
- winning_team_id
- created_at

### match_participant

- id
- match_id
- puuid
- participant_id
- team_id
- champion_id
- champion_name
- individual_position
- win
- kills
- deaths
- assists
- total_damage_dealt_to_champions
- total_damage_taken
- gold_earned
- total_minions_killed
- neutral_minions_killed
- vision_score
- wards_placed
- wards_killed

### timeline_frame

- id
- match_id
- minute
- participant_id
- current_gold
- total_gold
- level
- xp
- minions_killed
- jungle_minions_killed
- position_x
- position_y

### timeline_event

- id
- match_id
- timestamp
- minute
- event_type
- participant_id
- killer_id
- victim_id
- assisting_participant_ids
- monster_type
- building_type
- lane_type
- item_id
- position_x
- position_y

### player_match_phase_metric

- id
- match_id
- puuid
- champion_id
- position
- lane_cs_diff_10
- lane_gold_diff_10
- lane_xp_diff_10
- death_before_14
- objective_death_count
- teamfight_participation
- side_death_count
- lane_score
- objective_score
- teamfight_score
- side_score

## 8. API Endpoints Draft

Backend API endpoints:

- POST /api/accounts/search/
- GET /api/accounts/{account_id}/summary/
- GET /api/accounts/{account_id}/champions/
- GET /api/accounts/{account_id}/feedback/
- GET /api/accounts/{account_id}/matches/
- GET /api/champions/matchups/
- GET /api/reports/patch-analysis/

## 9. Power BI Dashboard Plan

Dashboard 1: Player Summary
- Recent win rate
- Champion performance
- Phase score radar chart
- Recent match table
- Improvement priority cards

Dashboard 2: Champion Matchup
- My champion vs opponent champion heatmap
- Win rate by matchup
- 10-minute gold difference by matchup
- CS difference by matchup

Dashboard 3: Patch Analysis
- Champion win rate before/after patch
- Pick rate before/after patch
- Ban rate before/after patch
- Balance change impact

## 10. Development Order

Phase 1:
- Understand Riot API response structure
- Fetch PUUID from Riot ID
- Fetch recent match IDs
- Fetch match detail JSON
- Fetch timeline JSON

Phase 2:
- Design PostgreSQL schema
- Save accounts, matches, participants, timeline frames, timeline events
- Prevent duplicate match insertion

Phase 3:
- Create SQL queries and views for analysis metrics
- Calculate lane, objective, teamfight, and side-lane metrics

Phase 4:
- Build Django REST API
- Return summary, champion, matchup, and feedback data

Phase 5:
- Build Vue frontend
- Display insight cards and charts

Phase 6:
- Connect PostgreSQL to Power BI
- Build BI dashboards

Phase 7:
- Write README
- Add ERD
- Add data pipeline diagram
- Add SQL query examples
- Add Power BI dashboard screenshots
- Add example insights
- Add limitations and future improvements

## 11. Important Constraints

- Do not hardcode Riot API keys.
- Use environment variables for secrets.
- Do not build everything at once.
- Prioritize MVP first.
- Prefer understandable rule-based analysis before complex machine learning.
- Every recommendation should be explainable.
- Use SQL actively because this project is for a data analyst portfolio.
- Store raw data and processed metrics separately where possible.