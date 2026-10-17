using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

#pragma warning disable CA1814 // Prefer jagged arrays over multidimensional

namespace ProjectHub.Api.Data.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Projects",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    Name = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: false),
                    Description = table.Column<string>(type: "nvarchar(1000)", maxLength: 1000, nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "datetime2", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Projects", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Tasks",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    ProjectId = table.Column<int>(type: "int", nullable: false),
                    Title = table.Column<string>(type: "nvarchar(200)", maxLength: 200, nullable: false),
                    Status = table.Column<int>(type: "int", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "datetime2", nullable: false),
                    DueDate = table.Column<DateTime>(type: "datetime2", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Tasks", x => x.Id);
                    table.CheckConstraint("CK_Tasks_Status", "[Status] IN (0, 1, 2)");
                    table.ForeignKey(
                        name: "FK_Tasks_Projects_ProjectId",
                        column: x => x.ProjectId,
                        principalTable: "Projects",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.InsertData(
                table: "Projects",
                columns: new[] { "Id", "CreatedAt", "Description", "Name" },
                values: new object[,]
                {
                    { 1, new DateTime(2026, 9, 1, 9, 0, 0, 0, DateTimeKind.Utc), "New marketing site", "Website redesign" },
                    { 2, new DateTime(2026, 9, 5, 9, 0, 0, 0, DateTimeKind.Utc), null, "Mobile app" },
                    { 3, new DateTime(2026, 9, 9, 9, 0, 0, 0, DateTimeKind.Utc), "Admin dashboards", "Internal tools" }
                });

            migrationBuilder.InsertData(
                table: "Tasks",
                columns: new[] { "Id", "CreatedAt", "DueDate", "ProjectId", "Status", "Title" },
                values: new object[,]
                {
                    { 1, new DateTime(2026, 9, 2, 9, 0, 0, 0, DateTimeKind.Utc), new DateTime(2026, 9, 10, 17, 0, 0, 0, DateTimeKind.Utc), 1, 2, "Design mockups" },
                    { 2, new DateTime(2026, 9, 4, 9, 0, 0, 0, DateTimeKind.Utc), new DateTime(2026, 10, 1, 17, 0, 0, 0, DateTimeKind.Utc), 1, 1, "Build landing page" },
                    { 3, new DateTime(2026, 9, 6, 9, 0, 0, 0, DateTimeKind.Utc), new DateTime(2027, 1, 15, 17, 0, 0, 0, DateTimeKind.Utc), 1, 0, "SEO audit" },
                    { 4, new DateTime(2026, 9, 3, 9, 0, 0, 0, DateTimeKind.Utc), new DateTime(2026, 9, 5, 17, 0, 0, 0, DateTimeKind.Utc), 1, 2, "Write copy" },
                    { 5, new DateTime(2026, 9, 5, 9, 0, 0, 0, DateTimeKind.Utc), new DateTime(2026, 9, 30, 17, 0, 0, 0, DateTimeKind.Utc), 2, 1, "Login screen" },
                    { 6, new DateTime(2026, 9, 7, 9, 0, 0, 0, DateTimeKind.Utc), null, 2, 0, "Push notifications" },
                    { 7, new DateTime(2026, 9, 8, 9, 0, 0, 0, DateTimeKind.Utc), new DateTime(2026, 10, 10, 17, 0, 0, 0, DateTimeKind.Utc), 2, 0, "App store listing" }
                });

            migrationBuilder.CreateIndex(
                name: "IX_Projects_Name",
                table: "Projects",
                column: "Name",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Tasks_ProjectId",
                table: "Tasks",
                column: "ProjectId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Tasks");

            migrationBuilder.DropTable(
                name: "Projects");
        }
    }
}
