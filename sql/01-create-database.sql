-- Topic 8, script 1: create the database.
-- Run it with "Execute SQL Script" (the whole file), not "Execute SQL Statement".
-- Safe to run again: it only creates the database if it doesn't exist yet.

IF DB_ID(N'ProjectHubDb') IS NULL CREATE DATABASE ProjectHubDb;
GO

-- Check: the new database should be in this list (one row: ProjectHubDb).
SELECT name, create_date FROM sys.databases WHERE name = N'ProjectHubDb';
