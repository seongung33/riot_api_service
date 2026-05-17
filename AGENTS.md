# AGENTS.md

## Project Overview

This repository is for a League of Legends player insight analysis service.

The goal is to use Riot API data to analyze player behavior and provide actionable feedback through a Django backend, Vue frontend, PostgreSQL database, and Power BI reports.

Before implementing features, read:

- docs/PROJECT_BRIEF.md

## Working Rules

- Do not build too many features at once.
- Always work in small, reviewable steps.
- Prefer simple, explainable analysis logic first.
- Do not introduce machine learning unless the baseline rule-based or SQL-based analysis is already implemented.
- Do not hardcode API keys or secrets.
- Use environment variables for Riot API keys and database credentials.
- Keep raw Riot API data separate from processed analysis metrics when possible.
- Use PostgreSQL-friendly schema and SQL.
- Add comments where data logic is non-obvious.
- When creating analysis metrics, explain the reasoning behind the metric.

## Backend Rules

Backend stack:

- Django
- Django REST Framework
- PostgreSQL

Backend directory:

- backend/

Expected backend responsibilities:

- Riot API integration
- Data collection
- Data normalization
- Database persistence
- Analysis API endpoints
- Feedback generation logic

Do not make frontend logic responsible for analysis.  
The frontend should mainly display API results.

## Frontend Rules

Frontend stack:

- Vue.js

Frontend directory:

- frontend/

Expected frontend responsibilities:

- Riot ID search form
- Player summary display
- Champion insight display
- Feedback card display
- Simple charts where useful

Keep UI simple and clear.  
Prioritize understandability over visual complexity.

## Data Analysis Rules

Use SQL and Python for analysis.

Important analysis categories:

- Basic player performance
- Champion performance
- Champion matchup performance
- Laning phase metrics
- Objective phase metrics
- Teamfight metrics
- Side-lane metrics
- Patch-level champion performance

Recommended output format:

- Clear metric
- Interpretation
- Actionable recommendation

Example:

"Your 10-minute CS difference is positive, but your objective-before-death rate is high. Focus on recalling and setting vision 60 seconds before dragon."

## Done Criteria

A task is done only when:

- The implementation matches docs/PROJECT_BRIEF.md
- Code is understandable
- Secrets are not exposed
- Database changes are documented
- API responses are testable
- The user can understand what changed
- If possible, run relevant tests or commands and report the result

## Communication Style

When explaining changes, use Korean.

Explain:

1. What was changed
2. Why it was changed
3. How to run or test it
4. What the next recommended step is