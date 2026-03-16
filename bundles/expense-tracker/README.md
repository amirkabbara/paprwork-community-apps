# Expense Tracker

Track daily expenses with category breakdowns and a visual chart.

## Features

- Add expenses with amount, category, and description
- View expense history sorted by date
- Category breakdown with a pie chart
- Delete individual expenses
- Persistent storage via Paprwork's built-in DB API

## Categories

Food, Transport, Entertainment, Shopping, Bills, Health, Other

## Data Storage

Uses the Papr DB API (`/api/db/exec`, `/api/db/query`, `/api/db/write`) for local SQLite storage. Data persists across sessions and stays on your machine.
