# Database Best Practices

**Purpose**: Conventions and patterns for SQLite database design, implementation, and repository layers.
**Status**: 🟢 Active
**Tags**: #architecture, #database, #standards

---

## Quick Reference

| # | Rule | Summary |
|---|---|---|
| [1](#-naming-conventions) | **Naming Conventions** | Objects = Singular, Tables/Repos = Plural. |
| [2](#-architecture-layers) | **Architecture** | Record → Repository → Manager. |
| [3](#-database-schema-rules) | **Schema** | Use Junction Tables for M:N relationships. |
| [4](#-data-flow-patterns) | **Data Flow** | Manager calls Repo, Repo returns Typed Objects. |
| [5](#-performance-best-practices) | **Performance** | Use Transactions for bulk inserts. |
| [6](#️-data-integrity-rules) | **Integrity** | Validate foreign keys, use Soft Deletes. |
| [7](#-type-safe-enums) | **Enums** | Store as Int, use Enum in code. |

---

## 📋 Naming Conventions

### Core Principle: Object is SINGULAR, Table is PLURAL

**Strict Rule** - No exceptions:
- **Database TABLE**: Plural (e.g., `Puzzles`, `PuzzleLists`, `GameStats`)
- **Record/Object CLASS**: Singular (e.g., `Puzzle`, `PuzzleList`, `GameStat`)
- **Repository CLASS**: Plural (e.g., `PuzzlesRepository`, `PuzzleListsRepository`, `GameStatsRepository`)

### Reasoning
- **Tables** hold multiple records → plural name
- **Classes** represent a single instance → singular name
- **Repositories** manage collections of objects → plural name

### Examples

✅ **CORRECT:**
```csharp
[Table("Puzzles")]
public class Puzzle { }  // Single puzzle record

public class PuzzlesRepository { }  // Manages multiple puzzles
```

❌ **INCORRECT:**
```csharp
[Table("Puzzle")]
public class PuzzleRecord { }  // Table should be plural

public class PuzzleRepository { }  // Should indicate plurality
```

---

## 🏗️ Architecture Layers

### Layer 1: Record Classes (Assets/Scripts/Core/)
**Purpose**: Represent a single database row  
**Naming**: Singular (e.g., `Puzzle.cs`, `PuzzleList.cs`, `GameStat.cs`)  
**Location**: `Assets/Scripts/Core/`  
**Attributes**: SQLite.NET attributes (`[Table]`, `[PrimaryKey]`, `[Indexed]`, etc.)

**Example**:
```csharp
[Table("Puzzles")]
public class Puzzle
{
    [PrimaryKey, AutoIncrement]
    public int Id { get; set; }
    
    [NotNull]
    public string PuzzleString { get; set; }
    
    [Indexed]
    public DifficultyLevel Difficulty { get; set; }
}
```

### Layer 2: Repository Classes (Assets/Scripts/Database/)
**Purpose**: Data access layer for a single table or related tables  
**Naming**: Plural (e.g., `PuzzlesRepository.cs`, `PuzzleListsRepository.cs`)  
**Location**: `Assets/Scripts/Database/`  
**Responsibility**: CRUD operations, queries, transactions

**Pattern**:
```csharp
public class PuzzlesRepository
{
    private readonly SQLiteAsyncConnection _db;
    
    public PuzzlesRepository(SQLiteAsyncConnection db)
    {
        _db = db;
    }
    
    public async Task<Puzzle> GetAsync(int id) { }
    public async Task<List<Puzzle>> GetAllAsync() { }
    public async Task InsertAsync(Puzzle puzzle) { }
    // ... more methods ...
}
```

### Layer 3: Manager Classes (Assets/Scripts/Managers/)
**Purpose**: Business logic, orchestration, game flow  
**Naming**: Purpose-specific (e.g., `GameManager.cs`, `DatabaseManager.cs`)  
**Location**: `Assets/Scripts/Managers/`  
**Responsibility**: Use repositories, implement game rules, manage state

---

## 🗄️ Database Schema Rules

### Junction Tables (Many-to-Many Relationships)
When you need multiple entities of type A to link with multiple entities of type B:

**Pattern**: `[EntityA][EntityB]` or `[EntityA]Members`

**Example**: `PuzzleListMember.cs`
```csharp
[Table("PuzzleListMembers")]
public class PuzzleListMember
{
    [PrimaryKey, AutoIncrement]
    public int Id { get; set; }
    
    [NotNull, Indexed]
    public int ListId { get; set; }        // FK to PuzzleLists
    
    [NotNull, Indexed]
    public int PuzzleId { get; set; }      // FK to Puzzles
    
    public int? OrderInList { get; set; }  // Additional data
}
```

**Why this matters**: Same puzzle can be in multiple lists!

### Repository Responsibility for Junction Tables
The repository for the primary table should handle its junction relationships:

```csharp
public class PuzzleListsRepository
{
    // Handles both PuzzleList AND PuzzleListMember operations
    public async Task AddMultiplePuzzlesToListAsync(int listId, List<int> puzzleIds) { }
    public async Task GetPuzzlesInListAsync(int listId) { }
    public async Task RemovePuzzleFromListAsync(int listId, int puzzleId) { }
}
```

---

## 📝 File Structure

```
Assets/
├── Scripts/
│   ├── Core/                          ← Record classes
│   │   ├── Puzzle.cs                  (singular, table: Puzzles)
│   │   ├── PuzzleList.cs              (singular, table: PuzzleLists)
│   │   ├── GameStat.cs                (singular, table: GameStats)
│   │   ├── DifficultyLevel.cs         (enum)
│   │   ├── ListType.cs                (enum)
│   │   └── ...
│   │
│   ├── Database/                      ← Repository classes
│   │   ├── PuzzlesRepository.cs       (plural, handles Puzzle records)
│   │   ├── PuzzleListsRepository.cs   (plural, handles PuzzleList + PuzzleListMember)
│   │   └── GameStatsRepository.cs     (plural, handles GameStat records)
│   │
│   └── Managers/                      ← Business logic
│       ├── DatabaseManager.cs         (initialization, lifecycle)
│       ├── GameManager.cs             (game flow)
│       └── ...
│
└── Resources/
    ├── PuzzleLists/
    │   └── to_load.json               (manifest: files to load)
    └── Puzzles/
        └── 1-development_pack-1-to-10.json
```

---

## 🔄 Data Flow Patterns

### Pattern 1: Creating Records
```csharp
// 1. Create record instance (singular class)
var puzzle = new Puzzle
{
    PuzzleString = "1..5...",
    SolutionString = "123456789...",
    Difficulty = DifficultyLevel.Medium,
    DifficultyScore = 4.5f
};

// 2. Use repository (plural class) to save
await PuzzlesRepository.InsertAsync(puzzle);

// 3. Repository handles database transaction
```

### Pattern 2: Querying Records
```csharp
// 1. Get repository from manager
var puzzleRepo = DatabaseManager.Instance.PuzzlesRepository;

// 2. Use typed queries
var mediumPuzzles = await puzzleRepo.GetByDifficultyAsync(DifficultyLevel.Medium);

// 3. Repository returns typed list
foreach (var puzzle in mediumPuzzles) { }
```

### Pattern 3: Many-to-Many Relationships
```csharp
// Use junction repository (PuzzleListsRepository)
var listRepo = DatabaseManager.Instance.PuzzleListsRepository;

// Add puzzles to a list (handles PuzzleListMember)
await listRepo.AddMultiplePuzzlesToListAsync(listId: 1, puzzleIds: new[] { 1, 2, 3 });

// Query puzzles in a list
var puzzlesInList = await listRepo.GetPuzzlesInListAsync(listId: 1);
```

---

## ⚡ Performance Best Practices

### Transactions for Bulk Operations
When importing many puzzles, use transactions:

```csharp
// In PuzzlesRepository:
public async Task InsertMultipleAsync(List<Puzzle> puzzles)
{
    using (await _db.BeginTransactionAsync())
    {
        try
        {
            foreach (var puzzle in puzzles)
            {
                await _db.InsertAsync(puzzle);
            }
            await _db.CommitAsync();
        }
        catch
        {
            await _db.RollbackAsync();
            throw;
        }
    }
}
```

### PRAGMA Settings for SQLite
Set these during initialization:

```csharp
await _db.ExecuteAsync("PRAGMA journal_mode=WAL");    // Write-Ahead Logging
await _db.ExecuteAsync("PRAGMA synchronous=NORMAL");  // Balance speed/safety
await _db.ExecuteAsync("PRAGMA cache_size=10000");    // Increase cache
```

### Indexing Strategy
- Index foreign keys (for joins)
- Index frequently queried columns
- Index used in WHERE clauses

---

## 🛡️ Data Integrity Rules

### Soft Deletes vs Hard Deletes
Use `IsActive` flags instead of deleting:

```csharp
[NotNull]
public int IsActive { get; set; } = 1;  // 1 = active, 0 = inactive

// Query only active records
var activeLists = await listRepo.GetAsync(x => x.IsActive == 1);
```

**Benefit**: Data recovery, audit trails, statistics consistency

### Foreign Key Constraints
Always validate foreign keys before inserting:

```csharp
// Before adding puzzle to list
var puzzle = await puzzleRepo.GetAsync(puzzleId);
if (puzzle == null) throw new InvalidOperationException("Puzzle not found");

var list = await listRepo.GetAsync(listId);
if (list == null) throw new InvalidOperationException("List not found");

// Then proceed with insertion
```

---

## 📚 Type-Safe Enums

### When to Use Enums
Store as integers in database, use enums in code:

```csharp
public enum DifficultyLevel
{
    Easy = 0,
    Medium = 1,
    Hard = 2,
    Expert = 3
}

public enum ListType
{
    Featured = 0,
    Daily = 1,
    UserCreated = 2,
    Tournament = 3,
    Imported = 4
}
```

**Benefits**:
- Type safety in C# code
- Efficient storage (integers in DB)
- Easy to extend
- Self-documenting

---

## 🧪 Testing Guidelines

### Repository Testing
Test each repository's CRUD and query methods:

```csharp
[Test]
public async Task GetByIdReturnsCorrectRecord()
{
    var puzzle = new Puzzle { /* ... */ };
    int id = await repo.InsertAsync(puzzle);
    
    var retrieved = await repo.GetAsync(id);
    Assert.AreEqual(id, retrieved.Id);
}
```

### Junction Table Testing
Test many-to-many relationships:

```csharp
[Test]
public async Task AddingMultiplePuzzlesToListWorks()
{
    int listId = await listRepo.InsertAsync(new PuzzleList { /* ... */ });
    var puzzleIds = new[] { 1, 2, 3 };
    
    await listRepo.AddMultiplePuzzlesToListAsync(listId, puzzleIds);
    
    var puzzles = await listRepo.GetPuzzlesInListAsync(listId);
    Assert.AreEqual(3, puzzles.Count);
}
```

---

## 📋 Quick Checklist

- [ ] Record class is **singular** (`Puzzle`, not `PuzzleRecord`)
- [ ] Table attribute is **plural** (`[Table("Puzzles")]`)
- [ ] Repository class is **plural** (`PuzzlesRepository`)
- [ ] Repository location is `Assets/Scripts/Database/`
- [ ] Record class location is `Assets/Scripts/Core/`
- [ ] Foreign keys are indexed
- [ ] Transactions used for bulk inserts
- [ ] Soft deletes via `IsActive` field
- [ ] Type-safe enums for categorical data
- [ ] All async methods use `await` pattern

---

**Last Updated**: December 9, 2025  
**Maintained By**: Development Team  
**Status**: Active – Reference for all future database work

