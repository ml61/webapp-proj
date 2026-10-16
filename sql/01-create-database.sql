-- Topic 8, script 1: create the database.
-- Safe to run again: it only creates the database if it doesn't exist yet.
-- Run while connected to the server (database "master" is fine).

IF DB_ID(N'ProjectHubDb') IS NULL
    CREATE DATABASE ProjectHubDb;
GO

-- Check: the new database should be in this list.
SELECT name, create_date FROM sys.databases WHERE name = N'ProjectHubDb';
