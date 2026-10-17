using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace ProjectHub.Api.Data;

// SQL Server's DATETIME2 stores a date and time but NOT its "Kind" (UTC / Local / Unspecified).
// So EF Core reads every DateTime back as Kind = Unspecified, and JSON would then print "2026-09-01T09:00:00"
// without the "Z" -- the client can't tell it's UTC. We store UTC only (Topic 1 rule), so:
//   to the database:   Local times are converted to UTC; UTC and Unspecified are stored as they are (assumed UTC)
//   from the database: mark the value as UTC
public class UtcDateTimeConverter() : ValueConverter<DateTime, DateTime>(
    toDatabase => toDatabase.Kind == DateTimeKind.Local ? toDatabase.ToUniversalTime() : toDatabase,
    fromDatabase => DateTime.SpecifyKind(fromDatabase, DateTimeKind.Utc));
