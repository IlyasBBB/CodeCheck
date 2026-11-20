# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- Origin: group project of the TDLog course (software development techniques), École Centrale Casablanca, 2024-2025, team of seven.
- Audience of this version: a recruiter or engineer opening the repository and running it locally, plus students who want to practise Python.

## Product Purpose

A Django platform to practise Python: a new member takes an initial test (10 graded questions), gets a level, then solves problems grouped by domain. Each submission runs against test cases on the server; solving a problem earns points (fewer when the time limit is exceeded), giving up costs 20 points, and points drive the level.

## Capabilities and Constraints

- Code runs in a subprocess with a 5-second timeout and resource limits; it is not a sandbox, so the app must not be exposed publicly as is.
- Domains: Basic Programming, Data Structures, Algorithms, String Manipulation, Mathematics (sample data command).
- Templates: Django, CodeMirror 5 for the editor, SweetAlert2 for dialogs. Interface language: English.

## Evidence on Hand

- Code, tests and sample data only. No users, no community, no achievements system: never claim them.

## Product Principles

1. The problem, the editor and the test results are visible together.
2. Levels and points are shown as they are computed, nothing decorative.
3. Every claim on the home page exists in the code.
